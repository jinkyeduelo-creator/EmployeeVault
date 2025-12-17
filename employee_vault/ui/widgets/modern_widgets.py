"""
Modern UI Widgets for Employee Vault
Contains toast notifications, loading spinners, animated buttons, and more
"""

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize,
    Signal, QObject, QEvent
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QLinearGradient,
    QFont, QFontMetrics
)
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout,
    QGraphicsOpacityEffect, QApplication
)


# ============================================================================
# TOAST NOTIFICATION SYSTEM
# ============================================================================

class ToastNotification(QFrame):
    """
    Modern toast notification (non-blocking alternative to QMessageBox)
    Usage:
        ToastNotification.show_success(parent, "Operation successful!")
        ToastNotification.show_error(parent, "Error occurred")
        ToastNotification.show_info(parent, "Information")
        ToastNotification.show_warning(parent, "Warning message")
    """

    def __init__(self, message, toast_type="info", parent=None, duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Color schemes
        colors = {
            "info": {"bg": "#2196F3", "icon": "ℹ️"},
            "success": {"bg": "#4CAF50", "icon": "✓"},
            "warning": {"bg": "#FF9800", "icon": "⚠️"},
            "error": {"bg": "#F44336", "icon": "✗"}
        }

        color_scheme = colors.get(toast_type, colors["info"])

        # Setup UI
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color_scheme['bg']};
                border-radius: 10px;
                padding: 12px 20px;
            }}
            QLabel {{
                color: white;
                font-weight: 600;
                font-size: 13px;
                background: transparent;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Icon
        icon_label = QLabel(color_scheme['icon'])
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        # Adjust size
        self.adjustSize()
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)

        # Position at bottom-right of parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.width() - self.width() - 20
            y = parent_rect.height() - self.height() - 20
            self.move(parent.mapToGlobal(QPoint(x, y)))

        # Slide in animation
        self.slide_in()

        # Auto-hide after duration
        QTimer.singleShot(duration, self.fade_out)

    def slide_in(self):
        """Slide in from bottom"""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.show()
        self.fade_animation.start()

    def fade_out(self):
        """Fade out animation"""
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(self.deleteLater)
        fade_out.start()

    @staticmethod
    def show_info(parent, message, duration=3000):
        """Show info toast"""
        toast = ToastNotification(message, "info", parent, duration)
        return toast

    @staticmethod
    def show_success(parent, message, duration=3000):
        """Show success toast"""
        toast = ToastNotification(message, "success", parent, duration)
        return toast

    @staticmethod
    def show_warning(parent, message, duration=3000):
        """Show warning toast"""
        toast = ToastNotification(message, "warning", parent, duration)
        return toast

    @staticmethod
    def show_error(parent, message, duration=3000):
        """Show error toast"""
        toast = ToastNotification(message, "error", parent, duration)
        return toast


# ============================================================================
# LOADING SPINNER
# ============================================================================

class LoadingSpinner(QWidget):
    """
    Animated loading spinner
    Usage:
        spinner = LoadingSpinner(parent)
        spinner.start()
        # ... do work ...
        spinner.stop()
    """

    def __init__(self, parent=None, size=40, color=None):
        super().__init__(parent)
        self.size = size
        self.color = color or QColor("#2196F3")
        self.angle = 0
        self.setFixedSize(size, size)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.setInterval(50)  # 20 FPS

    def start(self):
        """Start spinning"""
        self.show()
        self.timer.start()

    def stop(self):
        """Stop spinning"""
        self.timer.stop()
        self.hide()

    def rotate(self):
        """Rotate the spinner"""
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        """Draw the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw spinning arc
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.translate(rect.width() / 2, rect.height() / 2)
        painter.rotate(self.angle)
        painter.translate(-rect.width() / 2, -rect.height() / 2)

        pen = QPen(self.color, 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawArc(rect, 0, 270 * 16)


# ============================================================================
# LOADING OVERLAY
# ============================================================================

class LoadingOverlay(QWidget):
    """
    Full-screen loading overlay with spinner and message
    Usage:
        overlay = LoadingOverlay(parent, "Loading...")
        overlay.show()
        # ... do work ...
        overlay.hide()
    """

    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Spinner
        self.spinner = LoadingSpinner(self, 60)
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)

        # Message
        self.label = QLabel(message)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 150);
                padding: 10px 20px;
                border-radius: 8px;
            }
        """)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)

        # Start spinner
        self.spinner.start()

        # Match parent size
        if parent:
            self.setGeometry(parent.rect())

    def paintEvent(self, event):
        """Draw semi-transparent background"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

    def set_message(self, message):
        """Update loading message"""
        self.label.setText(message)


# ============================================================================
# ANIMATED BUTTON
# ============================================================================

class AnimatedButton(QPushButton):
    """
    Button with hover animations
    - Grows slightly on hover
    - Ripple effect on click
    """

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.default_height = 36
        self.setMinimumHeight(self.default_height)

        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"minimumHeight")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Scale factor
        self.scale_factor = 1.0

    def enterEvent(self, event):
        """Mouse enter - grow button"""
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self.height())
        self.hover_animation.setEndValue(self.default_height + 4)
        self.hover_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse leave - shrink button"""
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self.height())
        self.hover_animation.setEndValue(self.default_height)
        self.hover_animation.start()
        super().leaveEvent(event)


# ============================================================================
# CIRCULAR PHOTO HELPER
# ============================================================================

def create_circular_pixmap(pixmap, size=160):
    """
    Convert square pixmap to circular
    Usage:
        circular_photo = create_circular_pixmap(original_photo, 160)
        label.setPixmap(circular_photo)
    """
    from PySide6.QtGui import QPixmap, QPainter, QPainterPath

    if pixmap.isNull():
        return QPixmap()

    # Scale to size
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # Create circular mask
    result = QPixmap(size, size)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing, True)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()

    return result


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ToastNotification',
    'LoadingSpinner',
    'LoadingOverlay',
    'AnimatedButton',
    'add_fade_in_animation',
    'create_circular_pixmap'
]
