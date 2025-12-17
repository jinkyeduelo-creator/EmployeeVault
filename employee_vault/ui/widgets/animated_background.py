"""
Animated Gradient Background Widget
Creates a smooth, animated gradient background that uses theme colors.
Performance-conscious with configurable FPS and enable/disable toggle.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, Property, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QLinearGradient, QRadialGradient, QColor, QPainterPath


class AnimatedGradientBackground(QWidget):
    """
    A widget that paints an animated gradient background.
    Uses theme colors and animates smoothly with configurable performance settings.
    """
    
    # Animation modes
    MODE_LINEAR = "linear"      # Simple rotating linear gradient
    MODE_RADIAL = "radial"      # Pulsing radial gradient
    MODE_WAVE = "wave"          # Wave-like motion
    MODE_AURORA = "aurora"      # Aurora borealis effect
    
    def __init__(self, parent=None, theme_colors=None, mode=MODE_WAVE, fps=30):
        super().__init__(parent)
        
        # Make widget transparent to mouse events so content can receive them
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Theme colors (will be updated when theme changes)
        self._theme_colors = theme_colors or {
            "primary": "#2196F3",
            "primary_dark": "#1976D2",
            "secondary": "#FF9800",
            "background": "#1a1a1a",
            "accent": "#4CAF50",
        }
        
        # Parse colors
        self._update_gradient_colors()
        
        # Animation state
        self._t = 0.0  # Animation progress [0, 1]
        self._angle = 0.0  # Rotation angle in degrees
        self._enabled = True
        self._mode = mode
        self._fps = fps
        self._intensity = 0.15  # How much the gradient moves (0-1)
        
        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        
        # Variant animation for smooth interpolation
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(8000)  # 8 seconds for full cycle
        self._anim.setLoopCount(-1)  # Infinite loop
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._anim.valueChanged.connect(self._on_value_changed)
        
    def _update_gradient_colors(self):
        """Parse theme colors into QColor objects"""
        self._color1 = QColor(self._theme_colors.get("primary", "#2196F3"))
        self._color2 = QColor(self._theme_colors.get("secondary", "#FF9800"))
        self._color3 = QColor(self._theme_colors.get("accent", "#4CAF50"))
        self._bg_color = QColor(self._theme_colors.get("background", "#1a1a1a"))
        
        # Create semi-transparent versions for subtlety
        self._color1.setAlphaF(0.3)
        self._color2.setAlphaF(0.2)
        self._color3.setAlphaF(0.15)
        
    def set_theme_colors(self, theme_colors: dict):
        """Update gradient colors when theme changes"""
        self._theme_colors = theme_colors
        self._update_gradient_colors()
        self.update()
        
    def set_enabled(self, enabled: bool):
        """Enable or disable the animation"""
        self._enabled = enabled
        if enabled:
            self.start()
        else:
            self.stop()
        self.update()
        
    def is_enabled(self) -> bool:
        return self._enabled
        
    def set_fps(self, fps: int):
        """Set animation frame rate (affects performance)"""
        self._fps = max(1, min(60, fps))  # Clamp between 1-60
        if self._timer.isActive():
            self._timer.setInterval(1000 // self._fps)
            
    def set_mode(self, mode: str):
        """Set animation mode"""
        self._mode = mode
        self.update()
        
    def set_intensity(self, intensity: float):
        """Set animation intensity (0.0 - 1.0)"""
        self._intensity = max(0.0, min(1.0, intensity))
        
    def start(self):
        """Start the background animation"""
        if not self._enabled:
            return
        self._anim.start()
        self._timer.start(1000 // self._fps)
        
    def stop(self):
        """Stop the background animation"""
        self._anim.stop()
        self._timer.stop()
        
    def _on_tick(self):
        """Timer tick - update angle for rotation effects"""
        self._angle = (self._angle + 0.5) % 360
        self.update()
        
    def _on_value_changed(self, value):
        """Animation value changed"""
        self._t = float(value)
        
    def paintEvent(self, event):
        """Paint the animated gradient background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        rect = self.rect()
        
        if not self._enabled:
            # Just fill with solid background color
            painter.fillRect(rect, self._bg_color)
            return
            
        # Fill base background first
        painter.fillRect(rect, self._bg_color)
        
        # Draw animated gradient based on mode
        if self._mode == self.MODE_LINEAR:
            self._paint_linear(painter, rect)
        elif self._mode == self.MODE_RADIAL:
            self._paint_radial(painter, rect)
        elif self._mode == self.MODE_WAVE:
            self._paint_wave(painter, rect)
        elif self._mode == self.MODE_AURORA:
            self._paint_aurora(painter, rect)
        else:
            self._paint_wave(painter, rect)  # Default to wave
            
    def _paint_linear(self, painter, rect):
        """Simple rotating linear gradient"""
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        # Calculate gradient endpoints based on angle
        rad = math.radians(self._angle)
        dx = math.cos(rad) * rect.width() * 0.7
        dy = math.sin(rad) * rect.height() * 0.7
        
        p1 = QPointF(center_x - dx, center_y - dy)
        p2 = QPointF(center_x + dx, center_y + dy)
        
        gradient = QLinearGradient(p1, p2)
        gradient.setColorAt(0.0, self._color1)
        gradient.setColorAt(0.5, self._color2)
        gradient.setColorAt(1.0, self._color1)
        
        painter.fillRect(rect, gradient)
        
    def _paint_radial(self, painter, rect):
        """Pulsing radial gradient"""
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        # Pulsing radius based on animation
        pulse = 0.8 + 0.2 * math.sin(self._t * math.pi * 2)
        radius = max(rect.width(), rect.height()) * pulse
        
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0.0, self._color1)
        gradient.setColorAt(0.5, self._color2)
        gradient.setColorAt(1.0, self._bg_color)
        
        painter.fillRect(rect, gradient)
        
    def _paint_wave(self, painter, rect):
        """Wave-like flowing gradient - most visually appealing"""
        w = rect.width()
        h = rect.height()
        
        # Create multiple overlapping gradients for wave effect
        for i in range(3):
            # Each wave has different phase and position
            phase = self._t + (i * 0.33)
            phase = phase % 1.0
            
            # Calculate wave position
            x_offset = w * self._intensity * math.sin(phase * math.pi * 2 + i)
            y_offset = h * self._intensity * math.cos(phase * math.pi * 2 + i * 0.7)
            
            # Gradient from offset position
            x1 = w * 0.3 + x_offset
            y1 = h * 0.2 + y_offset
            x2 = w * 0.7 - x_offset
            y2 = h * 0.8 - y_offset
            
            gradient = QLinearGradient(x1, y1, x2, y2)
            
            # Use different colors for each wave layer
            if i == 0:
                c = QColor(self._color1)
                c.setAlphaF(0.15)
            elif i == 1:
                c = QColor(self._color2)
                c.setAlphaF(0.1)
            else:
                c = QColor(self._color3)
                c.setAlphaF(0.08)
                
            transparent = QColor(0, 0, 0, 0)
            
            gradient.setColorAt(0.0, transparent)
            gradient.setColorAt(0.3, c)
            gradient.setColorAt(0.7, c)
            gradient.setColorAt(1.0, transparent)
            
            painter.fillRect(rect, gradient)
            
    def _paint_aurora(self, painter, rect):
        """Aurora borealis effect with flowing curtains"""
        w = rect.width()
        h = rect.height()
        
        # Create multiple "curtains" of light
        for i in range(4):
            phase = self._t + (i * 0.25)
            phase = phase % 1.0
            
            # Vertical curtain that sways
            sway = math.sin(phase * math.pi * 2) * w * 0.1
            curtain_x = w * (0.2 + i * 0.2) + sway
            
            # Create path for aurora curtain
            path = QPainterPath()
            path.moveTo(curtain_x - 50, 0)
            
            # Wavy top edge
            for x in range(int(curtain_x - 50), int(curtain_x + 50), 10):
                wave_y = 20 * math.sin((x + phase * 100) * 0.05)
                path.lineTo(x, wave_y)
                
            path.lineTo(curtain_x + 50, 0)
            path.lineTo(curtain_x + 30, h)
            path.lineTo(curtain_x - 30, h)
            path.closeSubpath()
            
            # Gradient for this curtain
            gradient = QLinearGradient(curtain_x, 0, curtain_x, h)
            
            if i % 2 == 0:
                c = QColor(self._color1)
            else:
                c = QColor(self._color3)
            c.setAlphaF(0.1)
            
            gradient.setColorAt(0.0, c)
            gradient.setColorAt(0.5, QColor(0, 0, 0, 0))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
            
            painter.fillPath(path, gradient)


class AnimatedBackgroundContainer(QWidget):
    """
    A container widget that has an animated background but allows
    child widgets to be placed on top of it.
    """
    
    def __init__(self, parent=None, theme_colors=None, mode="wave", enabled=True):
        super().__init__(parent)
        
        # Create the background widget
        self._background = AnimatedGradientBackground(
            self, 
            theme_colors=theme_colors,
            mode=mode
        )
        
        # Start if enabled
        if enabled:
            self._background.start()
        else:
            self._background.set_enabled(False)
            
    def resizeEvent(self, event):
        """Keep background sized to container"""
        self._background.setGeometry(self.rect())
        super().resizeEvent(event)
        
    def set_enabled(self, enabled: bool):
        """Enable/disable the background animation"""
        self._background.set_enabled(enabled)
        
    def set_theme_colors(self, theme_colors: dict):
        """Update theme colors"""
        self._background.set_theme_colors(theme_colors)
        
    def set_mode(self, mode: str):
        """Set animation mode"""
        self._background.set_mode(mode)
        
    def start(self):
        """Start animation"""
        self._background.start()
        
    def stop(self):
        """Stop animation"""
        self._background.stop()
