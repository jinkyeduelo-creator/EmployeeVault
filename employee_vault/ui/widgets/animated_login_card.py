"""
Animated Login Card - Hover-to-Expand with Animated Border
iOS Frosted Glass Style with Smooth Rotating Gradient Border
v2.0 - Upgraded with QVariantAnimation for smoother 60fps effects
"""

import math
from PySide6.QtCore import (
    Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, Property, QSize, QPointF, Signal, QRectF, QRegularExpression, QVariantAnimation
)
from PySide6.QtGui import (
    QPainter, QPen, QLinearGradient, QColor, QFont, QBrush, QCursor, QPainterPath, QRegularExpressionValidator, QRadialGradient
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QApplication, QGraphicsOpacityEffect, QSizePolicy
)

# Import RippleEffect for modern button interactions
try:
    from employee_vault.ui.widgets.advanced_effects import RippleEffect
except ImportError:
    RippleEffect = None

# Import iOS button styling helper to apply frosted glass styles
try:
    # Attempt local import; if run within package, this will succeed
    from ios_button_styles import apply_ios_style, get_ios_frosted_glass_style
except Exception:
    # Fallback: define no-op functions when styling helper is unavailable
    def apply_ios_style(button, color='blue', theme_colors=None):
        return
    def get_ios_frosted_glass_style(color='blue', theme_colors=None):
        return ""

# === COLOR CONSTANTS - EmployeeVault Branding ===
# Border gradient colors
BORDER_COLOR_PRIMARY = QColor(74, 158, 255)      # Blue (#4a9eff)
BORDER_COLOR_ACCENT = QColor(156, 39, 176)       # Purple (#9c27b0)

# Background colors
BG_OUTER = QColor(20, 25, 45, 235)              # Dark blue outer card
BG_INNER = QColor(30, 35, 50, 200)              # Lighter inner panel

# Input field colors
INPUT_BG_BASE = "rgba(255, 255, 255, 0.08)"
INPUT_BG_HOVER = "rgba(255, 255, 255, 0.12)"
INPUT_BG_FOCUS = "rgba(74, 158, 255, 0.15)"
INPUT_BORDER_BASE = "rgba(255, 255, 255, 0.2)"
INPUT_BORDER_HOVER = "rgba(255, 255, 255, 0.3)"
INPUT_BORDER_FOCUS = "rgba(74, 158, 255, 0.6)"
INPUT_PLACEHOLDER = "rgba(255, 255, 255, 0.35)"  # More transparent

# Button colors
BUTTON_BG_GRADIENT_START = "rgba(255, 255, 255, 0.18)"  # Brighter
BUTTON_BG_GRADIENT_MID = "rgba(74, 158, 255, 0.4)"     # Brighter
BUTTON_BG_GRADIENT_END = "rgba(33, 150, 243, 0.7)"     # Brighter
BUTTON_BORDER_TOP = "rgba(255, 255, 255, 0.6)"         # Stronger

# Close button colors
CLOSE_BTN_BG = "rgba(244, 67, 54, 0.3)"          # Red translucent
CLOSE_BTN_HOVER = "rgba(244, 67, 54, 0.6)"       # Red brighter
CLOSE_BTN_TEXT = "#ffffff"

# Error label color
ERROR_COLOR = "#f44336"  # Material red

# Sizes
COLLAPSED_WIDTH = 300
COLLAPSED_HEIGHT = 110
EXPANDED_WIDTH = 400
EXPANDED_HEIGHT = 480  # Taller to fit error label

BORDER_WIDTH = 3.0      # More visible border
BORDER_OPACITY = 1.0    # Full opacity for vibrant animation
CARD_RADIUS = 24

# Margins (reduced from 30px to 20px)
CARD_MARGIN = 20


