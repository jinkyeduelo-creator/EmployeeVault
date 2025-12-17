"""
Table models for Employee Vault UI
Contains QAbstractTableModel implementations
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor, QPixmap, QPainter, QPainterPath
from typing import Any
import os

from employee_vault.app_config import HEADERS, ALERT_DAYS, contract_days_left, PHOTOS_DIR

# Photo cache for thumbnail display
_photo_cache = {}

def _get_photo_pixmap(emp_id: str) -> QPixmap:
    """Load and cache employee photo with circular mask"""
    if not emp_id:
        return None
    
    if emp_id in _photo_cache:
        return _photo_cache[emp_id]
    
    # Try to find the photo
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        photo_path = os.path.join(PHOTOS_DIR, f"{emp_id}{ext}")
        if os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                # Scale to 40x40 for thumbnail
                scaled = pixmap.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                
                # Create circular mask
                size = min(scaled.width(), scaled.height())
                circular = QPixmap(size, size)
                circular.fill(Qt.transparent)
                
                painter = QPainter(circular)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)
                
                # Center the image
                x_offset = (scaled.width() - size) // 2
                y_offset = (scaled.height() - size) // 2
                painter.drawPixmap(-x_offset, -y_offset, scaled)
                painter.end()
                
                _photo_cache[emp_id] = circular
                return circular
    
    return None

class EmployeesTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.data_list=data
        self.search_term = ""  # FEATURE: Search highlighting

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
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        e=self.data_list[index.row()]; col=index.column()
        
        # v4.0: Row number column styling
        if col == 0 and role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if col == 0 and role == Qt.ForegroundRole:
            return QColor("#888888")
        
        # Photo column - display circular thumbnail
        if col == 1:
            if role == Qt.DecorationRole:
                emp_id = e.get("emp_id", "")
                return _get_photo_pixmap(emp_id)
            return None
        
        if role==Qt.ToolTipRole:
            d=contract_days_left(e);
            if d is not None: return f"Contract expired {-d} day(s) ago" if d<0 else f"Contract expires in {d} day(s)"

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
            if d is not None and col == 10:  # Shifted from 9 to 10 due to Photo column
                if d < 0:  # Expired
                    return QColor("#ff6b6b")  # Bright red
                elif d <= 7:  # Critical - less than 7 days
                    return QColor("#ff6b6b")  # Red
                elif d <= 14:  # Warning - less than 14 days
                    return QColor("#ff9800")  # Orange
                elif d <= 30:  # Caution - less than 30 days
                    return QColor("#ffeb3b")  # Yellow
            # Make other columns more visible for highlighted rows
            if d is not None and d <= 30 and col != 10:  # Shifted from 9 to 10 due to Photo column
                return QColor("#ffffff")  # White text for better contrast
        if role==Qt.DisplayRole:
            if col == 0:
                return str(index.row() + 1)  # Row number
            if col == 1:
                return ""  # Photo column - handled by DecorationRole

            # Get raw values (shifted by +1 for Photo column)
            values = ["",  # Row number handled above
                    "",   # Photo column handled above
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

            # FEATURE: Apply highlighting to searchable columns (emp_id, name, department, position)
            if self.search_term and col in [2, 3, 6, 7]:  # emp_id, name, department, position (shifted by +1 for Photo)
                value = self._highlight_text(str(value))

            return value
        return None
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role==Qt.DisplayRole and orientation==Qt.Horizontal: return HEADERS[section]
        return super().headerData(section, orientation, role)
    def setDataList(self, data): self.beginResetModel(); self.data_list=data; self.endResetModel()


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
    parts = re.split(r'(\d+)', text)
    result = []
    for part in parts:
        if part.isdigit():
            result.append((0, int(part)))
        else:
            result.append((1, part.lower()))
    return result


class EmployeesFilter(QSortFilterProxyModel):
    def __init__(self): super().__init__(); self.term=""; self.status="All"
    def setTerm(self, t): self.term=t.lower(); self.invalidateFilter()
    def setStatus(self, s): self.status=s; self.invalidateFilter()
    
    def lessThan(self, left, right):
        """Natural numeric sort for row # and Emp ID columns"""
        col = left.column()
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)
        
        # Column 0 = Row number, Column 2 = Emp ID
        if col in [0, 2]:
            return natural_sort_key(left_data) < natural_sort_key(right_data)
        return super().lessThan(left, right)
    
    def filterAcceptsRow(self, row, parent):
        m=self.sourceModel()
        # Column indices shifted by +1 for Photo column: emp_id=2, name=3, dept=6, pos=7, status=12
        empid=(m.data(m.index(row,2,parent)) or ""); name=(m.data(m.index(row,3,parent)) or ""); dept=(m.data(m.index(row,6,parent)) or ""); pos=(m.data(m.index(row,7,parent)) or ""); stat=(m.data(m.index(row,12,parent)) or "Active")
        if self.status=="Active" and stat!="Active": return False
        if self.status=="Resigned" and stat!="Resigned": return False
        if self.term: return self.term in (" ".join([name,dept,pos,empid]).lower())
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



