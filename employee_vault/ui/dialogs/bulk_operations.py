"""
Bulk Operations Dialog
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
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase
from employee_vault.ui.modern_ui_helper import show_success_toast, show_error_toast, show_warning_toast
from employee_vault.ui.ios_button_styles import apply_ios_style

class BulkOperationsDialog(AnimatedDialogBase):
    """Bulk edit multiple employees at once"""
    def __init__(self, parent, db, employees):
        # v4.4.1: Use fade animation for bulk operations
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.employees = employees
        self.setWindowTitle("📦 Bulk Operations")
        self.resize(550, 450)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>📦 Bulk Operations</h2>"))

        selection_group = QGroupBox("Select Employees")
        selection_layout = QVBoxLayout(selection_group)

        self.employee_list = QListWidget()
        apply_table_fixes(self.employee_list)  # v4.5.0: Apply all table fixes
        self.employee_list.setSelectionMode(QListWidget.MultiSelection)

        for emp in employees:
            status = "" if not emp.get('resign_date') else " [Resigned]"
            item = QListWidgetItem(f"{emp['emp_id']} - {emp['name']} ({emp.get('department', 'N/A')}){status}")
            item.setData(Qt.UserRole, emp)
            self.employee_list.addItem(item)

        selection_layout.addWidget(self.employee_list)

        # Phase 3: iOS frosted glass for selection buttons
        select_btns = QHBoxLayout()
        select_all_btn = ModernAnimatedButton("Select All")
        apply_ios_style(select_all_btn, 'green')
        select_all_btn.clicked.connect(self.employee_list.selectAll)
        select_btns.addWidget(select_all_btn)

        select_none_btn = ModernAnimatedButton("Clear Selection")
        apply_ios_style(select_none_btn, 'gray')
        select_none_btn.clicked.connect(self.employee_list.clearSelection)
        select_btns.addWidget(select_none_btn)

        selection_layout.addLayout(select_btns)
        layout.addWidget(selection_group)

        ops_group = QGroupBox("Choose Operation")
        ops_layout = QVBoxLayout(ops_group)

        # Phase 3: iOS frosted glass for operation buttons
        bulk_dept_btn = ModernAnimatedButton("🏢 Change Department")
        apply_ios_style(bulk_dept_btn, 'blue')
        bulk_dept_btn.clicked.connect(self.bulk_change_department)
        ops_layout.addWidget(bulk_dept_btn)

        bulk_position_btn = ModernAnimatedButton("💼 Change Position")
        apply_ios_style(bulk_position_btn, 'blue')
        bulk_position_btn.clicked.connect(self.bulk_change_position)
        ops_layout.addWidget(bulk_position_btn)

        bulk_agency_btn = ModernAnimatedButton("🏛️ Change Agency")
        apply_ios_style(bulk_agency_btn, 'blue')
        bulk_agency_btn.clicked.connect(self.bulk_change_agency)
        ops_layout.addWidget(bulk_agency_btn)

        bulk_archive_btn = ModernAnimatedButton("📦 Archive Selected")
        apply_ios_style(bulk_archive_btn, 'orange')
        bulk_archive_btn.clicked.connect(self.bulk_archive)
        ops_layout.addWidget(bulk_archive_btn)

        bulk_export_btn = ModernAnimatedButton("📄 Export Selected")
        apply_ios_style(bulk_export_btn, 'green')
        bulk_export_btn.clicked.connect(self.bulk_export)
        ops_layout.addWidget(bulk_export_btn)

        layout.addWidget(ops_group)

        self.status_label = QLabel("Select employees and choose an operation")
        layout.addWidget(self.status_label)

        # Phase 3: iOS frosted glass for Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def get_selected_employees(self):
        return [item.data(Qt.UserRole) for item in self.employee_list.selectedItems()]

    def bulk_change_department(self):
        selected = self.get_selected_employees()
        if not selected:
            show_warning_toast(self, "Please select employees first.")
            return

        dept, ok = QInputDialog.getItem(self, "Change Department",
                                       "New department:",
                                       ["Office", "Warehouse", "Store"], 0, False)
        if not ok: return

        reply = QMessageBox.question(self, "Confirm",
                                    f"Change department to '{dept}' for {len(selected)} employee(s)?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for emp in selected:
                self.db.conn.execute("UPDATE employees SET department=? WHERE emp_id=?",
                    (dept, emp['emp_id']))
            self.db.conn.commit()
            show_success_toast(self, f"Updated {len(selected)} employee(s) successfully!")
            self.status_label.setText(f"✅ Changed department for {len(selected)} employees")

    def bulk_change_position(self):
        selected = self.get_selected_employees()
        if not selected:
            show_warning_toast(self, "Please select employees first.")
            return

        position, ok = QInputDialog.getText(self, "Change Position", "New position:")
        if not ok or not position: return

        reply = QMessageBox.question(self, "Confirm",
                                    f"Change position to '{position}' for {len(selected)} employee(s)?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for emp in selected:
                self.db.conn.execute("UPDATE employees SET position=? WHERE emp_id=?",
                    (position, emp['emp_id']))
            self.db.conn.commit()
            show_success_toast(self, f"Updated {len(selected)} employee(s) successfully!")
            self.status_label.setText(f"✅ Changed position for {len(selected)} employees")

    def bulk_change_agency(self):
        selected = self.get_selected_employees()
        if not selected:
            show_warning_toast(self, "Please select employees first.")
            return

        agencies = ["Direct Hire"] + self.db.get_agencies()
        agency, ok = QInputDialog.getItem(self, "Change Agency", "New agency:", agencies, 0, False)
        if not ok: return

        agency_value = None if agency == "Direct Hire" else agency

        reply = QMessageBox.question(self, "Confirm",
                                    f"Change agency to '{agency}' for {len(selected)} employee(s)?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for emp in selected:
                self.db.conn.execute("UPDATE employees SET agency=? WHERE emp_id=?",
                    (agency_value, emp['emp_id']))
            self.db.conn.commit()
            show_success_toast(self, f"Updated {len(selected)} employee(s) successfully!")
            self.status_label.setText(f"✅ Changed agency for {len(selected)} employees")

    def bulk_archive(self):
        selected = self.get_selected_employees()
        if not selected:
            show_warning_toast(self, "Please select employees first.")
            return

        reason, ok = QInputDialog.getText(self, "Archive Reason", "Reason for archiving:")
        if not ok or not reason: return

        reply = QMessageBox.question(self, "Confirm",
                                    f"Archive {len(selected)} employee(s)?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for emp in selected:
                self.db.archive_employee(emp['emp_id'], "admin", reason)
            show_success_toast(self, f"Archived {len(selected)} employee(s) successfully!")
            self.status_label.setText(f"✅ Archived {len(selected)} employees")

    def bulk_export(self):
        selected = self.get_selected_employees()
        if not selected:
            show_warning_toast(self, "Please select employees first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Selected Employees",
            f"selected_employees_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON Files (*.json)")

        if not filename: return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(selected, f, indent=2, ensure_ascii=False)
            show_success_toast(self, f"Exported {len(selected)} employee(s) successfully!")
            self.status_label.setText(f"✅ Exported {len(selected)} employees")
        except Exception as e:
            show_error_toast(self, f"Export failed: {str(e)}")


# ==================== v2.0 DIALOG CLASSES ====================

class PrintPreviewHelper(AnimatedDialogBase):
    """Print preview dialog"""
    def __init__(self, document_html, parent=None):
        # v4.4.1: Use smooth fade for print preview
        super().__init__(parent, animation_style="fade", animation_duration=250)
        self.setWindowTitle("Print Preview")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        # Web view for preview
        self.web_view = QWebEngineView()
        self.web_view.setHtml(document_html)
        layout.addWidget(self.web_view)

        # Buttons
        btn_layout = QHBoxLayout()
        print_btn = ModernAnimatedButton("🖨️ Print")
        print_btn.clicked.connect(self.print_document)
        cancel_btn = ModernAnimatedButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.should_print = False

    def print_document(self):
        self.should_print = True
        self.accept()


