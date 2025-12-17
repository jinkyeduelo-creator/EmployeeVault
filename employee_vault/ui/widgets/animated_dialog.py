"""
Animated Dialog - Smooth Dialog Entrance/Exit Animations
Scale, fade, and slide animations for QDialog

v4.4.1: Enhanced with theme support and easy global integration
- AnimatedDialogBase: Simple drop-in replacement for QDialog
- Multiple animation styles available
- Theme-aware backdrop
- Professional entrance/exit animations
"""

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint,
    QSequentialAnimationGroup, QParallelAnimationGroup, Property, QTimer
)
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import QDialog, QGraphicsOpacityEffect, QWidget


class AnimatedDialog(QDialog):
    """
    Base dialog class with smooth entrance/exit animations
    Supports multiple animation styles: scale, fade, slide
    """

    def __init__(self, parent=None, animation_type="scale"):
        super().__init__(parent)

        self._animation_type = animation_type
        self._backdrop_opacity = 0

        # Remove default window frame for custom styling
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create backdrop widget (dark overlay)
        self.backdrop = QWidget(self)
        self.backdrop.setStyleSheet("background: rgba(0, 0, 0, 180);")
        self.backdrop.setGeometry(self.geometry())
        self.backdrop.lower()  # Send to back

        # Opacity effect for fade animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)

        # Animations
        self.backdrop_anim = QPropertyAnimation(self, b"backdrop_opacity")
        self.backdrop_anim.setDuration(250)
        self.backdrop_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.entrance_anim = self._create_entrance_animation()
        self.exit_anim = self._create_exit_animation()

    def get_backdrop_opacity(self):
        return self._backdrop_opacity

    def set_backdrop_opacity(self, value):
        self._backdrop_opacity = value
        self.backdrop.setStyleSheet(f"background: rgba(0, 0, 0, {int(value * 180)});")

    backdrop_opacity = Property(float, get_backdrop_opacity, set_backdrop_opacity)

    def _create_entrance_animation(self):
        """Create entrance animation based on type"""
        anim_group = QParallelAnimationGroup()

        if self._animation_type == "scale":
            # Scale from center
            self.setGraphicsEffect(self.opacity_effect)

            # Opacity animation
            opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            opacity_anim.setDuration(300)
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
            anim_group.addAnimation(opacity_anim)

        elif self._animation_type == "slide_up":
            # Slide from bottom
            geo_anim = QPropertyAnimation(self, b"geometry")
            geo_anim.setDuration(300)
            geo_anim.setEasingCurve(QEasingCurve.OutCubic)
            anim_group.addAnimation(geo_anim)

        # Backdrop fade in
        anim_group.addAnimation(self.backdrop_anim)

        return anim_group

    def _create_exit_animation(self):
        """Create exit animation"""
        anim_group = QParallelAnimationGroup()

        if self._animation_type == "scale":
            # Scale to center and fade out
            opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            opacity_anim.setDuration(250)
            opacity_anim.setStartValue(1.0)
            opacity_anim.setEndValue(0.0)
            opacity_anim.setEasingCurve(QEasingCurve.InCubic)
            anim_group.addAnimation(opacity_anim)

        elif self._animation_type == "slide_down":
            # Slide to bottom
            geo_anim = QPropertyAnimation(self, b"geometry")
            geo_anim.setDuration(250)
            geo_anim.setEasingCurve(QEasingCurve.InCubic)
            anim_group.addAnimation(geo_anim)

        # Backdrop fade out
        backdrop_anim = QPropertyAnimation(self, b"backdrop_opacity")
        backdrop_anim.setDuration(250)
        backdrop_anim.setStartValue(1.0)
        backdrop_anim.setEndValue(0.0)
        anim_group.addAnimation(backdrop_anim)

        return anim_group

    def showEvent(self, event):
        """Override show to add entrance animation"""
        super().showEvent(event)

        # Position backdrop
        if self.parent():
            self.backdrop.setGeometry(0, 0, self.width(), self.height())

        # Animate entrance
        if self._animation_type == "scale":
            self.entrance_anim.start()
            self.backdrop_anim.setStartValue(0)
            self.backdrop_anim.setEndValue(1.0)
            self.backdrop_anim.start()

        elif self._animation_type == "slide_up":
            # Start from below
            original_geo = self.geometry()
            start_geo = QRect(
                original_geo.x(),
                self.parent().height() if self.parent() else 1000,
                original_geo.width(),
                original_geo.height()
            )
            self.setGeometry(start_geo)

            geo_anim = self.entrance_anim.animationAt(0)
            geo_anim.setStartValue(start_geo)
            geo_anim.setEndValue(original_geo)
            self.entrance_anim.start()

            self.backdrop_anim.setStartValue(0)
            self.backdrop_anim.setEndValue(1.0)
            self.backdrop_anim.start()

    def closeEvent(self, event):
        """Override close to add exit animation"""
        # Prevent immediate close
        event.ignore()

        # Animate exit
        self.exit_anim.finished.connect(lambda: QDialog.closeEvent(self, event))

        if self._animation_type == "slide_down":
            # Slide to bottom
            geo_anim = self.exit_anim.animationAt(0)
            current_geo = self.geometry()
            end_geo = QRect(
                current_geo.x(),
                self.parent().height() if self.parent() else 1000,
                current_geo.width(),
                current_geo.height()
            )
            geo_anim.setStartValue(current_geo)
            geo_anim.setEndValue(end_geo)

        self.exit_anim.start()

    def resizeEvent(self, event):
        """Ensure backdrop resizes with dialog"""
        super().resizeEvent(event)
        if hasattr(self, 'backdrop'):
            self.backdrop.setGeometry(0, 0, self.width(), self.height())


