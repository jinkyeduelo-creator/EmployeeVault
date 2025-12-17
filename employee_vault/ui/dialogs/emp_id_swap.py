"""
Employee ID Swap Dialog
Allows admin to swap the sequential numbers (NNN) between two employee IDs
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.ui.widgets import AnimatedDialogBase, FloatingLabelLineEdit, PulseButton, ModernAnimatedButton
from employee_vault.ui.modern_ui_helper import show_success_toast, show_error_toast, show_warning_toast
from employee_vault.ui.ios_button_styles import apply_ios_style


class EmpIDSwapDialog(AnimatedDialogBase):
    """
    Dialog for swapping employee ID sequential numbers (NNN)
    Example: O-002-05 and O-003-04 → O-003-05 and O-002-04
    Admin only feature
    """

    def __init__(self, db, current_user, parent=None):
        super().__init__(parent, animation_style="slide")
        self.db = db
        self.current_user = current_user

        self.setWindowTitle("Swap Employee IDs")
        self.resize(600, 450) # Increased height slightly to prevent squashing

        layout = QVBoxLayout(self)
        # Add margins so content doesn't touch edges (Fixes button cut-off at bottom)
        layout.setContentsMargins(25, 25, 25, 25) 

        # Header
        header = QLabel("<h2>🔄 Swap Employee ID Numbers</h2>")
        layout.addWidget(header)

        # --- FIX 2: Removed background color ---
        desc = QLabel(
            "This function allows you to swap the sequential numbers (NNN) between two employee IDs.\n"
            "Example: O-002-05 and O-003-04 will become O-003-05 and O-002-04\n\n"
            "⚠️ This action affects multiple database records and cannot be undone easily."
        )
        desc.setWordWrap(True)
        # Changed background to transparent, kept text color
        desc.setStyleSheet("color: #aaa; padding: 10px; background: transparent;") 
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Employee ID inputs
        form_layout = QFormLayout()

        self.emp_id_1 = FloatingLabelLineEdit("First Employee ID (e.g., O-002-05)")
        self.emp_id_1.setFixedWidth(300)
        form_layout.addRow("Employee ID 1:", self.emp_id_1)

        self.emp_id_2 = FloatingLabelLineEdit("Second Employee ID (e.g., O-003-04)")
        self.emp_id_2.setFixedWidth(300)
        form_layout.addRow("Employee ID 2:", self.emp_id_2)

        layout.addLayout(form_layout)

        layout.addSpacing(20)

        # Preview section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        # --- FIX 2: Removed background color for initial state ---
        self.preview_label = QLabel("Enter both employee IDs to see preview")
        self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #888;")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        # Connect inputs to update preview
        self.emp_id_1.textChanged.connect(self._update_preview)
        self.emp_id_2.textChanged.connect(self._update_preview)

        layout.addStretch()
        layout.addSpacing(15)
        # --- FIX 1: Fixed Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.swap_btn = PulseButton("🔄 Swap Employee IDs")
        apply_ios_style(self.swap_btn, 'blue')
        self.swap_btn.setEnabled(False)
        self.swap_btn.start_pulse()

        # Explicitly set height to ensure text fits
        self.swap_btn.setMinimumHeight(50) 

        cancel_btn = ModernAnimatedButton("❌ Cancel")
        apply_ios_style(cancel_btn, 'gray')

        # Explicitly set height to ensure text fits
        cancel_btn.setMinimumHeight(50)

        btn_layout.addWidget(self.swap_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # Connect signals
        self.swap_btn.clicked.connect(self._perform_swap)
        cancel_btn.clicked.connect(self.reject)

    def _find_employee_by_sequence(self, seq_input):
        """
        Find employee by sequence number (NNN) or full ID.
        Returns the full employee ID if found, or None.
        
        Examples:
            "002" → finds "O-002-05" 
            "O-002-05" → returns "O-002-05"
        """
        seq_input = seq_input.strip().upper()
        
        # If it's already a full ID, return as-is
        if self._parse_emp_id(seq_input):
            return seq_input
        
        # If it's just a number (sequence), search for matching employee
        if seq_input.isdigit():
            # Pad to 3 digits if needed
            seq_padded = seq_input.zfill(3)
            
            # Search all employees for matching sequence
            all_emps = self.db.all_employees()
            for emp in all_emps:
                emp_id = emp.get('emp_id', '')
                parsed = self._parse_emp_id(emp_id)
                if parsed and parsed[1] == seq_padded:
                    return emp_id
        
        return None

    def _parse_emp_id(self, emp_id):
        """
        Parse employee ID into components
        Returns: (prefix, sequence, year) or None if invalid
        Example: "O-002-05" → ("O", "002", "05")
        """
        parts = emp_id.strip().split("-")
        if len(parts) != 3:
            return None

        prefix, seq, year = parts

        # Validate
        if not prefix or not seq.isdigit() or not year.isdigit():
            return None

        if len(seq) != 3 or len(year) != 2:
            return None

        return (prefix, seq, year)

    def _build_emp_id(self, prefix, seq, year):
        """Build employee ID from components"""
        return f"{prefix}-{seq}-{year}"

    def _update_preview(self):
        """Update preview when IDs change"""
        input_1 = self.emp_id_1.text().strip().upper()
        input_2 = self.emp_id_2.text().strip().upper()
        
        if not input_1 or not input_2:
            self.preview_label.setText("Enter both employee IDs to see preview\n\n💡 Tip: You can enter just the number (e.g., 002) or full ID (e.g., O-002-05)")
            self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #888;")
            self.swap_btn.setEnabled(False)
            return

        # Smart lookup - find by sequence number or full ID
        emp_id_1 = self._find_employee_by_sequence(input_1)
        emp_id_2 = self._find_employee_by_sequence(input_2)
        
        if not emp_id_1:
            self.preview_label.setText(f"❌ No employee found with ID or sequence '{input_1}'\n\n💡 Enter the sequence number (e.g., 002) or full ID (e.g., O-002-05)")
            self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #f44336;")
            self.swap_btn.setEnabled(False)
            return
            
        if not emp_id_2:
            self.preview_label.setText(f"❌ No employee found with ID or sequence '{input_2}'\n\n💡 Enter the sequence number (e.g., 003) or full ID (e.g., O-003-04)")
            self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #f44336;")
            self.swap_btn.setEnabled(False)
            return

        # Parse both IDs
        parsed_1 = self._parse_emp_id(emp_id_1)
        parsed_2 = self._parse_emp_id(emp_id_2)

        if not parsed_1 or not parsed_2:
            self.preview_label.setText("❌ Invalid employee ID format. Expected format: X-NNN-YY")
            self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #f44336;")
            self.swap_btn.setEnabled(False)
            return

        prefix_1, seq_1, year_1 = parsed_1
        prefix_2, seq_2, year_2 = parsed_2

        # Check if employees exist (should always exist since we used smart lookup)
        emp_1 = self.db.get_employee(emp_id_1)
        emp_2 = self.db.get_employee(emp_id_2)

        if not emp_1 or not emp_2:
            self.preview_label.setText("❌ Employee not found in database")
            self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #f44336;")
            self.swap_btn.setEnabled(False)
            return
        
        # Store resolved IDs for perform_swap
        self._resolved_id_1 = emp_id_1
        self._resolved_id_2 = emp_id_2

        # Build new IDs
        new_id_1 = self._build_emp_id(prefix_1, seq_2, year_1)
        new_id_2 = self._build_emp_id(prefix_2, seq_1, year_2)

        # Show preview
        preview_text = f"""
