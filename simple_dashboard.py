from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QComboBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap

class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.expanded = True
        self.setFixedWidth(200)
        self.setStyleSheet("background: #232946; color: #fff;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        # Logo and company name
        logo = QLabel()
        logo.setPixmap(QPixmap("logo.png").scaled(40, 40, Qt.KeepAspectRatio))
        name = QLabel("Company Name")
        name.setStyleSheet("font-weight: bold; font-size: 18px;")
        logo_row = QHBoxLayout()
        logo_row.addWidget(logo)
        logo_row.addWidget(name)
        logo_row.addStretch()
        logo_widget = QWidget()
        logo_widget.setLayout(logo_row)
        self.layout.addWidget(logo_widget)
        # Navigation buttons
        self.buttons = []
        for text in ["Dashboard", "Employees", "Documents", "Payroll", "Chat"]:
            btn = QPushButton(text)
            btn.setStyleSheet("QPushButton { text-align: left; padding: 10px; border: none; }"
                              "QPushButton:hover { background: #393e6a; }")
            self.layout.addWidget(btn)
            self.buttons.append(btn)
        self.layout.addStretch()
        # Collapse/Expand
        self.toggle_btn = QPushButton("⮜")
        self.toggle_btn.clicked.connect(self.toggle)
        self.layout.addWidget(self.toggle_btn)

    def toggle(self):
        new_width = 60 if self.expanded else 200
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(new_width)
        self.animation.start()
        self.expanded = not self.expanded
        self.toggle_btn.setText("⮞" if not self.expanded else "⮜")

class TopBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #121629; color: #fff;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addStretch()
        # User profile
        self.profile = QLabel("User Name")
        self.profile.setPixmap(QPixmap("user.png").scaled(32, 32, Qt.KeepAspectRatio))
        self.dropdown = QComboBox()
        self.dropdown.addItems(["Profile", "Settings", "Logout"])
        layout.addWidget(self.profile)
        layout.addWidget(self.dropdown)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Dashboard")
        self.setMinimumSize(900, 600)
        # Layouts
        central = QWidget()
        main_layout = QVBoxLayout(central)
        self.topbar = TopBar()
        main_layout.addWidget(self.topbar)
        content_layout = QHBoxLayout()
        self.sidebar = Sidebar()
        content_layout.addWidget(self.sidebar)
        # Main content area
        self.stack = QStackedWidget()
        for i in range(5):
            page = QLabel(f"Page {i+1}")
            page.setAlignment(Qt.AlignCenter)
            self.stack.addWidget(page)
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)
        self.setCentralWidget(central)

if __name__ == "__main__":
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()
