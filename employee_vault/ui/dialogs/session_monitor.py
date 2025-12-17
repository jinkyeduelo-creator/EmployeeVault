"""
Session Monitor Dialog
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


class SessionMonitorDialog(AnimatedDialogBase):
    """Dialog for monitoring active sessions with idle status and force logout"""
    def __init__(self, db, parent=None, current_user=None):
        # v4.4.1: Use fade animation for session monitor
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.current_user = current_user  # To prevent self-logout
        self.setWindowTitle("Active Sessions")
        self.setMinimumSize(800, 450)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h2>👥 Active Sessions</h2>")
        layout.addWidget(title)

        # Toolbar - Phase 3: iOS frosted glass styling
        toolbar = QHBoxLayout()
        refresh_btn = ModernAnimatedButton("🔄 Refresh")
        apply_ios_style(refresh_btn, 'blue')
        refresh_btn.clicked.connect(self.load_sessions)
        toolbar.addWidget(refresh_btn)
        
        # v4.5.0: Force Logout button for admins
        self.force_logout_btn = ModernAnimatedButton("⚠️ Force Logout Selected")
        apply_ios_style(self.force_logout_btn, 'red')
        self.force_logout_btn.clicked.connect(self._force_logout_selected)
        self.force_logout_btn.setEnabled(False)  # Disabled until selection
        toolbar.addWidget(self.force_logout_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table - added Status column for idle indicator
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Username", "Computer", "Login Time", "Last Activity", "Duration", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # v4.5.0: Apply all table fixes (cursor + focus rectangle)
        apply_table_fixes(self.table)
        self.table.verticalHeader().setVisible(False)  # Hide vertical header to remove bullets
        layout.addWidget(self.table)

        # Close button - Phase 3: iOS frosted glass styling
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.load_sessions()

    def _on_selection_changed(self):
        """Enable/disable force logout button based on selection"""
        selected_rows = self.table.selectionModel().selectedRows()
        self.force_logout_btn.setEnabled(len(selected_rows) > 0)

    def _force_logout_selected(self):
        """Force logout selected sessions"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        usernames = []
        for idx in selected_rows:
            username = self.table.item(idx.row(), 0).text()
            # Prevent self-logout
            if username == self.current_user:
                QMessageBox.warning(self, "Cannot Logout", "You cannot force logout your own session.")
                continue
            usernames.append(username)
        
        if not usernames:
            return
            
        # Confirm
        reply = QMessageBox.question(
            self, "Confirm Force Logout",
            f"Are you sure you want to force logout these users?\n\n" + "\n".join(usernames),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for username in usernames:
                self.db.force_logout_user(username)
            self.load_sessions()  # Refresh
            QMessageBox.information(self, "Success", f"Force logged out {len(usernames)} user(s).")

    def load_sessions(self):
        sessions = self.db.get_active_sessions()
        self.table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            # Store session ID for force logout
            username_item = QTableWidgetItem(session['username'])
            username_item.setData(Qt.UserRole, session.get('id'))  # Store session ID
            self.table.setItem(row, 0, username_item)
            self.table.setItem(row, 1, QTableWidgetItem(session.get('computer_name', 'Unknown')))
            self.table.setItem(row, 2, QTableWidgetItem(session['login_time']))
            self.table.setItem(row, 3, QTableWidgetItem(session['last_activity']))

            # Calculate duration
            try:
                login_time = datetime.fromisoformat(session['login_time'])
                duration = datetime.now() - login_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            except:
                duration_str = "Unknown"

            self.table.setItem(row, 4, QTableWidgetItem(duration_str))
            
            # v4.5.0: Calculate idle status (5 min = idle)
            try:
                last_activity = datetime.fromisoformat(session['last_activity'])
                idle_seconds = (datetime.now() - last_activity).total_seconds()
                if idle_seconds > 300:  # 5 minutes
                    idle_mins = int(idle_seconds // 60)
                    status_item = QTableWidgetItem(f"🔴 Idle ({idle_mins}m)")
                    status_item.setForeground(QColor("#ff6b6b"))
                else:
                    status_item = QTableWidgetItem("🟢 Active")
                    status_item.setForeground(QColor("#4ade80"))
            except:
                status_item = QTableWidgetItem("❓ Unknown")
            
            self.table.setItem(row, 5, status_item)


# ==================== END v2.0 DIALOG CLASSES ====================


