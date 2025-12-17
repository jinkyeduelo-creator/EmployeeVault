"""
Store Management Dialogs
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
from employee_vault.ui.widgets import apply_table_fixes
from employee_vault.ui.widgets import (
    ModernAnimatedButton, AnimatedDialogBase,
    NeumorphicGradientLineEdit, NeumorphicGradientTextEdit
)

class StoreManagementDialog(AnimatedDialogBase):
    """Dialog for managing stores"""
    def __init__(self, db, parent=None):
        # v4.4.1: Use fade animation for store management
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.setWindowTitle("Manage Stores/Branches")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h2>🏪 Store Management</h2>")
        layout.addWidget(title)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = ModernAnimatedButton("➕ Add Store")
        add_btn.clicked.connect(self.add_store)
        edit_btn = ModernAnimatedButton("✏️ Edit Store")
        edit_btn.clicked.connect(self.edit_store)
        toggle_btn = ModernAnimatedButton("🔄 Activate/Deactivate")
        toggle_btn.clicked.connect(self.toggle_store)
        refresh_btn = ModernAnimatedButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_stores)

        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(toggle_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        apply_table_fixes(self.table)  # v4.5.0: Apply all table fixes
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Company", "Branch", "Address", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setCursor(Qt.ArrowCursor)  # Fix: Use normal arrow cursor instead of IBeam
        self.table.viewport().setCursor(Qt.ArrowCursor)  # Also set on viewport
        self.table.verticalHeader().setVisible(False)  # Fix: Hide vertical header to remove bullets

        # Fix: Remove focus rectangle (the rounded border around focused cells)
        self.table.setStyleSheet("""
            QTableWidget {
                outline: 0;
            }
            QTableWidget::item:focus {
                border: none;
                outline: none;
            }
        """)

        # Add double-click to select functionality
        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

        # Close button
        close_btn = ModernAnimatedButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.load_stores()

    def _on_double_click(self, index):
        """Handle double-click to auto-select store"""
        row = index.row()
        if row >= 0:
            # Get the store ID
            store_id = int(self.table.item(row, 0).text())
            # Close dialog and signal selection
            self.accept()

    def load_stores(self):
        stores = self.db.get_all_stores()
        self.table.setRowCount(len(stores))

        for row, store in enumerate(stores):
            self.table.setItem(row, 0, QTableWidgetItem(str(store['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(store['company_name']))
            self.table.setItem(row, 2, QTableWidgetItem(store['branch_name']))
            self.table.setItem(row, 3, QTableWidgetItem(store.get('address', '')))
            status = "✅ Active" if store['active'] else "❌ Inactive"
            self.table.setItem(row, 4, QTableWidgetItem(status))

    def add_store(self):
        dialog = AddEditStoreDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_stores()

    def edit_store(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a store to edit")
            return

        store_id = int(self.table.item(row, 0).text())
        dialog = AddEditStoreDialog(self.db, store_id=store_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_stores()

    def toggle_store(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a store")
            return

        store_id = int(self.table.item(row, 0).text())
        status_text = self.table.item(row, 4).text()
        is_active = "Active" in status_text

        action = "deactivate" if is_active else "activate"
        reply = QMessageBox.question(self, "Confirm",
                                     f"Are you sure you want to {action} this store?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.toggle_store_active(store_id, not is_active):
                self.load_stores()
            else:
                QMessageBox.critical(self, "Error", "Failed to update store status")


class AddEditStoreDialog(AnimatedDialogBase):
    """Dialog for adding/editing a store"""
    def __init__(self, db, store_id=None, parent=None):
        # v4.4.1: Use fade animation for store add/edit
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.store_id = store_id
        self.setWindowTitle("Edit Store" if store_id else "Add New Store")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.company_edit = NeumorphicGradientLineEdit("Enter company name")
        self.company_edit.setMinimumHeight(70)
        self.branch_edit = NeumorphicGradientLineEdit("Enter branch name")
        self.branch_edit.setMinimumHeight(70)
        self.address_edit = NeumorphicGradientTextEdit("Enter store address...", min_height=100)
        self.address_edit.setMinimumHeight(120)
        self.address_edit.setMaximumHeight(140)

        form.addRow("Company Name:", self.company_edit)
        form.addRow("Branch Name:", self.branch_edit)
        form.addRow("Address:", self.address_edit)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = ModernAnimatedButton("💾 Save")
        save_btn.clicked.connect(self.save_store)
        cancel_btn = ModernAnimatedButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Load existing data if editing
        if self.store_id:
            self.load_store_data()

    def load_store_data(self):
        stores = self.db.get_all_stores()
        for store in stores:
            if store['id'] == self.store_id:
                self.company_edit.line_edit.setText(store['company_name'])
                self.branch_edit.line_edit.setText(store['branch_name'])
                self.address_edit.text_edit.setPlainText(store.get('address', ''))
                break

    def save_store(self):
        company = self.company_edit.line_edit.text().strip()
        branch = self.branch_edit.line_edit.text().strip()
        address = self.address_edit.text_edit.toPlainText().strip()

        if not company or not branch:
            QMessageBox.warning(self, "Warning", "Company and Branch names are required")
            return

        if self.store_id:
            success = self.db.update_store(self.store_id, company, branch, address)
        else:
            success = self.db.add_store(company, branch, address)

        if success:
            QMessageBox.information(self, "Success", "Store saved successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save store")