<b>Current IDs:</b><br>
• {emp_id_1} → <b>{emp_1['name']}</b><br>
• {emp_id_2} → <b>{emp_2['name']}</b><br>
<br>
<b>After swap:</b><br>
• {new_id_1} → <b>{emp_1['name']}</b> (sequence changed from {seq_1} to {seq_2})<br>
• {new_id_2} → <b>{emp_2['name']}</b> (sequence changed from {seq_2} to {seq_1})<br>
"""

        self.preview_label.setText(preview_text)
        # --- FIX 2: Transparent background, kept text color Green ---
        self.preview_label.setStyleSheet("padding: 10px; background: transparent; color: #4caf50;")
        self.swap_btn.setEnabled(True)

    def _perform_swap(self):
        """Perform the employee ID swap"""
        # Use resolved IDs from preview (supports both sequence and full ID input)
        if not hasattr(self, '_resolved_id_1') or not hasattr(self, '_resolved_id_2'):
            show_error_toast(self, "Please enter valid employee IDs first")
            return
            
        emp_id_1 = self._resolved_id_1
        emp_id_2 = self._resolved_id_2

        # Parse IDs
        parsed_1 = self._parse_emp_id(emp_id_1)
        parsed_2 = self._parse_emp_id(emp_id_2)

        if not parsed_1 or not parsed_2:
            show_error_toast(self, "Invalid employee ID format")
            return

        prefix_1, seq_1, year_1 = parsed_1
        prefix_2, seq_2, year_2 = parsed_2

        # Build new IDs
        new_id_1 = self._build_emp_id(prefix_1, seq_2, year_1)
        new_id_2 = self._build_emp_id(prefix_2, seq_1, year_2)

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Swap",
            f"Are you sure you want to swap these employee IDs?\n\n"
            f"{emp_id_1} → {new_id_1}\n"
            f"{emp_id_2} → {new_id_2}\n\n"
            f"This will update all related records (photos, files, audit logs).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            import logging
            logging.info(f"=== EMPLOYEE ID SWAP START ===")
            logging.info(f"Swapping: {emp_id_1} ↔ {emp_id_2}")
            logging.info(f"New IDs will be: {new_id_1}, {new_id_2}")
            
            # Use a transaction to ensure atomicity
            self.db.conn.execute("BEGIN TRANSACTION")

            # Use temporary IDs to avoid conflicts
            temp_id_1 = f"TEMP_{emp_id_1}"
            temp_id_2 = f"TEMP_{emp_id_2}"

            # Step 1: Move emp_id_1 to temp
            cursor = self.db.conn.execute("UPDATE employees SET emp_id = ? WHERE emp_id = ?", (temp_id_1, emp_id_1))
            logging.info(f"Step 1: {emp_id_1} → {temp_id_1} (rows affected: {cursor.rowcount})")

            # Step 2: Move emp_id_2 to new_id_1
            cursor = self.db.conn.execute("UPDATE employees SET emp_id = ? WHERE emp_id = ?", (new_id_1, emp_id_2))
            logging.info(f"Step 2: {emp_id_2} → {new_id_1} (rows affected: {cursor.rowcount})")

            # Step 3: Move temp to new_id_2
            cursor = self.db.conn.execute("UPDATE employees SET emp_id = ? WHERE emp_id = ?", (new_id_2, temp_id_1))
            logging.info(f"Step 3: {temp_id_1} → {new_id_2} (rows affected: {cursor.rowcount})")

            # Update employee_files table
            try:
                self.db.conn.execute("UPDATE employee_files SET emp_id = ? WHERE emp_id = ?", (temp_id_1, emp_id_1))
                self.db.conn.execute("UPDATE employee_files SET emp_id = ? WHERE emp_id = ?", (new_id_1, emp_id_2))
                self.db.conn.execute("UPDATE employee_files SET emp_id = ? WHERE emp_id = ?", (new_id_2, temp_id_1))
            except Exception as e:
                import logging
                logging.warning(f"Could not update employee_files: {e}")

            # Update audit logs if they exist
            try:
                self.db.conn.execute("UPDATE audit_log SET record_id = ? WHERE record_id = ?", (temp_id_1, emp_id_1))
                self.db.conn.execute("UPDATE audit_log SET record_id = ? WHERE record_id = ?", (new_id_1, emp_id_2))
                self.db.conn.execute("UPDATE audit_log SET record_id = ? WHERE record_id = ?", (new_id_2, temp_id_1))
                logging.info("Updated audit_log records")
            except Exception as e:
                logging.warning(f"Could not update audit_log: {e}")

            # Commit transaction with checkpoint for network drives
            logging.info("Committing transaction...")
            self.db.commit_and_checkpoint()
            logging.info("Transaction committed with checkpoint")

            # Rename photo files
            import os
            from employee_vault.config import PHOTOS_DIR, FILES_DIR

            # Swap photos
            photo_1 = os.path.join(PHOTOS_DIR, f"{emp_id_1}.png")
            photo_2 = os.path.join(PHOTOS_DIR, f"{emp_id_2}.png")
            temp_photo = os.path.join(PHOTOS_DIR, f"TEMP_{emp_id_1}.png")

            if os.path.exists(photo_1):
                os.rename(photo_1, temp_photo)
            if os.path.exists(photo_2):
                os.rename(photo_2, os.path.join(PHOTOS_DIR, f"{new_id_1}.png"))
            if os.path.exists(temp_photo):
                os.rename(temp_photo, os.path.join(PHOTOS_DIR, f"{new_id_2}.png"))

            # Swap file folders
            folder_1 = os.path.join(FILES_DIR, emp_id_1)
            folder_2 = os.path.join(FILES_DIR, emp_id_2)
            temp_folder = os.path.join(FILES_DIR, f"TEMP_{emp_id_1}")

            if os.path.exists(folder_1):
                os.rename(folder_1, temp_folder)
            if os.path.exists(folder_2):
                os.rename(folder_2, os.path.join(FILES_DIR, new_id_1))
            if os.path.exists(temp_folder):
                os.rename(temp_folder, os.path.join(FILES_DIR, new_id_2))

            # Log the action
            try:
                self.db.log_action(
                    username=self.current_user,
                    action="SWAP_EMP_ID",
                    table_name="employees",
                    record_id=f"{emp_id_1},{emp_id_2}",
                    details=f"Swapped IDs: {emp_id_1}↔{emp_id_2} → {new_id_1}↔{new_id_2}"
                )
            except:
                pass

            show_success_toast(
                self,
                f"Successfully swapped employee IDs!\n\n"
                f"{emp_id_1} → {new_id_1}\n"
                f"{emp_id_2} → {new_id_2}"
            )

            self.accept()

        except Exception as e:
            # Rollback on error
            self.db.conn.rollback()
            show_error_toast(
                self,
                f"Failed to swap employee IDs:\n{str(e)}\n\n"
                "The operation has been rolled back."
            )
            import traceback
            import logging
            logging.error(f"Employee ID swap failed: {traceback.format_exc()}")