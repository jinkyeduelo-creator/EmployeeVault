"""
Employees Page
Main employees list and management page
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import *
from employee_vault.database import DB
from employee_vault.models import *
from employee_vault.ui.widgets import *
from employee_vault.ui.widgets import ModernAnimatedButton, apply_table_fixes, SmoothAnimatedDialog
from employee_vault.ui.dialogs.employee_form import EmployeeForm
from employee_vault.ui.ios_button_styles import apply_ios_style
from employee_vault.ui.modern_ui_helper import show_warning_toast, show_error_toast

class HTMLDelegate(QStyledItemDelegate):
    """Custom delegate to render HTML in table cells - Phase 1.2: with document caching"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Phase 1.2: Cache parsed QTextDocument instances
        self._doc_cache = {}
        self._max_cache = 500  # Limit cache size to prevent memory bloat

    def paint(self, painter, option, index):
        # Performance instrumentation (Phase 0)
        start = time.perf_counter()

        # Use the original option object directly - creating new one causes SystemError
        options = QStyleOptionViewItem(option)
        options.text = index.data(Qt.DisplayRole) or ""
        options.font = painter.font()
        options.palette = option.palette
        options.rect = option.rect
        options.state = option.state
        options.widget = option.widget

        style = QApplication.style() if options.widget is None else options.widget.style()

        # Phase 1.2: Use cached QTextDocument to avoid re-parsing HTML on every paint
        text = options.text
        cache_key = (text, options.font.toString())

        if cache_key in self._doc_cache:
            # Use cached document
            doc = self._doc_cache[cache_key]
        else:
            # Create and cache new document
            if len(self._doc_cache) >= self._max_cache:
                # Evict 25% oldest entries when cache is full
                to_remove = list(self._doc_cache.keys())[:125]
                for key in to_remove:
                    del self._doc_cache[key]

            doc = QTextDocument()
            doc.setHtml(text)
            doc.setDefaultFont(options.font)
            self._doc_cache[cache_key] = doc

        # Set text color from option
        doc.setDefaultStyleSheet(f"body {{ color: {options.palette.color(QPalette.Text).name()}; }}")

        # Clear text to prevent default drawing
        options.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, options, painter)

        # Draw HTML content
        ctx = QAbstractTextDocumentLayout.PaintContext()

        # Highlighting for selection
        if option.state & QStyle.State_Selected:
            ctx.palette.setColor(QPalette.Text, option.palette.color(QPalette.HighlightedText))

        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

        # Performance instrumentation (Phase 0) - log slow paints only
        elapsed = (time.perf_counter() - start)*1000
        if elapsed > 5:  # Log paints >5ms
            print(f"[PERF] Cell paint: {elapsed:.2f}ms")

