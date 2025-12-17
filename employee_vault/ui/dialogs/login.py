"""
Login Dialog
"""

import os
import json
import time
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import *
from employee_vault.config import _verify_pwd, _hash_pwd, _needs_password_rehash, _check_pwd, _verify_pin, _hash_pin, validate_pin_strength, PIN_MIN_LENGTH, PIN_MAX_LENGTH
from employee_vault.database import DB
from employee_vault.validators import *
from employee_vault.utils import *
from employee_vault.models import *
from employee_vault.ui.widgets import *
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase, FloatingLabelLineEdit, GlowLineEdit, AnimatedLoginCard

# v5.1: Load theme colors for login card
def _load_login_theme_colors():
    """Load theme colors from settings for login card theming"""
    try:
        from employee_vault.app_config import MODERN_THEMES
        settings_file = os.path.join(os.path.dirname(DB_FILE), "settings.json")
        theme_name = "default"
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                theme_name = settings.get("theme_color", "default")
        
        theme = MODERN_THEMES.get(theme_name, MODERN_THEMES.get("default", {}))
        return theme
    except Exception as e:
        logging.warning(f"Could not load theme for login: {e}")
        return None


# Phase 2.1: LoginWorker - Move expensive auth operations off UI thread
class LoginWorker(QThread):
    """Background thread for authentication to prevent UI freeze"""
    login_success = Signal(dict)  # user data
    login_failed = Signal(str)     # error message
    migration_required = Signal(str)  # username for PIN setup

    def __init__(self, db, username, pin):
        super().__init__()
        self.db = db
        self.username = username
        self.pin = pin

    def run(self):
        """Execute authentication in background thread"""
        try:
            # All blocking operations run here (off UI thread)
            # Auto-reset check
            if self.db.auto_reset_pin_on_lockout(self.username, max_attempts=5):
                try:
                    self.db.log_security_event(
                        event_type="PIN_AUTO_RESET",
                        username=self.username,
                        details="PIN automatically reset due to too many failed attempts",
                        severity="WARNING"
                    )
                except Exception:
                    pass
                self.login_failed.emit("🔄 Too many failed attempts. Your PIN has been reset.")
                return

            # Get user (blocking DB query)
            user = self.db.get_user(self.username)

            if not user:
                # Record failed attempt
                self.db.record_login_attempt(self.username, success=False)
                self._log_failed_attempt()
                self.login_failed.emit("❌ Invalid username or PIN")
                return

            # Check PIN authentication (bcrypt - expensive 200-500ms operation)
            if "pin" in user and user["pin"] and _verify_pin(self.pin, user["pin"]):
                # Success - clear failed attempts
                self.db.clear_login_attempts(user["username"])
                self.db.record_login_attempt(user["username"], success=True)

                try:
                    self.db.log_security_event(
                        event_type="LOGIN_SUCCESS",
                        username=user["username"],
                        details="User logged in successfully via PIN",
                        severity="INFO"
                    )
                except Exception:
                    pass

                self.login_success.emit(user)
                return

            # MIGRATION SUPPORT: Try password authentication
            elif "password" in user and user["password"] and (not ("pin" in user) or not user["pin"]):
                if _verify_pwd(self.pin, user["password"]):
                    self.migration_required.emit(user["username"])
                    return

            # Failed authentication
            self.db.record_login_attempt(user["username"], success=False)
            self._log_failed_attempt()

            # Get remaining attempts
            failed_count = self.db.get_recent_failed_attempts(self.username)
            remaining = 5 - failed_count

            if remaining <= 2 and remaining > 0:
                self.login_failed.emit(f"❌ Invalid credentials. {remaining} attempt(s) remaining")
            elif remaining <= 0:
                self.login_failed.emit("❌ Invalid credentials. Account will be locked")
            else:
                self.login_failed.emit("❌ Invalid username or PIN")

        except Exception as e:
            logging.error(f"Login worker error: {e}")
            self.login_failed.emit(f"Login error: {str(e)}")

    def _log_failed_attempt(self):
        """Log failed login attempt"""
        try:
            self.db.log_action(
                username=self.username,
                action="LOGIN_FAILED",
                table_name="users",
                details=f"Failed login attempt for username: {self.username}"
            )
            self.db.log_security_event(
                event_type="LOGIN_FAILED",
                username=self.username,
                details="Failed login attempt - invalid credentials",
                severity="WARNING"
            )
        except:
            pass