class IOSToggleSwitch(QWidget):
    """iOS-style animated toggle switch"""
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._checked = False
        self._circle_position = 2.0

        # Animation for circle movement
        self.anim = QPropertyAnimation(self, b"circlePosition", self)
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_circlePosition(self):
        return self._circle_position

    def set_circlePosition(self, pos):
        self._circle_position = pos
        self.update()

    circlePosition = Property(float, fget=get_circlePosition, fset=set_circlePosition)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate_toggle()
            self.toggled.emit(checked)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._animate_toggle()
        self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _animate_toggle(self):
        if self._checked:
            self.anim.setStartValue(self._circle_position)
            self.anim.setEndValue(22.0)  # Right position
        else:
            self.anim.setStartValue(self._circle_position)
            self.anim.setEndValue(2.0)   # Left position
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw track (background)
        track_rect = QRectF(0, 0, 44, 24)
        if self._checked:
            # Blue when checked
            track_color = QColor(74, 158, 255, 180)
        else:
            # Gray when unchecked
            track_color = QColor(120, 120, 120, 100)

        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track_rect, 12, 12)

        # Draw circle (thumb)
        circle_y = 2
        circle_rect = QRectF(self._circle_position, circle_y, 20, 20)

        # White circle with shadow effect
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawEllipse(circle_rect)