class EmployeesPage(QWidget):
    # Signal to request refresh from parent
    refresh_requested = Signal()
    
    def __init__(self, on_view, on_edit, on_delete_selected):
        super().__init__(); self.on_view=on_view; self.on_edit=on_edit; self.on_delete_selected=on_delete_selected
        self.db = DB(DB_FILE)  # Database connection for agency list
        
        v=QVBoxLayout(self); hdr=QHBoxLayout(); hdr.addWidget(QLabel("<h2>👥 All Employees</h2>"))
        
        # v5.1: Add Refresh button (F5 also works as keyboard shortcut)
        self.refresh_btn = ModernAnimatedButton("🔄 Refresh")
        apply_ios_style(self.refresh_btn, 'green')
        self.refresh_btn.setToolTip("Refresh employee list (F5)")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        hdr.addWidget(self.refresh_btn)
        
        hdr.addStretch(1)
        
        # Enhanced Search button - Phase 3: iOS frosted glass
        self.advanced_search_btn = ModernAnimatedButton("🔍 Advanced Search")
        apply_ios_style(self.advanced_search_btn, 'blue')
        self.advanced_search_btn.setToolTip("Open advanced search with multiple filters")

        # Common dropdown styling - compact size
        dropdown_style = """
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 65, 80, 0.95),
                    stop:1 rgba(40, 45, 55, 0.98));
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 10px;
                color: white;
                font-size: 11px;
                min-width: 80px;
                max-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid rgba(74, 158, 255, 0.5);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(70, 75, 90, 0.95),
                    stop:1 rgba(50, 55, 65, 0.98));
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid rgba(255, 255, 255, 0.7);
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(35, 40, 50, 0.98);
                border: 1px solid rgba(74, 158, 255, 0.3);
                border-radius: 8px;
                selection-background-color: rgba(74, 158, 255, 0.4);
                color: white;
                padding: 4px;
            }
        """

        self._wheel_guard = WheelGuard(self)

        # Department filter dropdown
        self.department_filter = NeumorphicGradientComboBox("All Depts")
        self.department_filter.setMinimumHeight(70)
        self.department_filter.combo_box.setFocusPolicy(Qt.ClickFocus)
        self.department_filter.combo_box.installEventFilter(self._wheel_guard)
        self.department_filter.addItems(["All Depts", "Office", "Warehouse", "Store"])
        self.department_filter.setToolTip("Filter by department")
        self.department_filter.combo_box.currentTextChanged.connect(self._on_department_filter_changed)

        # Agency filter dropdown
        self.agency_filter = NeumorphicGradientComboBox("All Agencies")
        self.agency_filter.setMinimumHeight(70)
        self.agency_filter.combo_box.setFocusPolicy(Qt.ClickFocus)
        self.agency_filter.combo_box.installEventFilter(self._wheel_guard)
        self.agency_filter.addItem("All Agencies")
        self._load_agencies()  # Load agencies from database
        self.agency_filter.setToolTip("Filter by agency")
        self.agency_filter.combo_box.currentTextChanged.connect(self._on_agency_filter_changed)

        # Status filter dropdown
        self.status = NeumorphicGradientComboBox("All Status")
        self.status.setMinimumHeight(70)
        self.status.combo_box.setFocusPolicy(Qt.ClickFocus)
        self.status.combo_box.installEventFilter(self._wheel_guard)
        self.status.addItems(["All Status", "Active", "Not Active", "Resigned"])
        self.status.setToolTip("Filter by employment status")

        # Clear filters button
        self.clear_filters_btn = ModernAnimatedButton("✕ Clear")
        apply_ios_style(self.clear_filters_btn, 'gray')
        self.clear_filters_btn.setToolTip("Clear all filters")
        self.clear_filters_btn.clicked.connect(self._clear_all_filters)
        self.clear_filters_btn.setVisible(False)  # Hidden until filters are active

        # Column visibility toggle button
        self.column_toggle_btn = ModernAnimatedButton("👁️ Columns")
        apply_ios_style(self.column_toggle_btn, 'purple')
        self.column_toggle_btn.setToolTip("Show/hide table columns")
        self.column_toggle_btn.clicked.connect(self._show_column_menu)

        hdr.addWidget(self.department_filter)
        hdr.addWidget(self.agency_filter)
        hdr.addWidget(self.status)
        hdr.addWidget(self.clear_filters_btn)
        hdr.addWidget(self.column_toggle_btn)
        v.addLayout(hdr)

        # FEATURE: Filter chips container
        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 5, 0, 5)
        self.chips_layout.setSpacing(8)
        self.chips_layout.addStretch(1)
        self.chips_container.setVisible(False)  # Hidden until filters are active
        v.addWidget(self.chips_container)

        # Phase 3: iOS frosted glass for action buttons
        act=QHBoxLayout()
        self.edit_btn = ModernAnimatedButton("✏️ Edit Selected")
        apply_ios_style(self.edit_btn, 'blue')
        self.edit_btn.setEnabled(False)  # Initially disabled
        self.delete_btn=ModernAnimatedButton("🗑️ Delete Selected (0)")
        apply_ios_style(self.delete_btn, 'red')
        self.delete_btn.setEnabled(False)  # Initially disabled
        sel=ModernAnimatedButton("Select All (Ctrl+A)")
        apply_ios_style(sel, 'green')
        
        # Search field - positioned AFTER Select All button (on the right)
        self.search=FloatingLabelLineEdit("🔍 Search...")
        self.search.setMinimumWidth(200)
        self.search.setMaximumWidth(300)
        
        act.addWidget(self.edit_btn) # Add it to the layout
        act.addWidget(self.delete_btn)
        act.addWidget(sel)
        act.addWidget(self.search)  # Search field after Select All
        act.addStretch(1)
        v.addLayout(act)
        self.model=EmployeesTableModel([]); self.proxy=EmployeesFilter(); self.proxy.setSourceModel(self.model)
        # Enable dynamic sorting so sort is applied automatically when data changes
        self.proxy.setDynamicSortFilter(True)
        self.proxy.setSortRole(Qt.EditRole)  # Use EditRole for proper numeric sorting
        self.table=QTableView()
        self.table.setModel(self.proxy); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSelectionMode(QAbstractItemView.ExtendedSelection); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # v4.5.0: Apply all table fixes (cursor + focus rectangle)
        apply_table_fixes(self.table)
        # Ensure photo avatars render at full size and stay centered
        self.table.setIconSize(QSize(44, 44))
        
        # Modern hover effects for table rows
        self.table.setStyleSheet("""
            QTableView {
                gridline-color: rgba(255, 255, 255, 0.1);
                border: none;
            }
            QTableView::item {
                padding: 8px;
            }
            QTableView::item:hover {
                background-color: rgba(33, 150, 243, 0.2);
            }
            QTableView::item:selected {
                background-color: rgba(33, 150, 243, 0.4);
            }
        """)

        self.table.verticalHeader().setVisible(False)  # Hide vertical header to remove bullets

        # Set row height to accommodate photo thumbnails (40x40 photos + padding)
        self.table.verticalHeader().setDefaultSectionSize(50)

        # Auto-resize columns to fit content
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # Last section stretches to fill available space
        header.setStretchLastSection(True)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table.doubleClicked.connect(self._double)
        self.table.setSortingEnabled(True)
        # Set default sort on proxy model BEFORE data is loaded
        self.proxy.sort(2, Qt.AscendingOrder)  # Sort by Emp ID column
        v.addWidget(self.table, 1)

        # FEATURE: Contract expiry color legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("<b>Contract Status:</b>"))

        def create_legend_item(color, text):
            lbl = QLabel(f"  {text}  ")
            lbl.setStyleSheet(f"""
                background-color: rgba{color};
                border-radius: 4px;
                padding: 4px 8px;
                margin: 0px 4px;
                font-size: 11px;
            """)
            return lbl

        legend_layout.addWidget(create_legend_item("(244, 67, 54, 40)", "⚠️ Expired"))
        legend_layout.addWidget(create_legend_item("(244, 67, 54, 30)", "🔴 < 7 days"))
        legend_layout.addWidget(create_legend_item("(255, 152, 0, 25)", "🟠 < 14 days"))
        legend_layout.addWidget(create_legend_item("(255, 235, 59, 20)", "🟡 < 30 days"))
        legend_layout.addStretch(1)

        v.addLayout(legend_layout)

        # QUICK WIN #2: Search debouncing - only search after user stops typing (300ms delay)
        # FEATURE: Search highlighting - also set search term on model
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._on_search_changed)
        self.search.textChanged.connect(lambda: self.search_timer.start(300))

        # Enable HTML text formatting for table to support highlighted search results
        self.table.setItemDelegate(HTMLDelegate(self.table))

        # MICRO-INTERACTION: Enable mouse tracking for hover row effect
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        self.table.viewport().installEventFilter(self)

        # Load saved column visibility preferences
        self._load_column_visibility()

        self.status.currentTextChanged.connect(self._on_status_changed)
        self.search.textChanged.connect(self._on_search_text_changed)
        self.edit_btn.clicked.connect(self._edit) # <-- Add this
        self.delete_btn.clicked.connect(self._delete)
        sel.clicked.connect(self._select_all)
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._update_btn())
        self.addAction(QAction(self, shortcut=QKeySequence.Delete, triggered=self._delete)); self.addAction(QAction(self, shortcut=QKeySequence("Ctrl+A"), triggered=self._select_all))

        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def pause_updates_for_animation(self):
        """Phase 1.1: Pause table updates during sidebar animation to prevent lag"""
        self.table.setUpdatesEnabled(False)

    def resume_updates_after_animation(self):
        """Phase 1.1: Resume table updates after sidebar animation completes"""
        self.table.setUpdatesEnabled(True)

    def _create_filter_chip(self, text, on_remove):
        """Create a filter chip with iOS frosted glass styling"""
        chip = QWidget()
        chip.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(74, 158, 255, 0.3),
                                           stop:1 rgba(25, 118, 210, 0.5));
                border-top: 1.5px solid rgba(255, 255, 255, 0.4);
                border-left: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 16px;
                padding: 4px 12px;
            }
        """)

        layout = QHBoxLayout(chip)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        label = QLabel(text)
        label.setStyleSheet("color: white; background: transparent; border: none; font-size: 12px; font-weight: bold;")
        layout.addWidget(label)

        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                color: white;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
        """)
        close_btn.setFixedSize(16, 16)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(on_remove)
        layout.addWidget(close_btn)

        return chip

    def _update_filter_chips(self):
        """Update the filter chips display"""
        # Clear existing chips
        while self.chips_layout.count() > 1:  # Keep the stretch
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_filters = False

        # Search chip
        search_text = self.search.text().strip()
        if search_text:
            chip = self._create_filter_chip(f"🔍 Search: {search_text}", lambda: self.search.clear())
            self.chips_layout.insertWidget(0, chip)
            has_filters = True

        # Department chip
        dept = self.department_filter.combo_box.currentText()
        if dept != "All Depts":
            chip = self._create_filter_chip(f"🏢 Dept: {dept}", lambda: self.department_filter.combo_box.setCurrentText("All Depts"))
            self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)
            has_filters = True

        # Agency chip
        agency = self.agency_filter.combo_box.currentText()
        if agency != "All Agencies":
            chip = self._create_filter_chip(f"🏭 Agency: {agency}", lambda: self.agency_filter.combo_box.setCurrentText("All Agencies"))
            self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)
            has_filters = True

        # Status chip
        status = self.status.combo_box.currentText()
        if status != "All Status":
            chip = self._create_filter_chip(f"📊 Status: {status}", lambda: self.status.combo_box.setCurrentText("All Status"))
            self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)
            has_filters = True

        self.chips_container.setVisible(has_filters)
        self.clear_filters_btn.setVisible(has_filters)

    def _on_search_text_changed(self):
        """Handle search text changes (immediate for chips, debounced for actual search)"""
        self._update_filter_chips()

    def _on_status_changed(self, status):
        """Handle status filter changes"""
        self.proxy.setStatus(status)
        self._update_filter_chips()

    def _on_department_filter_changed(self, dept):
        """Handle department filter changes"""
        self.proxy.setDepartment(dept)
        self._update_filter_chips()

    def _on_agency_filter_changed(self, agency):
        """Handle agency filter changes"""
        self.proxy.setAgency(agency)
        self._update_filter_chips()

    def _clear_all_filters(self):
        """Clear all filters"""
        self.search.clear()
        self.department_filter.combo_box.setCurrentText("All Depts")
        self.agency_filter.combo_box.setCurrentText("All Agencies")
        self.status.combo_box.setCurrentText("All Status")
        self._update_filter_chips()

    def _load_agencies(self):
        """Load agencies from database"""
        try:
            agencies = self.db.get_agencies()
            for agency in agencies:
                self.agency_filter.addItem(agency)
        except Exception as e:
            logging.warning(f"Failed to load agencies: {e}")

    def refresh_agencies(self):
        """Refresh the agency filter dropdown"""
        current = self.agency_filter.combo_box.currentText()
        self.agency_filter.clear()
        self.agency_filter.addItem("All Agencies")
        self._load_agencies()
        # Restore selection if still valid
        idx = self.agency_filter.findText(current)
        if idx >= 0:
            self.agency_filter.combo_box.setCurrentIndex(idx)

    def _on_search_changed(self):
        """Update both filter and highlighting when search changes"""
        search_text = self.search.text()
        self.proxy.setTerm(search_text)
        self.model.set_search_term(search_text)

    def set_data(self, employees):
        """Set employee data with stagger animation"""
        self.model.setDataList(employees)
        # Re-apply default sort by Emp ID number (column 2) after loading data
        # Using proxy.sort() ensures the sort is applied immediately
        self.proxy.sort(2, Qt.AscendingOrder)
        self.proxy.invalidate()  # Force proxy to re-sort
        self._update_btn()
        # Scroll to top to show first employees (1-7) instead of last viewed position
        self.table.scrollToTop()
        # Trigger stagger animation for visible rows
        self._animate_rows()
    
    def _animate_rows(self):
        """Animate rows appearing with stagger effect"""
        # Get visible rows
        visible_count = min(self.proxy.rowCount(), 20)  # Limit to first 20 visible
        
        # Stagger animation: fade in rows one by one
        for i in range(visible_count):
            QTimer.singleShot(i * 30, lambda row=i: self._fade_in_row(row))
    
    def _fade_in_row(self, row):
        """Fade in a single row (visual feedback via selection flash)"""
        try:
            if row < self.proxy.rowCount():
                index = self.proxy.index(row, 0)
                # Brief visual flash effect - removed scrollTo to preserve top position
                pass
        except:
            pass  # Ignore if row no longer exists

    def _update_btn(self):
        selected_count = len(self.table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(selected_count == 1) # Enable only if 1 is selected
        self.delete_btn.setEnabled(selected_count > 0) # Enable if 1 or more are selected
        self.delete_btn.setText(f"🗑️ Delete Selected ({selected_count})")
    
    def eventFilter(self, obj, event):
        """Event filter for micro-interaction hover effects on table rows"""
        if obj == self.table.viewport():
            if event.type() == QEvent.MouseMove:
                # Get the row under the mouse cursor
                index = self.table.indexAt(event.pos())
                if index.isValid():
                    # Map proxy row to source row
                    source_index = self.proxy.mapToSource(index)
                    self.model.set_hovered_row(source_index.row())
                else:
                    self.model.set_hovered_row(-1)
            elif event.type() == QEvent.Leave:
                # Mouse left the table viewport
                self.model.set_hovered_row(-1)
        return super().eventFilter(obj, event)
    
    def _on_refresh_clicked(self):
        """Handle refresh button click - emit signal for parent to refresh data"""
        self.refresh_requested.emit()
        # Visual feedback
        self.refresh_btn.setText("🔄 Refreshing...")
        self.refresh_btn.setEnabled(False)
        # Re-enable after a short delay
        QTimer.singleShot(500, lambda: (
            self.refresh_btn.setText("🔄 Refresh"),
            self.refresh_btn.setEnabled(True)
        ))
    
    def _edit(self):
        try:
            selected_rows = self.table.selectionModel().selectedRows()
            if len(selected_rows) != 1:
                show_warning_toast(self, "Please select exactly one employee to edit.")
                return

            source_row = self.proxy.mapToSource(selected_rows[0]).row()
            if source_row < 0 or source_row >= len(self.model.data_list):
                show_warning_toast(
                    self,
                    "Invalid selection. The employee list may have been refreshed.\n"
                    "Please refresh (F5) and try again."
                )
                return

            employee_data = self.model.data_list[source_row]
            if not employee_data:
                show_warning_toast(
                    self,
                    "Unable to retrieve employee data.\n"
                    "Please refresh the list (F5) and try again."
                )
                return

            self.on_edit(employee_data)
        except Exception as e:
            show_error_toast(
                self,
                f"Failed to open employee: {str(e)}\n"
                "Please refresh the list and try again."
            )
            logging.error(f"Failed to open employee for editing: {e}")
    
    def _double(self, idx):
        """Handle double-click - open quick edit for specific columns or view for others"""
        source_idx = self.proxy.mapToSource(idx)
        row = source_idx.row()
        col = idx.column()
        
        if 0 <= row < self.model.rowCount():
            employee = self.model.data_list[row]
            
            # Photo column (col 1) - show photo preview popup
            if col == 1:
                self._show_photo_preview(employee)
                return
            
            # v4.5.0: Quick edit for specific columns (Salary=4, SSS=5 - shifted for Photo column)
            editable_cols = {
                4: ('salary', 'Salary/Day', 'Enter salary amount'),
                5: ('sss_number', 'SSS Number', 'XX-XXXXXXX-X'),
            }
            
            if col in editable_cols:
                field_key, field_label, placeholder = editable_cols[col]
                self._show_quick_edit_dialog(employee, field_key, field_label, placeholder)
            else:
                # Default: open view dialog
                self.on_view(employee)

    def _show_photo_preview(self, employee):
        """Show scalable photo preview popup with zoom controls"""
        from employee_vault.config import PHOTOS_DIR
        from employee_vault.ui.widgets import SmoothAnimatedDialog
        
        emp_id = employee.get('emp_id', '')
        emp_name = employee.get('name', 'Unknown')
        
        # Find photo file
        photo_path = None
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            test_path = os.path.join(PHOTOS_DIR, f"{emp_id}{ext}")
            if os.path.exists(test_path):
                photo_path = test_path
                break
        
        if not photo_path:
            from employee_vault.ui.modern_ui_helper import show_warning_toast
            show_warning_toast(self, f"No photo found for {emp_name}")
            return
        
        # Create preview dialog
        dialog = SmoothAnimatedDialog(self, animation_style="fade")
        dialog.setWindowTitle(f"📷 Photo - {emp_name}")
        dialog.resize(500, 550)
        
        layout = QVBoxLayout(dialog)
        
        # Header with employee info
        header = QLabel(f"<h3>{emp_name}</h3><p>Employee ID: {emp_id}</p>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Scrollable image area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        
        # Image label
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        original_pixmap = QPixmap(photo_path)
        
        # Store for zoom
        dialog.original_pixmap = original_pixmap
        dialog.img_label = img_label
        dialog.zoom_level = 1.0
        
        def update_image():
            if dialog.original_pixmap.isNull():
                return
            scaled_size = dialog.original_pixmap.size() * dialog.zoom_level
            # Fix: QSize doesn't have toSize() - use width/height directly
            scaled_pixmap = dialog.original_pixmap.scaled(
                int(scaled_size.width()),
                int(scaled_size.height()),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            dialog.img_label.setPixmap(scaled_pixmap)
        
        # Initial display
        dialog.zoom_level = min(400 / original_pixmap.width(), 400 / original_pixmap.height(), 1.0)
        update_image()
        
        scroll_area.setWidget(img_label)
        layout.addWidget(scroll_area, 1)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        
        zoom_out_btn = ModernAnimatedButton("➖ Zoom Out")
        apply_ios_style(zoom_out_btn, 'gray')
        def zoom_out():
            dialog.zoom_level = max(0.25, dialog.zoom_level - 0.25)
            update_image()
        zoom_out_btn.clicked.connect(zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        zoom_label = QLabel("100%")
        zoom_label.setAlignment(Qt.AlignCenter)
        zoom_label.setMinimumWidth(60)
        dialog.zoom_label = zoom_label
        
        def update_zoom_label():
            dialog.zoom_label.setText(f"{int(dialog.zoom_level * 100)}%")
        
        # Reconnect update_image to also update label
        original_update = update_image
        def update_image():
            original_update()
            update_zoom_label()
        
        zoom_layout.addWidget(zoom_label)
        
        zoom_in_btn = ModernAnimatedButton("➕ Zoom In")
        apply_ios_style(zoom_in_btn, 'gray')
        def zoom_in():
            dialog.zoom_level = min(3.0, dialog.zoom_level + 0.25)
            update_image()
        zoom_in_btn.clicked.connect(zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        
        fit_btn = ModernAnimatedButton("🔲 Fit")
        apply_ios_style(fit_btn, 'blue')
        def fit_to_window():
            dialog.zoom_level = min(400 / original_pixmap.width(), 400 / original_pixmap.height(), 1.0)
            update_image()
        fit_btn.clicked.connect(fit_to_window)
        zoom_layout.addWidget(fit_btn)
        
        actual_btn = ModernAnimatedButton("1:1 Actual")
        apply_ios_style(actual_btn, 'green')
        def actual_size():
            dialog.zoom_level = 1.0
            update_image()
        actual_btn.clicked.connect(actual_size)
        zoom_layout.addWidget(actual_btn)
        
        layout.addLayout(zoom_layout)
        
        # Close button
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        # Initial zoom label update
        update_zoom_label()
        
        dialog.exec()

    def _show_context_menu(self, pos):
        """Show right-click context menu for employee table"""
        index = self.table.indexAt(pos)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(30, 35, 50, 240);
                border: 2px solid rgba(74, 158, 255, 0.5);
                border-radius: 12px;
                padding: 8px;
            }
            QMenu::item {
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                background: transparent;
            }
            QMenu::item:selected {
                background: rgba(74, 158, 255, 0.3);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.2);
                margin: 5px 10px;
            }
        """)
        
        # Get selected employees
        selected_rows = set(self.proxy.mapToSource(i).row() for i in self.table.selectionModel().selectedRows())
        
        if index.isValid():
            source_idx = self.proxy.mapToSource(index)
            row = source_idx.row()
            if 0 <= row < self.model.rowCount():
                employee = self.model.data_list[row]
                
                # View action
                view_action = menu.addAction("👁️ View Details")
                view_action.triggered.connect(lambda: self.on_view(employee))
                
                # Edit action
                edit_action = menu.addAction("✏️ Edit Employee")
                edit_action.triggered.connect(lambda: self.on_edit(employee))
                
                # View photo action
                photo_action = menu.addAction("📷 View Photo")
                photo_action.triggered.connect(lambda: self._show_photo_preview(employee))
                
                menu.addSeparator()
        
        # Delete selected (only if there's selection)
        if selected_rows:
            delete_action = menu.addAction(f"🗑️ Delete Selected ({len(selected_rows)})")
            delete_action.triggered.connect(self._delete)
        
        menu.addSeparator()
        
        # Select All
        select_all_action = menu.addAction("☑️ Select All (Ctrl+A)")
        select_all_action.triggered.connect(self._select_all)
        
        # Clear Selection
        if selected_rows:
            clear_action = menu.addAction("☐ Clear Selection")
            clear_action.triggered.connect(self.table.clearSelection)
        
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def _show_quick_edit_dialog(self, employee, field_key, field_label, placeholder):
        """Show a quick edit dialog for a single field"""
        from PySide6.QtWidgets import QInputDialog
        
        current_value = employee.get(field_key, '')
        
        new_value, ok = QInputDialog.getText(
            self,
            f"Edit {field_label}",
            f"Enter new {field_label} for {employee.get('name', 'Employee')}:",
            text=str(current_value) if current_value else ''
        )
        
        if ok and new_value != current_value:
            # Signal that we want to quick-save this field
            # For now, emit the edit signal to open the full form
            # In a future enhancement, we could save directly to DB
            self.on_edit(employee)
    
    def _select_all(self): self.table.selectAll(); self._update_btn()
    def _delete(self):
        rows=sorted(set(self.proxy.mapToSource(i).row() for i in self.table.selectionModel().selectedRows()))
        if not rows:
            show_warning_toast(
                self,
                "No employees selected for deletion.\n"
                "Please select one or more employees from the list."
            )
            return
        self.on_delete_selected([self.model.data_list[r] for r in rows]); self._update_btn()

    def _show_column_menu(self):
        """Show column visibility menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(30, 35, 50, 240);
                border: 2px solid rgba(74, 158, 255, 0.5);
                border-radius: 12px;
                padding: 8px;
            }
            QMenu::item {
                color: white;
                padding: 8px 24px;
                border-radius: 6px;
                background: transparent;
            }
            QMenu::item:selected {
                background: rgba(74, 158, 255, 0.3);
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                margin-right: 8px;
            }
            QMenu::indicator:checked {
                background: rgba(74, 158, 255, 0.8);
                border: 2px solid white;
                border-radius: 4px;
            }
            QMenu::indicator:unchecked {
                background: rgba(100, 100, 100, 0.5);
                border: 2px solid rgba(200, 200, 200, 0.5);
                border-radius: 4px;
            }
        """)

        # Skip row number column (0), start from 1
        for col in range(1, len(HEADERS)):
            action = menu.addAction(HEADERS[col])
            action.setCheckable(True)
            is_visible = not self.table.isColumnHidden(col)
            action.setChecked(is_visible)
            # Store column index in action's data
            action.setData(col)
        
        # Connect to a single handler that reads the action
        menu.triggered.connect(self._on_column_action_triggered)

        # Show menu at button position
        pos = self.column_toggle_btn.mapToGlobal(self.column_toggle_btn.rect().bottomLeft())
        menu.exec(pos)
    
    def _on_column_action_triggered(self, action):
        """Handle column menu action triggered"""
        col = action.data()
        if col is not None:
            visible = action.isChecked()
            self._toggle_column(col, visible)

    def _toggle_column(self, col, visible):
        """Toggle column visibility and save preference"""
        if visible:
            self.table.showColumn(col)
        else:
            self.table.hideColumn(col)
        self._save_column_visibility()

    def _save_column_visibility(self):
        """Save column visibility preferences to QSettings"""
        settings = QSettings("EmployeeVault", "ColumnVisibility")
        for col in range(1, len(HEADERS)):
            settings.setValue(f"column_{col}_visible", not self.table.isColumnHidden(col))

    def _load_column_visibility(self):
        """Load column visibility preferences from QSettings"""
        settings = QSettings("EmployeeVault", "ColumnVisibility")
        for col in range(1, len(HEADERS)):
            # Default to visible for all columns
            visible = settings.value(f"column_{col}_visible", True, type=bool)
            if not visible:
                self.table.hideColumn(col)
