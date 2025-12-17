"""
Glassmorphism Widgets - Modern Frosted Glass Effect
Creates beautiful semi-transparent panels with blur effect
"""

from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPainterPath, QRegion
)
from PySide6.QtWidgets import (
    QWidget, QFrame, QGraphicsBlurEffect, QGraphicsOpacityEffect,
    QVBoxLayout, QLabel, QPushButton
)


class GlassPanel(QFrame):
    """
    Semi-transparent panel with frosted glass effect
    Perfect for overlays, modals, and floating panels
    """

    def __init__(self, parent=None, blur_radius=10, opacity=0.7):
        super().__init__(parent)
        self._border_color = QColor(255, 255, 255, 80)
        self._bg_opacity = opacity

        # Note: Qt's blur effect is limited. For true glassmorphism,
        # we use semi-transparent backgrounds with subtle gradients
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, {int(opacity * 20)});
                border: 1px solid rgba(255, 255, 255, {int(opacity * 40)});
                border-radius: 16px;
            }}
        """)

        # Subtle shadow for depth
        self.setGraphicsEffect(self._create_shadow())

    def _create_shadow(self):
        """Create subtle shadow effect"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        return shadow

    def paintEvent(self, event):
        """Custom paint for glass effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create glass background with gradient
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 16, 16)

        # Gradient for depth
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor(255, 255, 255, int(self._bg_opacity * 40)))
        gradient.setColorAt(1, QColor(255, 255, 255, int(self._bg_opacity * 20)))

        painter.fillPath(path, gradient)

        # Border with shine effect
        painter.setPen(QPen(self._border_color, 1))
        painter.drawPath(path)

        # Top highlight for glass effect
        highlight_gradient = QLinearGradient(0, 0, 0, rect.height() * 0.3)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 60))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))

        highlight_path = QPainterPath()
        highlight_path.addRoundedRect(
            rect.x() + 2, rect.y() + 2,
            rect.width() - 4, rect.height() * 0.3,
            14, 14
        )
        painter.fillPath(highlight_path, highlight_gradient)


class GlassPanelDark(QFrame):
    """
    Dark variant of glass panel
    Perfect for dark themes
    """

    def __init__(self, parent=None, blur_radius=10, opacity=0.7):
        super().__init__(parent)
        self._border_color = QColor(255, 255, 255, 40)
        self._bg_opacity = opacity

        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(30, 30, 30, {int(opacity * 80)});
                border: 1px solid rgba(255, 255, 255, {int(opacity * 20)});
                border-radius: 16px;
            }}
        """)

        # Shadow
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        """Custom paint for dark glass effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 16, 16)

        # Dark gradient
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor(40, 40, 40, int(self._bg_opacity * 200)))
        gradient.setColorAt(1, QColor(20, 20, 20, int(self._bg_opacity * 220)))

        painter.fillPath(path, gradient)

        # Border
        painter.setPen(QPen(self._border_color, 1))
        painter.drawPath(path)


class AnimatedGlassPanel(GlassPanelDark):
    """
    Glass panel that animates in/out with scale and fade
    Perfect for dialogs and popups
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale_factor = 0.8
        self._panel_opacity = 0

        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)
        # Note: Can't use both shadow and opacity effects simultaneously
        # So we'll toggle between them

        # Animations
        self.scale_anim = QPropertyAnimation(self, b"scale_factor")
        self.scale_anim.setDuration(300)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBack)

        self.opacity_anim = QPropertyAnimation(self, b"panel_opacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_scale_factor(self):
        return self._scale_factor

    def set_scale_factor(self, value):
        self._scale_factor = value
        self.update()

    scale_factor = Property(float, get_scale_factor, set_scale_factor)

    def get_panel_opacity(self):
        return self._panel_opacity

    def set_panel_opacity(self, value):
        self._panel_opacity = value
        if hasattr(self, 'opacity_effect'):
            self.opacity_effect.setOpacity(value)

    panel_opacity = Property(float, get_panel_opacity, set_panel_opacity)

    def show_animated(self):
        """Show with animation"""
        self.show()

        # Use opacity effect for animation
        self.setGraphicsEffect(self.opacity_effect)

        # Scale animation
        self.scale_anim.setStartValue(0.8)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.start()

        # Opacity animation
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()

    def hide_animated(self, callback=None):
        """Hide with animation"""
        # Scale animation
        self.scale_anim.setStartValue(1.0)
        self.scale_anim.setEndValue(0.8)
        self.scale_anim.start()

        # Opacity animation
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        if callback:
            self.opacity_anim.finished.connect(callback)
        else:
            self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()


class GlassCard(GlassPanelDark):
    """
    Glass card with content
    Pre-styled for common use cases
    """

    def __init__(self, title="", content="", parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        if title:
            title_label = QLabel(f"<b>{title}</b>")
            title_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    background: transparent;
                    border: none;
                }
            """)
            layout.addWidget(title_label)

        if content:
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 200);
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }
            """)
            layout.addWidget(content_label)

        layout.addStretch()


