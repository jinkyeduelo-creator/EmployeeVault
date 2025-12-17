"""
Permission Editor Dialog
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
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase

class PermissionEditorDialog(AnimatedDialogBase):
    """Dialog for editing user permissions"""
    def __init__(self, db, username, parent=None):
        # v4.4.1: Use fade animation for permissions
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.username = username
        self.setWindowTitle(f"Edit Permissions - {username}")
        self.setMinimumSize(600, 700)

        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(f"<b>Configure permissions for user: {username}</b>")
        layout.addWidget(info)

        # Scroll area for permissions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Load current permissions
        self.perms = self.db.get_user_permissions(username)

        # Permission checkboxes
        self.perm_checks = {}

        perm_groups = {
            "Dashboard & Employees": [
                ("dashboard", "Access Dashboard"),
                ("employees", "View Employees"),
                ("add_employee", "Add New Employees"),
                ("edit_employee", "Edit Employees"),
                ("delete_employee", "Delete Employees"),
            ],
            "Features": [
                ("print_system", "Access Printing System"),
                ("bulk_operations", "Bulk Operations"),
                ("reports", "Generate Reports"),
                ("letters", "Generate Letters"),
            ],
            "Administration": [
                ("user_management", "Manage Users"),
                ("settings", "Access Settings"),
                ("audit_log", "View Audit Log"),
                ("backup_restore", "Backup & Restore"),
                ("archive", "Archive Management"),
            ]
        }

        for group_name, permissions in perm_groups.items():
            group_box = QGroupBox(group_name)
            group_layout = QVBoxLayout()

            for perm_key, perm_label in permissions:
                cb = QCheckBox(perm_label)
                cb.setChecked(self.perms.get(perm_key, False))
                self.perm_checks[perm_key] = cb
                group_layout.addWidget(cb)

            group_box.setLayout(group_layout)
            scroll_layout.addWidget(group_box)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = ModernAnimatedButton("💾 Save Permissions")
        save_btn.clicked.connect(self.save_permissions)
        cancel_btn = ModernAnimatedButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_permissions(self):
        new_perms = {}
        for key, cb in self.perm_checks.items():
            new_perms[key] = cb.isChecked()

        if self.db.update_user_permissions(self.username, new_perms):
            QMessageBox.information(self, "Success", "Permissions updated successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to update permissions")


