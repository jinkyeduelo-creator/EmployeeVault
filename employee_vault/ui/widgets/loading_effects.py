"""
Modern Loading Effects for EmployeeVault
Skeletons, shimmers, spinners, and progress indicators
"""

import math
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QBrush, QPen, QPainterPath,
    QRadialGradient
)


class ShimmerSkeleton(QWidget):
    """Skeleton loader with animated shimmer effect"""
    
    def __init__(self, parent=None, height: int = 20, rounded: bool = True):
        super().__init__(parent)
        self.skeleton_height = height
        self.rounded = rounded
        
        self.shimmer_position = 0.0
        self.shimmer_animation = QPropertyAnimation(self, b"shimmer_property")
        self.shimmer_animation.setDuration(1500)
        self.shimmer_animation.setStartValue(0.0)
        self.shimmer_animation.setEndValue(1.0)
        self.shimmer_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.shimmer_animation.setLoopCount(-1)  # Infinite
        
        self.setFixedHeight(height)
        self.shimmer_animation.start()
    
    def paintEvent(self, event):
        """Draw skeleton with shimmer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Base skeleton color
        base_color = QColor(200, 200, 200, 100)
        painter.fillRect(self.rect(), base_color)
        
        # Shimmer gradient
        shimmer_x = self.width() * self.shimmer_position
        gradient = QLinearGradient(
            shimmer_x - 100, 0,
            shimmer_x + 100, 0
        )
        
        gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 80))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        
        if self.rounded:
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()), 4, 4)
            painter.fillPath(path, QBrush(gradient))
        else:
            painter.fillRect(self.rect(), gradient)
    
    def get_shimmer_position(self):
        return self.shimmer_position
    
    def set_shimmer_position(self, value):
        self.shimmer_position = value
        self.update()
    
    shimmer_property = property(get_shimmer_position, set_shimmer_position)


class ModernSpinner(QWidget):
    """Smooth circular spinner with theme awareness"""
    
    def __init__(self, parent=None, size: int = 40, thickness: int = 4):
        super().__init__(parent)
        self.spinner_size = size
        self.thickness = thickness
        self.rotation_angle = 0
        
        self.setFixedSize(size, size)
        
        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self.update_rotation)
        self.rotation_timer.start(16)  # ~60 FPS
    
    def update_rotation(self):
        """Update spinner rotation"""
        self.rotation_angle = (self.rotation_angle + 6) % 360
        self.update()
    
    def paintEvent(self, event):
        """Draw spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center the drawing
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation_angle)
        
        # Create gradient for spinner
        gradient = QLinearGradient(-self.spinner_size/2, 0, self.spinner_size/2, 0)
        gradient.setColorAt(0.0, QColor(33, 150, 243, 255))  # Blue
        gradient.setColorAt(1.0, QColor(33, 150, 243, 50))
        
        pen = QPen(QBrush(gradient), self.thickness, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw arc (270 degrees)
        rect = QRectF(
            -self.spinner_size/2 + self.thickness,
            -self.spinner_size/2 + self.thickness,
            self.spinner_size - self.thickness * 2,
            self.spinner_size - self.thickness * 2
        )
        painter.drawArc(rect, 0, 270 * 16)  # Qt uses 1/16th degree units
    
    def start(self):
        """Start spinner animation"""
        self.rotation_timer.start()
    
    def stop(self):
        """Stop spinner animation"""
        self.rotation_timer.stop()


class BreathingDots(QWidget):
    """Three dots that breathe/pulse in sequence"""
    
    def __init__(self, parent=None, dot_size: int = 10):
        super().__init__(parent)
        self.dot_size = dot_size
        self.dot_count = 3
        self.animation_phase = 0.0
        
        self.setFixedSize(dot_size * 3 + 20, dot_size + 10)
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(50)  # ~20 FPS
    
    def update_animation(self):
        """Update breathing animation phase"""
        self.animation_phase = (self.animation_phase + 0.1) % (math.pi * 2)
        self.update()
    
    def paintEvent(self, event):
        """Draw breathing dots"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_y = self.height() / 2
        spacing = self.dot_size + 10
        start_x = (self.width() - (spacing * (self.dot_count - 1))) / 2
        
        for i in range(self.dot_count):
            # Calculate scale based on phase offset
            phase_offset = i * (math.pi * 2 / 3)
            scale = 0.5 + 0.5 * math.sin(self.animation_phase + phase_offset)
            
            # Calculate opacity
            opacity = int(100 + 155 * scale)
            
            # Draw dot
            dot_color = QColor(33, 150, 243, opacity)
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.NoPen)
            
            x = start_x + i * spacing
            radius = self.dot_size / 2 * (0.6 + 0.4 * scale)
            
            painter.drawEllipse(
                QPointF(x, center_y),
                radius, radius
            )
    
    def start(self):
        """Start breathing animation"""
        self.animation_timer.start()
    
    def stop(self):
        """Stop breathing animation"""
        self.animation_timer.stop()


class RippleProgress(QWidget):
    """Ripple/wave progress indicator"""
    
    def __init__(self, parent=None, size: int = 60):
        super().__init__(parent)
        self.indicator_size = size
        self.ripple_phase = 0.0
        
        self.setFixedSize(size, size)
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_ripple)
        self.animation_timer.start(30)  # ~30 FPS
    
    def update_ripple(self):
        """Update ripple animation"""
        self.ripple_phase = (self.ripple_phase + 0.05) % 1.0
        self.update()
    
    def paintEvent(self, event):
        """Draw ripple effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = QPointF(self.width() / 2, self.height() / 2)
        max_radius = self.indicator_size / 2
        
        # Draw 3 expanding ripples
        for i in range(3):
            phase_offset = i / 3.0
            phase = (self.ripple_phase + phase_offset) % 1.0
            
            radius = max_radius * phase
            opacity = int(255 * (1.0 - phase))
            
            color = QColor(33, 150, 243, opacity)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            painter.drawEllipse(center, radius, radius)
    
    def start(self):
        """Start ripple animation"""
        self.animation_timer.start()
    
    def stop(self):
        """Stop ripple animation"""
        self.animation_timer.stop()


class ProgressBar(QWidget):
    """Modern animated progress bar"""
    
    def __init__(self, parent=None, height: int = 6):
        super().__init__(parent)
        self.bar_height = height
        self.progress_value = 0.0
        self.indeterminate = False
        self.animation_position = 0.0
        
        self.setFixedHeight(height)
        
        # Animation for indeterminate mode
        self.indeterminate_animation = QPropertyAnimation(self, b"animation_position_property")
        self.indeterminate_animation.setDuration(1500)
        self.indeterminate_animation.setStartValue(0.0)
        self.indeterminate_animation.setEndValue(1.0)
        self.indeterminate_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.indeterminate_animation.setLoopCount(-1)
        
        # Animation for progress changes
        self.progress_animation = QPropertyAnimation(self, b"progress_property")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def set_progress(self, value: float):
        """Set progress (0.0 to 1.0) with animation"""
        self.indeterminate = False
        self.indeterminate_animation.stop()
        
        self.progress_animation.stop()
        self.progress_animation.setStartValue(self.progress_value)
        self.progress_animation.setEndValue(max(0.0, min(1.0, value)))
        self.progress_animation.start()
    
    def set_indeterminate(self, enabled: bool = True):
        """Enable/disable indeterminate mode"""
        self.indeterminate = enabled
        
        if enabled:
            self.indeterminate_animation.start()
        else:
            self.indeterminate_animation.stop()
    
    def paintEvent(self, event):
        """Draw progress bar"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        bg_color = QColor(200, 200, 200, 50)
        painter.fillRect(self.rect(), bg_color)
        
        if self.indeterminate:
            # Draw indeterminate animation
            bar_width = self.width() * 0.3
            bar_x = (self.width() - bar_width) * self.animation_position
            
            gradient = QLinearGradient(bar_x, 0, bar_x + bar_width, 0)
            gradient.setColorAt(0.0, QColor(33, 150, 243, 100))
            gradient.setColorAt(0.5, QColor(33, 150, 243, 255))
            gradient.setColorAt(1.0, QColor(33, 150, 243, 100))
            
            painter.fillRect(int(bar_x), 0, int(bar_width), self.height(), gradient)
        else:
            # Draw progress
            bar_width = self.width() * self.progress_value
            
            gradient = QLinearGradient(0, 0, bar_width, 0)
            gradient.setColorAt(0.0, QColor(33, 150, 243))
            gradient.setColorAt(1.0, QColor(100, 181, 246))
            
            painter.fillRect(0, 0, int(bar_width), self.height(), gradient)
    
    def get_progress(self):
        return self.progress_value
    
    def set_progress_value(self, value):
        self.progress_value = value
        self.update()
    
    def get_animation_position(self):
        return self.animation_position
    
    def set_animation_position(self, value):
        self.animation_position = value
        self.update()
    
    progress_property = property(get_progress, set_progress_value)
    animation_position_property = property(get_animation_position, set_animation_position)


class SkeletonCardLayout(QWidget):
    """Pre-built skeleton layout for card loading"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header = ShimmerSkeleton(height=30, rounded=True)
        layout.addWidget(header)
        
        # Content rows
        for _ in range(3):
            row = ShimmerSkeleton(height=20, rounded=True)
            layout.addWidget(row)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(ShimmerSkeleton(height=15, rounded=True))
        footer_layout.addStretch()
        footer_layout.addWidget(ShimmerSkeleton(height=15, rounded=True))
        
        layout.addLayout(footer_layout)