class NeumorphicButton(QPushButton):
    """
    Neumorphic (soft UI) button
    Subtle shadows create extruded effect
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self._is_pressed = False

        self.setMinimumHeight(50)
        self.setStyleSheet("""
            QPushButton {
                background: #2d2d2d;
                border: none;
                border-radius: 22px;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #333333;
            }
        """)

        # Dual shadow effect for neumorphism
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        self.shadow_light = QGraphicsDropShadowEffect()
        self.shadow_light.setBlurRadius(10)
        self.shadow_light.setOffset(-4, -4)
        self.shadow_light.setColor(QColor(60, 60, 60, 180))

        self.shadow_dark = QGraphicsDropShadowEffect()
        self.shadow_dark.setBlurRadius(10)
        self.shadow_dark.setOffset(4, 4)
        self.shadow_dark.setColor(QColor(0, 0, 0, 200))

        # Apply normal shadow by default
        self.setGraphicsEffect(self.shadow_dark)

    def mousePressEvent(self, event):
        """Invert shadows on press"""
        self._is_pressed = True
        # When pressed, invert shadow to create "pressed in" effect
        self.setGraphicsEffect(self.shadow_light)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Restore shadows on release"""
        self._is_pressed = False
        self.setGraphicsEffect(self.shadow_dark)
        super().mouseReleaseEvent(event)