class LoginDialog(QDialog):
    def __init__(self, db, icon=None):
        super().__init__(parent=None)
        self.setWindowTitle("Cuddly Employees Information")
        if icon:
            self.setWindowIcon(icon)
        self.db = db

        # Make dialog frameless for custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # v5.1: Load theme colors for the login card
        self._theme_colors = _load_login_theme_colors()

        # Main layout with dark gradient background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Background container - transparent to show animated login card
        bg_container = QWidget()
        bg_container.setObjectName("bg_container")
        bg_container.setStyleSheet("QWidget#bg_container { background: transparent; }")

        container_layout = QVBoxLayout(bg_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar is now inside the animated login card
        # Make the card itself draggable
        self.dragging = False
        self.drag_position = None

        # Create animated login card (contains title bar, close button, and form)
        # v5.1: Pass theme colors for themed appearance
        self.card = AnimatedLoginCard(theme_colors=self._theme_colors)

        # Make the card draggable by installing mouse event filter on its window title area
        # We'll install event handlers after the card is created

        # Center the card in the dialog
        container_layout.addWidget(
            self.card,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # Add bottom row with forgot password and create account buttons
        # External buttons removed - using card's internal links instead

        main_layout.addWidget(bg_container)

        # v2.0: Use event filter for dragging instead of overriding card methods
        # This preserves the card's native hover expand/collapse behavior
        self.card.installEventFilter(self)

        # Wire up card events
        self.card.login_btn.clicked.connect(self.attempt_login)
        # Note: show_password_check is now a toggle switch, visibility is handled in the card
        self.card.password_edit.returnPressed.connect(self.attempt_login)
        self.card.username_edit.returnPressed.connect(self.card.password_edit.setFocus)
        
        # Dynamic PIN validation: restrict to numbers if user has PIN
        self.card.username_edit.textChanged.connect(self._check_user_pin_status)
        self.card.closeRequested.connect(self.reject)  # Wire up close button

        # Wire up card's action buttons to dialog methods (forgot/create)
        # The AnimatedLoginCard now exposes QPushButton objects instead of rich-text labels
        # for the "Forgot Password" and "Create Account" actions.  Connect their clicked
        # signals directly to the appropriate handlers on this dialog.
        try:
            self.card.forgot_btn.clicked.connect(lambda: self._forgot_password())
        except AttributeError:
            # Fallback to legacy label if still present
            if hasattr(self.card, 'forgot_label'):
                self.card.forgot_label.linkActivated.connect(lambda: self._forgot_password())
        try:
            self.card.signup_btn.clicked.connect(lambda: self.create_account())
        except AttributeError:
            # Fallback to legacy label if still present
            if hasattr(self.card, 'signup_label'):
                self.card.signup_label.linkActivated.connect(lambda: self.create_account())

        # Wire up card size changes to dialog resizing
        self.card.sizeChanged.connect(self._on_card_size_changed)

        # Map card fields to dialog properties for compatibility
        self.username = self.card.username_edit
        self.password = self.card.password_edit
        self.show_password_check = self.card.show_password_check
        
        # v5.3: Accessibility attributes for screen readers
        self.card.username_edit.setAccessibleName("Username")
        self.card.username_edit.setAccessibleDescription("Enter your username to log in")
        self.card.password_edit.setAccessibleName("PIN or Password")
        self.card.password_edit.setAccessibleDescription("Enter your PIN or password")
        self.card.login_btn.setAccessibleName("Login Button")
        self.card.login_btn.setAccessibleDescription("Click to log in to the application")

        # Set initial focus on username field
        self.card.username_edit.setFocus()

        # Set explicit tab order for keyboard navigation
        self.setTabOrder(self.card.username_edit, self.card.password_edit)
        self.setTabOrder(self.card.password_edit, self.card.show_password_check)
        self.setTabOrder(self.card.show_password_check, self.card.login_btn)

        # Set initial dialog size - optimized for COLLAPSED card (with padding)
        # Card: 300x110, Dialog needs padding (60 left + 60 right = 120, 40 top + 60 bottom = 100)
        self.resize(420, 210)  # 300+120=420, 110+100=210

        # Center on screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def _on_card_size_changed(self, card_size):
        """Resize dialog when card expands/collapses"""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve

        # Calculate dialog size based on card size + padding
        # Padding: 60 left + 60 right = 120, 40 top + 60 bottom = 100
        new_width = card_size.width() + 120
        new_height = card_size.height() + 100

        # Animate dialog resize
        self.resize_anim = QPropertyAnimation(self, b"size")
        self.resize_anim.setDuration(180)  # Match card animation speed
        self.resize_anim.setStartValue(self.size())
        self.resize_anim.setEndValue(QSize(new_width, new_height))
        self.resize_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.resize_anim.start()

        # Keep dialog centered during resize
        screen = QApplication.primaryScreen().availableGeometry()
        def update_center():
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        self.resize_anim.valueChanged.connect(update_center)

    def eventFilter(self, obj, event):
        """Event filter for card dragging - preserves card's hover behavior"""
        if obj == self.card:
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Only allow dragging from the top 60px (window title area)
                    if event.position().y() < 60:
                        self.dragging = True
                        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                        return True  # Consume event for dragging
            elif event.type() == event.Type.MouseMove:
                if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
                    self.move(event.globalPosition().toPoint() - self.drag_position)
                    return True  # Consume event for dragging
            elif event.type() == event.Type.MouseButtonRelease:
                if self.dragging:
                    self.dragging = False
                    return True  # Consume event
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle ESC key to close dialog"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _forgot_password(self):
        """Handle forgot password - with security questions"""
        # v4.4.1: Use quick fade animation for this dialog
        from employee_vault.ui.widgets import QuickAnimatedDialog
        dialog = QuickAnimatedDialog(self, animation_style="fade")
        dialog.setWindowTitle("🔑 Reset Password")
        dialog.resize(450, 300)

        # Set dialog stylesheet for transparent labels
        dialog.setStyleSheet("""
            QLabel {
                background: transparent;
                color: rgba(255, 255, 255, 0.9);
            }
        """)

        layout = QVBoxLayout(dialog)

        # Header
        header = QLabel("<h2>🔑 Password Reset</h2>")
        header.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(header)

        # Instructions
        info = QLabel("Enter your username to begin the password reset process.")
        info.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.8);")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Username field with neumorphic gradient styling
        form = QFormLayout()
        username_field = NeumorphicGradientLineEdit("Enter your username")
        form.addRow("", username_field)
        layout.addLayout(form)

        # Result label
        result_label = QLabel("")
        result_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9);")
        result_label.setWordWrap(True)
        layout.addWidget(result_label)

        # Buttons - Phase 3: iOS frosted glass styling
        btn_layout = QHBoxLayout()
        next_btn = ModernAnimatedButton("Next →")
        next_btn.setEnabled(False)
        next_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(76, 175, 80, 0.3),
                                           stop:1 rgba(56, 142, 60, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(76, 175, 80, 0.4),
                                           stop:1 rgba(56, 142, 60, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.08),
                                           stop:0.5 rgba(158, 158, 158, 0.2),
                                           stop:1 rgba(97, 97, 97, 0.4));
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        setup_questions_btn = ModernAnimatedButton("📝 Set Up Security Questions")
        setup_questions_btn.setVisible(False)
        setup_questions_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(33, 150, 243, 0.3),
                                           stop:1 rgba(25, 118, 210, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(33, 150, 243, 0.4),
                                           stop:1 rgba(25, 118, 210, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        close_btn = ModernAnimatedButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(158, 158, 158, 0.3),
                                           stop:1 rgba(97, 97, 97, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(158, 158, 158, 0.4),
                                           stop:1 rgba(97, 97, 97, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        btn_layout.addStretch()
        btn_layout.addWidget(setup_questions_btn)
        btn_layout.addWidget(next_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        current_username = None

        def check_account():
            nonlocal current_username
            username = username_field.text().strip()
            if not username:
                result_label.setText("⚠️ Please enter a username")
                result_label.setStyleSheet("color: #ff9800;")
                next_btn.setEnabled(False)
                setup_questions_btn.setVisible(False)
                return

            user = self.db.get_user(username)
            if not user:
                result_label.setText("✗ Account not found")
                result_label.setStyleSheet("color: #f44336;")
                next_btn.setEnabled(False)
                setup_questions_btn.setVisible(False)
                return

            # Check if user has security questions
            if self.db.has_security_questions(username):
                result_label.setText(f"✓ Account found: <b>{user['name']}</b><br>Security questions available ✓<br>Click 'Next' to answer security questions.")
                result_label.setStyleSheet("color: #4CAF50;")
                next_btn.setEnabled(True)
                setup_questions_btn.setVisible(False)
                current_username = username
            else:
                result_label.setText(f"✓ Account found: <b>{user['name']}</b><br><br>⚠️ No security questions set up yet.<br>Click 'Set Up Security Questions' below to create them now!")
                result_label.setStyleSheet("color: #ff9800;")
                next_btn.setEnabled(False)
                setup_questions_btn.setVisible(True)
                current_username = username

        def proceed_to_questions():
            if current_username:
                dialog.accept()
                self._verify_security_questions(current_username)

        def setup_security_questions():
            """Allow user to set up security questions during forgot password flow"""
            if current_username:
                dialog.accept()
                self._setup_security_questions_for_recovery(current_username)

        username_field.textChanged.connect(lambda: next_btn.setEnabled(False))
        username_field.returnPressed.connect(check_account)
        next_btn.clicked.connect(proceed_to_questions)
        setup_questions_btn.clicked.connect(setup_security_questions)
        close_btn.clicked.connect(dialog.accept)

        # Add a check button - Phase 3: iOS frosted glass
        check_btn = ModernAnimatedButton("Check Account")
        check_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(33, 150, 243, 0.3),
                                           stop:1 rgba(25, 118, 210, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(33, 150, 243, 0.4),
                                           stop:1 rgba(25, 118, 210, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        btn_layout.insertWidget(1, check_btn)
        check_btn.clicked.connect(check_account)

        dialog.exec()

    def _forgot_password(self):
        """Handle forgot PIN - self-service PIN reset"""
        from employee_vault.ui.widgets import SmoothAnimatedDialog
        
        dlg = SmoothAnimatedDialog(self, animation_style="fade")
        dlg.setWindowTitle("🔑 Reset PIN")
        dlg.resize(450, 280)
        
        layout = QVBoxLayout(dlg)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🔑 Reset Your PIN")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info
        info = QLabel("To reset your PIN, please verify your identity:")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        layout.addWidget(info)
        
        # Username with neumorphic gradient styling
        username_edit = NeumorphicGradientLineEdit("Enter your username")
        username_edit.setMinimumHeight(70)
        layout.addWidget(username_edit)
        
        # Error label
        error_label = QLabel("")
        error_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(dlg.reject)
        
        reset_btn = QPushButton("Reset PIN")
        reset_btn.setFixedHeight(40)
        reset_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(reset_btn)
        layout.addLayout(button_layout)
        
        def verify_and_reset():
            username = username_edit.line_edit.text().strip()

            error_label.setText("")

            if not username:
                error_label.setText("⚠️ Please enter your username")
                return

            # Check if user exists
            user = self.db.get_user(username)
            if not user:
                error_label.setText("❌ Username not found")
                return

            # User verified - now set new PIN
            dlg.accept()
            self._set_new_pin_dialog(username)

        reset_btn.clicked.connect(verify_and_reset)
        username_edit.returnPressed.connect(verify_and_reset)
        
        dlg.exec()
    
    def _set_new_pin_dialog(self, username):
        """Dialog to set a new PIN after verification"""
        from employee_vault.ui.widgets import SmoothAnimatedDialog
        
        dlg = SmoothAnimatedDialog(self, animation_style="fade")
        dlg.setWindowTitle("Set New PIN")
        dlg.resize(400, 300)
        
        layout = QVBoxLayout(dlg)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("✅ Identity Verified")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info
        info = QLabel("Please set your new PIN:")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        layout.addWidget(info)
        
        # New PIN with neumorphic gradient styling
        pin_edit = NeumorphicGradientPasswordInput("Enter 4-6 digit PIN")
        pin_edit.line_edit.setMaxLength(6)
        pin_edit.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$')))
        pin_edit.setMinimumHeight(70)
        layout.addWidget(pin_edit)

        # Confirm PIN with neumorphic gradient styling
        confirm_edit = NeumorphicGradientPasswordInput("Re-enter PIN")
        confirm_edit.line_edit.setMaxLength(6)
        confirm_edit.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$')))
        confirm_edit.setMinimumHeight(70)
        layout.addWidget(confirm_edit)
        
        # Error label
        error_label = QLabel("")
        error_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(dlg.reject)
        
        save_btn = QPushButton("Save PIN")
        save_btn.setFixedHeight(40)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        def save_new_pin():
            pin = pin_edit.line_edit.text()
            confirm = confirm_edit.line_edit.text()

            error_label.setText("")

            if not pin or not confirm:
                error_label.setText("⚠️ Please fill in both fields")
                return

            if pin != confirm:
                error_label.setText("❌ PINs do not match")
                confirm_edit.line_edit.clear()
                confirm_edit.line_edit.setFocus()
                return

            # Validate PIN strength
            is_valid, errors = validate_pin_strength(pin)
            if not is_valid:
                error_label.setText(f"❌ {errors[0]}")
                pin_edit.line_edit.clear()
                confirm_edit.line_edit.clear()
                pin_edit.line_edit.setFocus()
                return
            
            # Update PIN in database
            try:
                self.db.update_user_pin(username, pin)
                dlg.accept()
                
                QMessageBox.information(
                    self,
                    "PIN Reset Successful",
                    f"Your PIN has been reset successfully!\n\nYou can now log in with your new PIN.",
                    QMessageBox.StandardButton.Ok
                )
                
            except Exception as e:
                error_label.setText(f"❌ Error: {str(e)}")
                logging.error(f"Error resetting PIN: {e}")
        
        save_btn.clicked.connect(save_new_pin)
        confirm_edit.line_edit.returnPressed.connect(save_new_pin)
        
        dlg.exec()

    def _verify_security_questions(self, username):
        """Verify security questions and allow password reset"""
        # v4.4.1: Animated dialog for security questions
        from employee_vault.ui.widgets import AnimatedDialogBase
        dialog = AnimatedDialogBase(self, animation_style="fade")
        dialog.setWindowTitle("🔐 Verify Security Questions")
        dialog.resize(500, 500)

        layout = QVBoxLayout(dialog)

        # Header
        header = QLabel("<h2>🔐 Answer Security Questions</h2>")
        layout.addWidget(header)

        info = QLabel(f"Answer at least <b>2 out of 3</b> questions correctly to reset your password.")
        info.setWordWrap(True)
        info.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(info)

        # Get security questions
        questions = self.db.get_security_questions(username)
        if not questions:
            QMessageBox.warning(
                dialog,
                "Security Questions Not Set",
                "No security questions found for this account.\n\n"
                "You cannot reset your password using security questions.\n"
                "Please contact your administrator for password reset assistance."
            )
            return

        # Create answer fields with neumorphic gradient styling
        form = QVBoxLayout()
        answer_fields = {}

        for question_id, question_text in questions:
            # Question label
            label = QLabel(f"<b>{question_text}</b>")
            label.setWordWrap(True)
            label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-bottom: 5px;")
            form.addWidget(label)

            # Answer field with neumorphic gradient
            answer_field = NeumorphicGradientLineEdit("Enter your answer")
            answer_field.setMinimumHeight(70)
            form.addWidget(answer_field)
            answer_fields[question_id] = answer_field

            # Add spacing
            if question_id < len(questions) - 1:
                spacer = QLabel("")
                spacer.setFixedHeight(15)
                form.addWidget(spacer)

        layout.addLayout(form)

        # Result label
        result_label = QLabel("")
        result_label.setWordWrap(True)
        layout.addWidget(result_label)

        # Buttons - Phase 3: iOS frosted glass
        btn_layout = QHBoxLayout()
        verify_btn = ModernAnimatedButton("✓ Verify Answers")
        verify_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(76, 175, 80, 0.3),
                                           stop:1 rgba(56, 142, 60, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(76, 175, 80, 0.4),
                                           stop:1 rgba(56, 142, 60, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        cancel_btn = ModernAnimatedButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(158, 158, 158, 0.3),
                                           stop:1 rgba(97, 97, 97, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(158, 158, 158, 0.4),
                                           stop:1 rgba(97, 97, 97, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        btn_layout.addStretch()
        btn_layout.addWidget(verify_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def verify_answers():
            # Collect answers
            answers = {qid: field.line_edit.text() for qid, field in answer_fields.items()}

            # Verify
            if self.db.verify_security_answers(username, answers):
                result_label.setText("✓ Verification successful!")
                result_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                dialog.accept()
                self._reset_password_dialog(username)
            else:
                result_label.setText("✗ Verification failed. At least 2 answers must be correct.")
                result_label.setStyleSheet("color: #f44336; font-weight: bold;")

        verify_btn.clicked.connect(verify_answers)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def _reset_password_dialog(self, username):
        """Dialog to set new password after verification"""
        # v4.4.1: Animated dialog for password reset
        from employee_vault.ui.widgets import QuickAnimatedDialog
        dialog = QuickAnimatedDialog(self, animation_style="fade")
        dialog.setWindowTitle("🔑 Set New Password")
        dialog.resize(450, 400)

        layout = QVBoxLayout(dialog)

        # Header
        header = QLabel("<h2>🔑 Set New Password</h2>")
        layout.addWidget(header)

        user = self.db.get_user(username)
        info = QLabel(f"Create a new password for: <b>{user['name']}</b> ({username})")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Form with neumorphic gradient styling
        form = QVBoxLayout()

        pw1 = NeumorphicGradientPasswordInput("Enter new password")
        pw1.setMinimumHeight(70)

        # Add password requirements widget
        pw_req = PasswordRequirementsWidget()
        pw1.line_edit.textChanged.connect(pw_req.update_requirements)

        pw2 = NeumorphicGradientPasswordInput("Confirm new password")
        pw2.setMinimumHeight(70)

        # Note: Show password toggle built into NeumorphicGradientPasswordInput widgets

        form.addWidget(pw1)
        form.addWidget(pw_req)
        form.addWidget(pw2)

        layout.addLayout(form)

        # Result label
        result_label = QLabel("")
        result_label.setWordWrap(True)
        layout.addWidget(result_label)

        # Buttons - Phase 3: iOS frosted glass
        btn_layout = QHBoxLayout()
        reset_btn = ModernAnimatedButton("✓ Reset Password")
        reset_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(76, 175, 80, 0.3),
                                           stop:1 rgba(56, 142, 60, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(76, 175, 80, 0.4),
                                           stop:1 rgba(56, 142, 60, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        cancel_btn = ModernAnimatedButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(158, 158, 158, 0.3),
                                           stop:1 rgba(97, 97, 97, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(158, 158, 158, 0.4),
                                           stop:1 rgba(97, 97, 97, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
        """)
        btn_layout.addStretch()
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def reset_password():
            if not pw1.line_edit.text() or not pw2.line_edit.text():
                result_label.setText("⚠️ Please fill in both password fields")
                result_label.setStyleSheet("color: #ff9800;")
                return

            if pw1.line_edit.text() != pw2.line_edit.text():
                result_label.setText("✗ Passwords do not match")
                result_label.setStyleSheet("color: #f44336;")
                return

            # Validate password strength
            is_valid, error_msg, strength = validate_password_strength(pw1.line_edit.text())
            if not is_valid:
                result_label.setText(f"✗ {error_msg}")
                result_label.setStyleSheet("color: #f44336;")
                return

            # Reset password
            try:
                self.db.update_user_password(username, pw1.line_edit.text())
                QMessageBox.information(dialog, "Success",
                    f"✓ Password reset successfully!\n\n"
                    f"Password Strength: {strength}\n\n"
                    f"You can now login with your new password.")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(
                    dialog,
                    "Password Reset Failed",
                    f"Failed to reset password:\n{e}\n\n"
                    "Possible causes:\n"
                    "• Database is locked by another user\n"
                    "• Insufficient permissions\n"
                    "• Database file is read-only\n\n"
                    "Please try again or contact your administrator."
                )

        reset_btn.clicked.connect(reset_password)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()
    
    def _check_user_pin_status(self):
        """Check if username has PIN and apply number-only validator"""
        username = self.card.username_edit.text().strip()
        if not username:
            # Clear validator when no username
            self.card.password_edit.setValidator(None)
            self.card.password_edit.setMaxLength(50)
            return
        
        # Check if user exists and has PIN
        try:
            user = self.db.get_user(username)
            if user and "pin" in user.keys() and user["pin"]:
                # User has PIN - apply numeric validator
                from PySide6.QtGui import QRegularExpressionValidator
                from PySide6.QtCore import QRegularExpression
                validator = QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$'))
                self.card.password_edit.setValidator(validator)
                self.card.password_edit.setMaxLength(6)
            else:
                # User has password or doesn't exist - allow any input
                self.card.password_edit.setValidator(None)
                self.card.password_edit.setMaxLength(50)
        except Exception:
            # If error checking, allow any input (safe fallback)
            self.card.password_edit.setValidator(None)
            self.card.password_edit.setMaxLength(50)

    def attempt_login(self):
        """Phase 2: Async login with instant UI response"""
        # Performance instrumentation (Phase 0)
        start = time.perf_counter()

        u = self.card.username_edit.text().strip().lower()
        p = self.card.password_edit.text()

        # Clear any previous error
        self.card.error_label.setText("")

        # Quick validation (stays on UI thread - fast)
        if not u or not p:
            self.card.error_label.setText("⚠️ Please enter username and PIN")
            print(f"[PERF] Login attempt (validation fail): {(time.perf_counter() - start)*1000:.2f}ms")
            return

        # Quick format check for existing PIN users
        r = self.db.get_user(u)
        if r and "pin" in r.keys() and r["pin"]:
            if not p.isdigit():
                self.card.error_label.setText("⚠️ PIN must be numbers only (4-6 digits)")
                print(f"[PERF] Login attempt (PIN format): {(time.perf_counter() - start)*1000:.2f}ms")
                return
            if not (4 <= len(p) <= 6):
                self.card.error_label.setText("⚠️ PIN must be 4-6 digits")
                print(f"[PERF] Login attempt (PIN length): {(time.perf_counter() - start)*1000:.2f}ms")
                return

        # Phase 2: UI responds INSTANTLY - show loading immediately
        self.card.set_loading(True)
        self.card.login_btn.setEnabled(False)
        print(f"[PERF] Login UI ready (instant): {(time.perf_counter() - start)*1000:.2f}ms")

        # Phase 2.1: Start background worker (non-blocking)
        self.login_worker = LoginWorker(self.db, u, p)
        self.login_worker.login_success.connect(self._on_login_success)
        self.login_worker.login_failed.connect(self._on_login_failed)
        self.login_worker.migration_required.connect(self._on_migration_required)
        self.login_worker.start()  # Non-blocking - returns immediately

    def _on_login_success(self, user):
        """Phase 2: Handler for successful login from worker thread"""
        self.actual_username = user["username"]

        # Check if user needs PIN setup
        if self.db.user_needs_pin_setup(user["username"]):
            self.card.set_loading(False)
            self.card.login_btn.setEnabled(True)
            self._force_pin_change(user["username"])
            print(f"[PERF] Login complete (PIN setup required)")
            return

        # Success - show animation and proceed
        self.card.set_loading(False)
        self.card.show_success()
        # Quick transition to dashboard
        QTimer.singleShot(150, self.accept)
        print(f"[PERF] Login complete (success)")

    def _on_login_failed(self, error_message):
        """Phase 2: Handler for failed login from worker thread"""
        self.card.set_loading(False)
        self.card.login_btn.setEnabled(True)

        # Check if this is a PIN reset message
        if "reset" in error_message.lower():
            self.card.error_label.setText(error_message)
            self.card.password_edit.clear()
            # Extract username for PIN change
            u = self.card.username_edit.text().strip().lower()
            QTimer.singleShot(2000, lambda: self._force_pin_change(u))
        else:
            self.card.error_label.setText(error_message)
            self.card.password_edit.clear()
            self.card.password_edit.setFocus()

        print(f"[PERF] Login complete (failed)")

    def _on_migration_required(self, username):
        """Phase 2: Handler for password migration from worker thread"""
        self.card.set_loading(False)
        self.card.login_btn.setEnabled(True)
        self.card.error_label.setText("⚠️ Migration required: Please set up your new PIN")
        QTimer.singleShot(1500, lambda: self._force_pin_change(username))
        print(f"[PERF] Login complete (migration)")
    
    def _force_pin_change(self, username):
        """Force user to set up a new PIN (for migration or first-time setup)"""
        from employee_vault.ui.widgets import SmoothAnimatedDialog
        
        dlg = SmoothAnimatedDialog(self, animation_style="fade")
        dlg.setWindowTitle("Set Up Your PIN")
        dlg.resize(400, 300)
        
        layout = QVBoxLayout(dlg)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🔐 Set Up Your PIN")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info message
        info = QLabel("For security, please set up a new 4-6 digit PIN.\nWe recommend using 6 digits for better security.")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(info)
        
        # PIN input with neumorphic gradient styling
        pin_edit = NeumorphicGradientPasswordInput("Enter 4-6 digit PIN")
        pin_edit.line_edit.setMaxLength(6)
        pin_edit.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$')))
        pin_edit.setMinimumHeight(70)
        layout.addWidget(pin_edit)

        # Confirm PIN input with neumorphic gradient styling
        confirm_edit = NeumorphicGradientPasswordInput("Re-enter PIN")
        confirm_edit.line_edit.setMaxLength(6)
        confirm_edit.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$')))
        confirm_edit.setMinimumHeight(70)
        layout.addWidget(confirm_edit)
        
        # Error label
        error_label = QLabel("")
        error_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(dlg.reject)
        
        save_btn = QPushButton("Set PIN")
        save_btn.setFixedHeight(40)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        def validate_and_save():
            pin = pin_edit.line_edit.text()
            confirm = confirm_edit.line_edit.text()

            error_label.setText("")

            if not pin or not confirm:
                error_label.setText("⚠️ Please fill in both fields")
                return

            if pin != confirm:
                error_label.setText("❌ PINs do not match")
                confirm_edit.line_edit.clear()
                confirm_edit.line_edit.setFocus()
                return

            # Validate PIN strength
            is_valid, errors = validate_pin_strength(pin)
            if not is_valid:
                error_label.setText(f"❌ {errors[0]}")
                pin_edit.line_edit.clear()
                confirm_edit.line_edit.clear()
                pin_edit.line_edit.setFocus()
                return
            
            # Update PIN in database
            try:
                self.db.update_user_pin(username, pin)
                self.actual_username = username
                dlg.accept()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "PIN Set Successfully",
                    f"Your PIN has been set successfully!\nYou can now use it to log in.",
                    QMessageBox.StandardButton.Ok
                )
                
                # Accept the login dialog to proceed
                self.accept()
                
            except Exception as e:
                error_label.setText(f"❌ Error: {str(e)}")
                logging.error(f"Error setting PIN: {e}")
        
        save_btn.clicked.connect(validate_and_save)
        confirm_edit.returnPressed.connect(validate_and_save)
        
        if dlg.exec() != QDialog.DialogCode.Accepted:
            # User cancelled - reject login
            self.reject()
    
    def create_account(self):
        # v4.4.1: Animated dialog for account creation
        from employee_vault.ui.widgets import SmoothAnimatedDialog
        dlg=SmoothAnimatedDialog(self, animation_style="slide"); dlg.setWindowTitle("Create Account"); dlg.resize(420, 550)

        # Set dialog stylesheet for transparent labels
        dlg.setStyleSheet("""
            QLabel {
                background: transparent;
                color: rgba(255, 255, 255, 0.9);
            }
        """)

        v=QVBoxLayout(dlg); f=QFormLayout()

        # iOS frosted glass input styling
        ios_input_style = """
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1.5px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 13px;
                color: white;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1.5px solid rgba(255, 255, 255, 0.3);
            }
            QLineEdit:focus {
                border: 2px solid rgba(74, 158, 255, 0.6);
                background: rgba(74, 158, 255, 0.15);
                outline: none;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.35);
            }
        """

        # Create account fields with neumorphic gradient styling
        username = NeumorphicGradientLineEdit("Username")
        username.setMinimumHeight(70)

        name = NeumorphicGradientLineEdit("Full Name")
        name.setMinimumHeight(70)

        pw = NeumorphicGradientPasswordInput("PIN (4-6 digits)")
        pw.line_edit.setMaxLength(6)
        pw.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$')))
        pw.setMinimumHeight(70)

        # Add PIN hint label
        pin_hint = QLabel("💡 Use 4-6 digits. Avoid simple patterns like 0000 or 1234")
        pin_hint.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; background: transparent;")
        pin_hint.setWordWrap(True)

        pw2 = NeumorphicGradientPasswordInput("Confirm PIN")
        pw2.line_edit.setMaxLength(6)
        pw2.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d{0,6}$')))
        pw2.setMinimumHeight(70)

        # Note: Show PIN toggle built into NeumorphicGradientPasswordInput widgets

        f.addRow("", username)
        f.addRow("", name)
        f.addRow("", pw)
        f.addRow("", pin_hint)  # Add PIN hint
        f.addRow("", pw2)
        v.addLayout(f)
        
        row=QHBoxLayout()

        # Phase 3: iOS frosted glass buttons
        ok=PulseButton("✓ Create Account")
        ok.start_pulse()
        ok.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(76, 175, 80, 0.3),
                                           stop:1 rgba(56, 142, 60, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(76, 175, 80, 0.4),
                                           stop:1 rgba(56, 142, 60, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(56, 142, 60, 0.5),
                                           stop:1 rgba(46, 125, 50, 0.8));
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)

        cancel=ModernAnimatedButton("Cancel")
        cancel.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(158, 158, 158, 0.3),
                                           stop:1 rgba(97, 97, 97, 0.6));
                border-top: 1.5px solid rgba(255, 255, 255, 0.5);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 22px;
                margin: 3px;

            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(158, 158, 158, 0.4),
                                           stop:1 rgba(97, 97, 97, 0.7));
                border-top: 1.5px solid rgba(255, 255, 255, 0.6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(97, 97, 97, 0.5),
                                           stop:1 rgba(66, 66, 66, 0.8));
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)

        row.addStretch(1); row.addWidget(ok); row.addWidget(cancel); v.addLayout(row)
        
        def do_register():
            if not all([username.line_edit.text().strip(), name.line_edit.text().strip(), pw.line_edit.text(), pw2.line_edit.text()]):
                QMessageBox.critical(
                    dlg,
                    "Missing Information",
                    "All fields are required to create an account.\n\n"
                    "Please fill in:\n"
                    "• Username\n"
                    "• Full Name\n"
                    "• PIN\n"
                    "• Confirm PIN"
                )
                return
            if pw.line_edit.text()!=pw2.line_edit.text():
                QMessageBox.critical(
                    dlg,
                    "PIN Mismatch",
                    "The PINs you entered do not match.\n\n"
                    "Please make sure both PIN fields contain the exact same PIN."
                )
                return

            # v4.6.0: Validate PIN strength (replacing password validation)
            is_valid, errors = validate_pin_strength(pw.line_edit.text())
            if not is_valid:
                error_msg = "PIN does not meet requirements:\n\n" + "\n".join(f"✗ {err}" for err in errors)
                QMessageBox.critical(dlg, "Invalid PIN",
                                   f"{error_msg}\n\n"
                                   "Requirements:\n"
                                   "• Must be 4-6 digits\n"
                                   "• Avoid simple patterns (0000, 1234, etc.)\n"
                                   "• Avoid repeated digits (1111, 2222, etc.)")
                return

            try:
                created_username = username.line_edit.text().strip()
                self.db.create_user(created_username, name.line_edit.text().strip(), pw.line_edit.text(), role="user")

                # v4.6.0: Security questions removed - admin resets PIN if needed
                QMessageBox.information(
                    dlg,
                    "Account Created Successfully",
                    f"Account '{created_username}' has been created!\n\n"
                    "You can now log in with your username and PIN.\n\n"
                    "If you forget your PIN, contact an administrator for a reset."
                )
                
                dlg.accept()  # Close the signup dialog

            except sqlite3.IntegrityError as e:
                logging.error(f"IntegrityError during user creation: {e}")
                error_msg = str(e).lower()
                
                # Check if it's specifically a username conflict
                if "unique" in error_msg or "username" in error_msg:
                    QMessageBox.critical(
                        dlg,
                        "Username Already Taken",
                        f"The username '{username.text().strip()}' is already in use.\n\n"
                        "Please choose a different username and try again."
                    )
                else:
                    # Other integrity error (like NOT NULL constraint)
                    QMessageBox.critical(
                        dlg,
                        "Account Creation Failed",
                        f"Failed to create account due to database constraint.\n\n"
                        f"Error: {str(e)}\n\n"
                        "Please contact an administrator."
                    )
            except Exception as e:
                logging.error(f"Unexpected error during user creation: {e}")
                QMessageBox.critical(
                    dlg,
                    "Account Creation Failed",
                    f"An unexpected error occurred:\n\n{str(e)}\n\n"
                    "Please contact an administrator."
                )
        
        ok.clicked.connect(do_register); cancel.clicked.connect(dlg.reject); dlg.exec()

    def _setup_security_questions(self, username, parent_dialog, password_strength):
        """Setup security questions for password recovery"""
        # v4.4.1: Animated dialog for security question setup
        from employee_vault.ui.widgets import AnimatedDialogBase
        sq_dlg = AnimatedDialogBase(parent_dialog, animation_style="fade")
        sq_dlg.setWindowTitle("🔐 Setup Security Questions")
        sq_dlg.resize(500, 450)

        layout = QVBoxLayout(sq_dlg)

        # Header
        header = QLabel("<h2>🔐 Setup Password Recovery</h2>")
        layout.addWidget(header)

        info = QLabel("Please select and answer 3 security questions. These will be used to reset your password if you forget it.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #b0b0b0; margin-bottom: 10px;")
        layout.addWidget(info)

        # Form for 3 questions with neumorphic gradient styling
        form = QVBoxLayout()
        question_combos = []
        answer_fields = []

        for i in range(3):
            # Question label
            q_label = QLabel(f"<b>Question {i+1}:</b>")
            q_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 10px;")
            form.addWidget(q_label)

            # Question dropdown with neumorphic gradient
            q_combo = NeumorphicGradientComboBox(f"Select Question {i+1}")
            q_combo.addItems(SECURITY_QUESTIONS)
            q_combo.setCurrentIndex(i * 3)  # Spread out default selections
            q_combo.setMinimumHeight(70)
            question_combos.append(q_combo)
            form.addWidget(q_combo)

            # Answer field with neumorphic gradient
            answer_field = NeumorphicGradientLineEdit("Enter your answer")
            answer_field.setMinimumHeight(70)
            answer_fields.append(answer_field)
            form.addWidget(answer_field)

            # Add spacing
            if i < 2:
                spacer = QLabel("")
                spacer.setFixedHeight(15)
                form.addWidget(spacer)

        layout.addLayout(form)

        # Info text
        note = QLabel("ℹ️ <i>Answers are case-insensitive. You'll need to answer 2 out of 3 correctly to reset your password.</i>")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888888; font-size: 11px; margin-top: 10px;")
        layout.addWidget(note)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = ModernAnimatedButton("✓ Save Questions")
        skip_btn = ModernAnimatedButton("Skip (Not Recommended)")
        skip_btn.setStyleSheet("background-color: #666666;")

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(skip_btn)
        layout.addLayout(btn_layout)

        def save_questions():
            # Validate all fields
            for i, answer_field in enumerate(answer_fields):
                if not answer_field.text().strip():
                    QMessageBox.warning(sq_dlg, "Incomplete", f"Please answer Question {i+1}")
                    return

            # Check for duplicate questions
            selected_questions = [combo.currentText() for combo in question_combos]
            if len(set(selected_questions)) != 3:
                QMessageBox.warning(sq_dlg, "Duplicate Questions", "Please select 3 different questions")
                return

            # Save to database
            questions_and_answers = [
                (question_combos[i].currentText(), answer_fields[i].line_edit.text())
                for i in range(3)
            ]

            try:
                self.db.save_security_questions(username, questions_and_answers)
                QMessageBox.information(sq_dlg, "Success",
                    f"✓ Account created successfully!\n\n"
                    f"Password Strength: {password_strength}\n"
                    f"Security Questions: Set ✓\n\n"
                    f"You can now login with your credentials.")
                sq_dlg.accept()
                parent_dialog.accept()
            except Exception as e:
                QMessageBox.critical(
                    sq_dlg,
                    "Failed to Save Security Questions",
                    f"Unable to save security questions:\n{e}\n\n"
                    "Your account was created, but security questions could not be saved.\n"
                    "You can set them up later from your account settings.\n\n"
                    "You can now log in with your username and password."
                )

        def skip_questions():
            reply = QMessageBox.question(sq_dlg, "Skip Security Questions?",
                "Are you sure you want to skip setting up security questions?\n\n"
                "⚠️ Without security questions, you won't be able to reset your password if you forget it.\n"
                "You will need an administrator to reset it for you.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                QMessageBox.information(parent_dialog, "Success",
                    f"✓ Account created successfully!\n\n"
                    f"Password Strength: {password_strength}\n"
                    f"Security Questions: Not Set ⚠️\n\n"
                    f"You can now login with your credentials.")
                sq_dlg.accept()
                parent_dialog.accept()

        save_btn.clicked.connect(save_questions)
        skip_btn.clicked.connect(skip_questions)

        sq_dlg.exec()

    def _setup_security_questions_for_recovery(self, username):
        """Setup security questions during password recovery flow"""
        # v4.4.1: Animated dialog for recovery security questions
        from employee_vault.ui.widgets import AnimatedDialogBase
        sq_dlg = AnimatedDialogBase(self, animation_style="fade")
        sq_dlg.setWindowTitle("🔐 Setup Security Questions")
        sq_dlg.resize(500, 500)

        layout = QVBoxLayout(sq_dlg)

        # Header
        header = QLabel("<h2>🔐 Setup Security Questions</h2>")
        layout.addWidget(header)

        user = self.db.get_user(username)
        info = QLabel(f"<b>{user['name']}</b>, set up your security questions to continue with password reset.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #b0b0b0; margin-bottom: 10px;")
        layout.addWidget(info)

        note = QLabel("Please select and answer 3 security questions. After saving, you'll be able to use them to reset your password.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888888; margin-bottom: 15px;")
        layout.addWidget(note)

        # Form for 3 questions with neumorphic gradient styling
        form = QVBoxLayout()
        question_combos = []
        answer_fields = []

        for i in range(3):
            # Question label
            q_label = QLabel(f"<b>Question {i+1}:</b>")
            q_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 10px;")
            form.addWidget(q_label)

            # Question dropdown with neumorphic gradient
            q_combo = NeumorphicGradientComboBox(f"Select Question {i+1}")
            q_combo.addItems(SECURITY_QUESTIONS)
            q_combo.setCurrentIndex(i * 3)  # Spread out default selections
            q_combo.setMinimumHeight(70)
            question_combos.append(q_combo)
            form.addWidget(q_combo)

            # Answer field with neumorphic gradient
            answer_field = NeumorphicGradientLineEdit("Enter your answer")
            answer_field.setMinimumHeight(70)
            answer_fields.append(answer_field)
            form.addWidget(answer_field)

            # Add spacing
            if i < 2:
                spacer = QLabel("")
                spacer.setFixedHeight(15)
                form.addWidget(spacer)

        layout.addLayout(form)

        # Info text
        reminder = QLabel("ℹ️ <i>Answers are case-insensitive. You'll need to answer 2 out of 3 correctly to reset your password.</i>")
        reminder.setWordWrap(True)
        reminder.setStyleSheet("color: #888888; font-size: 11px; margin-top: 10px;")
        layout.addWidget(reminder)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = ModernAnimatedButton("✓ Save & Continue")
        cancel_btn = ModernAnimatedButton("Cancel")

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def save_and_proceed():
            # Validate all fields
            for i, answer_field in enumerate(answer_fields):
                if not answer_field.text().strip():
                    QMessageBox.warning(sq_dlg, "Incomplete", f"Please answer Question {i+1}")
                    return

            # Check for duplicate questions
            selected_questions = [combo.currentText() for combo in question_combos]
            if len(set(selected_questions)) != 3:
                QMessageBox.warning(sq_dlg, "Duplicate Questions", "Please select 3 different questions")
                return

            # Save to database
            questions_and_answers = [
                (question_combos[i].currentText(), answer_fields[i].line_edit.text())
                for i in range(3)
            ]

            try:
                self.db.save_security_questions(username, questions_and_answers)
                sq_dlg.accept()

                # Show success message
                QMessageBox.information(
                    self,
                    "Security Questions Saved",
                    "✓ Your security questions have been saved successfully!\n\n"
                    "Now answer them to verify and reset your password."
                )

                # Proceed to verify the questions they just set up
                self._verify_security_questions(username)

            except Exception as e:
                QMessageBox.critical(
                    sq_dlg,
                    "Failed to Save Security Questions",
                    f"Unable to save security questions:\n{e}\n\n"
                    "Please try again or contact an administrator."
                )

        save_btn.clicked.connect(save_and_proceed)
        cancel_btn.clicked.connect(sq_dlg.reject)

        sq_dlg.exec()