class ScaleDialog(AnimatedDialog):
    """Dialog that scales in from center"""

    def __init__(self, parent=None):
        super().__init__(parent, animation_type="scale")


class SlideUpDialog(AnimatedDialog):
    """Dialog that slides up from bottom"""

    def __init__(self, parent=None):
        super().__init__(parent, animation_type="slide_up")


class FadeDialog(QDialog):
    """Simple fade in/out dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)

        # Fade animation
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, event):
        """Fade in on show"""
        super().showEvent(event)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def closeEvent(self, event):
        """Fade out on close"""
        event.ignore()
        self.fade_anim.finished.connect(lambda: QDialog.closeEvent(self, event))
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()


class BounceDialog(QDialog):
    """Dialog that bounces in"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scale = 0.0

        # Scale animation with bounce
        self.scale_anim = QPropertyAnimation(self, b"scale")
        self.scale_anim.setDuration(500)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBounce)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        # Note: QDialog doesn't support direct scaling
        # This would need to be implemented with custom paintEvent
        # or by scaling child widgets

    scale = Property(float, get_scale, set_scale)

    def showEvent(self, event):
        """Bounce in on show"""
        super().showEvent(event)
        self.scale_anim.setStartValue(0.0)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.start()


# ============================================================================
# v4.4.1: Simple Drop-in Replacement for Global Integration
# ============================================================================

