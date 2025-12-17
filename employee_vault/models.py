"""
Table models for Employee Vault UI
Contains QAbstractTableModel implementations
v4.6.0: Enhanced with lazy photo loading
"""

import os
from collections import OrderedDict
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QSize, QThread, Signal, QObject, QRunnable, QThreadPool
from PySide6.QtGui import QColor, QPixmap, QIcon
from typing import Any, Set

from employee_vault.config import HEADERS, ALERT_DAYS, contract_days_left, PHOTOS_DIR, get_employee_photos


# Phase 1.3: Async photo loading infrastructure
class PhotoSignals(QObject):
    """Signals for async photo loading"""
    photo_loaded = Signal(str, object)  # emp_id, pixmap

class PhotoLoadRunnable(QRunnable):
    """Phase 1.3: QRunnable for loading photos asynchronously in QThreadPool"""
    def __init__(self, emp_id: str, photo_path: str, signals: PhotoSignals):
        super().__init__()
        self.emp_id = emp_id
        self.photo_path = photo_path
        self.signals = signals

    def run(self):
        """Load photo in background thread"""
        try:
            pixmap = QPixmap(self.photo_path)
            if not pixmap.isNull():
                # Scale to thumbnail size
                thumbnail = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.signals.photo_loaded.emit(self.emp_id, thumbnail)
        except Exception:
            # Silently fail if photo can't be loaded
            pass


class EmployeesTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.data_list=data
        self.search_term = ""  # FEATURE: Search highlighting

        # Phase 1.3: LRU cache with bounded size for photo thumbnails
        self._photo_cache = OrderedDict()  # OrderedDict for LRU eviction
        self._max_cache_size = 100  # Limit to 100 photos in memory

        self._photo_path_cache = {}  # Cache for photo path lookups (prevents repeated disk I/O)
        self._loading_photos: Set[str] = set()  # Photos currently being loaded
        self._hovered_row = -1  # Micro-interaction: track hovered row

        # Phase 1.3: Async photo loading setup
        self._photo_signals = PhotoSignals()
        self._photo_signals.photo_loaded.connect(self._on_photo_loaded)

        # Create placeholder pixmap for loading state
        self._placeholder_pixmap = QPixmap(32, 32)
        self._placeholder_pixmap.fill(QColor(60, 60, 60, 100))

    def get_hovered_row(self) -> int:
        """Get currently hovered row index"""
        return self._hovered_row
    
    def set_hovered_row(self, row: int):
        """Set hovered row for micro-interaction highlight (optimized)"""
        if self._hovered_row != row:
            old_row = self._hovered_row
            self._hovered_row = row
            # PERFORMANCE: Only emit BackgroundRole changes to avoid triggering full repaint
            roles = [Qt.BackgroundRole]
            if old_row >= 0:
                self.dataChanged.emit(
                    self.index(old_row, 0),
                    self.index(old_row, self.columnCount() - 1),
                    roles
                )
            if row >= 0:
                self.dataChanged.emit(
                    self.index(row, 0),
                    self.index(row, self.columnCount() - 1),
                    roles
                )

    def set_search_term(self, term: str):
        """Set the search term for highlighting"""
        self.search_term = term.lower().strip()
        self.layoutChanged.emit()  # Refresh display

    def _highlight_text(self, text: str) -> str:
        """Add HTML highlighting to search matches"""
        if not self.search_term or not text:
            return text

        # Case-insensitive search
        text_lower = text.lower()
        term_lower = self.search_term

        if term_lower not in text_lower:
            return text

        # Find all occurrences and highlight them
        result = []
        last_pos = 0

        while True:
            pos = text_lower.find(term_lower, last_pos)
            if pos == -1:
                result.append(text[last_pos:])
                break

            # Add text before match
            result.append(text[last_pos:pos])

            # Add highlighted match
            match = text[pos:pos + len(term_lower)]
            result.append(f'<span style="background-color: #ffff00; color: #000000; font-weight: bold;">{match}</span>')

            last_pos = pos + len(term_lower)

        return ''.join(result)

    def rowCount(self, parent=QModelIndex()): return len(self.data_list)
    def columnCount(self, parent=QModelIndex()): return len(HEADERS)
    
    def _get_photo_thumbnail(self, emp_id):
        """Phase 1.3: Get cached photo thumbnail with async loading and LRU eviction"""
        # Check cache first
        if emp_id in self._photo_cache:
            # Move to end (most recently used)
            self._photo_cache.move_to_end(emp_id)
            return self._photo_cache[emp_id]

        # Check if already loading
        if emp_id in self._loading_photos:
            return self._placeholder_pixmap  # Show placeholder while loading

        # Mark as loading
        self._loading_photos.add(emp_id)

        # Check path cache first to avoid repeated disk I/O
        if emp_id in self._photo_path_cache:
            photo_path = self._photo_path_cache[emp_id]
        else:
            # v5.2: Try new folder structure first, then legacy
            photos = get_employee_photos(emp_id)
            photo_path = photos[0] if photos else None

            # Fallback to legacy location
            if not photo_path:
                legacy_path = os.path.join(PHOTOS_DIR, f"{emp_id}.png")
                if os.path.exists(legacy_path):
                    photo_path = legacy_path

            # Cache the path lookup result (even if None)
            self._photo_path_cache[emp_id] = photo_path

        if photo_path and os.path.exists(photo_path):
            # Queue async load using QThreadPool
            runnable = PhotoLoadRunnable(emp_id, photo_path, self._photo_signals)
            QThreadPool.globalInstance().start(runnable)
        else:
            # No photo found - cache None and stop loading
            self._photo_cache[emp_id] = None
            self._loading_photos.discard(emp_id)

        # Return placeholder immediately
        return self._placeholder_pixmap

    def _on_photo_loaded(self, emp_id: str, thumbnail: QPixmap):
        """Phase 1.3: Callback when photo is loaded asynchronously"""
        # Evict oldest entry if cache is full
        if len(self._photo_cache) >= self._max_cache_size:
            self._photo_cache.popitem(last=False)  # Remove oldest (FIFO from front)

        # Add to cache
        self._photo_cache[emp_id] = thumbnail
        self._loading_photos.discard(emp_id)

        # Update only the specific row
        for i, emp in enumerate(self.data_list):
            if emp.get("emp_id") == emp_id:
                index = self.index(i, 1)  # Photo column
                self.dataChanged.emit(index, index, [Qt.DecorationRole])
                break
    
    def invalidate_photo_cache(self, emp_id: str = None):
        """Invalidate photo cache for an employee or all employees.
        Call this after uploading/editing a photo to force reload."""
        if emp_id:
            self._photo_cache.pop(emp_id, None)
            self._photo_path_cache.pop(emp_id, None)
            self._loading_photos.discard(emp_id)
        else:
            # Clear all caches
            self._photo_cache.clear()
            self._photo_path_cache.clear()
            self._loading_photos.clear()
    
    def update_photo_cache(self, emp_id: str, pixmap):
        """Update photo cache from background loader - Phase 1.3: with LRU eviction"""
        # Evict oldest entry if cache is full
        if len(self._photo_cache) >= self._max_cache_size:
            self._photo_cache.popitem(last=False)

        self._photo_cache[emp_id] = pixmap
        self._loading_photos.discard(emp_id)

        # Find row and emit dataChanged
        for i, emp in enumerate(self.data_list):
            if emp.get("emp_id") == emp_id:
                index = self.index(i, 1)  # Photo column
                self.dataChanged.emit(index, index, [Qt.DecorationRole])
                break
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        e=self.data_list[index.row()]; col=index.column()
        
        # v4.0: Row number column styling
        if col == 0 and role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if col == 0 and role == Qt.ForegroundRole:
            return QColor("#888888")
        
        # Photo column (col 1)
        if col == 1:
            emp_id = e.get("emp_id", "")
            if role == Qt.DecorationRole:
                thumbnail = self._get_photo_thumbnail(emp_id)
                if thumbnail:
                    return thumbnail
                return None
            elif role == Qt.DisplayRole:
                # Show placeholder text if no photo
                thumbnail = self._get_photo_thumbnail(emp_id)
                if thumbnail is None:
                    return "📷"
                return ""
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            elif role == Qt.ToolTipRole:
                thumbnail = self._get_photo_thumbnail(emp_id)
                if thumbnail is None:
                    return "No photo - click to add"
                return "Employee photo"
            elif role == Qt.SizeHintRole:
                return QSize(40, 40)
            return None
        
        if role==Qt.ToolTipRole:
            d=contract_days_left(e);
            if d is not None: return f"Contract expired {-d} day(s) ago" if d<0 else f"Contract expires in {d} day(s)"

        # MICRO-INTERACTION: Hover row highlight
        if role == Qt.BackgroundRole and index.row() == self._hovered_row:
            # Return subtle highlight for hovered row
            return QColor(255, 255, 255, 15)  # Subtle white overlay

        # FEATURE: Enhanced contract expiry highlighting
        if role==Qt.BackgroundRole:
            d=contract_days_left(e)
            if d is not None:
                if d < 0:  # Expired
                    return QColor(244, 67, 54, 40)  # Red with 40 alpha (subtle)
                elif d <= 7:  # Less than 7 days
                    return QColor(244, 67, 54, 30)  # Red with 30 alpha
                elif d <= 14:  # Less than 14 days
                    return QColor(255, 152, 0, 25)  # Orange with 25 alpha
                elif d <= 30:  # Less than 30 days
                    return QColor(255, 235, 59, 20)  # Yellow with 20 alpha

        if role==Qt.ForegroundRole:
            d=contract_days_left(e);
            # Enhanced text color for contract expiry column (shifted due to Photo column)
            if d is not None and col == 10:  # Contract Expiry column
                if d < 0:  # Expired
                    return QColor("#ff6b6b")  # Bright red
                elif d <= 7:  # Critical - less than 7 days
                    return QColor("#ff6b6b")  # Red
                elif d <= 14:  # Warning - less than 14 days
                    return QColor("#ff9800")  # Orange
                elif d <= 30:  # Caution - less than 30 days
                    return QColor("#ffeb3b")  # Yellow
            # Make other columns more visible for highlighted rows
            if d is not None and d <= 30 and col != 10:
                return QColor("#ffffff")  # White text for better contrast
        # PERFORMANCE: EditRole returns raw data for sorting (no photo loading, no formatting)
        if role == Qt.EditRole:
            if col == 0:
                # Extract number from Emp ID for sorting (e.g., "D-001-25" -> 1)
                return extract_emp_id_number(e.get("emp_id", ""))
            if col == 1:
                return ""  # Photo column - no sortable data
            # Raw values for sorting (no formatting)
            raw_values = {
                2: e.get("emp_id", ""),
                3: e.get("name", ""),
                4: float(e.get('salary', 0)),  # Numeric for proper sorting
                5: e.get("sss_number", "") or "",
                6: e.get("department", ""),
                7: e.get("position", ""),
                8: e.get("hire_date", ""),
                9: e.get("agency", "") or "",
                10: e.get("contract_expiry", "") or "",
                11: e.get("resign_date", "") or "",
                12: "Active" if not e.get("resign_date") else "Resigned"
            }
            return raw_values.get(col, "")
        
        if role==Qt.DisplayRole:
            if col == 0:
                # Show number from Emp ID (e.g., "D-001-25" -> "1")
                return str(extract_emp_id_number(e.get("emp_id", "")))

            # Get raw values (shifted by 1 due to Photo column)
            values = ["",  # Row number handled above
                    "",  # Photo column handled above
                    e.get("emp_id",""),
                    e.get("name",""),
                    f"₱{float(e.get('salary', 0)):,.2f}",  # Salary column with Philippine Peso formatting
                    e.get("sss_number","") or "—",
                    e.get("department",""),
                    e.get("position",""),
                    e.get("hire_date",""),
                    e.get("agency","") or "—",
                    e.get("contract_expiry","") or "—",
                    e.get("resign_date","") or "—",
                    ("Active" if not e.get("resign_date") else f"Resigned-{e.get('resign_date')}")]

            value = values[col]

            # FEATURE: Apply highlighting to searchable columns (shifted due to Photo column)
            # emp_id=2, name=3, department=6, position=7
            if self.search_term and col in [2, 3, 6, 7]:
                value = self._highlight_text(str(value))

            return value
        return None
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role==Qt.DisplayRole and orientation==Qt.Horizontal: return HEADERS[section]
        return super().headerData(section, orientation, role)
    def setDataList(self, data): 
        self.beginResetModel()
        self.data_list=data
        # Clear all photo caches on data refresh to pick up new/updated photos
        self._photo_cache = {}
        self._photo_path_cache = {}
        self._loading_photos.clear()
        self.endResetModel()


