"""
Excel/CSV Import Dialog
Allows importing multiple employees from Excel or CSV files with column mapping
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

try:
    import pandas as pd
except ImportError:
    pd = None

from employee_vault.ui.widgets import (
    ModernAnimatedButton, AnimatedDialogBase,
    NeumorphicGradientLineEdit, NeumorphicGradientTextEdit, NeumorphicGradientComboBox
)
from employee_vault.ui.modern_ui_helper import show_success_toast, show_error_toast, show_warning_toast
from employee_vault.ui.ios_button_styles import apply_ios_style


class ExcelImportDialog(AnimatedDialogBase):
    """Dialog for importing employees from Excel/CSV files"""

    # Database field definitions
    DB_FIELDS = {
        'emp_id': {'label': 'Employee ID*', 'required': True},
        'name': {'label': 'Full Name*', 'required': True},
        'sss_number': {'label': 'SSS Number', 'required': False},
        'tin_number': {'label': 'TIN Number', 'required': False},
        'philhealth_number': {'label': 'PhilHealth Number', 'required': False},
        'pagibig_number': {'label': 'Pag-IBIG Number', 'required': False},
        'department': {'label': 'Department', 'required': False},
        'position': {'label': 'Position', 'required': False},
        'hire_date': {'label': 'Hire Date', 'required': False},
        'salary': {'label': 'Salary', 'required': False},
        'agency': {'label': 'Agency', 'required': False},
        'contract_expiry': {'label': 'Contract Expiry', 'required': False},
        'email': {'label': 'Email', 'required': False},
        'phone': {'label': 'Phone', 'required': False},
        'address': {'label': 'Address', 'required': False},
        'emergency_contact': {'label': 'Emergency Contact', 'required': False},
        'emergency_phone': {'label': 'Emergency Phone', 'required': False},
    }

    def __init__(self, db, parent=None):
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.df = None  # Pandas DataFrame
        self.column_mappings = {}  # Excel column -> DB field mapping

        self.setWindowTitle("📥 Import Employees from Excel/CSV")
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>📥 Import Employees from Excel/CSV</h2>")
        header.setStyleSheet("color: #4a9eff; padding: 10px;")
        layout.addWidget(header)

        # Check if pandas is available
        if pd is None:
            error_label = QLabel(
                "<p style='color: #ff6b6b;'><b>Error:</b> Required library 'pandas' is not installed.</p>"
                "<p>Please install it with: <code>pip install pandas openpyxl</code></p>"
            )
            error_label.setWordWrap(True)
            layout.addWidget(error_label)

            close_btn = ModernAnimatedButton("✗ Close")
            apply_ios_style(close_btn, 'gray')
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return

        # Step indicator
        self.step_label = QLabel("<b>Step 1:</b> Select Excel/CSV file")
        self.step_label.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(self.step_label)

        # Stacked widget for different steps
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        # Step 1: File selection
        self._create_file_selection_page()

        # Step 2: Column mapping
        self._create_column_mapping_page()

        # Step 3: Preview and import
        self._create_preview_page()

        # Navigation buttons
        btn_layout = QHBoxLayout()

        self.back_btn = ModernAnimatedButton("← Back")
        apply_ios_style(self.back_btn, 'gray')
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setEnabled(False)

        self.next_btn = ModernAnimatedButton("Next →")
        apply_ios_style(self.next_btn, 'blue')
        self.next_btn.clicked.connect(self._go_next)
        self.next_btn.setEnabled(False)

        self.import_btn = ModernAnimatedButton("📥 Import Employees")
        apply_ios_style(self.import_btn, 'green')
        self.import_btn.clicked.connect(self._import_employees)
        self.import_btn.setVisible(False)

        close_btn = ModernAnimatedButton("✗ Cancel")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.back_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _create_file_selection_page(self):
        """Step 1: File selection"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Instructions
        instructions = QLabel(
            "<p><b>Instructions:</b></p>"
            "<ul>"
            "<li>Select an Excel (.xlsx, .xls) or CSV (.csv) file</li>"
            "<li>The file should have a header row with column names</li>"
            "<li>Required fields: <b>Employee ID</b> and <b>Full Name</b></li>"
            "<li>Other fields are optional but recommended</li>"
            "</ul>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # File selection
        file_group = QGroupBox("Select File")
        file_layout = QVBoxLayout(file_group)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("File:"))
        self.file_path = NeumorphicGradientLineEdit("Select an Excel or CSV file...")
        self.file_path.setMinimumHeight(70)
        self.file_path.line_edit.setReadOnly(True)
        file_row.addWidget(self.file_path, 1)

        browse_btn = ModernAnimatedButton("📁 Browse")
        apply_ios_style(browse_btn, 'blue')
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        file_layout.addLayout(file_row)

        layout.addWidget(file_group)

        # File info
        self.file_info = NeumorphicGradientTextEdit("File information will appear here...", min_height=150)
        self.file_info.setMinimumHeight(170)
        self.file_info.text_edit.setReadOnly(True)
        self.file_info.setMaximumHeight(190)
        layout.addWidget(QLabel("<b>File Information:</b>"))
        layout.addWidget(self.file_info)

        layout.addStretch(1)
        self.stack.addWidget(page)

    def _create_column_mapping_page(self):
        """Step 2: Column mapping"""
        page = QWidget()
        layout = QVBoxLayout(page)

        instructions = QLabel(
            "<p><b>Map Excel/CSV columns to database fields:</b></p>"
            "<p>Fields marked with <span style='color: #ff6b6b;'>*</span> are required.</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Scrollable mapping area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                background-color: rgba(45, 45, 48, 0.5);
            }
        """)

        mapping_widget = QWidget()
        self.mapping_layout = QFormLayout(mapping_widget)
        self.mapping_layout.setSpacing(10)

        self.mapping_combos = {}

        scroll.setWidget(mapping_widget)
        layout.addWidget(scroll, 1)

        # Auto-map button
        auto_btn = ModernAnimatedButton("🔄 Auto-Map Columns")
        apply_ios_style(auto_btn, 'blue')
        auto_btn.clicked.connect(self._auto_map_columns)
        layout.addWidget(auto_btn)

        self.stack.addWidget(page)

    def _create_preview_page(self):
        """Step 3: Preview and import"""
        page = QWidget()
        layout = QVBoxLayout(page)

        instructions = QLabel(
            "<p><b>Preview imported data:</b></p>"
            "<p>Review the data below and choose how to handle duplicates.</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Duplicate handling
        dup_group = QGroupBox("Duplicate Handling")
        dup_layout = QHBoxLayout(dup_group)

        self.dup_skip = QRadioButton("Skip duplicates (keep existing)")
        self.dup_skip.setChecked(True)
        self.dup_update = QRadioButton("Update existing employees")
        self.dup_prompt = QRadioButton("Prompt for each duplicate")

        dup_layout.addWidget(self.dup_skip)
        dup_layout.addWidget(self.dup_update)
        dup_layout.addWidget(self.dup_prompt)
        dup_layout.addStretch(1)

        layout.addWidget(dup_group)

        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(45, 45, 48, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QHeaderView::section {
                background-color: rgba(74, 158, 255, 0.3);
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout.addWidget(QLabel("<b>Data Preview (first 100 rows):</b>"))
        layout.addWidget(self.preview_table, 1)

        # Summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 13px; padding: 8px;")
        layout.addWidget(self.summary_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                text-align: center;
                background-color: rgba(45, 45, 48, 0.95);
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                 stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress)

        self.stack.addWidget(page)

    def _browse_file(self):
        """Browse for Excel/CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel or CSV File",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            self.file_path.line_edit.setText(file_path)
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """Load Excel/CSV file into pandas DataFrame"""
        try:
            self.file_info.text_edit.clear()
            self.file_info.text_edit.append(f"📂 Loading file: {os.path.basename(file_path)}")

            # Read file based on extension
            ext = Path(file_path).suffix.lower()

            if ext == '.csv':
                self.df = pd.read_csv(file_path)
                self.file_info.text_edit.append("✓ CSV file loaded successfully")
            elif ext in ['.xlsx', '.xls']:
                self.df = pd.read_excel(file_path)
                self.file_info.text_edit.append("✓ Excel file loaded successfully")
            else:
                show_error_toast(self, "Unsupported file format")
                return

            # Display file info
            self.file_info.text_edit.append(f"\n📊 <b>File Statistics:</b>")
            self.file_info.text_edit.append(f"  • Rows: {len(self.df)}")
            self.file_info.text_edit.append(f"  • Columns: {len(self.df.columns)}")
            self.file_info.text_edit.append(f"\n<b>Columns found:</b>")

            for col in self.df.columns[:20]:  # Show first 20 columns
                self.file_info.text_edit.append(f"  • {col}")

            if len(self.df.columns) > 20:
                self.file_info.text_edit.append(f"  ... and {len(self.df.columns) - 20} more")

            self.next_btn.setEnabled(True)
            logging.info(f"Loaded import file: {file_path} ({len(self.df)} rows)")

        except Exception as e:
            show_error_toast(self, f"Error loading file:\n{e}")
            logging.error(f"Import file load error: {e}")
            self.next_btn.setEnabled(False)

    def _populate_mapping_combos(self):
        """Populate the column mapping dropdowns"""
        # Clear existing
        for i in reversed(range(self.mapping_layout.rowCount())):
            self.mapping_layout.removeRow(i)
        self.mapping_combos.clear()

        if self.df is None:
            return

        excel_columns = ['(Not mapped)'] + list(self.df.columns)

        # Create combo boxes for each DB field
        for field_name, field_info in self.DB_FIELDS.items():
            label_text = field_info['label']
            if field_info['required']:
                label_text += ' <span style="color: #ff6b6b;">*</span>'

            label = QLabel(label_text)
            combo = NeumorphicGradientComboBox("(Not mapped)")
            combo.setMinimumHeight(70)
            combo.combo_box.addItems(excel_columns)

            self.mapping_combos[field_name] = combo
            self.mapping_layout.addRow(label, combo)

    def _auto_map_columns(self):
        """Automatically map columns based on similar names"""
        if self.df is None:
            return

        excel_cols_lower = {col.lower(): col for col in self.df.columns}

        # Mapping patterns (DB field -> possible Excel column names)
        patterns = {
            'emp_id': ['employee id', 'emp id', 'id', 'employee number', 'emp no'],
            'name': ['name', 'full name', 'employee name', 'fullname'],
            'sss_number': ['sss', 'sss number', 'sss no', 'sss#'],
            'tin_number': ['tin', 'tin number', 'tin no', 'tin#'],
            'philhealth_number': ['philhealth', 'philhealth number', 'phil health', 'philhealth no'],
            'pagibig_number': ['pagibig', 'pag-ibig', 'pagibig number', 'pag-ibig no'],
            'department': ['department', 'dept', 'division'],
            'position': ['position', 'job title', 'title', 'designation'],
            'hire_date': ['hire date', 'date hired', 'employment date', 'start date'],
            'salary': ['salary', 'monthly salary', 'basic salary', 'wage'],
            'agency': ['agency', 'employment agency'],
            'contract_expiry': ['contract expiry', 'contract end', 'expiry date', 'end date'],
            'email': ['email', 'email address', 'e-mail'],
            'phone': ['phone', 'mobile', 'contact number', 'mobile number', 'phone number'],
            'address': ['address', 'home address', 'residential address'],
            'emergency_contact': ['emergency contact', 'emergency contact name', 'next of kin'],
            'emergency_phone': ['emergency phone', 'emergency contact number', 'emergency number'],
        }

        mapped_count = 0

        for field_name, possible_names in patterns.items():
            combo = self.mapping_combos.get(field_name)
            if not combo:
                continue

            # Try to find a match
            for pattern in possible_names:
                if pattern in excel_cols_lower:
                    excel_col = excel_cols_lower[pattern]
                    index = combo.combo_box.findText(excel_col)
                    if index >= 0:
                        combo.combo_box.setCurrentIndex(index)
                        mapped_count += 1
                        break

        if mapped_count > 0:
            show_success_toast(self, f"Auto-mapped {mapped_count} columns!")
        else:
            show_warning_toast(self, "Could not auto-map columns. Please map manually.")

    def _go_back(self):
        """Go to previous step"""
        current = self.stack.currentIndex()
        if current > 0:
            self.stack.setCurrentIndex(current - 1)
            self._update_navigation()

    def _go_next(self):
        """Go to next step"""
        current = self.stack.currentIndex()

        if current == 0:
            # Going from file selection to column mapping
            if self.df is None:
                show_warning_toast(self, "Please select a file first")
                return
            self._populate_mapping_combos()
            self.stack.setCurrentIndex(1)

        elif current == 1:
            # Going from column mapping to preview
            if not self._validate_mappings():
                return
            self._build_preview()
            self.stack.setCurrentIndex(2)

        self._update_navigation()

    def _update_navigation(self):
        """Update navigation buttons based on current step"""
        current = self.stack.currentIndex()

        # Update step label
        if current == 0:
            self.step_label.setText("<b>Step 1:</b> Select Excel/CSV file")
        elif current == 1:
            self.step_label.setText("<b>Step 2:</b> Map columns to database fields")
        elif current == 2:
            self.step_label.setText("<b>Step 3:</b> Preview and import")

        # Update buttons
        self.back_btn.setEnabled(current > 0)
        self.next_btn.setVisible(current < 2)
        self.import_btn.setVisible(current == 2)

    def _validate_mappings(self) -> bool:
        """Validate that required fields are mapped"""
        self.column_mappings.clear()

        missing_required = []

        for field_name, field_info in self.DB_FIELDS.items():
            combo = self.mapping_combos.get(field_name)
            if not combo:
                continue

            selected = combo.combo_box.currentText()

            if selected != '(Not mapped)':
                self.column_mappings[field_name] = selected
            elif field_info['required']:
                missing_required.append(field_info['label'])

        if missing_required:
            show_error_toast(
                self,
                f"Required fields not mapped:\n" + "\n".join(f"• {f}" for f in missing_required)
            )
            return False

        return True

    def _build_preview(self):
        """Build preview table from mapped data"""
        if self.df is None or not self.column_mappings:
            return

        # Create preview DataFrame with mapped columns
        preview_df = pd.DataFrame()

        for db_field, excel_col in self.column_mappings.items():
            if excel_col in self.df.columns:
                preview_df[self.DB_FIELDS[db_field]['label']] = self.df[excel_col]

        # Populate table (first 100 rows)
        preview_data = preview_df.head(100)

        self.preview_table.clear()
        self.preview_table.setRowCount(len(preview_data))
        self.preview_table.setColumnCount(len(preview_data.columns))
        self.preview_table.setHorizontalHeaderLabels(preview_data.columns)

        for row_idx, (_, row) in enumerate(preview_data.iterrows()):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                self.preview_table.setItem(row_idx, col_idx, item)

        self.preview_table.resizeColumnsToContents()

        # Update summary
        total_rows = len(self.df)
        self.summary_label.setText(
            f"<b>Total rows to import:</b> {total_rows} employees\n"
            f"<b>Mapped fields:</b> {len(self.column_mappings)} fields"
        )

    def _import_employees(self):
        """Import employees from the loaded data"""
        if self.df is None or not self.column_mappings:
            show_warning_toast(self, "No data to import")
            return

        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.df))
        self.import_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.back_btn.setEnabled(False)

        try:
            # Get existing employee IDs
            existing_employees = self.db.get_all_employees()
            existing_ids = {emp['emp_id']: emp for emp in existing_employees}

            success_count = 0
            skipped_count = 0
            updated_count = 0
            error_count = 0

            for idx, row in self.df.iterrows():
                self.progress.setValue(idx + 1)
                QApplication.processEvents()

                # Build employee data dictionary
                emp_data = {}
                for db_field, excel_col in self.column_mappings.items():
                    value = row.get(excel_col)
                    # Convert NaN to None
                    emp_data[db_field] = None if pd.isna(value) else str(value)

                emp_id = emp_data.get('emp_id')

                if not emp_id:
                    error_count += 1
                    continue

                # Handle duplicates
                if emp_id in existing_ids:
                    if self.dup_skip.isChecked():
                        skipped_count += 1
                        continue
                    elif self.dup_update.isChecked():
                        # Update existing employee
                        try:
                            emp_data['id'] = existing_ids[emp_id]['id']
                            self.db.update_employee(emp_data)
                            updated_count += 1
                            logging.info(f"Updated employee via import: {emp_id}")
                        except Exception as e:
                            logging.error(f"Error updating {emp_id}: {e}")
                            error_count += 1
                        continue
                    else:  # Prompt for each
                        reply = QMessageBox.question(
                            self,
                            "Duplicate Found",
                            f"Employee '{emp_id}' already exists.\n\nUpdate or skip?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            try:
                                emp_data['id'] = existing_ids[emp_id]['id']
                                self.db.update_employee(emp_data)
                                updated_count += 1
                            except Exception as e:
                                logging.error(f"Error updating {emp_id}: {e}")
                                error_count += 1
                        else:
                            skipped_count += 1
                        continue

                # Add new employee
                try:
                    self.db.add_employee(emp_data)
                    success_count += 1
                    logging.info(f"Imported new employee: {emp_id}")
                except Exception as e:
                    logging.error(f"Error importing {emp_id}: {e}")
                    error_count += 1

            # Show results
            result_msg = (
                f"Import Complete!\n\n"
                f"✓ Added: {success_count}\n"
                f"🔄 Updated: {updated_count}\n"
                f"⊘ Skipped: {skipped_count}\n"
                f"✗ Errors: {error_count}"
            )

            if error_count > 0:
                show_warning_toast(self, result_msg)
            else:
                show_success_toast(self, result_msg)

            logging.info(f"Import completed: {success_count} added, {updated_count} updated")

            # Close dialog after successful import
            if success_count > 0 or updated_count > 0:
                self.accept()

        except Exception as e:
            show_error_toast(self, f"Import error:\n{e}")
            logging.error(f"Employee import error: {e}")
        finally:
            self.progress.setVisible(False)
            self.import_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.back_btn.setEnabled(True)
