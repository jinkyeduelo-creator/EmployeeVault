"""
Advanced UI Effects for EmployeeVault
Micro-interactions, ripples, glows, and visual feedback
"""

import math
from PySide6.QtCore import (
    Qt, QPoint, QPointF, QTimer, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QRectF, Signal, QObject, Property
)
from PySide6.QtWidgets import (
    QPushButton, QLineEdit, QCheckBox, QWidget, QGraphicsOpacityEffect,
    QLabel
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, QPainterPath,
    QLinearGradient, QPaintEvent, QMouseEvent
)


class RippleEffect(QWidget):
    """Material Design ripple effect overlay"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.ripples = []
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_ripples)
        self.animation_timer.start(16)  # ~60 FPS
    
    def add_ripple(self, position: QPoint, color: QColor = None):
        """Add new ripple at position"""
        if color is None:
            color = QColor(255, 255, 255, 100)
        
        ripple = {
            'pos': position,
            'radius': 0,
            'max_radius': max(self.width(), self.height()) * 1.5,
            'opacity': 1.0,
            'color': color
        }
        self.ripples.append(ripple)
    
    def update_ripples(self):
        """Update ripple animations"""
        updated_ripples = []
        
        for ripple in self.ripples:
            ripple['radius'] += ripple['max_radius'] / 20  # Expand speed
            ripple['opacity'] -= 0.05  # Fade speed
            
            if ripple['opacity'] > 0:
                updated_ripples.append(ripple)
        
        self.ripples = updated_ripples
        self.update()
    
    def paintEvent(self, event):
        """Draw ripples"""
        if not self.ripples:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for ripple in self.ripples:
            color = QColor(ripple['color'])
            color.setAlphaF(ripple['opacity'])
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                ripple['pos'],
                int(ripple['radius']),
                int(ripple['radius'])
            )


class RippleButton(QPushButton):
    """Button with Material Design ripple effect"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.ripple_overlay = RippleEffect(self)
        self.ripple_overlay.setGeometry(self.rect())
        self.ripple_overlay.raise_()
    
    def resizeEvent(self, event):
        """Update ripple overlay size"""
        super().resizeEvent(event)
        self.ripple_overlay.setGeometry(self.rect())
    
    def mousePressEvent(self, event: QMouseEvent):
        """Add ripple on click"""
        super().mousePressEvent(event)
        self.ripple_overlay.add_ripple(event.pos())


class GlowPulseLineEdit(QLineEdit):
    """Line edit with glowing pulse effect when focused"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.glow_opacity = 0.0
        self.glow_animation = QPropertyAnimation(self, b"glow_opacity_property")
        self.glow_animation.setDuration(1000)
        self.glow_animation.setStartValue(0.3)
        self.glow_animation.setEndValue(0.8)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.glow_animation.setLoopCount(-1)  # Infinite
    
    def focusInEvent(self, event):
        """Start glow pulse when focused"""
        super().focusInEvent(event)
        self.glow_animation.start()
    
    def focusOutEvent(self, event):
        """Stop glow pulse when focus lost"""
        super().focusOutEvent(event)
        self.glow_animation.stop()
        self.glow_opacity = 0.0
        self.update()
    
    def paintEvent(self, event):
        """Draw line edit with glow"""
        super().paintEvent(event)
        
        if self.hasFocus() and self.glow_opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw glow effect
            glow_color = QColor(33, 150, 243)  # Blue
            glow_color.setAlphaF(self.glow_opacity)
            
            pen = QPen(glow_color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            rect = self.rect().adjusted(1, 1, -1, -1)
            painter.drawRoundedRect(rect, 4, 4)
    
    def get_glow_opacity(self):
        return self.glow_opacity
    
    def set_glow_opacity(self, value):
        self.glow_opacity = value
        self.update()
    
    glow_opacity_property = property(get_glow_opacity, set_glow_opacity)


class BounceCheckBox(QCheckBox):
    """Checkbox with bounce animation when toggled"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.scale_factor = 1.0
        self.bounce_animation = None
    
    def nextCheckState(self):
        """Override to add bounce effect"""
        super().nextCheckState()
        self.play_bounce()
    
    def play_bounce(self):
        """Play bounce animation"""
        if self.bounce_animation and self.bounce_animation.state() == QPropertyAnimation.Running:
            return
        
        # Create bounce sequence
        self.bounce_animation = QPropertyAnimation(self, b"scale_property")
        self.bounce_animation.setDuration(400)
        self.bounce_animation.setStartValue(1.0)
        self.bounce_animation.setKeyValueAt(0.3, 1.3)
        self.bounce_animation.setKeyValueAt(0.6, 0.9)
        self.bounce_animation.setEndValue(1.0)
        self.bounce_animation.setEasingCurve(QEasingCurve.OutElastic)
        self.bounce_animation.start()
    
    def get_scale(self):
        return self.scale_factor
    
    def set_scale(self, value):
        self.scale_factor = value
        self.update()
    
    scale_property = property(get_scale, set_scale)


