"""
Modern Animated Button Widget with Ripple Effect and Hover Animations
CSS-like animations for PySide6
"""

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect,
    QTimer, Property, QSequentialAnimationGroup, QParallelAnimationGroup,
    QVariantAnimation, QAbstractAnimation
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect, QGraphicsOpacityEffect


# Global flag to control shadow effects (disable for performance optimization)
ENABLE_BUTTON_SHADOWS = False  # Set to False to improve performance on older systems


class AnimatedButton(QPushButton):
    """
    Modern button with smooth animations:
    - Ripple effect on click (Material Design)
    - Elevation/shadow changes on hover (optional, controlled by ENABLE_BUTTON_SHADOWS)
    - Smooth scale animation on hover
    - Color transition effects
    """

    def __init__(self, text="", icon_text="", parent=None, enable_shadow=None):
        super().__init__(text, parent)
        self._elevation = 5
        self._scale = 1.0
        self._ripples = []  # Now stores dict with 'anim' key for QVariantAnimation
        self.shadow = None

        # Shadow is now optional for performance
        # Use the instance override if provided, otherwise use global setting
        use_shadow = enable_shadow if enable_shadow is not None else ENABLE_BUTTON_SHADOWS
        
        if use_shadow:
            # Setup shadow effect for elevation (only if enabled)
            self.shadow = QGraphicsDropShadowEffect()
            self.shadow.setBlurRadius(15)
            self.shadow.setOffset(0, self._elevation)
            self.shadow.setColor(QColor(0, 0, 0, 80))
            self.setGraphicsEffect(self.shadow)

        # Animations
        self.elevation_anim = QPropertyAnimation(self, b"elevation")
        self.elevation_anim.setDuration(200)
        self.elevation_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Cursor removed per user request - was distracting
        # self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(50)

    def get_elevation(self):
        return self._elevation

    def set_elevation(self, value):
        self._elevation = value
        if self.shadow:
            self.shadow.setOffset(0, value)
            self.shadow.setBlurRadius(value * 3)
        self.update()

    elevation = Property(int, get_elevation, set_elevation)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = Property(float, get_scale, set_scale)

    def enterEvent(self, event):
        """Hover enter - increase elevation and scale"""
        # Animate elevation
        self.elevation_anim.stop()
        self.elevation_anim.setStartValue(self._elevation)
        self.elevation_anim.setEndValue(8)
        self.elevation_anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hover leave - restore elevation and scale"""
        # Animate elevation back
        self.elevation_anim.stop()
        self.elevation_anim.setStartValue(self._elevation)
        self.elevation_anim.setEndValue(5)
        self.elevation_anim.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Mouse press - create ripple effect using QVariantAnimation"""
        if event.button() == Qt.LeftButton:
            # Add ripple at click position with QVariantAnimation
            ripple_pos = event.pos()
            max_radius = max(self.width(), self.height()) * 1.5
            
            ripple = {
                'pos': ripple_pos,
                'radius': 0,
                'opacity': 1.0,
                'max_radius': max_radius,
                'anim': None
            }
            
            # Create QVariantAnimation for this ripple
            anim = QVariantAnimation(self)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setDuration(400)  # 400ms ripple animation
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            # Store reference to ripple for the animation callback
            def update_ripple(value):
                ripple['radius'] = max_radius * value
                ripple['opacity'] = 1.0 - value
                self.update()
            
            def cleanup_ripple():
                if ripple in self._ripples:
                    self._ripples.remove(ripple)
                self.update()
            
            anim.valueChanged.connect(update_ripple)
            anim.finished.connect(cleanup_ripple)
            
            ripple['anim'] = anim
            self._ripples.append(ripple)
            
            # Start animation (auto-cleanup when finished)
            anim.start(QAbstractAnimation.DeleteWhenStopped)

            # Press animation - decrease elevation
            self.elevation_anim.stop()
            self.elevation_anim.setStartValue(self._elevation)
            self.elevation_anim.setEndValue(2)
            self.elevation_anim.setDuration(100)
            self.elevation_anim.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Mouse release - restore elevation"""
        if event.button() == Qt.LeftButton:
            # Release animation - restore elevation
            self.elevation_anim.stop()
            self.elevation_anim.setStartValue(self._elevation)
            self.elevation_anim.setEndValue(8 if self.underMouse() else 5)
            self.elevation_anim.setDuration(200)
            self.elevation_anim.start()

        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Custom paint to draw ripples"""
        # Draw button background first
        super().paintEvent(event)

        # Draw ripples on top
        if self._ripples:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            for ripple in self._ripples:
                color = QColor(255, 255, 255, int(ripple['opacity'] * 100))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(
                    ripple['pos'],
                    int(ripple['radius']),
                    int(ripple['radius'])
                )