class AnimatedLoginCard(QWidget):
    """
    Modern login card with hover-to-expand animation and rotating gradient border.

    Features:
    - Hover to expand (compact → full form)
    - Animated rotating gradient border (uses theme colors)
    - iOS frosted glass background
    - Smooth transitions (180ms with OutCubic easing)
    - Auto-collapse when mouse leaves
    - Close button (X) in top-right
    - v5.1: Theme-aware colors
    """

    # Signals
    closeRequested = Signal()
    sizeChanged = Signal(QSize)  # Emitted when card size changes (for dialog resizing)

    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent)
        
        # v5.1: Store theme colors for themed appearance
        self._theme_colors = theme_colors or {}
        self._setup_theme_colors()

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        # Animation states
        self.angle = 0.0  # Border rotation angle
        self.expanded = False  # Start collapsed to show animation
        self.close_btn_hover = False  # Track close button hover
        self.hover_enabled = True  # Control whether hover expand/collapse is enabled

        # Size definitions (using constants)
        self.collapsed_size = QSize(COLLAPSED_WIDTH, COLLAPSED_HEIGHT)
        self.expanded_size = QSize(EXPANDED_WIDTH, EXPANDED_HEIGHT)

        # Border animation settings (using constants)
        self.border_width = BORDER_WIDTH
        self.radius = CARD_RADIUS

        # Widget properties
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Initialize size property for animation (start collapsed)
        self._current_size = self.collapsed_size
        self.setMinimumSize(self._current_size)
        self.setMaximumSize(self._current_size)
        self.resize(self._current_size)

        # Size animation (faster for snappier feel)
        self.size_anim = QPropertyAnimation(self, b"animSize", self)
        self.size_anim.setDuration(180)  # Faster: 180ms instead of 220ms
        self.size_anim.setEasingCurve(QEasingCurve.Type.OutCubic)  # Snappier easing

        # Setup UI
        self._setup_ui()

        # v2.0: Smooth border animation using QVariantAnimation (60fps equivalent)
        self._border_phase = 0.0  # Animation phase [0, 1]
        self.border_anim = QVariantAnimation(self)
        self.border_anim.setStartValue(0.0)
        self.border_anim.setEndValue(1.0)
        self.border_anim.setDuration(3000)  # 3 seconds for full rotation (smooth)
        self.border_anim.setLoopCount(-1)  # Infinite loop
        self.border_anim.valueChanged.connect(self._on_border_phase_changed)
        self.border_anim.start()

        # Login button glow animation state
        self.button_glow_value = 0.0
        self.button_glow_direction = 1
        
        # Button glow timer (separate from border for independent control)
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._update_button_glow_tick)
        self.glow_timer.start(50)

        # Loading state
        self.is_loading = False
        self.loading_angle = 0
    
    def _setup_theme_colors(self):
        """v5.1: Setup gradient colors based on theme"""
        # Default colors (EmployeeVault branding)
        default_primary = "#4a9eff"      # Blue
        default_secondary = "#9c27b0"    # Purple
        default_accent = "#00c8ff"       # Cyan
        
        if self._theme_colors:
            # Use theme colors
            primary = self._theme_colors.get("primary", default_primary)
            secondary = self._theme_colors.get("secondary", default_secondary)
            accent = self._theme_colors.get("accent", default_accent)
        else:
            primary = default_primary
            secondary = default_secondary
            accent = default_accent
        
        # Convert to QColor for gradient
        self._gradient_color1 = QColor(primary)
        self._gradient_color2 = QColor(secondary)
        self._gradient_color3 = QColor(accent)
        
        # Derive additional colors for 5-color gradient
        # Create a pink from secondary + accent blend
        pink_r = min(255, int((self._gradient_color2.red() + 255) / 2))
        pink_g = min(255, int((self._gradient_color2.green() + 64) / 2))
        pink_b = min(255, int((self._gradient_color2.blue() + 129) / 2))
        self._gradient_color4 = QColor(pink_r, pink_g, pink_b)
    
    def _on_border_phase_changed(self, value):
        """Update border phase and trigger repaint - smooth animation callback"""
        self._border_phase = float(value)
        self.angle = self._border_phase * 360.0  # Convert to degrees for gradient
        self.update()
    
    def _update_button_glow_tick(self):
        """Update button glow animation (subtle pulse)"""
        if self.expanded:  # Only animate when form is visible
            self.button_glow_value += 0.03 * self.button_glow_direction
            if self.button_glow_value >= 1.0:
                self.button_glow_value = 1.0
                self.button_glow_direction = -1
            elif self.button_glow_value <= 0.0:
                self.button_glow_value = 0.0
                self.button_glow_direction = 1
            self._update_button_glow()

    def reset_state(self):
        """Reset card to initial collapsed state - call after logout to ensure clean state"""
        # Stop any running animations
        self.size_anim.stop()
        
        # Reset state flags
        self.expanded = False
        self.hover_enabled = True
        self.is_loading = False
        self.loading_angle = 0
        self.close_btn_hover = False
        
        # Reset size to collapsed
        self._current_size = self.collapsed_size
        self.setMinimumSize(self._current_size)
        self.setMaximumSize(self._current_size)
        self.resize(self._current_size)
        
        # Hide form elements (collapsed state)
        if hasattr(self, 'form_container'):
            self.form_container.hide()
        if hasattr(self, 'window_title_container'):
            self.window_title_container.hide()
        if hasattr(self, 'window_close_btn'):
            self.window_close_btn.hide()
        
        # Clear form fields
        if hasattr(self, 'username_edit'):
            self.username_edit.clear()
        if hasattr(self, 'password_edit'):
            self.password_edit.clear()
        if hasattr(self, 'error_label'):
            self.error_label.setText("")
            self.error_label.hide()
        
        # Reset login button
        if hasattr(self, 'login_btn'):
            self.login_btn.setText("🔓 Sign In")
            self.login_btn.setEnabled(True)
        
        # Restart border animation if stopped
        if hasattr(self, 'border_anim'):
            if self.border_anim.state() != QVariantAnimation.State.Running:
                self.border_anim.start()
        
        # Trigger repaint
        self.update()

    def _setup_ui(self):
        """Setup the login form UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        self.main_layout.setSpacing(6)

        # === WINDOW TITLE BAR (at the top) ===
        self.window_title_container = QWidget()
        self.window_title_container.setStyleSheet("background: transparent;")
        window_title_row = QHBoxLayout(self.window_title_container)
        window_title_row.setSpacing(0)
        window_title_row.setContentsMargins(0, 0, 0, 8)

        # Window title text (Bigger and Centered with gradient and glow)
        window_title = QLabel("Cuddly International Corporation")
        # FORCE CENTER ALIGNMENT
        window_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        window_title.setStyleSheet("""
            background: transparent;
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 255, 255, 0.95),
                stop:0.5 rgba(107, 179, 255, 1),
                stop:1 rgba(255, 255, 255, 0.95));
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.5px;

        """)

        # Add widget with stretch factor 1 (This forces it to fill the width and center the text)
        window_title_row.addWidget(window_title, 1)

        # === CLOSE BUTTON (X) ===
        self.window_close_btn = QPushButton("×")
        self.window_close_btn.setFixedSize(32, 32)
        self.window_close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.window_close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.6);
                font-size: 24px;
                font-weight: bold;
                border-radius: 16px;
                padding: 0px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background: rgba(244, 67, 54, 0.8);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(211, 47, 47, 1);
            }
        """)
        self.window_close_btn.clicked.connect(self._handle_close_button)
        self.window_close_btn.hide() # Hidden initially

        # Add the title container to main layout
        self.window_title_container.hide()
        self.main_layout.addWidget(self.window_title_container)

        # Add close button separately at the very top right overlay
        close_row = QHBoxLayout()
        close_row.setContentsMargins(0, 0, 0, 0)
        close_row.addStretch()
        close_row.addWidget(self.window_close_btn)
        self.main_layout.insertLayout(0, close_row)

        # === TITLE ROW (LOGIN) ===
        title_row = QHBoxLayout()
        title_row.setSpacing(4)

        self.icon_left = QLabel("🔐")
        self.icon_right = QLabel("✨")
        self.icon_left.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_right.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        for lbl in (self.icon_left, self.icon_right):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background: transparent;")
            font = QFont()
            font.setPointSize(14)
            lbl.setFont(font)

        self.title = QLabel("LOGIN")
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9);")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title.setFont(title_font)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_row.addWidget(self.icon_left)
        title_row.addStretch()
        title_row.addWidget(self.title)
        title_row.addStretch()
        title_row.addWidget(self.icon_right)

        self.main_layout.addLayout(title_row)

        # === FORM CONTAINER ===
        self.form_container = QWidget()
        self.form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(self.form_container)
        form_layout.setContentsMargins(0, 4, 0, 12)  # Added bottom margin for pill buttons
        form_layout.setSpacing(10)

        # Username with neumorphic gradient input
        from employee_vault.ui.widgets.animated_input import NeumorphicGradientLineEdit, NeumorphicGradientPasswordInput
        self.username_container = NeumorphicGradientLineEdit(
            "Username",
            float_y=10,    # Floating Label: Lower numbers = Higher up
            rest_y=25,    # Resting Label: Higher numbers = Lower down
            input_y=4    # Input Text: Higher numbers = Lower down
        )
        self.username_container.setMinimumHeight(70)
        self.username_edit = self.username_container.line_edit

        # PIN with neumorphic gradient password input (includes show/hide toggle)
        self.password_container = NeumorphicGradientPasswordInput(
            "PIN (4-6 digits)", 
            float_y=10,    # Floating Label: Lower numbers = Higher up
            rest_y=25,    # Resting Label: Higher numbers = Lower down
            input_y=4    # Input Text: Higher numbers = Lower down
        )
        self.password_container.setMinimumHeight(70)
        self.password_edit = self.password_container.line_edit
        # Set max length but NO validator - allow passwords during migration
        self.password_edit.setMaxLength(50)  # Allow longer for password migration
        # Note: Validator removed to allow old password entry during migration

        # Show PIN Toggle is now built into NeumorphicGradientPasswordInput
        # Keep a reference for compatibility
        show_password_container = QWidget()
        show_password_container.setFixedHeight(0)  # Hide old toggle since it's built-in now
        show_password_container.hide()

        # Dummy toggle for compatibility (the real toggle is in password_container)
        self.show_password_toggle = None
        self.show_password_check = None

        # Login Button
        self.login_btn = QPushButton("🔓 Sign In")
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.login_btn.setDefault(True)  # Make this the default button (Enter key triggers it)
        self.login_btn.installEventFilter(self)
        
        # Add ripple effect overlay for modern interaction feedback
        if RippleEffect is not None:
            self._login_ripple = RippleEffect(self.login_btn)
            self._login_ripple.setGeometry(self.login_btn.rect())
            self._login_ripple.raise_()
        
        # (Button styling code kept condensed for brevity - it's fine in your file)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BUTTON_BG_GRADIENT_START},
                    stop:0.5 {BUTTON_BG_GRADIENT_MID},
                    stop:1 {BUTTON_BG_GRADIENT_END});
                border: 1.5px solid rgba(74, 158, 255, 0.6);
                border-top: 2px solid {BUTTON_BORDER_TOP};
                border-radius: 24px;
                padding: 10px 24px;
                font-size: 15px;
                font-weight: 700;
                color: white;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25),
                    stop:0.5 rgba(74, 158, 255, 0.5),
                    stop:1 rgba(33, 150, 243, 0.8));
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """)

        # Error Label (no fixed height to prevent truncation)
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(28)
        self.error_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.error_label.setStyleSheet(f"color: {ERROR_COLOR}; font-size: 12px; font-weight: 500; padding: 4px 8px;")

        # Bottom Row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.forgot_btn = QPushButton("Forgot PIN?")
        self.forgot_btn.setFixedHeight(36)
        self.forgot_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.forgot_btn.setAutoDefault(False)  # Prevent triggering on Enter key
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.4),
                    stop:1 rgba(33, 150, 243, 0.3));
                border: 1.5px solid rgba(255, 255, 255, 0.25);
                border-radius: 18px;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 0px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.6),
                    stop:1 rgba(33, 150, 243, 0.5));
                border: 1.5px solid rgba(255, 255, 255, 0.35);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(33, 150, 243, 0.5),
                    stop:1 rgba(25, 118, 210, 0.6));
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        self.forgot_btn.installEventFilter(self)

        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setFixedHeight(36)
        self.signup_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.signup_btn.setAutoDefault(False)  # Prevent triggering on Enter key
        self.signup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(76, 175, 80, 0.4),
                    stop:1 rgba(56, 142, 60, 0.3));
                border: 1.5px solid rgba(255, 255, 255, 0.25);
                border-radius: 18px;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 0px 20px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(76, 175, 80, 0.6),
                    stop:1 rgba(56, 142, 60, 0.5));
                border: 1.5px solid rgba(255, 255, 255, 0.35);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(56, 142, 60, 0.5),
                    stop:1 rgba(46, 125, 50, 0.6));
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        self.signup_btn.installEventFilter(self)

        bottom_row.addWidget(self.forgot_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(self.signup_btn)

        # Assemble Form
        form_layout.addWidget(self.username_container)
        form_layout.addWidget(self.password_container)
        form_layout.addWidget(show_password_container)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.login_btn)
        form_layout.addWidget(self.error_label)
        form_layout.addSpacing(4)
        form_layout.addLayout(bottom_row)

        self.main_layout.addWidget(self.form_container)

        self._apply_styles()
        # Hide form initially (collapsed state)
        self.form_container.hide()
        self.window_title_container.hide()
        self.window_close_btn.hide()

        # Ensure no fields have focus initially (prevent cursor stuck on username)
        self.username_edit.clearFocus()
        self.password_edit.clearFocus()
        self.username_edit.setCursorPosition(0)
        self.username_edit.deselect()
        self.password_edit.setCursorPosition(0)
        self.password_edit.deselect()

    def _apply_styles(self):
        """Apply iOS frosted glass styling with focus/hover states and animations"""
        self.setStyleSheet(f"""
            QWidget {{
                color: #f5f5f5;
                font-family: 'Segoe UI', 'SF Pro Display', Arial;
            }}
            QLineEdit {{
                background: {INPUT_BG_BASE};
                border: 1.5px solid {INPUT_BORDER_BASE};
                border-radius: 20px;
                padding: 4px 16px;
                font-size: 13px;
                color: white;
            }}
            QLineEdit:hover {{
                background: {INPUT_BG_HOVER};
                border: 1.5px solid {INPUT_BORDER_HOVER};
            }}
            QLineEdit:focus {{
                border: 2px solid {INPUT_BORDER_FOCUS};
                background: {INPUT_BG_FOCUS};
                outline: none;
                padding: 7px 15px;  /* Compensate for thicker border */
            }}
            QLineEdit::placeholder {{
                color: {INPUT_PLACEHOLDER};
            }}
            QCheckBox {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1.5px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.05);
            }}
            QCheckBox::indicator:hover {{
                border: 1.5px solid rgba(255, 255, 255, 0.5);
                background: rgba(255, 255, 255, 0.08);
            }}
            QCheckBox::indicator:checked {{
                background: rgba(74, 158, 255, 0.6);
                border: 1.5px solid rgba(74, 158, 255, 0.8);
            }}
            QLabel {{
                font-size: 11pt;
            }}
        """)

        # Removed setting objectName on login button; styling now applied directly via iOS frosted glass helper

    # === PROPERTY FOR ANIMATION ===
    def get_animSize(self):
        return self._current_size

    def set_animSize(self, size: QSize):
        self._current_size = size
        self.setMinimumSize(size)
        self.setMaximumSize(size)
        self.resize(size)

    animSize = Property(QSize, fget=get_animSize, fset=set_animSize)

    # === SHOW EVENT === (Ensure animations start when widget becomes visible)
    def showEvent(self, event):
        """Called when widget becomes visible - ensure all animations are running"""
        super().showEvent(event)
        
        # Ensure border animation is running
        if hasattr(self, 'border_anim'):
            if self.border_anim.state() != QVariantAnimation.State.Running:
                self.border_anim.start()
        
        # Ensure glow timer is running
        if hasattr(self, 'glow_timer'):
            if not self.glow_timer.isActive():
                self.glow_timer.start(50)
        
        # Force initial repaint
        self.update()

    # === HOVER DETECTION === (v2.0 - Fixed flickering with debounce)
    def enterEvent(self, event):
        """Expand when mouse enters - smooth animation"""
        if self.hover_enabled:
            # Cancel any pending collapse
            if hasattr(self, '_collapse_timer') and self._collapse_timer.isActive():
                self._collapse_timer.stop()
            # Only expand if not already expanded
            if not self.expanded:
                self.set_expanded(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Collapse when mouse leaves (with debounce to prevent flickering)"""
        if self.hover_enabled:
            # Use a short delay to debounce rapid enter/leave events
            # This prevents flickering when mouse moves between child widgets
            if not hasattr(self, '_collapse_timer'):
                self._collapse_timer = QTimer(self)
                self._collapse_timer.setSingleShot(True)
                self._collapse_timer.timeout.connect(self._delayed_collapse_check)
            
            # Start/restart the debounce timer (150ms delay)
            self._collapse_timer.start(150)
        super().leaveEvent(event)
    
    def _delayed_collapse_check(self):
        """Check if mouse is truly outside after debounce delay"""
        if not self.hover_enabled:
            return
        
        # Don't collapse while size animation is running
        if self.size_anim.state() == QPropertyAnimation.State.Running:
            return
            
        # Check if cursor is actually outside the widget
        global_pos = QCursor.pos()
        local_pos = self.mapFromGlobal(global_pos)
        
        # Use a slightly larger rect to account for border/glow
        check_rect = self.rect().adjusted(-10, -10, 10, 10)
        
        if not check_rect.contains(local_pos) and self.expanded:
            self.set_expanded(False)

    def mousePressEvent(self, event):
        """Clear focus from input fields when clicking elsewhere"""
        # Call super first to ensure proper event propagation
        super().mousePressEvent(event)

        # Get the widget at the click position
        clicked_widget = self.childAt(event.pos())

        # Check if click is on input fields or their containers
        is_input_click = False
        widget = clicked_widget
        while widget is not None and widget != self:
            if widget in (self.username_edit, self.password_edit,
                          self.username_container, self.password_container):
                is_input_click = True
                break
            widget = widget.parent()

        # Clear focus if clicked outside input areas
        if not is_input_click:
            # Clear focus from both containers and their child widgets
            self.username_container.clearFocus()
            self.password_container.clearFocus()
            self.username_edit.clearFocus()
            self.password_edit.clearFocus()

            # Set focus to the card itself to ensure focus goes somewhere
            if self.focusPolicy() == Qt.FocusPolicy.NoFocus:
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setFocus(Qt.FocusReason.MouseFocusReason)

    def eventFilter(self, obj, event):
        """Handle focus animations for input fields and hover effects for buttons"""
        from PySide6.QtCore import QEvent, QPropertyAnimation

        # Handle input field focus animations
        if obj in (self.username_edit, self.password_edit):
            if event.type() == QEvent.Type.FocusIn:
                # Ensure other field loses focus properly
                other_field = self.password_edit if obj == self.username_edit else self.username_edit
                if other_field.hasFocus():
                    other_field.clearFocus()

                # Subtle scale animation on focus
                anim = QPropertyAnimation(obj, b"minimumHeight", self)
                anim.setDuration(150)
                anim.setStartValue(40)
                anim.setEndValue(42)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.start()
                # Store animation to prevent garbage collection
                obj._focus_anim = anim

            elif event.type() == QEvent.Type.FocusOut:
                # Return to normal size
                anim = QPropertyAnimation(obj, b"minimumHeight", self)
                anim.setDuration(150)
                anim.setStartValue(42)
                anim.setEndValue(40)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.start()
                # Store animation to prevent garbage collection
                obj._focus_anim = anim

        # Handle button hover animations (using opacity effect to avoid height-based flickering)
        elif hasattr(self, 'login_btn') and hasattr(self, 'forgot_btn') and hasattr(self, 'signup_btn') and \
             obj in (self.login_btn, self.forgot_btn, self.signup_btn):
            # No height animation - CSS :hover handles visual feedback
            # Add ripple effect on click for login button
            if event.type() == QEvent.Type.MouseButtonPress and obj == self.login_btn:
                if hasattr(self, '_login_ripple') and self._login_ripple is not None:
                    self._login_ripple.setGeometry(obj.rect())
                    self._login_ripple.add_ripple(event.pos(), QColor(255, 255, 255, 100))

        return super().eventFilter(obj, event)

    def _toggle_password_visibility(self, checked):
        """Toggle password visibility based on switch state"""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _handle_close_button(self):
        """Handle close button click with confirmation dialog"""
        from PySide6.QtWidgets import QMessageBox

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to close Employee Vault?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # User confirmed, emit closeRequested signal
            self.closeRequested.emit()

    def set_loading(self, loading: bool):
        """Set loading state - disables button and shows spinner"""
        self.is_loading = loading
        self.login_btn.setEnabled(not loading)
        self.username_edit.setEnabled(not loading)
        self.password_edit.setEnabled(not loading)

        if loading:
            self.login_btn.setText("⏳ Signing In...")
        else:
            self.login_btn.setText("🔓 Sign In")

    def show_success(self):
        """Show success animation"""
        self.login_btn.setText("✓ Success!")
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.18),
                    stop:0.5 rgba(76, 175, 80, 0.5),
                    stop:1 rgba(56, 142, 60, 0.8));
                border: 2px solid rgba(76, 175, 80, 0.9);
                border-radius: 24px;
                padding: 10px 24px;
                font-size: 15px;
                font-weight: 700;
                color: white;
    
            }}
        """)
        self.error_label.setText("")

    def set_expanded(self, expand: bool):
        """Animate between collapsed and expanded states"""
        if expand == self.expanded:
            return

        self.expanded = expand
        self.size_anim.stop()

        if expand:
            # Expanding: show form and window title bar first, then animate
            self.form_container.show()
            self.window_title_container.show()  # Show window title bar when expanded
            self.window_close_btn.show()  # <--- NEW: Show button immediately
            self.size_anim.setStartValue(self.collapsed_size)
            self.size_anim.setEndValue(self.expanded_size)
            # Emit signal for dialog to resize
            self.sizeChanged.emit(self.expanded_size)

            # Set focus to username AFTER expansion animation completes
            def _set_initial_focus():
                try:
                    # Clear any existing focus first
                    self.username_edit.clearFocus()
                    self.password_edit.clearFocus()
                    # Set cursor position to 0 and deselect
                    self.username_edit.setCursorPosition(0)
                    self.username_edit.deselect()
                    self.password_edit.setCursorPosition(0)
                    self.password_edit.deselect()
                    # Now set focus to username
                    self.username_edit.setFocus()
                    self.size_anim.finished.disconnect(_set_initial_focus)
                except:
                    pass
            self.size_anim.finished.connect(_set_initial_focus)
        else:
            # Collapsing: animate first, hide form and window title bar after
            # Clear focus and cursor from both fields immediately
            self.username_edit.clearFocus()
            self.password_edit.clearFocus()
            self.username_edit.setCursorPosition(0)
            self.username_edit.deselect()
            self.password_edit.setCursorPosition(0)
            self.password_edit.deselect()

            self.size_anim.setStartValue(self.expanded_size)
            self.size_anim.setEndValue(self.collapsed_size)
            # Emit signal for dialog to resize
            self.sizeChanged.emit(self.collapsed_size)

            def _hide_form():
                if not self.expanded:
                    self.form_container.hide()
                    self.window_title_container.hide()  # Hide window title bar when collapsed
                    self.window_close_btn.hide()  # <--- NEW: Hide button after animation
                    try:
                        self.size_anim.finished.disconnect(_hide_form)
                    except:
                        pass

            self.size_anim.finished.connect(_hide_form)

        self.size_anim.start()

    # === ANIMATED BORDER (v2.0 - QVariantAnimation driven) ===
    # Border animation is now handled by _on_border_phase_changed()
    # Button glow is handled by _update_button_glow_tick()

    def _update_button_glow(self):
        """Apply subtle pulsing glow to login button"""
        # Calculate glow intensity (0.6 to 0.9)
        glow = 0.6 + (self.button_glow_value * 0.3)

        # Update button style with new glow
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BUTTON_BG_GRADIENT_START},
                    stop:0.5 {BUTTON_BG_GRADIENT_MID},
                    stop:1 {BUTTON_BG_GRADIENT_END});
                border: 1.5px solid rgba(74, 158, 255, {glow});
                border-top: 2px solid {BUTTON_BORDER_TOP};
                border-radius: 24px;
                padding: 10px 24px;
                font-size: 15px;
                font-weight: 700;
                color: white;
    
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25),
                    stop:0.5 rgba(74, 158, 255, 0.5),
                    stop:1 rgba(33, 150, 243, 0.8));
                border: 2px solid rgba(74, 158, 255, 0.9);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(33, 150, 243, 0.5),
                    stop:1 rgba(25, 118, 210, 0.9));
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """)

    def _build_gradient(self, rect):
        """Build rotating gradient with multiple colors for vibrant neon effect (v2.0)"""
        # Use smooth phase-based angle from QVariantAnimation
        rad = math.radians(self.angle)
        
        # Calculate gradient endpoints using circular motion for smooth rotation
        cx = rect.center().x()
        cy = rect.center().y()
        r = max(rect.width(), rect.height()) / 2
        
        # Circular motion for gradient endpoints
        x1 = cx + r * math.cos(rad)
        y1 = cy + r * math.sin(rad)
        x2 = cx - r * math.cos(rad)
        y2 = cy - r * math.sin(rad)

        grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))
        
        # v5.1: Use theme-derived colors for gradient (falls back to defaults if not set)
        if hasattr(self, '_gradient_color1') and self._gradient_color1:
            grad.setColorAt(0.0, self._gradient_color1)     # Primary (theme)
            grad.setColorAt(0.25, self._gradient_color2)    # Secondary (theme)
            grad.setColorAt(0.5, self._gradient_color3)     # Accent (theme)
            grad.setColorAt(0.75, self._gradient_color4)    # Derived pink
            grad.setColorAt(1.0, self._gradient_color1)     # Primary (seamless loop)
        else:
            # Fallback to original hardcoded colors
            grad.setColorAt(0.0, QColor(74, 158, 255))     # Blue (primary)
            grad.setColorAt(0.25, QColor(156, 39, 176))    # Purple (accent)
            grad.setColorAt(0.5, QColor(0, 200, 255))      # Cyan
            grad.setColorAt(0.75, QColor(255, 64, 129))    # Pink
            grad.setColorAt(1.0, QColor(74, 158, 255))     # Blue (seamless loop)
        
        return grad

    def paintEvent(self, event):
        """Custom paint: frosted glass background + animated border with glow effect (v2.0)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Inner rect (accounting for border and glow)
        rect = self.rect().adjusted(
            self.border_width + 2,
            self.border_width + 2,
            -self.border_width - 2,
            -self.border_width - 2
        )

        # === DROP SHADOW (when expanded) ===
        if self.expanded:
            shadow_rect = rect.adjusted(-5, -5, 5, 5)
            shadow_color = QColor(0, 0, 0, 80)
            painter.setBrush(shadow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(shadow_rect, self.radius + 4, self.radius + 4)

        # === BACKGROUND: iOS Frosted Glass ===
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(BG_OUTER)
        painter.drawRoundedRect(rect, self.radius, self.radius)

        # === GLOW EFFECT (behind border for neon look) ===
        grad = self._build_gradient(rect)
        
        # Draw outer glow (wider, more transparent) - creates the neon halo
        glow_pen = QPen(grad, self.border_width * 5)
        glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setOpacity(0.25)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, self.radius, self.radius)
        
        # Draw middle glow layer
        mid_glow_pen = QPen(grad, self.border_width * 3)
        mid_glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setOpacity(0.4)
        painter.setPen(mid_glow_pen)
        painter.drawRoundedRect(rect, self.radius, self.radius)
        
        # Reset opacity for main border
        painter.setOpacity(1.0)

        # === ANIMATED NEON BORDER (crisp main line) ===
        border_pen = QPen(grad, self.border_width * 2)
        border_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        border_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(border_pen)
        painter.drawRoundedRect(rect, self.radius, self.radius)
