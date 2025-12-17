"""
User Management Dialogs
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import *
from employee_vault.database import DB
from employee_vault.validators import *
from employee_vault.utils import *
from employee_vault.models import *
from employee_vault.ui.widgets import *
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase, apply_table_fixes
from employee_vault.ui.ios_button_styles import apply_ios_style
from employee_vault.ui.dialogs.permissions import PermissionEditorDialog


class UserManagementDialog(AnimatedDialogBase):
    """Professional User Management Interface"""
    def __init__(self, db, current_user, parent=None):
        # v4.4.1: Use fade animation for user management
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.current_user = current_user
        self.setWindowTitle("👥 User Management")
        self.resize(900, 600)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>👥 User Management</h2>")
        main_layout.addWidget(header)

        # Top toolbar
        toolbar = QHBoxLayout()

        # Phase 3: iOS frosted glass styling
        self.add_btn = ModernAnimatedButton("➕ Add User")
        apply_ios_style(self.add_btn, 'green')
        self.add_btn.clicked.connect(self._add_user)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = ModernAnimatedButton("✏️ Edit User")
        apply_ios_style(self.edit_btn, 'blue')
        self.edit_btn.clicked.connect(self._edit_user)
        self.edit_btn.setEnabled(False)
        toolbar.addWidget(self.edit_btn)

        self.reset_pw_btn = ModernAnimatedButton("🔑 Reset PIN")
        apply_ios_style(self.reset_pw_btn, 'orange')
        self.reset_pw_btn.clicked.connect(self._reset_password)
        self.reset_pw_btn.setEnabled(False)
        toolbar.addWidget(self.reset_pw_btn)

        self.delete_btn = ModernAnimatedButton("🗑️ Delete User")
        apply_ios_style(self.delete_btn, 'red')
        self.delete_btn.clicked.connect(self._delete_user)
        self.delete_btn.setEnabled(False)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()

        # v2.0 FIXED: Add Edit Permissions button
        edit_perm_btn = ModernAnimatedButton("🔐 Edit Permissions")
        apply_ios_style(edit_perm_btn, 'purple')
        edit_perm_btn.setToolTip("Edit permissions for selected user")
        edit_perm_btn.clicked.connect(self._edit_permissions)
        toolbar.addWidget(edit_perm_btn)

        refresh_btn = ModernAnimatedButton("🔄 Refresh")
        apply_ios_style(refresh_btn, 'blue')
        refresh_btn.clicked.connect(self._load_users)
        toolbar.addWidget(refresh_btn)

        main_layout.addLayout(toolbar)

        # Users table
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Remove cursor changes (no more hand cursor!)
        apply_table_fixes(self.table)  # v4.5.0: Apply cursor and focus rectangle fixes

        # Fix: Remove focus rectangle (the rounded border around focused cells)
        self.table.setStyleSheet("""
            QTableView {
                outline: 0;
            }
            QTableView::item:focus {
                border: none;
                outline: none;
            }
        """)
        self.table.doubleClicked.connect(self._edit_user)

        self.model = UserTableModel([])
        self.table.setModel(self.model)

        # Connect selection AFTER setting model
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        main_layout.addWidget(self.table)

        # Info label
        self.info_label = QLabel()
        main_layout.addWidget(self.info_label)

        # Bottom buttons
        bottom = QHBoxLayout()
        bottom.addStretch()

        # Phase 3: iOS frosted glass styling
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)

        main_layout.addLayout(bottom)

        # Load initial data
        self._load_users()

    def _load_users(self):
        """Load all users from database"""
        try:
            users = self.db.all_users()
            self.model.set_data(users)

            # Auto-resize columns
            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setStretchLastSection(True)

            # Update info
            admin_count = sum(1 for u in users if u['role'] == 'admin')
            user_count = len(users) - admin_count
            self.info_label.setText(f"📊 Total: <b>{len(users)}</b> users | "
                                   f"👑 Admins: <b>{admin_count}</b> | "
                                   f"👤 Users: <b>{user_count}</b>")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {e}")

    def _on_selection_changed(self):
        """Enable/disable buttons based on selection"""
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.reset_pw_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _get_selected_user(self):
        """Get currently selected user"""
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        row = indexes[0].row()
        return self.model.users[row]

    def _add_user(self):
        """Show dialog to add new user"""
        dlg = AddEditUserDialog(self.db, None, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_users()
            self.db.log_action(
                username=self.current_user,
                action="ADDED",
                table_name="users",
                record_id=dlg.username_input.line_edit.text(),
                details=f"Added user: {dlg.name_input.line_edit.text()}"
            )

    def _edit_user(self):
        """Show dialog to edit selected user"""
        user = self._get_selected_user()
        if not user:
            return

        # Prevent editing yourself
        if user['username'] == self.current_user:
            QMessageBox.warning(self, "Cannot Edit",
                              "You cannot edit your own user account while logged in.\n\n"
                              "Ask another administrator to change your details.")
            return

        dlg = AddEditUserDialog(self.db, user, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_users()
            self.db.log_action(
                username=self.current_user,
                action="EDITED",
                table_name="users",
                record_id=user['username'],
                details=f"Edited user: {user['name']}"
            )

    def _reset_password(self):
        """Reset PIN for selected user (v4.6.0: Changed from password to PIN)"""
        user = self._get_selected_user()
        if not user:
            return

        # Prevent resetting your own PIN this way
        if user['username'] == self.current_user:
            QMessageBox.warning(self, "Cannot Reset",
                              "You cannot reset your own PIN through this interface.\n\n"
                              "Please log out and use 'Forgot PIN' at the login screen, "
                              "or contact another administrator.")
            return

        new_pin, ok = QInputDialog.getText(
            self,
            "Reset PIN",
            f"Enter new PIN for <b>{user['name']}</b> (@{user['username']}):\n\n"
            f"PIN must be 4-6 digits only.",
            QLineEdit.Password
        )

        if ok and new_pin:
            # v4.6.0: Use PIN validation instead of password validation
            from employee_vault.config import validate_pin_strength
            is_valid, errors = validate_pin_strength(new_pin)
            if not is_valid:
                QMessageBox.warning(self, "Invalid PIN",
                                  "PIN does not meet requirements:\n\n" +
                                  "\n".join(f"• {err}" for err in errors))
                return

            confirm_pin, ok = QInputDialog.getText(
                self,
                "Confirm PIN",
                "Confirm new PIN:",
                QLineEdit.Password
            )

            if ok and confirm_pin:
                if new_pin != confirm_pin:
                    QMessageBox.warning(self, "PIN Mismatch",
                                      "PINs do not match!")
                    return

                try:
                    self.db.update_user_pin(user['username'], new_pin)
                    QMessageBox.information(self, "Success",
                                          f"PIN reset successfully for {user['name']}!\n\n"
                                          f"They can now log in with their new PIN.")
                    self.db.log_action(
                        username=self.current_user,
                        action="PIN_RESET",
                        table_name="users",
                        record_id=user['username'],
                        details=f"Reset PIN for user: {user['name']}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to reset PIN: {e}")

    def _delete_user(self):
        """Delete selected user"""
        user = self._get_selected_user()
        if not user:
            return

        # Prevent deleting yourself
        if user['username'] == self.current_user:
            QMessageBox.warning(self, "Cannot Delete",
                              "You cannot delete your own user account while logged in!")
            return

        # Prevent deleting the last admin
        if user['role'] == 'admin':
            admin_count = sum(1 for u in self.model.users if u['role'] == 'admin')
            if admin_count <= 1:
                QMessageBox.warning(self, "Cannot Delete",
                                  "Cannot delete the last administrator account!\n\n"
                                  "There must be at least one admin user.")
                return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user:\n\n"
            f"👤 <b>{user['name']}</b> (@{user['username']})\n"
            f"🔰 Role: <b>{user['role'].upper()}</b>\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_user(user['username'])
                QMessageBox.information(self, "Success",
                                      f"User {user['name']} deleted successfully!")
                self._load_users()
                self.db.log_action(
                    username=self.current_user,
                    action="DELETED",
                    table_name="users",
                    record_id=user['username'],
                    details=f"Deleted user: {user['name']}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")

    def _edit_permissions(self):
        """Open permission editor for selected user - v2.0 FIXED"""
        user = self._get_selected_user()
        if not user:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a user to edit permissions.\n\n"
                "Click on a user in the table first."
            )
            return

        username = user['username']

        # Don't allow editing admin permissions
        if username == "admin":
            QMessageBox.information(
                self,
                "Cannot Edit Admin",
                "Administrator permissions cannot be modified.\n\n"
                "Admin always has full access to all features."
            )
            return

        # Open permission editor dialog
        try:
            dialog = PermissionEditorDialog(self.db, username, self)
            if dialog.exec() == QDialog.Accepted:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Permissions updated for user '{user['name']}'.\n\n"
                    f"User must log out and log back in for changes to take effect."
                )

                # Log the change
                logging.info(f"Permissions updated for user: {username}")
                self.db.log_action(
                    username=self.current_user,
                    action="UPDATED",
                    table_name="user_permissions",
                    record_id=username,
                    details=f"Updated permissions for user: {user['name']}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit permissions: {e}")


class AddEditUserDialog(AnimatedDialogBase):
    """Dialog for adding or editing a user"""
    def __init__(self, db, user=None, parent=None):
        # v4.4.1: Use fade animation for user add/edit
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.user = user
        self.is_edit = user is not None

        self.setWindowTitle("✏️ Edit User" if self.is_edit else "➕ Add New User")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Header
        header_text = f"<h3>✏️ Edit User</h3>" if self.is_edit else "<h3>➕ Create New User</h3>"
        layout.addWidget(QLabel(header_text))

        # Form with neumorphic gradient styling
        form = QVBoxLayout()

        # Username
        username_label = QLabel("👤 Username:")
        username_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 5px;")
        form.addWidget(username_label)
        self.username_input = NeumorphicGradientLineEdit("e.g., john_doe")
        self.username_input.setMinimumHeight(70)
        if self.is_edit:
            self.username_input.line_edit.setText(user['username'])
            self.username_input.setEnabled(False)  # Can't change username
        form.addWidget(self.username_input)

        # Full Name
        name_label = QLabel("📝 Full Name:")
        name_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 5px;")
        form.addWidget(name_label)
        self.name_input = NeumorphicGradientLineEdit("e.g., John Doe")
        self.name_input.setMinimumHeight(70)
        if self.is_edit:
            self.name_input.line_edit.setText(user['name'])
        form.addWidget(self.name_input)

        # Role
        role_label = QLabel("🔰 Role:")
        role_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 5px;")
        form.addWidget(role_label)
        self.role_combo = NeumorphicGradientComboBox("Select Role")
        self.role_combo.addItems(["user", "admin"])
        self.role_combo.setMinimumHeight(70)
        if self.is_edit:
            index = self.role_combo.findText(user['role'])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        form.addWidget(self.role_combo)

        # Role description
        role_desc = QLabel(
            "👤 <b>User</b>: Can view, add, and edit employees\n"
            "👑 <b>Admin</b>: Full access including delete and system settings"
        )
        role_desc.setStyleSheet("background: transparent; color: #888; font-size: 12px; margin-bottom: 10px;")
        form.addWidget(role_desc)

        # Password (only for new users)
        if not self.is_edit:
            pw_label = QLabel("🔑 Password:")
            pw_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 5px;")
            form.addWidget(pw_label)

            self.password_input = NeumorphicGradientPasswordInput("Minimum 12 characters (uppercase, lowercase, number, special char)")
            self.password_input.setMinimumHeight(70)
            form.addWidget(self.password_input)

            # PHASE 6: Password strength meter
            self.strength_label = QLabel()
            self.strength_bar = QProgressBar()
            self.strength_bar.setMaximum(100)
            self.strength_bar.setTextVisible(False)
            self.strength_bar.setFixedHeight(8)
            self.strength_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    background-color: rgba(45, 45, 48, 0.95);
                }
                QProgressBar::chunk {
                    border-radius: 3px;
                }
            """)

            strength_container = QWidget()
            strength_layout = QVBoxLayout(strength_container)
            strength_layout.setContentsMargins(0, 0, 0, 0)
            strength_layout.setSpacing(4)
            strength_layout.addWidget(self.strength_bar)
            strength_layout.addWidget(self.strength_label)

            form.addWidget(strength_container)

            # Connect password input to strength meter
            self.password_input.line_edit.textChanged.connect(self._update_password_strength)

            confirm_label = QLabel("🔑 Confirm Password:")
            confirm_label.setStyleSheet("background: transparent; color: rgba(255, 255, 255, 0.9); margin-top: 5px;")
            form.addWidget(confirm_label)

            self.confirm_password_input = NeumorphicGradientPasswordInput("Re-enter password")
            self.confirm_password_input.setMinimumHeight(70)
            form.addWidget(self.confirm_password_input)
        else:
            info = QLabel("ℹ️ Use 'Reset Password' button to change password")
            info.setStyleSheet("background: transparent; color: #4a9eff; font-size: 12px;")
            form.addWidget(info)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons - Phase 3: iOS frosted glass styling
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = ModernAnimatedButton("Cancel")
        apply_ios_style(cancel_btn, 'gray')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = ModernAnimatedButton("💾 Save" if self.is_edit else "➕ Create User")
        apply_ios_style(save_btn, 'green')
        save_btn.clicked.connect(self._save)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save(self):
        """Validate and save user"""
        username = self.username_input.line_edit.text().strip()
        name = self.name_input.line_edit.text().strip()
        role = self.role_combo.currentText()

        # Validation
        if not username:
            QMessageBox.warning(self, "Invalid Input", "Please enter a username.")
            return

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a full name.")
            return

        # Username validation (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            QMessageBox.warning(self, "Invalid Username",
                              "Username can only contain letters, numbers, and underscores.")
            return

        if not self.is_edit:
            # New user - need password
            password = self.password_input.line_edit.text()
            confirm = self.confirm_password_input.line_edit.text()

            if not password:
                QMessageBox.warning(self, "Invalid Input", "Please enter a password.")
                return

            # PHASE 2 FIX: Validate password strength using consistent validation
            from employee_vault.config import validate_password_strength
            is_valid, errors = validate_password_strength(password)
            if not is_valid:
                QMessageBox.critical(self, "Weak Password",
                                   "Password does not meet security requirements:\n\n" +
                                   "\n".join(f"• {err}" for err in errors) +
                                   "\n\nExample: MyP@ssw0rd2024")
                return

            if password != confirm:
                QMessageBox.warning(self, "Password Mismatch",
                                  "Passwords do not match!")
                return

            # Check if username exists
            if self.db.user_exists(username):
                QMessageBox.warning(self, "Username Exists",
                                  f"Username '{username}' already exists!\n\nPlease choose a different username.")
                return

            try:
                self.db.create_user(username, name, password, role)
                QMessageBox.information(self, "Success",
                                      f"User '{name}' created successfully!\n\n"
                                      f"Username: {username}\n"
                                      f"Role: {role.upper()}")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create user: {e}")
        else:
            # Edit existing user
            try:
                self.db.update_user(username, name, role)
                QMessageBox.information(self, "Success",
                                      f"User '{name}' updated successfully!")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update user: {e}")

    def _update_password_strength(self, password):
        """
        PHASE 6: Calculate and display password strength
        Checks: length, uppercase, lowercase, numbers, special chars
        """
        if not password:
            self.strength_bar.setValue(0)
            self.strength_label.setText("")
            return

        strength = 0
        feedback = []

        # Length check (40 points max)
        if len(password) >= 12:
            strength += 40
        elif len(password) >= 8:
            strength += 25
            feedback.append("Longer is better")
        else:
            strength += 10
            feedback.append("Too short")

        # Uppercase letters (15 points)
        if any(c.isupper() for c in password):
            strength += 15
        else:
            feedback.append("Add uppercase")

        # Lowercase letters (15 points)
        if any(c.islower() for c in password):
            strength += 15
        else:
            feedback.append("Add lowercase")

        # Numbers (15 points)
        if any(c.isdigit() for c in password):
            strength += 15
        else:
            feedback.append("Add numbers")

        # Special characters (15 points)
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password):
            strength += 15
        else:
            feedback.append("Add special chars")

        # Update progress bar
        self.strength_bar.setValue(strength)

        # Update color based on strength
        if strength < 40:
            color = "#e74c3c"  # Red - Weak
            text = "❌ Weak"
        elif strength < 70:
            color = "#f39c12"  # Orange - Fair
            text = "⚠️ Fair"
        elif strength < 90:
            color = "#3498db"  # Blue - Good
            text = "✓ Good"
        else:
            color = "#2ecc71"  # Green - Strong
            text = "✓✓ Strong"

        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                background-color: rgba(45, 45, 48, 0.95);
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

        # Update label
        if feedback:
            self.strength_label.setText(f"{text} - {', '.join(feedback)}")
        else:
            self.strength_label.setText(f"{text} - Excellent password!")

        self.strength_label.setStyleSheet(f"color: {color}; font-size: 11px;")


class UserTableModel(QAbstractTableModel):
    """Table model for displaying users"""
    def __init__(self, users):
        super().__init__()
        self.users = users
        self.headers = ["Username", "Full Name", "Role"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.users)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        user = self.users[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return user['username']
            elif col == 1:
                return user['name']
            elif col == 2:
                return user['role'].upper()

        elif role == Qt.ForegroundRole:
            if col == 2:
                # Color code roles
                if user['role'] == 'admin':
                    return QColor("#ff9800")  # Orange for admin
                else:
                    return QColor("#4a9eff")  # Blue for user

        elif role == Qt.TextAlignmentRole:
            if col == 2:
                return Qt.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def set_data(self, users):
        """Update the data"""
        self.beginResetModel()
        self.users = users
        self.endResetModel()



