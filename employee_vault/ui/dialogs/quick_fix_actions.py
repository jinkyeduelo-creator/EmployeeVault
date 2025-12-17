"""
Quick Fix Actions Dialog
One-click actions to fix common data quality issues
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import contract_days_left
from employee_vault.ui.widgets import (
    ModernAnimatedButton, AnimatedDialogBase,
    NeumorphicGradientTextEdit
)
from employee_vault.ui.modern_ui_helper import show_success_toast, show_error_toast, show_warning_toast
from employee_vault.ui.ios_button_styles import apply_ios_style


class QuickFixActionsDialog(AnimatedDialogBase):
    """Dialog for one-click data quality fixes"""

    def __init__(self, db, parent=None):
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.setWindowTitle("🔧 Quick Fix Actions")
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>🔧 Quick Fix Actions</h2>")
        header.setStyleSheet("color: #4a9eff; padding: 10px;")
        layout.addWidget(header)

        instructions = QLabel(
            "<p>Quickly fix common data quality issues with one-click actions.</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)

        # Fix Action Cards
        self._create_fix_card(
            content_layout,
            "📷 Missing Photos",
            "Find employees without profile photos",
            "View Missing Photos",
            self._fix_missing_photos,
            'blue'
        )

        self._create_fix_card(
            content_layout,
            "📋 Incomplete Records",
            "Find employees with missing critical information",
            "View Incomplete Records",
            self._fix_incomplete_records,
            'orange'
        )

        self._create_fix_card(
            content_layout,
            "📅 Expiring Contracts",
            "Extend or renew contracts that are expiring soon",
            "Manage Expiring Contracts",
            self._fix_expiring_contracts,
            'red'
        )

        self._create_fix_card(
            content_layout,
            "🆔 Duplicate Employee IDs",
            "Check for and resolve duplicate employee IDs",
            "Check Duplicates",
            self._check_duplicate_ids,
            'purple'
        )

        self._create_fix_card(
            content_layout,
            "📞 Missing Contact Info",
            "Find employees without phone or email",
            "View Missing Contacts",
            self._fix_missing_contact,
            'green'
        )

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Results area
        self.results_text = NeumorphicGradientTextEdit("Quick fix results will appear here...", min_height=200)
        self.results_text.setMinimumHeight(220)
        self.results_text.text_edit.setReadOnly(True)
        self.results_text.setMaximumHeight(240)
        layout.addWidget(QLabel("<b>Results:</b>"))
        layout.addWidget(self.results_text)

        # Close button
        close_btn = ModernAnimatedButton("✗ Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def _create_fix_card(self, parent_layout, title, description, button_text, action, color):
        """Create a fix action card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.05),
                                           stop:1 rgba(45, 45, 48, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px;
            }
        """)

        card_layout = QHBoxLayout(card)

        # Info section
        info_layout = QVBoxLayout()
        title_label = QLabel(f"<b style='font-size: 16px;'>{title}</b>")
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 13px;")
        desc_label.setWordWrap(True)

        info_layout.addWidget(title_label)
        info_layout.addWidget(desc_label)
        card_layout.addLayout(info_layout, 1)

        # Action button
        btn = ModernAnimatedButton(button_text)
        apply_ios_style(btn, color)
        btn.clicked.connect(action)
        btn.setFixedHeight(50)
        card_layout.addWidget(btn)

        parent_layout.addWidget(card)

    def _fix_missing_photos(self):
        """Find employees without profile photos"""
        self.results_text.text_edit.clear()
        self.results_text.text_edit.append("<b>🔍 Scanning for missing photos...</b>\n")
        QApplication.processEvents()

        try:
            from employee_vault.config import PHOTOS_DIR

            all_employees = self.db.get_all_employees()
            missing_photos = []

            for emp in all_employees:
                emp_id = emp.get('emp_id', '')
                photo_path = os.path.join(PHOTOS_DIR, f"{emp_id}.png")

                if not os.path.exists(photo_path):
                    missing_photos.append(emp)

            if missing_photos:
                self.results_text.text_edit.append(f"<span style='color: #ffaa00;'>⚠</span> Found <b>{len(missing_photos)}</b> employees without photos:\n")

                for emp in missing_photos[:20]:  # Show first 20
                    emp_id = emp.get('emp_id', '')
                    name = emp.get('name', 'Unknown')
                    dept = emp.get('department', 'N/A')
                    self.results_text.text_edit.append(f"  • {emp_id} - {name} ({dept})")

                if len(missing_photos) > 20:
                    self.results_text.text_edit.append(f"\n  ... and {len(missing_photos) - 20} more")

                self.results_text.text_edit.append(f"\n<b>💡 Suggestion:</b> Use 'Batch Photo Upload' to upload multiple photos at once.")

            else:
                self.results_text.text_edit.append("<span style='color: #4CAF50;'>✓</span> All employees have profile photos!")

            logging.info(f"Missing photos check: {len(missing_photos)} found")

        except Exception as e:
            show_error_toast(self, f"Error checking photos:\n{e}")
            logging.error(f"Missing photos check error: {e}")

    def _fix_incomplete_records(self):
        """Find employees with incomplete critical information"""
        self.results_text.text_edit.clear()
        self.results_text.text_edit.append("<b>🔍 Scanning for incomplete records...</b>\n")
        QApplication.processEvents()

        try:
            all_employees = self.db.get_all_employees()
            incomplete = []

            # Critical fields to check
            critical_fields = [
                ('sss_number', 'SSS Number'),
                ('tin_number', 'TIN Number'),
                ('philhealth_number', 'PhilHealth Number'),
                ('emergency_contact', 'Emergency Contact'),
                ('emergency_phone', 'Emergency Phone'),
            ]

            for emp in all_employees:
                missing_fields = []

                for field_name, field_label in critical_fields:
                    value = emp.get(field_name)
                    if not value or str(value).strip() == '':
                        missing_fields.append(field_label)

                if missing_fields:
                    incomplete.append({
                        'employee': emp,
                        'missing': missing_fields
                    })

            if incomplete:
                self.results_text.text_edit.append(f"<span style='color: #ffaa00;'>⚠</span> Found <b>{len(incomplete)}</b> employees with incomplete records:\n")

                for item in incomplete[:15]:  # Show first 15
                    emp = item['employee']
                    emp_id = emp.get('emp_id', '')
                    name = emp.get('name', 'Unknown')
                    missing = ', '.join(item['missing'])
                    self.results_text.text_edit.append(f"  • <b>{emp_id}</b> - {name}")
                    self.results_text.text_edit.append(f"    Missing: {missing}")

                if len(incomplete) > 15:
                    self.results_text.text_edit.append(f"\n  ... and {len(incomplete) - 15} more")

                self.results_text.text_edit.append(f"\n<b>💡 Suggestion:</b> Edit these employees to complete their records.")

            else:
                self.results_text.text_edit.append("<span style='color: #4CAF50;'>✓</span> All employee records are complete!")

            logging.info(f"Incomplete records check: {len(incomplete)} found")

        except Exception as e:
            show_error_toast(self, f"Error checking records:\n{e}")
            logging.error(f"Incomplete records check error: {e}")

    def _fix_expiring_contracts(self):
        """Manage contracts that are expiring soon"""
        self.results_text.text_edit.clear()
        self.results_text.text_edit.append("<b>🔍 Scanning for expiring contracts...</b>\n")
        QApplication.processEvents()

        try:
            all_employees = self.db.get_all_employees()
            expiring = []
            expired = []

            for emp in all_employees:
                days_left = contract_days_left(emp)

                if days_left is not None:
                    if days_left < 0:
                        expired.append((emp, days_left))
                    elif days_left <= 30:
                        expiring.append((emp, days_left))

            # Sort by urgency
            expired.sort(key=lambda x: x[1])
            expiring.sort(key=lambda x: x[1])

            if expired:
                self.results_text.text_edit.append(f"<span style='color: #ff6b6b;'>⚠ EXPIRED:</span> <b>{len(expired)}</b> contracts\n")
                for emp, days in expired[:10]:
                    emp_id = emp.get('emp_id', '')
                    name = emp.get('name', 'Unknown')
                    expiry = emp.get('contract_expiry', 'N/A')
                    self.results_text.text_edit.append(f"  • {emp_id} - {name} (Expired: {expiry})")
                if len(expired) > 10:
                    self.results_text.text_edit.append(f"  ... and {len(expired) - 10} more\n")

            if expiring:
                self.results_text.text_edit.append(f"\n<span style='color: #ffaa00;'>⚠ EXPIRING SOON:</span> <b>{len(expiring)}</b> contracts\n")
                for emp, days in expiring[:10]:
                    emp_id = emp.get('emp_id', '')
                    name = emp.get('name', 'Unknown')
                    expiry = emp.get('contract_expiry', 'N/A')
                    self.results_text.text_edit.append(f"  • {emp_id} - {name} ({days} days left - {expiry})")
                if len(expiring) > 10:
                    self.results_text.text_edit.append(f"  ... and {len(expiring) - 10} more")

            if not expired and not expiring:
                self.results_text.text_edit.append("<span style='color: #4CAF50;'>✓</span> No contracts expiring in the next 30 days!")
            else:
                # Offer to extend contracts
                self.results_text.text_edit.append(f"\n<b>💡 Would you like to extend these contracts?</b>")

                reply = QMessageBox.question(
                    self,
                    "Extend Contracts",
                    f"Found {len(expired) + len(expiring)} contracts that need attention.\n\n"
                    "Would you like to extend them by 1 year?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self._bulk_extend_contracts(expired + expiring)

            logging.info(f"Expiring contracts check: {len(expiring)} expiring, {len(expired)} expired")

        except Exception as e:
            show_error_toast(self, f"Error checking contracts:\n{e}")
            logging.error(f"Expiring contracts check error: {e}")

    def _bulk_extend_contracts(self, contracts_list):
        """Bulk extend contracts by 1 year"""
        try:
            updated = 0

            for emp, _ in contracts_list:
                current_expiry = emp.get('contract_expiry')

                if not current_expiry:
                    continue

                # Parse current expiry date
                try:
                    expiry_date = datetime.strptime(current_expiry, '%Y-%m-%d')
                except:
                    # Try alternate format
                    try:
                        expiry_date = datetime.strptime(current_expiry, '%m/%d/%Y')
                    except:
                        continue

                # Extend by 1 year
                new_expiry = expiry_date + timedelta(days=365)
                new_expiry_str = new_expiry.strftime('%Y-%m-%d')

                # Update employee
                emp_data = emp.copy()
                emp_data['contract_expiry'] = new_expiry_str
                self.db.update_employee(emp_data)
                updated += 1

            self.results_text.text_edit.append(f"\n<span style='color: #4CAF50;'>✓</span> Extended <b>{updated}</b> contracts by 1 year!")
            show_success_toast(self, f"Extended {updated} contracts successfully!")
            logging.info(f"Bulk extended {updated} contracts")

        except Exception as e:
            show_error_toast(self, f"Error extending contracts:\n{e}")
            logging.error(f"Bulk extend contracts error: {e}")

    def _check_duplicate_ids(self):
        """Check for duplicate employee IDs"""
        self.results_text.text_edit.clear()
        self.results_text.text_edit.append("<b>🔍 Checking for duplicate employee IDs...</b>\n")
        QApplication.processEvents()

        try:
            all_employees = self.db.get_all_employees()
            id_map = {}
            duplicates = []

            # Build ID map
            for emp in all_employees:
                emp_id = emp.get('emp_id', '')

                if emp_id in id_map:
                    duplicates.append((emp_id, id_map[emp_id], emp))
                else:
                    id_map[emp_id] = emp

            if duplicates:
                self.results_text.text_edit.append(f"<span style='color: #ff6b6b;'>⚠ WARNING:</span> Found <b>{len(duplicates)}</b> duplicate employee IDs:\n")

                for emp_id, emp1, emp2 in duplicates:
                    name1 = emp1.get('name', 'Unknown')
                    name2 = emp2.get('name', 'Unknown')
                    self.results_text.text_edit.append(f"  • <b>{emp_id}</b>")
                    self.results_text.text_edit.append(f"    - {name1} (ID: {emp1.get('id')})")
                    self.results_text.text_edit.append(f"    - {name2} (ID: {emp2.get('id')})")

                self.results_text.text_edit.append(f"\n<b>⚠ Action Required:</b> Please update duplicate IDs manually to ensure data integrity.")
                show_warning_toast(self, f"Found {len(duplicates)} duplicate IDs!")

            else:
                self.results_text.text_edit.append("<span style='color: #4CAF50;'>✓</span> No duplicate employee IDs found!")

            logging.info(f"Duplicate ID check: {len(duplicates)} found")

        except Exception as e:
            show_error_toast(self, f"Error checking duplicates:\n{e}")
            logging.error(f"Duplicate ID check error: {e}")

    def _fix_missing_contact(self):
        """Find employees without contact information"""
        self.results_text.text_edit.clear()
        self.results_text.text_edit.append("<b>🔍 Scanning for missing contact information...</b>\n")
        QApplication.processEvents()

        try:
            all_employees = self.db.get_all_employees()
            missing_contact = []

            for emp in all_employees:
                phone = emp.get('phone', '')
                email = emp.get('email', '')

                if (not phone or str(phone).strip() == '') and (not email or str(email).strip() == ''):
                    missing_contact.append(emp)

            if missing_contact:
                self.results_text.text_edit.append(f"<span style='color: #ffaa00;'>⚠</span> Found <b>{len(missing_contact)}</b> employees without phone or email:\n")

                for emp in missing_contact[:20]:
                    emp_id = emp.get('emp_id', '')
                    name = emp.get('name', 'Unknown')
                    dept = emp.get('department', 'N/A')
                    self.results_text.text_edit.append(f"  • {emp_id} - {name} ({dept})")

                if len(missing_contact) > 20:
                    self.results_text.text_edit.append(f"\n  ... and {len(missing_contact) - 20} more")

                self.results_text.text_edit.append(f"\n<b>💡 Suggestion:</b> Edit these employees to add phone or email contact information.")

            else:
                self.results_text.text_edit.append("<span style='color: #4CAF50;'>✓</span> All employees have contact information!")

            logging.info(f"Missing contact check: {len(missing_contact)} found")

        except Exception as e:
            show_error_toast(self, f"Error checking contacts:\n{e}")
            logging.error(f"Missing contact check error: {e}")
