"""
Print System Dialogs
Centralized print system with mandatory preview using QPrintPreviewDialog
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from employee_vault.config import *
from employee_vault.database import DB
from employee_vault.validators import *
from employee_vault.utils import *
from employee_vault.models import *
from employee_vault.ui.widgets import *
from employee_vault.ui.widgets import disable_cursor_changes
from employee_vault.ui.widgets import ModernAnimatedButton, SmoothAnimatedDialog
from employee_vault.ui.ios_button_styles import apply_ios_style


def print_with_preview(parent, content, title="Print Preview"):
    """
    Universal print function with mandatory preview.
    
    Args:
        parent: Parent widget
        content: Can be:
            - QTextDocument: For HTML/text content
            - QPixmap: For image content
            - PIL.Image: For PIL image content
            - str: HTML string to print
        title: Title for the preview dialog
    """
    from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
    
    printer = QPrinter(QPrinter.HighResolution)
    
    def handle_paint_request(printer):
        painter = None
        try:
            if isinstance(content, QTextDocument):
                content.print_(printer)
            elif isinstance(content, QPixmap):
                painter = QPainter(printer)
                rect = painter.viewport()
                size = content.size()
                size.scale(rect.size(), Qt.KeepAspectRatio)
                painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                painter.setWindow(content.rect())
                painter.drawPixmap(0, 0, content)
            elif isinstance(content, str):
                # HTML string
                doc = QTextDocument()
                doc.setHtml(content)
                doc.print_(printer)
            else:
                # Try PIL Image
                try:
                    from PIL import Image
                    import io
                    if isinstance(content, Image.Image):
                        # Convert PIL Image to QPixmap
                        img_byte_arr = io.BytesIO()
                        content.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        pixmap = QPixmap()
                        pixmap.loadFromData(img_byte_arr.read())
                        
                        painter = QPainter(printer)
                        rect = painter.viewport()
                        size = pixmap.size()
                        size.scale(rect.size(), Qt.KeepAspectRatio)
                        painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                        painter.setWindow(pixmap.rect())
                        painter.drawPixmap(0, 0, pixmap)
                except ImportError:
                    pass
        finally:
            if painter:
                painter.end()
    
    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle(f"🖨️ {title}")
    preview.resize(900, 700)
    preview.paintRequested.connect(handle_paint_request)
    preview.exec()


def print_image_with_preview(parent, pil_image, title="Print Image"):
    """
    Print a PIL Image with mandatory preview.
    Uses Qt's cross-platform printing instead of win32print.
    
    Args:
        parent: Parent widget
        pil_image: PIL Image object
        title: Title for the preview dialog
    """
    import io
    from PIL import Image
    
    # Convert PIL Image to QPixmap
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    pixmap = QPixmap()
    pixmap.loadFromData(img_byte_arr.read())
    
    print_with_preview(parent, pixmap, title)


class BatchPrintDialog(SmoothAnimatedDialog):
    """Dialog for printing multiple ID cards on one sheet"""
    def __init__(self, parent, db, card_generator):
        # v4.4.1: Use smooth fade for batch print (large dialog)
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.card_generator = card_generator
        self.setWindowTitle("🖨️ Batch Print ID Cards")
        self.resize(700, 700)  # v3.2: Increased height
        
        # v3.2: Make entire dialog scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Title
        title = QLabel("<h2>🖨️ Print Multiple ID Cards</h2>")
        title.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("Print multiple ID cards on a single sheet of paper. Select employees, paper size, and layout.")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px; margin: 10px;")
        layout.addWidget(info)
        
        # Employee Selection
        emp_group = QGroupBox("👥 Select Employees to Print")
        emp_layout = QVBoxLayout()
        
        # Phase 3: iOS frosted glass styling
        select_row = QHBoxLayout()
        select_all_btn = ModernAnimatedButton("Select All")
        apply_ios_style(select_all_btn, 'green')
        select_all_btn.clicked.connect(self._select_all)
        select_none_btn = ModernAnimatedButton("Select None")
        apply_ios_style(select_none_btn, 'gray')
        select_none_btn.clicked.connect(self._select_none)
        select_row.addWidget(select_all_btn)
        select_row.addWidget(select_none_btn)
        select_row.addStretch()
        emp_layout.addLayout(select_row)
        
        # v3.2: Employee list with VISIBLE checkboxes
        self.employee_list = QListWidget()
        disable_cursor_changes(self.employee_list)  # Remove hand cursor
        self.employee_list.setSelectionMode(QAbstractItemView.MultiSelection)
        # Fix checkbox visibility - make checked items visible
        self.employee_list.setStyleSheet("""
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)
        
        employees = self.db.all_employees()
        active_employees = [e for e in employees if not e.get('resign_date')]
        
        for emp in sorted(active_employees, key=lambda x: x.get('name', '')):
            item = QListWidgetItem(f"{emp.get('name')} (ID: {emp.get('emp_id')})")
            item.setData(Qt.UserRole, emp.get('emp_id'))
            item.setCheckState(Qt.Unchecked)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # v3.2: Ensure checkable
            self.employee_list.addItem(item)
        
        emp_layout.addWidget(self.employee_list)
        emp_group.setLayout(emp_layout)
        layout.addWidget(emp_group)
        
        # Print Settings
        settings_group = QGroupBox("⚙️ Print Settings")
        settings_layout = QVBoxLayout()
        
        # Paper size selection
        paper_row = QHBoxLayout()
        paper_row.addWidget(QLabel("<b>Paper Size:</b>"))
        self.paper_combo = NeumorphicGradientComboBox("Select Paper Size")
        self.paper_combo.setMinimumHeight(70)
        self.paper_combo.addItems(["A4 (210 x 297 mm)", "Letter (8.5 x 11 in)", "Legal (8.5 x 14 in)"])
        self.paper_combo.combo_box.currentIndexChanged.connect(self._update_layout_preview)
        paper_row.addWidget(self.paper_combo)
        paper_row.addStretch()
        settings_layout.addLayout(paper_row)
        
        # Cards per page
        cards_row = QHBoxLayout()
        cards_row.addWidget(QLabel("<b>Cards Per Page:</b>"))
        self.cards_combo = NeumorphicGradientComboBox("Select Cards Per Page")
        self.cards_combo.setMinimumHeight(70)
        self.cards_combo.addItems(["1 card per page", "2 cards per page", "4 cards per page (2x2)",
                                   "6 cards per page (2x3)", "8 cards per page (2x4)",
                                   "9 cards per page (3x3)", "10 cards per page (2x5)"])
        self.cards_combo.combo_box.setCurrentIndex(2)  # Default to 4 cards
        self.cards_combo.combo_box.currentIndexChanged.connect(self._update_layout_preview)
        cards_row.addWidget(self.cards_combo)
        cards_row.addStretch()
        settings_layout.addLayout(cards_row)
        
        # Card side selection
        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("<b>Print Side:</b>"))
        self.side_combo = NeumorphicGradientComboBox("Select Print Side")
        self.side_combo.setMinimumHeight(70)
        self.side_combo.addItems(["Front Only", "Back Only", "Both Sides (Front then Back)"])
        side_row.addWidget(self.side_combo)
        side_row.addStretch()
        settings_layout.addLayout(side_row)
        
        # Layout preview label
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("padding: 10px; background-color: white; border: 1px solid #ccc; margin: 10px;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self._update_layout_preview()
        settings_layout.addWidget(self.preview_label)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Set scroll area
        scroll_area.setWidget(content_widget)
        
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # Buttons - Phase 3: iOS frosted glass styling
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        preview_btn = ModernAnimatedButton("👁️ Preview")
        apply_ios_style(preview_btn, 'blue')
        preview_btn.clicked.connect(self._preview_print)
        btn_layout.addWidget(preview_btn)

        print_btn = ModernAnimatedButton("🖨️ Print")
        apply_ios_style(print_btn, 'green')
        print_btn.clicked.connect(self._do_print)
        btn_layout.addWidget(print_btn)

        cancel_btn = ModernAnimatedButton("Cancel")
        apply_ios_style(cancel_btn, 'gray')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _select_all(self):
        for i in range(self.employee_list.count()):
            item = self.employee_list.item(i)
            item.setCheckState(Qt.Checked)
    
    def _select_none(self):
        for i in range(self.employee_list.count()):
            item = self.employee_list.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def _update_layout_preview(self):
        paper = self.paper_combo.combo_box.currentText()
        cards = self.cards_combo.combo_box.currentText()
        preview_text = f"<b>Layout Preview:</b><br>{paper}<br>{cards}"
        self.preview_label.setText(preview_text)
    
    def _get_selected_employees(self):
        selected = []
        for i in range(self.employee_list.count()):
            item = self.employee_list.item(i)
            if item.checkState() == Qt.Checked:
                emp_id = item.data(Qt.UserRole)
                selected.append(emp_id)
        return selected
    
    def _preview_print(self):
        selected = self._get_selected_employees()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one employee.")
            return
        
        # Generate preview
        try:
            from PIL import Image
            
            # Get settings
            cards_per_page = int(self.cards_combo.combo_box.currentIndex())
            cards_map = {0: 1, 1: 2, 2: 4, 3: 6, 4: 8, 5: 9, 6: 10}
            cards_per_page = cards_map[cards_per_page]
            
            side_idx = self.side_combo.combo_box.currentIndex()  # 0=front, 1=back, 2=both
            
            # v3.2: Handle "Both Sides" preview
            if side_idx == 2:  # Both sides
                # Create front sheet
                front_sheet = self._create_print_sheet(selected, cards_per_page, "front")
                back_sheet = self._create_print_sheet(selected, cards_per_page, "back")
                
                # Save both sheets
                import tempfile
                temp_front = tempfile.NamedTemporaryFile(delete=False, suffix='_front.png')
                temp_back = tempfile.NamedTemporaryFile(delete=False, suffix='_back.png')
                front_sheet.save(temp_front.name)
                back_sheet.save(temp_back.name)
                
                # Show preview dialog with tabs for front and back
                # v4.4.1: Animated dialog for print preview
                from employee_vault.ui.widgets import AnimatedDialogBase
                preview_dialog = AnimatedDialogBase(self, animation_style="fade")
                preview_dialog.setWindowTitle("Print Preview - Both Sides")
                preview_dialog.resize(900, 700)
                
                preview_layout = QVBoxLayout(preview_dialog)
                
                # Create tab widget
                tabs = QTabWidget()
                
                # Front tab
                front_tab = QWidget()
                front_layout = QVBoxLayout(front_tab)
                front_label = QLabel()
                front_pixmap = QPixmap(temp_front.name)
                front_scaled = front_pixmap.scaled(850, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                front_label.setPixmap(front_scaled)
                front_label.setAlignment(Qt.AlignCenter)
                front_scroll = QScrollArea()
                front_scroll.setWidget(front_label)
                front_scroll.setWidgetResizable(True)
                front_layout.addWidget(front_scroll)
                tabs.addTab(front_tab, "🎴 Front Side")
                
                # Back tab
                back_tab = QWidget()
                back_layout = QVBoxLayout(back_tab)
                back_label = QLabel()
                back_pixmap = QPixmap(temp_back.name)
                back_scaled = back_pixmap.scaled(850, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                back_label.setPixmap(back_scaled)
                back_label.setAlignment(Qt.AlignCenter)
                back_scroll = QScrollArea()
                back_scroll.setWidget(back_label)
                back_scroll.setWidgetResizable(True)
                back_layout.addWidget(back_scroll)
                tabs.addTab(back_tab, "🎴 Back Side")
                
                preview_layout.addWidget(tabs)
                
                info_label = QLabel(f"Preview: {len(selected)} employee(s), {cards_per_page} cards/page, BOTH sides")
                info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; font-weight: bold;")
                preview_layout.addWidget(info_label)
                
                close_btn = ModernAnimatedButton("Close Preview")
                apply_ios_style(close_btn, 'gray')
                close_btn.clicked.connect(preview_dialog.close)
                preview_layout.addWidget(close_btn)
                
                preview_dialog.exec()
                
                # Cleanup
                os.unlink(temp_front.name)
                os.unlink(temp_back.name)
                
            else:  # Front or Back only
                side = "front" if side_idx == 0 else "back"
                sheet = self._create_print_sheet(selected, cards_per_page, side)
                
                # Save preview
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                sheet.save(temp_file.name)
                
                # Show preview
                # v4.4.1: Animated dialog for single side preview
                from employee_vault.ui.widgets import AnimatedDialogBase
                preview_dialog = AnimatedDialogBase(self, animation_style="fade")
                preview_dialog.setWindowTitle(f"Print Preview - {side.title()}")
                preview_dialog.resize(800, 600)
                
                preview_layout = QVBoxLayout(preview_dialog)
                
                label = QLabel()
                pixmap = QPixmap(temp_file.name)
                scaled_pixmap = pixmap.scaled(750, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
                label.setAlignment(Qt.AlignCenter)
                
                scroll = QScrollArea()
                scroll.setWidget(label)
                scroll.setWidgetResizable(True)
                preview_layout.addWidget(scroll)
                
                info_label = QLabel(f"Preview: {len(selected)} employee(s), {cards_per_page} cards/page, {side.title()} only")
                info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
                preview_layout.addWidget(info_label)
                
                close_btn = ModernAnimatedButton("Close Preview")
                apply_ios_style(close_btn, 'gray')
                close_btn.clicked.connect(preview_dialog.close)
                preview_layout.addWidget(close_btn)
                
                preview_dialog.exec()
                
                # Cleanup
                os.unlink(temp_file.name)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create preview:\n{str(e)}\n\nPlease check that all selected employees have photos.")
    
    def _create_print_sheet(self, emp_ids, cards_per_page, side):
        """Create a sheet with multiple ID cards arranged in a grid"""
        from PIL import Image
        
        # Paper sizes in pixels at 300 DPI
        paper_sizes = {
            0: (2480, 3508),  # A4: 210 x 297 mm
            1: (2550, 3300),  # Letter: 8.5 x 11 inches
            2: (2550, 4200),  # Legal: 8.5 x 14 inches
        }
        
        paper_idx = self.paper_combo.combo_box.currentIndex()
        sheet_width, sheet_height = paper_sizes[paper_idx]
        
        # Create white background
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        # Calculate grid layout
        grid_layouts = {
            1: (1, 1), 2: (1, 2), 4: (2, 2), 
            6: (2, 3), 8: (2, 4), 9: (3, 3), 10: (2, 5)
        }
        
        cols, rows = grid_layouts.get(cards_per_page, (2, 2))
        
        # Calculate card size and spacing
        card_width = 638  # CR80 standard at 300 DPI
        card_height = 1011
        
        # Scale cards to fit on sheet with margins
        margin = 100  # pixels
        available_width = (sheet_width - margin * 2) / cols
        available_height = (sheet_height - margin * 2) / rows
        
        scale = min(available_width / card_width, available_height / card_height) * 0.9
        
        scaled_width = int(card_width * scale)
        scaled_height = int(card_height * scale)
        
        # Calculate spacing
        x_spacing = (sheet_width - margin * 2) // cols
        y_spacing = (sheet_height - margin * 2) // rows
        
        # Place cards
        for idx, emp_id in enumerate(emp_ids[:cards_per_page]):
            if idx >= cards_per_page:
                break
            
            # Generate card
            try:
                card = self.card_generator.generate_card(emp_id, side=side)
                card_resized = card.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                
                # Calculate position (centered in each grid cell)
                row = idx // cols
                col = idx % cols
                
                x = margin + col * x_spacing + (x_spacing - scaled_width) // 2
                y = margin + row * y_spacing + (y_spacing - scaled_height) // 2
                
                sheet.paste(card_resized, (x, y))
            except Exception as e:
                logging.error(f"Failed to add card for employee {emp_id}: {e}")
        
        return sheet
    
    def _do_print(self):
        selected = self._get_selected_employees()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one employee.")
            return
        
        try:
            from PIL import Image
            
            # Get settings
            cards_per_page = int(self.cards_combo.combo_box.currentIndex())
            cards_map = {0: 1, 1: 2, 2: 4, 3: 6, 4: 8, 5: 9, 6: 10}
            cards_per_page = cards_map[cards_per_page]
            
            side_idx = self.side_combo.combo_box.currentIndex()
            
            # Progress dialog
            progress = QProgressDialog("Generating print sheets...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            sheets = []
            
            # Generate sheets for front
            if side_idx == 0 or side_idx == 2:
                for i in range(0, len(selected), cards_per_page):
                    if progress.wasCanceled():
                        return
                    
                    batch = selected[i:i+cards_per_page]
                    sheet = self._create_print_sheet(batch, cards_per_page, "front")
                    sheets.append(("Front", sheet))
                    
                    progress.setValue(int((i / len(selected)) * 50))
            
            # Generate sheets for back
            if side_idx == 1 or side_idx == 2:
                for i in range(0, len(selected), cards_per_page):
                    if progress.wasCanceled():
                        return
                    
                    batch = selected[i:i+cards_per_page]
                    sheet = self._create_print_sheet(batch, cards_per_page, "back")
                    sheets.append(("Back", sheet))
                    
                    if side_idx == 2:
                        progress.setValue(50 + int((i / len(selected)) * 50))
                    else:
                        progress.setValue(int((i / len(selected)) * 100))
            
            progress.setValue(100)
            progress.close()
            
            # Show print dialog
            if sheets:
                self._show_print_dialog(sheets)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create print sheets:\n{str(e)}")
    
    def _show_print_dialog(self, sheets):
        """Show print preview dialog (mandatory preview before printing)"""
        from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
        from PySide6.QtGui import QPainter
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Portrait)
        
        # Set paper size based on selection
        paper_sizes = {
            0: QPageSize.A4,
            1: QPageSize.Letter,
            2: QPageSize.Legal
        }
        printer.setPageSize(QPageSize(paper_sizes[self.paper_combo.combo_box.currentIndex()]))
        
        def handle_paint_request(printer):
            painter = QPainter()
            painter.begin(printer)
            
            for idx, (side_name, sheet) in enumerate(sheets):
                if idx > 0:
                    printer.newPage()
                
                # Convert PIL image to QPixmap
                import io
                img_byte_arr = io.BytesIO()
                sheet.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                pixmap = QPixmap()
                pixmap.loadFromData(img_byte_arr.read())
                
                # Scale to fit printer page
                target_rect = painter.viewport()
                scaled_pixmap = pixmap.scaled(
                    target_rect.width(), 
                    target_rect.height(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                # Center on page
                x = (target_rect.width() - scaled_pixmap.width()) // 2
                y = (target_rect.height() - scaled_pixmap.height()) // 2
                
                painter.drawPixmap(x, y, scaled_pixmap)
            
            painter.end()
        
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("🖨️ Print Preview - Batch ID Cards")
        preview.resize(900, 700)
        preview.paintRequested.connect(handle_paint_request)
        preview.exec()

# ============================================================================
# FEATURE A: PRINTING SYSTEM
# ============================================================================

class PrintSystemDialog(SmoothAnimatedDialog):
    """Professional printing system for employee records"""
    def __init__(self, parent, db, employees):
        # v4.4.1: Use smooth fade for print system
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.employees = employees
        self.setWindowTitle("🖨️ Print System")
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>🖨️ Print System</h2>"))

        # Phase 3: iOS frosted glass styling
        options_group = QGroupBox("What would you like to print?")
        options_layout = QVBoxLayout(options_group)

        print_profile_btn = ModernAnimatedButton("📄 Print Employee Profile")
        apply_ios_style(print_profile_btn, 'blue')
        print_profile_btn.setToolTip("Print detailed profile of selected employee")
        print_profile_btn.clicked.connect(self.print_employee_profile)
        options_layout.addWidget(print_profile_btn)

        print_list_btn = ModernAnimatedButton("📋 Print Employee List")
        apply_ios_style(print_list_btn, 'blue')
        print_list_btn.setToolTip("Print table of all employees")
        print_list_btn.clicked.connect(self.print_employee_list)
        options_layout.addWidget(print_list_btn)

        print_contracts_btn = ModernAnimatedButton("📊 Print Contract Report")
        apply_ios_style(print_contracts_btn, 'blue')
        print_contracts_btn.setToolTip("Print report of expiring contracts")
        print_contracts_btn.clicked.connect(self.print_contract_report)
        options_layout.addWidget(print_contracts_btn)

        layout.addWidget(options_group)

        filter_group = QGroupBox("Filter Options")
        filter_layout = QVBoxLayout(filter_group)

        self.include_resigned = QCheckBox("Include resigned employees")
        filter_layout.addWidget(self.include_resigned)

        self.include_photos = QCheckBox("Include photos in prints")
        self.include_photos.setChecked(True)
        filter_layout.addWidget(self.include_photos)

        layout.addWidget(filter_group)

        # Phase 3: iOS frosted glass styling
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def get_filtered_employees(self):
        if self.include_resigned.isChecked():
            return self.employees
        return [e for e in self.employees if not e.get('resign_date')]

    def print_employee_profile(self):
        employees = self.get_filtered_employees()
        if not employees:
            QMessageBox.warning(self, "No Employees", "No employees to print.")
            return

        names = [f"{e['emp_id']} - {e['name']}" for e in employees]
        name, ok = QInputDialog.getItem(self, "Select Employee",
                                       "Choose employee to print:", names, 0, False)
        if not ok: return

        emp_id = name.split(" - ")[0]
        employee = next((e for e in employees if e['emp_id'] == emp_id), None)
        if not employee: return

        html = self._generate_profile_html(employee)
        self._print_html(html, f"Employee Profile - {employee['name']}")

    def print_employee_list(self):
        employees = self.get_filtered_employees()
        if not employees:
            QMessageBox.warning(self, "No Employees", "No employees to print.")
            return
        html = self._generate_list_html(employees)
        self._print_html(html, "Employee List")

    def print_contract_report(self):
        employees = self.get_filtered_employees()
        with_contracts = [e for e in employees if e.get('contract_expiry')]
        if not with_contracts:
            QMessageBox.warning(self, "No Contracts", "No employees with contracts.")
            return
        html = self._generate_contract_html(with_contracts)
        self._print_html(html, "Contract Report")

    def _generate_profile_html(self, emp):
        photo_html = ""
        if self.include_photos.isChecked():
            photo_path = os.path.join(PHOTOS_DIR, f"{emp['emp_id']}.png")
            if os.path.exists(photo_path):
                # Convert photo to base64 for embedding in HTML
                import base64
                with open(photo_path, 'rb') as f:
                    photo_data = base64.b64encode(f.read()).decode('utf-8')
                photo_html = f'<img src="data:image/png;base64,{photo_data}" width="150" style="float:right; margin:10px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>'

        status = "Active" if not emp.get('resign_date') else f"Resigned ({emp.get('resign_date')})"

        html = f"""<html><head><style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
h1 {{ color: #2196F3; border-bottom: 2px solid #2196F3; }}
h2 {{ color: #555; margin-top: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
td:first-child {{ font-weight: bold; width: 200px; }}
.status {{ padding: 5px 10px; border-radius: 3px; display: inline-block; }}
.active {{ background: #4CAF50; color: white; }}
.resigned {{ background: #f44336; color: white; }}
</style></head><body>
{photo_html}
<h1>Employee Profile</h1>
<div class="status {'active' if not emp.get('resign_date') else 'resigned'}">{status}</div>
<h2>Personal Information</h2>
<table>
<tr><td>Employee ID:</td><td>{emp['emp_id']}</td></tr>
<tr><td>Name:</td><td>{emp['name']}</td></tr>
<tr><td>Email:</td><td>{emp.get('email', 'N/A')}</td></tr>
<tr><td>Phone:</td><td>{emp.get('phone', 'N/A')}</td></tr>
</table>
<h2>Employment Details</h2>
<table>
<tr><td>Department:</td><td>{emp.get('department', 'N/A')}</td></tr>
<tr><td>Position:</td><td>{emp.get('position', 'N/A')}</td></tr>
<tr><td>Hire Date:</td><td>{emp.get('hire_date', 'N/A')}</td></tr>
<tr><td>Salary:</td><td>₱{float(emp.get('salary', 0)):,.2f}</td></tr>
<tr><td>Agency:</td><td>{emp.get('agency') or 'Direct Hire'}</td></tr>
</table>
<h2>Government IDs</h2>
<table>
<tr><td>SSS Number:</td><td>{emp.get('sss_number', 'N/A')}</td></tr>
<tr><td>TIN:</td><td>{emp.get('tin', 'N/A')}</td></tr>
<tr><td>PhilHealth:</td><td>{emp.get('philhealth', 'N/A')}</td></tr>
<tr><td>Pag-IBIG:</td><td>{emp.get('pagibig', 'N/A')}</td></tr>
</table>
<h2>Contract Information</h2>
<table>
<tr><td>Contract Start:</td><td>{emp.get('contract_start_date', 'N/A')}</td></tr>
<tr><td>Contract Duration:</td><td>{emp.get('contract_months', 'N/A')} months</td></tr>
<tr><td>Contract Expiry:</td><td>{emp.get('contract_expiry', 'N/A')}</td></tr>
</table>
<h2>Emergency Contact</h2>
<table>
<tr><td>Name:</td><td>{emp.get('emergency_contact_name', 'N/A')}</td></tr>
<tr><td>Phone:</td><td>{emp.get('emergency_contact_phone', 'N/A')}</td></tr>
</table>
<p style="margin-top:30px; font-size:10px; color:#999;">
Printed on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
</body></html>"""
        return html

    def _generate_list_html(self, employees):
        rows = ""
        for emp in employees:
            status = "Active" if not emp.get('resign_date') else "Resigned"
            rows += f"""<tr>
<td>{emp['emp_id']}</td><td>{emp['name']}</td>
<td>{emp.get('department', 'N/A')}</td><td>{emp.get('position', 'N/A')}</td>
<td>₱{float(emp.get('salary', 0)):,.2f}</td><td>{status}</td>
</tr>"""

        html = f"""<html><head><style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
h1 {{ color: #2196F3; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th {{ background: #2196F3; color: white; padding: 10px; text-align: left; }}
td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
tr:hover {{ background: #f5f5f5; }}
</style></head><body>
<h1>Employee List</h1>
<p><b>Total Employees:</b> {len(employees)}</p>
<table><thead><tr>
<th>ID</th><th>Name</th><th>Department</th><th>Position</th><th>Salary</th><th>Status</th>
</tr></thead><tbody>{rows}</tbody></table>
<p style="margin-top:30px; font-size:10px; color:#999;">
Printed on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
</body></html>"""
        return html

    def _generate_contract_html(self, employees):
        from datetime import datetime as dt
        expiring_soon, future_expiry = [], []

        for emp in employees:
            try:
                expiry = dt.strptime(emp['contract_expiry'], "%m-%d-%Y")
                days_left = (expiry - dt.now()).days
                if days_left <= 30:
                    expiring_soon.append((emp, days_left))
                else:
                    future_expiry.append((emp, days_left))
            except: pass

        expiring_soon.sort(key=lambda x: x[1])
        future_expiry.sort(key=lambda x: x[1])

        rows = ""
        for emp, days in expiring_soon:
            color = "#f44336" if days <= 0 else "#ff9800"
            status = "EXPIRED" if days <= 0 else f"{days} days left"
            rows += f"""<tr style="background:{color}20;">
<td><b>{emp['emp_id']}</b></td><td><b>{emp['name']}</b></td>
<td>{emp.get('agency', 'Direct')}</td><td>{emp['contract_expiry']}</td>
<td style="color:{color}; font-weight:bold;">{status}</td></tr>"""

        for emp, days in future_expiry:
            rows += f"""<tr>
<td>{emp['emp_id']}</td><td>{emp['name']}</td>
<td>{emp.get('agency', 'Direct')}</td><td>{emp['contract_expiry']}</td>
<td>{days} days</td></tr>"""

        html = f"""<html><head><style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
h1 {{ color: #2196F3; }}
.warning {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th {{ background: #2196F3; color: white; padding: 10px; text-align: left; }}
td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
</style></head><body>
<h1>Contract Expiry Report</h1>
<p><b>Total Contracts:</b> {len(employees)}</p>
<p><b>Expiring Soon (≤30 days):</b> {len(expiring_soon)}</p>
{f'<div class="warning">⚠️ <b>WARNING:</b> {len(expiring_soon)} contract(s) expiring within 30 days!</div>' if expiring_soon else ''}
<table><thead><tr>
<th>ID</th><th>Name</th><th>Agency</th><th>Expiry Date</th><th>Status</th>
</tr></thead><tbody>{rows}</tbody></table>
<p style="margin-top:30px; font-size:10px; color:#999;">
Printed on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
</body></html>"""
        return html

    def _print_html(self, html, title):
        """Print HTML with preview dialog"""
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtCore import QTimer
        from employee_vault.ui.widgets import AnimatedDialogBase
        from employee_vault.ui.modern_ui_helper import show_success_toast

        # Create preview dialog
        preview_dlg = AnimatedDialogBase(self, animation_style="fade")
        preview_dlg.setWindowTitle(f"Print Preview - {title}")
        preview_dlg.resize(900, 700)

        preview_layout = QVBoxLayout(preview_dlg)

        # Add web view for preview
        web_view = QWebEngineView()
        web_view.setHtml(html)
        preview_layout.addWidget(web_view)

        # Add buttons - Phase 3: iOS frosted glass styling
        btn_layout = QHBoxLayout()
        print_btn = ModernAnimatedButton("🖨️ Print")
        apply_ios_style(print_btn, 'green')
        cancel_btn = ModernAnimatedButton("Cancel")
        apply_ios_style(cancel_btn, 'gray')
        btn_layout.addStretch()
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(cancel_btn)
        preview_layout.addLayout(btn_layout)

        # Connect buttons
        should_print = [False]  # Use list to avoid nonlocal issues
        def on_print():
            should_print[0] = True
            preview_dlg.accept()

        def on_close():
            # Properly clean up web view before closing
            web_view.setHtml("")  # Clear content
            web_view.deleteLater()  # Schedule for deletion
            preview_dlg.reject()

        print_btn.clicked.connect(on_print)
        cancel_btn.clicked.connect(on_close)

        # Show preview and wait for user decision
        result = preview_dlg.exec()

        # Give web view time to clean up
        QTimer.singleShot(50, lambda: None)

        if result == QDialog.Accepted and should_print[0]:
            # User clicked Print, show print dialog
            printer = QPrinter(QPrinter.HighResolution)
            printer.setDocName(title)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.Accepted:
                document = QTextDocument()
                document.setHtml(html)
                document.print_(printer)
                show_success_toast(self, "Document sent to printer!")

        # Final cleanup
        web_view.setParent(None)
        web_view.deleteLater()

# ============================================================================
# FEATURE B: BULK OPERATIONS
# ============================================================================

class BulkOperationsDialog(SmoothAnimatedDialog):
    """Bulk edit multiple employees at once"""
    def __init__(self, parent, db, employees):
        # v4.4.1: Use smooth fade for bulk operations
        super().__init__(parent, animation_style="fade")
        self.db = db
        self.employees = employees
        self.setWindowTitle("📦 Bulk Operations")
        self.resize(700, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>📦 Bulk Operations</h2>"))

        selection_group = QGroupBox("Select Employees")
        selection_layout = QVBoxLayout(selection_group)

        self.employee_list = QListWidget()
        disable_cursor_changes(self.employee_list)  # Remove hand cursor
        self.employee_list.setSelectionMode(QListWidget.MultiSelection)

        for emp in employees:
            status = "" if not emp.get('resign_date') else " [Resigned]"
            item = QListWidgetItem(f"{emp['emp_id']} - {emp['name']} ({emp.get('department', 'N/A')}){status}")
            item.setData(Qt.UserRole, emp)
            self.employee_list.addItem(item)

        selection_layout.addWidget(self.employee_list)

        # Phase 3: iOS frosted glass styling
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

        # Phase 3: iOS frosted glass styling
        ops_group = QGroupBox("Choose Operation")
        ops_layout = QVBoxLayout(ops_group)

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

        # Phase 3: iOS frosted glass styling
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
            QMessageBox.warning(self, "No Selection", "Please select employees first.")
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
            QMessageBox.information(self, "Success", f"Updated {len(selected)} employee(s)!")
            self.status_label.setText(f"✅ Changed department for {len(selected)} employees")

    def bulk_change_position(self):
        selected = self.get_selected_employees()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select employees first.")
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
            QMessageBox.information(self, "Success", f"Updated {len(selected)} employee(s)!")
            self.status_label.setText(f"✅ Changed position for {len(selected)} employees")

    def bulk_change_agency(self):
        selected = self.get_selected_employees()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select employees first.")
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
            QMessageBox.information(self, "Success", f"Updated {len(selected)} employee(s)!")
            self.status_label.setText(f"✅ Changed agency for {len(selected)} employees")

    def bulk_archive(self):
        selected = self.get_selected_employees()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select employees first.")
            return

        reason, ok = QInputDialog.getText(self, "Archive Reason", "Reason for archiving:")
        if not ok or not reason: return

        reply = QMessageBox.question(self, "Confirm",
                                    f"Archive {len(selected)} employee(s)?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for emp in selected:
                self.db.archive_employee(emp['emp_id'], "admin", reason)
            QMessageBox.information(self, "Success", f"Archived {len(selected)} employee(s)!")
            self.status_label.setText(f"✅ Archived {len(selected)} employees")

    def bulk_export(self):
        selected = self.get_selected_employees()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select employees first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Selected Employees",
            f"selected_employees_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON Files (*.json)")

        if not filename: return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(selected, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Success",
                                  f"Exported {len(selected)} employee(s) to:\n{filename}")
            self.status_label.setText(f"✅ Exported {len(selected)} employees")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")


# ==================== v2.0 DIALOG CLASSES ====================