import re

def natural_sort_key(text):
    """
    Extract numeric parts for natural sorting.
    e.g., 'EMP-001' -> ('EMP-', 1), '10' -> ('', 10)
    This ensures 1 < 2 < 10 instead of '1' < '10' < '2'
    """
    if text is None:
        return ('', 0)
    text = str(text)
    # Split into text and numeric parts
    parts = re.split(r'(\d+)', text)
    result = []
    for part in parts:
        if part.isdigit():
            result.append((0, int(part)))  # Numeric: sort by value
        else:
            result.append((1, part.lower()))  # Text: sort alphabetically
    return result


def extract_emp_id_number(emp_id):
    """
    Extract the numeric portion from Emp ID format like 'D-001-25' -> 1
    This is used for the # column to sync with Emp ID sorting.
    Example: 'D-001-25' -> 1, 'D-010-25' -> 10, 'D-100-25' -> 100
    """
    if not emp_id:
        return 0
    # Match pattern like D-NNN-YY (number between dashes)
    match = re.search(r'-0*(\d+)-', str(emp_id))
    if match:
        return int(match.group(1))
    # Fallback: find first number sequence
    match = re.search(r'0*(\d+)', str(emp_id))
    if match:
        return int(match.group(1))
    return 0


class EmployeesFilter(QSortFilterProxyModel):
    def __init__(self): 
        super().__init__()
        self.term = ""
        self.status = "All Status"
        self.department = "All Depts"
        self.agency = "All Agencies"
    
    def setTerm(self, t): 
        self.term = t.lower()
        self.invalidateFilter()
    
    def setStatus(self, s): 
        self.status = s
        self.invalidateFilter()
    
    def setDepartment(self, d):
        self.department = d
        self.invalidateFilter()
    
    def setAgency(self, a):
        self.agency = a
        self.invalidateFilter()
    
    def lessThan(self, left, right):
        """
        Override sorting to use natural numeric sort for row # and Emp ID columns.
        This fixes: 1, 10, 11, 2, 20 -> 1, 2, 10, 11, 20
        And: 001, 010, 002 -> 001, 002, 010
        
        PERFORMANCE: Uses Qt.EditRole to get raw data without triggering photo loading
        """
        col = left.column()
        
        # Use EditRole to avoid triggering photo loading/formatting
        left_data = self.sourceModel().data(left, Qt.EditRole)
        right_data = self.sourceModel().data(right, Qt.EditRole)
        
        # Handle None values
        if left_data is None:
            left_data = ""
        if right_data is None:
            right_data = ""
        
        # Column 0 = Row number (already int from EditRole - extracted from Emp ID)
        if col == 0:
            return (left_data or 0) < (right_data or 0)
        
        # Column 2 = Emp ID - sort by the numeric portion ONLY (e.g., C-033-25 -> 33)
        # This ensures 1, 2, 3... order regardless of prefix letter
        if col == 2:
            left_num = extract_emp_id_number(left_data)
            right_num = extract_emp_id_number(right_data)
            return left_num < right_num
        
        # Column 4 = Salary (numeric sort)
        if col == 4:
            return (left_data or 0) < (right_data or 0)
        
        # Default string comparison for other columns
        return str(left_data).lower() < str(right_data).lower()
    
    def filterAcceptsRow(self, row, parent):
        m = self.sourceModel()
        if not m:
            return True
        
        # Get employee data from model columns (shifted +1 due to Photo column)
        # Column indices: 0=#, 1=Photo, 2=EmpID, 3=Name, 4=Salary, 5=SSS, 6=Department, 7=Position, 8=HireDate, 9=Agency, 10=ContractExpiry, 11=ResignDate, 12=Status
        emp_id = m.data(m.index(row, 2, parent)) or ""
        name = m.data(m.index(row, 3, parent)) or ""
        dept = m.data(m.index(row, 6, parent)) or ""
        position = m.data(m.index(row, 7, parent)) or ""
        agency = m.data(m.index(row, 9, parent)) or ""
        stat = m.data(m.index(row, 12, parent)) or "Active"
        
        # Status filter
        if self.status == "Active" and not stat.startswith("Active"):
            return False
        if self.status == "Not Active" and stat.startswith("Active"):
            return False
        if self.status == "Resigned" and not stat.startswith("Resigned"):
            return False
        
        # Department filter (use prefix match for Store/Warehouse which have sub-locations)
        if self.department != "All Depts":
            if self.department == "Store":
                # Match all "Store - ..." entries
                if not dept.startswith("Store"):
                    return False
            elif self.department == "Warehouse":
                # Match all "Warehouse - ..." entries
                if not dept.startswith("Warehouse"):
                    return False
            elif dept != self.department:
                # Exact match for other departments like "Office"
                return False
        
        # Agency filter
        if self.agency != "All Agencies" and agency != self.agency and agency != "—":
            # Handle "—" (no agency) case
            if self.agency == "—" and agency != "—":
                return False
            elif self.agency != "—" and agency != self.agency:
                return False
        
        # Search term filter
        if self.term:
            searchable = " ".join([emp_id, name, dept, position, agency]).lower()
            if self.term not in searchable:
                return False
        
        return True


class UserTableModel(QAbstractTableModel):
    """Table model for displaying users"""
    def __init__(self, users):
        super().__init__()
        self.users = users
        self.headers = ["Username", "Full Name", "Role"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.users)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        user = self.users[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return user['username']
            elif col == 1:
                return user['name']
            elif col == 2:
                return user['role'].upper()

        elif role == Qt.ForegroundRole:
            if col == 2:
                # Color code roles
                if user['role'] == 'admin':
                    return QColor("#ff9800")  # Orange for admin
                else:
                    return QColor("#4a9eff")  # Blue for user

        elif role == Qt.TextAlignmentRole:
            if col == 2:
                return Qt.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def set_data(self, users):
        """Update the data"""
        self.beginResetModel()
        self.users = users
        self.endResetModel()



