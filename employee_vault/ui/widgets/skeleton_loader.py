"""
Skeleton Loading Screens - Modern Loading Placeholder
Shimmer effect animation for better perceived performance
"""

from PySide6.QtCore import (
    Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame


class SkeletonWidget(QWidget):
    """
    Base skeleton widget with shimmer animation
    Provides loading placeholder with wave effect
    """

    def __init__(self, width=100, height=20, radius=4, parent=None):
        super().__init__(parent)
        self._shimmer_pos = -1.0  # Position of shimmer wave (-1 to 2)
        self._width = width
        self._height = height
        self._radius = radius

        self.setFixedSize(width, height)

        # Shimmer animation
        self.shimmer_anim = QPropertyAnimation(self, b"shimmer_pos")
        self.shimmer_anim.setDuration(1500)
        self.shimmer_anim.setStartValue(-1.0)
        self.shimmer_anim.setEndValue(2.0)
        self.shimmer_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.shimmer_anim.setLoopCount(-1)  # Infinite
        self.shimmer_anim.start()

    def get_shimmer_pos(self):
        return self._shimmer_pos

    def set_shimmer_pos(self, value):
        self._shimmer_pos = value
        self.update()

    shimmer_pos = Property(float, get_shimmer_pos, set_shimmer_pos)

    def paintEvent(self, event):
        """Draw skeleton with shimmer effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Base skeleton color (dark gray)
        rect = QRect(0, 0, self.width(), self.height())

        # Create shimmer gradient
        gradient = QLinearGradient(
            int(self.width() * self._shimmer_pos),
            0,
            int(self.width() * (self._shimmer_pos + 0.5)),
            0
        )

        # Base color (gray)
        base_color = QColor("#2d2d2d")
        shimmer_color = QColor("#3d3d3d")  # Lighter gray for shimmer

        gradient.setColorAt(0, base_color)
        gradient.setColorAt(0.5, shimmer_color)
        gradient.setColorAt(1, base_color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self._radius, self._radius)


class SkeletonLine(SkeletonWidget):
    """Single line skeleton (for text)"""

    def __init__(self, width=200, parent=None):
        super().__init__(width=width, height=16, radius=4, parent=parent)


class SkeletonCircle(SkeletonWidget):
    """Circular skeleton (for avatars/icons)"""

    def __init__(self, size=40, parent=None):
        super().__init__(width=size, height=size, radius=size//2, parent=parent)


class SkeletonBlock(SkeletonWidget):
    """Block skeleton (for cards/images)"""

    def __init__(self, width=300, height=200, parent=None):
        super().__init__(width=width, height=height, radius=8, parent=parent)


class SkeletonEmployeeRow(QWidget):
    """
    Skeleton for employee table row
    Matches the employee list structure
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Row number
        layout.addWidget(SkeletonLine(30))

        # Employee ID
        layout.addWidget(SkeletonLine(80))

        # Name
        layout.addWidget(SkeletonLine(150))

        # SSS
        layout.addWidget(SkeletonLine(100))

        # Department
        layout.addWidget(SkeletonLine(100))

        # Position
        layout.addWidget(SkeletonLine(120))

        # Hire Date
        layout.addWidget(SkeletonLine(90))

        # Agency
        layout.addWidget(SkeletonLine(100))

        # Status
        layout.addWidget(SkeletonLine(60))

        layout.addStretch()


class SkeletonEmployeeList(QWidget):
    """
    Complete skeleton for employee list
    Shows multiple rows
    """

    def __init__(self, row_count=10, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Add header skeleton
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.addWidget(SkeletonLine(500, header))
        header_layout.addStretch()
        layout.addWidget(header)

        # Add row skeletons
        for _ in range(row_count):
            layout.addWidget(SkeletonEmployeeRow())

        layout.addStretch()


class SkeletonCard(QWidget):
    """
    Skeleton for a card/panel with avatar and text
    Perfect for dashboard widgets
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Avatar
        layout.addWidget(SkeletonCircle(60))

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        text_layout.addWidget(SkeletonLine(200))
        text_layout.addWidget(SkeletonLine(150))
        text_layout.addWidget(SkeletonLine(180))
        text_layout.addStretch()

        layout.addLayout(text_layout)
        layout.addStretch()


class SkeletonDashboard(QWidget):
    """
    Complete skeleton for dashboard page
    Shows cards in grid layout
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        layout.addWidget(SkeletonLine(300))
        layout.addSpacing(10)

        # Stats row
        stats_row = QHBoxLayout()
        for _ in range(4):
            stats_row.addWidget(SkeletonBlock(150, 100))
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # Cards
        for _ in range(5):
            layout.addWidget(SkeletonCard())

        layout.addStretch()


class SkeletonForm(QWidget):
    """
    Skeleton for form inputs
    Shows labeled input fields
    """

    def __init__(self, field_count=6, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        for _ in range(field_count):
            # Label
            layout.addWidget(SkeletonLine(100))

            # Input field
            layout.addWidget(SkeletonLine(300, parent=self))

        layout.addStretch()


class SkeletonProfile(QWidget):
    """
    Skeleton for employee profile view
    Avatar + details layout
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header with avatar
        header = QHBoxLayout()
        header.addWidget(SkeletonCircle(100))

        # Name and title
        name_layout = QVBoxLayout()
        name_layout.setSpacing(10)
        name_layout.addWidget(SkeletonLine(200))
        name_layout.addWidget(SkeletonLine(150))
        name_layout.addStretch()
        header.addLayout(name_layout)
        header.addStretch()

        main_layout.addLayout(header)

        # Details section
        for _ in range(8):
            detail_row = QHBoxLayout()
            detail_row.addWidget(SkeletonLine(120))
            detail_row.addWidget(SkeletonLine(250))
            detail_row.addStretch()
            main_layout.addLayout(detail_row)

        main_layout.addStretch()


class PulsingDot(QWidget):
    """
    Pulsing dot indicator (alternative to spinner)
    Three dots that pulse in sequence
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 30)
        self._pulse_phase = 0

        # Pulse timer
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_timer.start(200)  # Update every 200ms

    def _update_pulse(self):
        """Update pulse animation phase"""
        self._pulse_phase = (self._pulse_phase + 1) % 6
        self.update()

    def paintEvent(self, event):
        """Draw three pulsing dots"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        dot_size = 8
        spacing = 20
        y = self.height() // 2

        for i in range(3):
            x = 10 + i * spacing

            # Calculate opacity based on pulse phase
            phase_diff = abs(self._pulse_phase - i * 2)
            opacity = max(0.3, 1.0 - (phase_diff / 6.0))

            color = QColor(33, 150, 243)  # Primary blue
            color.setAlphaF(opacity)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x, y - dot_size//2, dot_size, dot_size)

    def start(self):
        """Start pulsing"""
        self.pulse_timer.start()

    def stop(self):
        """Stop pulsing"""
        self.pulse_timer.stop()