class PulseButton(AnimatedButton):
    """Button with continuous pulse animation for important actions"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        # Pulse animation
        self.pulse_anim = QPropertyAnimation(self, b"elevation")
        self.pulse_anim.setDuration(1000)
        self.pulse_anim.setStartValue(5)
        self.pulse_anim.setEndValue(12)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_anim.setLoopCount(-1)  # Infinite loop

    def start_pulse(self):
        """Start pulsing"""
        self.pulse_anim.start()

    def stop_pulse(self):
        """Stop pulsing"""
        self.pulse_anim.stop()
        self.set_elevation(5)


class IconButton(AnimatedButton):
    """Circular button with icon - perfect for FABs (Floating Action Buttons)"""

    def __init__(self, icon_text="", size=56, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QPushButton {{
                border-radius: {size // 2}px;
                font-size: {size // 3}px;
            }}
        """)


class GradientGlowButton(QPushButton):
    """
    Modern button with animated gradient background and glow effect on hover
    Perfect for primary actions with eye-catching animations
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._glow_intensity = 0
        self._gradient_angle = 0

        # Glow animation
        self.glow_anim = QPropertyAnimation(self, b"glow_intensity")
        self.glow_anim.setDuration(300)
        self.glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Gradient rotation animation
        self.gradient_anim = QPropertyAnimation(self, b"gradient_angle")
        self.gradient_anim.setDuration(2000)
        self.gradient_anim.setStartValue(0)
        self.gradient_anim.setEndValue(360)
        self.gradient_anim.setLoopCount(-1)  # Infinite loop

        self.setMinimumHeight(44)
        self.update_style()

    def get_glow_intensity(self):
        return self._glow_intensity

    def set_glow_intensity(self, value):
        self._glow_intensity = value
        self.update_style()

    glow_intensity = Property(int, get_glow_intensity, set_glow_intensity)

    def get_gradient_angle(self):
        return self._gradient_angle

    def set_gradient_angle(self, value):
        self._gradient_angle = value
        self.update()

    gradient_angle = Property(int, get_gradient_angle, set_gradient_angle)

    def update_style(self):
        """Update stylesheet with glow effect"""
        glow_size = int(self._glow_intensity * 0.5)

        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 200),
                    stop:1 rgba(118, 75, 162, 200)
                );
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 22px;
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 10px 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(118, 75, 162, 220),
                    stop:1 rgba(102, 126, 234, 220)
                );
                border: 2px solid rgba(255, 255, 255, 0.4);
            }}
            QPushButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(90, 60, 140, 255),
                    stop:1 rgba(80, 100, 200, 255)
                );
            }}
            QPushButton:disabled {{
                background: rgba(80, 80, 80, 100);
                border: 2px solid rgba(100, 100, 100, 100);
                color: rgba(150, 150, 150, 150);
            }}
        """)

        # Add drop shadow for glow (only if shadows are enabled)
        if ENABLE_BUTTON_SHADOWS and self._glow_intensity > 0:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(glow_size)
            shadow.setColor(QColor(102, 126, 234, self._glow_intensity * 2))
            shadow.setOffset(0, 0)
            self.setGraphicsEffect(shadow)

    def enterEvent(self, event):
        """Animate glow on hover"""
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow_intensity)
        self.glow_anim.setEndValue(60)
        self.glow_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Remove glow on leave"""
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow_intensity)
        self.glow_anim.setEndValue(0)
        self.glow_anim.start()
        super().leaveEvent(event)


class NeumorphicButton(QPushButton):
    """
    Neumorphic (soft UI) button with 3D raised/pressed effects
    Creates depth using dual shadows (light and dark)
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._pressed_state = False
        self._shadow_offset = 6

        # Shadow animation
        self.shadow_anim = QPropertyAnimation(self, b"shadow_offset")
        self.shadow_anim.setDuration(150)
        self.shadow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMinimumHeight(44)
        self.update_style()

    def get_shadow_offset(self):
        return self._shadow_offset

    def set_shadow_offset(self, value):
        self._shadow_offset = value
        self.update()

    shadow_offset = Property(int, get_shadow_offset, set_shadow_offset)

    def update_style(self):
        """Update stylesheet for neumorphic effect"""
        self.setStyleSheet(f"""
            QPushButton {{
                background: #2b2b2b;
                border: none;
                border-radius: 16px;
                color: rgba(255, 255, 255, 0.9);
                font-weight: 600;
                font-size: 14px;
                padding: 12px 28px;
            }}
            QPushButton:hover {{
                background: #323232;
            }}
            QPushButton:disabled {{
                background: #222222;
                color: rgba(150, 150, 150, 0.5);
            }}
        """)

    def paintEvent(self, event):
        """Custom paint for neumorphic shadows"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        if not self._pressed_state:
            # Raised state - draw outer shadows
            # Dark shadow (bottom-right)
            painter.setBrush(QColor(20, 20, 20, 100))
            painter.setPen(Qt.PenStyle.NoPen)
            shadow_rect = rect.adjusted(
                self._shadow_offset, self._shadow_offset,
                self._shadow_offset, self._shadow_offset
            )
            painter.drawRoundedRect(shadow_rect, 16, 16)

            # Light shadow (top-left)
            painter.setBrush(QColor(60, 60, 60, 50))
            light_rect = rect.adjusted(
                -self._shadow_offset, -self._shadow_offset,
                -self._shadow_offset, -self._shadow_offset
            )
            painter.drawRoundedRect(light_rect, 16, 16)
        else:
            # Pressed state - draw inner shadows
            painter.setBrush(QColor(15, 15, 15, 150))
            painter.setPen(Qt.PenStyle.NoPen)
            inner_rect = rect.adjusted(2, 2, -2, -2)
            painter.drawRoundedRect(inner_rect, 14, 14)

        # Call parent to draw text
        super().paintEvent(event)

    def mousePressEvent(self, event):
        """Animate to pressed state"""
        self._pressed_state = True
        self.shadow_anim.stop()
        self.shadow_anim.setStartValue(self._shadow_offset)
        self.shadow_anim.setEndValue(2)
        self.shadow_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Animate back to raised state"""
        self._pressed_state = False
        self.shadow_anim.stop()
        self.shadow_anim.setStartValue(self._shadow_offset)
        self.shadow_anim.setEndValue(6)
        self.shadow_anim.start()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """Increase shadow on hover"""
        if not self._pressed_state:
            self.shadow_anim.stop()
            self.shadow_anim.setStartValue(self._shadow_offset)
            self.shadow_anim.setEndValue(8)
            self.shadow_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Restore shadow on leave"""
        if not self._pressed_state:
            self.shadow_anim.stop()
            self.shadow_anim.setStartValue(self._shadow_offset)
            self.shadow_anim.setEndValue(6)
            self.shadow_anim.start()
        super().leaveEvent(event)