class AnimatedDialogBase(QDialog):
    """
    Drop-in replacement for QDialog with smooth fade animation

    Usage:
        # Instead of: class MyDialog(QDialog):
        # Use: class MyDialog(AnimatedDialogBase):

        # Or pass animation_style parameter:
        dialog = AnimatedDialogBase(self, animation_style="fade")
        dialog = AnimatedDialogBase(self, animation_style="scale")
        dialog = AnimatedDialogBase(self, animation_style="slide")

    Features:
    - Simple fade in/out by default
    - Optional scale or slide animations
    - No visual changes to dialog (keeps standard frame)
    - Works with all existing dialog code
    - Theme-aware (inherits parent theme)
    - Context-aware micro-animations (shake, bounce)
    """

    def __init__(self, parent=None, animation_style="fade", animation_duration=200):
        super().__init__(parent)

        self._animation_style = animation_style
        self._animation_duration = animation_duration
        self._is_closing = False
        self._window_opacity = 1.0

        # Setup animation based on style - use windowOpacity instead of QGraphicsOpacityEffect
        # This avoids QPainter conflicts
        if animation_style in ["fade", "scale"]:
            # Simple opacity fade using windowOpacity
            self.setWindowOpacity(0)
            self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self.fade_anim.setDuration(animation_duration)
            self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        elif animation_style == "slide":
            # Slide with opacity
            self.setWindowOpacity(0)
            self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self.fade_anim.setDuration(animation_duration)
            self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

            self.geo_anim = QPropertyAnimation(self, b"geometry")
            self.geo_anim.setDuration(animation_duration)
            self.geo_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Shake animation for errors
        self.shake_anim = QPropertyAnimation(self, b"pos")
        self.shake_anim.setDuration(400)
        self.shake_anim.setEasingCurve(QEasingCurve.OutBounce)
    
    def shake(self):
        """Shake dialog horizontally (for validation errors)"""
        if self.shake_anim.state() == QPropertyAnimation.Running:
            return
        
        original_pos = self.pos()
        
        # Create shake sequence: left -> right -> left -> center
        self.shake_anim.setKeyValueAt(0.0, original_pos)
        self.shake_anim.setKeyValueAt(0.25, QPoint(original_pos.x() - 10, original_pos.y()))
        self.shake_anim.setKeyValueAt(0.50, QPoint(original_pos.x() + 10, original_pos.y()))
        self.shake_anim.setKeyValueAt(0.75, QPoint(original_pos.x() - 5, original_pos.y()))
        self.shake_anim.setKeyValueAt(1.0, original_pos)
        
        self.shake_anim.start()
    
    def bounce_success(self):
        """Gentle bounce animation (for success confirmation)"""
        # Modify entrance animation to use bounce easing
        if hasattr(self, 'fade_anim') and self.isVisible():
            # Create a temporary scale-like effect using opacity pulse
            opacity_anim = QPropertyAnimation(self, b"windowOpacity")
            opacity_anim.setDuration(500)
            opacity_anim.setKeyValueAt(0.0, 1.0)
            opacity_anim.setKeyValueAt(0.3, 0.9)
            opacity_anim.setKeyValueAt(0.6, 1.05)  # Slight over-shoot (clamped to 1.0)
            opacity_anim.setKeyValueAt(1.0, 1.0)
            opacity_anim.setEasingCurve(QEasingCurve.OutBounce)
            opacity_anim.start()
    
    def pulse(self, count: int = 2):
        """Pulse animation to draw attention"""
        def run_pulse(remaining):
            if remaining <= 0:
                return
            
            pulse_anim = QPropertyAnimation(self, b"windowOpacity")
            pulse_anim.setDuration(300)
            pulse_anim.setStartValue(1.0)
            pulse_anim.setKeyValueAt(0.5, 0.7)
            pulse_anim.setEndValue(1.0)
            pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
            
            pulse_anim.finished.connect(lambda: run_pulse(remaining - 1))
            pulse_anim.start()
        
        run_pulse(count)

    def showEvent(self, event):
        """Animate entrance on show"""
        super().showEvent(event)

        if self._animation_style == "fade":
            # Simple fade in
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

        elif self._animation_style == "scale":
            # Fade in (scale effect would need transform which QDialog doesn't support well)
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

        elif self._animation_style == "slide":
            # Slide from top with fade
            original_geo = self.geometry()
            start_geo = QRect(
                original_geo.x(),
                original_geo.y() - 50,  # Start 50px above
                original_geo.width(),
                original_geo.height()
            )
            self.setGeometry(start_geo)

            self.geo_anim.setStartValue(start_geo)
            self.geo_anim.setEndValue(original_geo)
            self.geo_anim.start()

            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

    def closeEvent(self, event):
        """Animate exit on close"""
        if self._is_closing:
            # Already animating close, accept it
            event.accept()
            return

        # Prevent immediate close
        event.ignore()
        self._is_closing = True

        # Animate exit
        if self._animation_style == "fade":
            self.fade_anim.finished.connect(self._finish_close)
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

        elif self._animation_style == "scale":
            self.fade_anim.finished.connect(self._finish_close)
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

        elif self._animation_style == "slide":
            # Slide down with fade
            self.fade_anim.finished.connect(self._finish_close)

            current_geo = self.geometry()
            end_geo = QRect(
                current_geo.x(),
                current_geo.y() + 50,  # End 50px below
                current_geo.width(),
                current_geo.height()
            )

            self.geo_anim.setStartValue(current_geo)
            self.geo_anim.setEndValue(end_geo)
            self.geo_anim.start()

            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

    def _finish_close(self):
        """Complete the close after animation"""
        self._is_closing = False
        self.close()  # This will trigger closeEvent again, but _is_closing is True so it accepts
        self.deleteLater()


class QuickAnimatedDialog(AnimatedDialogBase):
    """
    Faster animated dialog (150ms) for quick interactions
    Good for: alerts, confirmations, small forms
    """
    def __init__(self, parent=None, animation_style="fade"):
        super().__init__(parent, animation_style=animation_style, animation_duration=150)


class SmoothAnimatedDialog(AnimatedDialogBase):
    """
    Slower animated dialog (300ms) for smooth, polished feel
    Good for: large forms, complex dialogs, settings
    """
    def __init__(self, parent=None, animation_style="fade"):
        super().__init__(parent, animation_style=animation_style, animation_duration=300)