class GlassToast(AnimatedGlassPanel):
    """
    Toast notification with glass effect
    Auto-dismissing with animation
    """

    def __init__(self, message, toast_type="info", parent=None, duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make mouse-transparent so users aren't distracted

        # Icons for different types
        icons = {
            "info": "ℹ️",
            "success": "✓",
            "warning": "⚠️",
            "error": "✗"
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        message_label = QLabel(f"{icons.get(toast_type, 'ℹ️')}  {message}")
        message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: 600;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(message_label)

        self.adjustSize()
        self.setMinimumWidth(250)

        # Show with animation
        self.show_animated()

        # Auto-dismiss
        from PySide6.QtCore import QTimer
        QTimer.singleShot(duration, lambda: self.hide_animated(callback=self.deleteLater))


class GlassmorphicButton(QPushButton):
    """
    Modern glassmorphic button with frosted glass effect
    CSS-like appearance with smooth animations and glass transparency
    v4.5.0: New button style for modern UI
    """

    def __init__(self, text="", icon=None, variant="primary", parent=None):
        super().__init__(text, parent)

        self.variant = variant
        self._hover_opacity = 0.0
        self._press_scale = 1.0
        self._ripple_radius = 0
        self._ripple_center = None

        # Minimum size for better touch targets
        self.setMinimumHeight(50)
        self.setMinimumWidth(100)

        # Color schemes for different variants
        self.variants = {
            "primary": {
                "base": "rgba(59, 130, 246, 0.6)",      # Blue with transparency
                "hover": "rgba(59, 130, 246, 0.8)",
                "border": "rgba(147, 197, 253, 0.5)",
                "text": "white"
            },
            "success": {
                "base": "rgba(34, 197, 94, 0.6)",       # Green
                "hover": "rgba(34, 197, 94, 0.8)",
                "border": "rgba(134, 239, 172, 0.5)",
                "text": "white"
            },
            "warning": {
                "base": "rgba(251, 146, 60, 0.6)",      # Orange
                "hover": "rgba(251, 146, 60, 0.8)",
                "border": "rgba(253, 186, 116, 0.5)",
                "text": "white"
            },
            "danger": {
                "base": "rgba(239, 68, 68, 0.6)",       # Red
                "hover": "rgba(239, 68, 68, 0.8)",
                "border": "rgba(252, 165, 165, 0.5)",
                "text": "white"
            },
            "glass": {
                "base": "rgba(255, 255, 255, 0.1)",     # Pure glass
                "hover": "rgba(255, 255, 255, 0.2)",
                "border": "rgba(255, 255, 255, 0.3)",
                "text": "white"
            },
            "dark": {
                "base": "rgba(30, 30, 30, 0.7)",        # Dark glass
                "hover": "rgba(40, 40, 40, 0.85)",
                "border": "rgba(100, 100, 100, 0.4)",
                "text": "white"
            }
        }

        self._update_style()

        # Glass shadow effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Get current theme's animation profile
        try:
            from employee_vault.ui.theme_manager import get_theme_manager
            from employee_vault.ui.theme_animations import get_animation_profile, get_easing_curve_enum

            theme_mgr = get_theme_manager()
            theme_name = theme_mgr.current_color_theme
            anim_profile = get_animation_profile(theme_name)

            hover_duration = anim_profile.get("button_hover_duration", 200)
            hover_curve = get_easing_curve_enum(anim_profile.get("button_hover_curve", "OutCubic"))
            press_duration = anim_profile.get("button_press_duration", 100)

            self.ripple_enabled = anim_profile.get("ripple_enabled", True)
        except:
            # Fallback to defaults if theme system not available
            hover_duration = 200
            hover_curve = QEasingCurve.OutCubic
            press_duration = 100
            self.ripple_enabled = True

        # Hover animation with theme-specific settings
        self.hover_anim = QPropertyAnimation(self, b"hover_opacity")
        self.hover_anim.setDuration(hover_duration)
        self.hover_anim.setEasingCurve(hover_curve)

        # Press animation with theme-specific settings
        self.press_anim = QPropertyAnimation(self, b"press_scale")
        self.press_anim.setDuration(press_duration)
        self.press_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _update_style(self):
        """Update button style based on variant"""
        colors = self.variants.get(self.variant, self.variants["primary"])

        self.setStyleSheet(f"""
            QPushButton {{
                background: {colors["base"]};
                border: 1.5px solid {colors["border"]};
                border-radius: 22px;
                color: {colors["text"]};
                font-weight: 600;
                font-size: 13px;
                padding: 10px 20px;
                backdrop-filter: blur(10px);
            }}
            QPushButton:hover {{
                background: {colors["hover"]};
                border: 1.5px solid {colors["border"]};
            }}
            QPushButton:pressed {{
                background: {colors["hover"]};
            }}
            QPushButton:disabled {{
                background: rgba(100, 100, 100, 0.3);
                border: 1.5px solid rgba(150, 150, 150, 0.3);
                color: rgba(255, 255, 255, 0.4);
            }}
        """)

    def set_variant(self, variant):
        """Change button variant (primary, success, warning, danger, glass, dark)"""
        if variant in self.variants:
            self.variant = variant
            self._update_style()

    # Property animations
    def get_hover_opacity(self):
        return self._hover_opacity

    def set_hover_opacity(self, value):
        self._hover_opacity = value
        self.update()

    hover_opacity = Property(float, get_hover_opacity, set_hover_opacity)

    def get_press_scale(self):
        return self._press_scale

    def set_press_scale(self, value):
        self._press_scale = value
        self.update()

    press_scale = Property(float, get_press_scale, set_press_scale)

    def enterEvent(self, event):
        """Animate on hover enter"""
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self._hover_opacity)
        self.hover_anim.setEndValue(1.0)
        self.hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animate on hover leave"""
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self._hover_opacity)
        self.hover_anim.setEndValue(0.0)
        self.hover_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Animate on press"""
        self.press_anim.stop()
        self.press_anim.setStartValue(1.0)
        self.press_anim.setEndValue(0.95)
        self.press_anim.start()

        # Start ripple effect
        self._ripple_center = event.position().toPoint()
        self._ripple_radius = 0

        # Ripple animation
        ripple_anim = QPropertyAnimation(self, b"ripple_radius")
        ripple_anim.setDuration(400)
        ripple_anim.setStartValue(0)
        ripple_anim.setEndValue(max(self.width(), self.height()))
        ripple_anim.setEasingCurve(QEasingCurve.OutCubic)
        ripple_anim.start()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Animate on release"""
        self.press_anim.stop()
        self.press_anim.setStartValue(self._press_scale)
        self.press_anim.setEndValue(1.0)
        self.press_anim.start()
        super().mouseReleaseEvent(event)

    def get_ripple_radius(self):
        return self._ripple_radius

    def set_ripple_radius(self, value):
        self._ripple_radius = value
        self.update()

    ripple_radius = Property(int, get_ripple_radius, set_ripple_radius)

    def paintEvent(self, event):
        """Custom paint for glass effect and ripple"""
        # Draw base button
        super().paintEvent(event)

        # Draw ripple effect
        if self._ripple_radius > 0 and self._ripple_center:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Ripple color with fade
            ripple_opacity = max(0, 100 - (self._ripple_radius / max(self.width(), self.height()) * 100))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, int(ripple_opacity)))
            painter.drawEllipse(
                self._ripple_center.x() - self._ripple_radius,
                self._ripple_center.y() - self._ripple_radius,
                self._ripple_radius * 2,
                self._ripple_radius * 2
            )
