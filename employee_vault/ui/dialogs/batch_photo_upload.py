"""
Batch Photo Upload from ZIP or Folder
Allows uploading multiple employee photos from a ZIP file or folder
"""

import os
import zipfile
import logging
from typing import Dict, List
from pathlib import Path

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import PHOTOS_DIR
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase
from employee_vault.ui.modern_ui_helper import show_success_toast, show_error_toast, show_warning_toast
from employee_vault.ui.ios_button_styles import apply_ios_style


class BatchPhotoUploadDialog(AnimatedDialogBase):
    """Dialog for batch uploading employee photos from ZIP or folder"""

    def __init__(self, db, parent=None):
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.source_type = "folder"  # "zip" or "folder"
        self.selected_path = None
        
        self.setWindowTitle("📦 Batch Photo Upload")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>📦 Batch Photo Upload</h2>")
        header.setStyleSheet("color: #4a9eff; padding: 10px;")
        layout.addWidget(header)

        # Instructions
        instructions = QLabel(
            "<p>Upload multiple employee photos at once from a <b>folder</b> or <b>ZIP file</b>.</p>"
            "<p><b>Photo Naming Format:</b></p>"
            "<ul>"
            "<li>Photos must be named with Employee ID (e.g., <b>O-001-23.jpg</b>, <b>O-002-23.png</b>)</li>"
            "<li>Supported formats: JPG, JPEG, PNG, BMP, GIF</li>"
            "<li>Photos can be in root or subdirectories</li>"
            "</ul>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Source type selection
        source_group = QGroupBox("Source Type")
        source_layout = QHBoxLayout(source_group)
        
        self.folder_radio = QRadioButton("📁 Folder")
        self.folder_radio.setChecked(True)
        self.folder_radio.toggled.connect(self._on_source_changed)
        
        self.zip_radio = QRadioButton("📦 ZIP File")
        self.zip_radio.toggled.connect(self._on_source_changed)
        
        source_layout.addWidget(self.folder_radio)
        source_layout.addWidget(self.zip_radio)
        source_layout.addStretch(1)
        layout.addWidget(source_group)

        # File/Folder selection
        file_layout = QHBoxLayout()
        self.source_label = QLabel("Folder:")
        file_layout.addWidget(self.source_label)
        self.file_path = NeumorphicGradientLineEdit("Select source path...")
        self.file_path.setMinimumHeight(70)
        self.file_path.line_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path, 1)

        self.browse_btn = ModernAnimatedButton("📁 Browse Folder")
        apply_ios_style(self.browse_btn, 'blue')
        self.browse_btn.clicked.connect(self._browse_source)
        file_layout.addWidget(self.browse_btn)
        layout.addLayout(file_layout)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.remove_bg_check = QCheckBox("Remove background from photos (AI)")
        self.remove_bg_check.setChecked(False)
        self.remove_bg_check.setToolTip("Use AI to remove background from photos (slower)")
        options_layout.addWidget(self.remove_bg_check)
        
        self.overwrite_check = QCheckBox("Overwrite existing photos")
        self.overwrite_check.setChecked(True)
        self.overwrite_check.setToolTip("Replace existing photos with new ones")
        options_layout.addWidget(self.overwrite_check)
        
        layout.addWidget(options_group)

        # Results area
        self.results_text = NeumorphicGradientTextEdit("Upload results will appear here...", min_height=200)
        self.results_text.setMinimumHeight(220)
        self.results_text.text_edit.setReadOnly(True)
        layout.addWidget(QLabel("<b>Results:</b>"))
        layout.addWidget(self.results_text, 1)

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
                                                 stop:0 #2196F3, stop:1 #42A5F5);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress)

        # Buttons
        btn_layout = QHBoxLayout()

        self.upload_btn = ModernAnimatedButton("📤 Upload Photos")
        apply_ios_style(self.upload_btn, 'green')
        self.upload_btn.clicked.connect(self._upload_photos)
        self.upload_btn.setEnabled(False)

        close_btn = ModernAnimatedButton("✗ Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _on_source_changed(self):
        """Handle source type change"""
        if self.folder_radio.isChecked():
            self.source_type = "folder"
            self.source_label.setText("Folder:")
            self.browse_btn.setText("📁 Browse Folder")
        else:
            self.source_type = "zip"
            self.source_label.setText("ZIP File:")
            self.browse_btn.setText("📦 Browse ZIP")
        
        # Clear selection
        self.file_path.line_edit.clear()
        self.results_text.text_edit.clear()
        self.upload_btn.setEnabled(False)
        self.selected_path = None

    def _browse_source(self):
        """Browse for folder or ZIP file"""
        if self.source_type == "folder":
            folder = QFileDialog.getExistingDirectory(
                self,
                "Select Folder with Employee Photos",
                "",
                QFileDialog.ShowDirsOnly
            )
            if folder:
                self.selected_path = folder
                self.file_path.setText(folder)
                self.upload_btn.setEnabled(True)
                self.results_text.text_edit.clear()
                self.results_text.append(f"✓ Folder selected: {folder}")
                self._preview_folder(folder)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select ZIP File with Employee Photos",
                "",
                "ZIP Files (*.zip)"
            )
            if file_path:
                self.selected_path = file_path
                self.file_path.setText(file_path)
                self.upload_btn.setEnabled(True)
                self.results_text.text_edit.clear()
                self.results_text.append(f"✓ ZIP file selected: {os.path.basename(file_path)}")
                self._preview_zip(file_path)

    def _preview_folder(self, folder_path):
        """Preview contents of folder"""
        try:
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
            image_files = []
            
            # Recursively find all images
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(image_extensions):
                        image_files.append(os.path.join(root, file))
            
            self.results_text.append(f"\n📊 <b>Folder Contents:</b>")
            self.results_text.append(f"  • Image files found: {len(image_files)}")
            self.results_text.append(f"\n<b>Images found:</b>")
            
            for img in image_files[:20]:  # Show first 20
                self.results_text.append(f"  • {os.path.basename(img)}")
            
            if len(image_files) > 20:
                self.results_text.append(f"  ... and {len(image_files) - 20} more")
                
        except Exception as e:
            show_error_toast(self, f"Error reading folder:\n{e}")
            logging.error(f"Error previewing folder: {e}")

    def _preview_zip(self, zip_path):
        """Preview contents of ZIP file"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files = [f for f in zip_ref.namelist() if not f.endswith('/')]
                image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

                self.results_text.append(f"\n📊 <b>ZIP Contents:</b>")
                self.results_text.append(f"  • Total files: {len(files)}")
                self.results_text.append(f"  • Image files: {len(image_files)}")
                self.results_text.append(f"\n<b>Images found:</b>")

                for img in image_files[:20]:  # Show first 20
                    self.results_text.append(f"  • {os.path.basename(img)}")

                if len(image_files) > 20:
                    self.results_text.append(f"  ... and {len(image_files) - 20} more")

        except Exception as e:
            show_error_toast(self, f"Error reading ZIP file:\n{e}")
            logging.error(f"Error previewing ZIP: {e}")

    def _extract_employee_id(self, filename: str) -> str:
        """Extract employee ID from filename"""
        # Remove extension
        name = Path(filename).stem

        # Common patterns:
        # O-001-23.jpg -> O-001-23
        # O-001-23_photo.jpg -> O-001-23
        # employee_O-001-23.jpg -> O-001-23

        # Look for pattern: Letter-###-## (e.g., O-001-23, S-045-24)
        import re
        match = re.search(r'([A-Z]-\d{3}-\d{2})', name.upper())
        if match:
            return match.group(1)

        # Return cleaned filename if no pattern found
        return name.strip()

    def _upload_photos(self):
        """Upload photos from folder or ZIP file"""
        if not self.selected_path:
            show_warning_toast(self, "Please select a source first")
            return
            
        if self.source_type == "folder":
            self._upload_from_folder()
        else:
            self._upload_from_zip()

    def _upload_from_folder(self):
        """Upload photos from a folder"""
        folder_path = self.selected_path
        if not folder_path or not os.path.isdir(folder_path):
            show_warning_toast(self, "Please select a valid folder")
            return

        self.results_text.text_edit.clear()
        self.results_text.append("<b>🚀 Starting batch upload from folder...</b>\n")
        self.progress.setVisible(True)
        self.upload_btn.setEnabled(False)

        try:
            # Get all employees for matching
            all_employees = self.db.get_all_employees()
            emp_ids = {emp['emp_id']: emp for emp in all_employees}

            self.results_text.append(f"📋 Found {len(emp_ids)} employees in database\n")

            # Find all image files
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
            image_files = []
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(image_extensions):
                        image_files.append(os.path.join(root, file))

            self.progress.setMaximum(len(image_files))
            successful = 0
            failed = 0
            not_found = 0
            skipped = 0

            for idx, img_path in enumerate(image_files):
                self.progress.setValue(idx + 1)
                QApplication.processEvents()

                filename = os.path.basename(img_path)
                emp_id = self._extract_employee_id(filename)

                if emp_id in emp_ids:
                    dest_path = os.path.join(PHOTOS_DIR, f"{emp_id}.png")
                    
                    # Check if photo exists and overwrite option
                    if os.path.exists(dest_path) and not self.overwrite_check.isChecked():
                        self.results_text.append(
                            f"<span style='color: #888888;'>⊘</span> {filename} - Photo exists, skipped"
                        )
                        skipped += 1
                        continue
                    
                    try:
                        # Load and process image
                        pixmap = QPixmap(img_path)

                        if not pixmap.isNull():
                            # Optionally remove background
                            if self.remove_bg_check.isChecked():
                                try:
                                    from employee_vault.utils import remove_background
                                    import tempfile
                                    
                                    # Save to temp, remove bg, load back
                                    temp_file = os.path.join(tempfile.gettempdir(), f"temp_{emp_id}.png")
                                    pixmap.save(temp_file, "PNG")
                                    remove_background(temp_file, temp_file)
                                    pixmap = QPixmap(temp_file)
                                    os.remove(temp_file)
                                except Exception as bg_err:
                                    logging.warning(f"Background removal failed for {emp_id}: {bg_err}")
                            
                            pixmap.save(dest_path, "PNG")
                            emp_name = emp_ids[emp_id].get('name', 'Unknown')
                            self.results_text.append(
                                f"<span style='color: #4CAF50;'>✓</span> {filename} → {emp_id} ({emp_name})"
                            )
                            successful += 1
                            logging.info(f"Batch photo uploaded: {emp_id}")
                        else:
                            self.results_text.append(
                                f"<span style='color: #ff6b6b;'>✗</span> {filename} - Invalid image"
                            )
                            failed += 1
                    except Exception as e:
                        self.results_text.append(
                            f"<span style='color: #ff6b6b;'>✗</span> {filename} - Error: {e}"
                        )
                        failed += 1
                        logging.error(f"Error processing {filename}: {e}")
                else:
                    self.results_text.append(
                        f"<span style='color: #ffaa00;'>⚠</span> {filename} - Employee '{emp_id}' not found"
                    )
                    not_found += 1

            # Summary
            self._show_summary(successful, failed, not_found, skipped)

        except Exception as e:
            show_error_toast(self, f"Error processing folder:\n{e}")
            logging.error(f"Batch photo upload error: {e}")
        finally:
            self.progress.setVisible(False)
            self.upload_btn.setEnabled(True)

    def _upload_from_zip(self):
        """Upload photos from ZIP file"""
        zip_path = self.selected_path
        if not zip_path or not os.path.exists(zip_path):
            show_warning_toast(self, "Please select a valid ZIP file")
            return

        self.results_text.text_edit.clear()
        self.results_text.append("<b>🚀 Starting batch upload from ZIP...</b>\n")
        self.progress.setVisible(True)
        self.upload_btn.setEnabled(False)

        try:
            # Get all employees for matching
            all_employees = self.db.get_all_employees()
            emp_ids = {emp['emp_id']: emp for emp in all_employees}

            self.results_text.append(f"📋 Found {len(emp_ids)} employees in database\n")

            # Extract and process photos
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                image_files = [f for f in zip_ref.namelist()
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))
                              and not f.endswith('/')]

                self.progress.setMaximum(len(image_files))
                successful = 0
                failed = 0
                not_found = 0
                skipped = 0

                for idx, img_path in enumerate(image_files):
                    self.progress.setValue(idx + 1)
                    QApplication.processEvents()

                    filename = os.path.basename(img_path)
                    emp_id = self._extract_employee_id(filename)

                    if emp_id in emp_ids:
                        dest_path = os.path.join(PHOTOS_DIR, f"{emp_id}.png")
                        
                        # Check if photo exists and overwrite option
                        if os.path.exists(dest_path) and not self.overwrite_check.isChecked():
                            self.results_text.append(
                                f"<span style='color: #888888;'>⊘</span> {filename} - Photo exists, skipped"
                            )
                            skipped += 1
                            continue
                        
                        try:
                            # Read image from ZIP
                            img_data = zip_ref.read(img_path)

                            # Convert to PNG and save
                            pixmap = QPixmap()
                            pixmap.loadFromData(img_data)

                            if not pixmap.isNull():
                                # Optionally remove background
                                if self.remove_bg_check.isChecked():
                                    try:
                                        from employee_vault.utils import remove_background
                                        import tempfile
                                        
                                        temp_file = os.path.join(tempfile.gettempdir(), f"temp_{emp_id}.png")
                                        pixmap.save(temp_file, "PNG")
                                        remove_background(temp_file, temp_file)
                                        pixmap = QPixmap(temp_file)
                                        os.remove(temp_file)
                                    except Exception as bg_err:
                                        logging.warning(f"Background removal failed for {emp_id}: {bg_err}")
                                
                                pixmap.save(dest_path, "PNG")
                                emp_name = emp_ids[emp_id].get('name', 'Unknown')
                                self.results_text.append(
                                    f"<span style='color: #4CAF50;'>✓</span> {filename} → {emp_id} ({emp_name})"
                                )
                                successful += 1
                                logging.info(f"Batch photo uploaded: {emp_id}")
                            else:
                                self.results_text.append(
                                    f"<span style='color: #ff6b6b;'>✗</span> {filename} - Invalid image"
                                )
                                failed += 1
                        except Exception as e:
                            self.results_text.append(
                                f"<span style='color: #ff6b6b;'>✗</span> {filename} - Error: {e}"
                            )
                            failed += 1
                            logging.error(f"Error processing {filename}: {e}")
                    else:
                        self.results_text.append(
                            f"<span style='color: #ffaa00;'>⚠</span> {filename} - Employee '{emp_id}' not found"
                        )
                        not_found += 1

                # Summary
                self._show_summary(successful, failed, not_found, skipped)

        except Exception as e:
            show_error_toast(self, f"Error processing ZIP file:\n{e}")
            logging.error(f"Batch photo upload error: {e}")
        finally:
            self.progress.setVisible(False)
            self.upload_btn.setEnabled(True)

    def _show_summary(self, successful, failed, not_found, skipped=0):
        """Show upload summary"""
        self.results_text.append(f"\n<b>📊 Summary:</b>")
        self.results_text.append(f"  <span style='color: #4CAF50;'>✓ Successful:</span> {successful}")
        if skipped > 0:
            self.results_text.append(f"  <span style='color: #888888;'>⊘ Skipped:</span> {skipped}")
        self.results_text.append(f"  <span style='color: #ff6b6b;'>✗ Failed:</span> {failed}")
        self.results_text.append(f"  <span style='color: #ffaa00;'>⚠ Not Found:</span> {not_found}")

        if successful > 0:
            show_success_toast(self, f"Successfully uploaded {successful} photos!")
        else:
            show_warning_toast(self, "No photos were uploaded successfully")