class HoverScaleWidget(QWidget):
    """Widget that scales up slightly on hover"""
    
    def __init__(self, parent=None, scale_amount: float = 1.05):
        super().__init__(parent)
        self.scale_amount = scale_amount
        self.current_scale = 1.0
        
        self.scale_animation = QPropertyAnimation(self, b"scale_property")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        """Scale up on hover"""
        super().enterEvent(event)
        self.scale_animation.stop()
        self.scale_animation.setStartValue(self.current_scale)
        self.scale_animation.setEndValue(self.scale_amount)
        self.scale_animation.start()
    
    def leaveEvent(self, event):
        """Scale down when hover ends"""
        super().leaveEvent(event)
        self.scale_animation.stop()
        self.scale_animation.setStartValue(self.current_scale)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()
    
    def get_scale(self):
        return self.current_scale
    
    def set_scale(self, value):
        self.current_scale = value
        self.update()
    
    scale_property = property(get_scale, set_scale)


class ElevatedCard(QWidget):
    """Card widget with elevation shadow that increases on hover"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.elevation = 2  # Shadow depth
        self.shadow_opacity = 0.2
        
        self.elevation_animation = QPropertyAnimation(self, b"elevation_property")
        self.elevation_animation.setDuration(250)
        self.elevation_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        """Increase elevation on hover"""
        super().enterEvent(event)
        self.elevation_animation.stop()
        self.elevation_animation.setStartValue(self.elevation)
        self.elevation_animation.setEndValue(8)
        self.elevation_animation.start()
    
    def leaveEvent(self, event):
        """Decrease elevation when hover ends"""
        super().leaveEvent(event)
        self.elevation_animation.stop()
        self.elevation_animation.setStartValue(self.elevation)
        self.elevation_animation.setEndValue(2)
        self.elevation_animation.start()
    
    def paintEvent(self, event):
        """Draw card with shadow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow
        shadow_color = QColor(0, 0, 0, int(self.shadow_opacity * self.elevation * 10))
        shadow_offset = self.elevation // 2
        
        shadow_rect = self.rect().adjusted(
            shadow_offset, shadow_offset, 
            -shadow_offset, -shadow_offset
        )
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(shadow_rect, 8, 8)
        
        # Draw card
        card_color = self.palette().window().color()
        painter.setBrush(QBrush(card_color))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -self.elevation, -self.elevation), 8, 8)
    
    def get_elevation(self):
        return self.elevation
    
    def set_elevation(self, value):
        self.elevation = value
        self.update()
    
    elevation_property = property(get_elevation, set_elevation)


class ShineEffect(QWidget):
    """Animated shine/glare effect that sweeps across widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.shine_position = -1.0  # -1 to 2 (off-screen to off-screen)
        self.shine_animation = None
        
    def start_shine(self):
        """Start shine animation"""
        if self.shine_animation and self.shine_animation.state() == QPropertyAnimation.Running:
            return
        
        self.shine_animation = QPropertyAnimation(self, b"shine_property")
        self.shine_animation.setDuration(800)
        self.shine_animation.setStartValue(-1.0)
        self.shine_animation.setEndValue(2.0)
        self.shine_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.shine_animation.start()
    
    def paintEvent(self, event):
        """Draw shine effect"""
        if self.shine_position < -0.5 or self.shine_position > 1.5:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient for shine
        gradient = QLinearGradient(
            self.width() * self.shine_position - 50,
            0,
            self.width() * self.shine_position + 50,
            0
        )
        
        gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 100))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        
        painter.fillRect(self.rect(), gradient)
    
    def get_shine_position(self):
        return self.shine_position
    
    def set_shine_position(self, value):
        self.shine_position = value
        self.update()
    
    shine_property = property(get_shine_position, set_shine_position)


class CountUpLabel(QLabel):
    """Label that animates numbers counting up"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.target_value = 0
        self._current_value = 0.0
        
        self.count_animation = QPropertyAnimation(self, b"currentValue")
        self.count_animation.setDuration(1000)
        self.count_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def set_target_value(self, value: int, animate: bool = True):
        """Set target value and optionally animate to it"""
        self.target_value = value
        
        if animate:
            self.count_animation.stop()
            self.count_animation.setStartValue(self._current_value)
            self.count_animation.setEndValue(float(value))
            self.count_animation.start()
        else:
            self.setCurrentValue(float(value))
    
    def getCurrentValue(self):
        return self._current_value
    
    def setCurrentValue(self, value):
        self._current_value = value
        self.setText(str(int(self._current_value)))
    
    # Qt property for animation
    currentValue = Property(float, getCurrentValue, setCurrentValue)


class PulseWidget(QWidget):
    """Widget that pulses its opacity"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.pulse_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0.5)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_animation.setLoopCount(-1)  # Infinite
    
    def start_pulse(self):
        """Start pulsing"""
        self.pulse_animation.start()
    
    def stop_pulse(self):
        """Stop pulsing"""
        self.pulse_animation.stop()
        self.opacity_effect.setOpacity(1.0)
