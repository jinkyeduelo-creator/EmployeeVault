"""
Page Transition Manager - Smooth Page Switching Animations
Cross-fade, slide, and other transition effects between pages
"""

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint,
    QSequentialAnimationGroup, QParallelAnimationGroup, Property, Signal
)
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget, QStackedWidget


class PageTransitionManager(QStackedWidget):
    """
    Enhanced QStackedWidget with smooth page transitions
    Supports fade, slide, and cross-fade animations
    """

    transition_finished = Signal()

    def __init__(self, parent=None, transition_type="fade"):
        super().__init__(parent)

        self._transition_type = transition_type
        self._is_animating = False
        self._current_index = 0
        self._next_index = 0

        # Track widgets with opacity animations
        self._animating_widgets = set()

    def set_transition_type(self, transition_type):
        """Change transition type (fade, slide_left, slide_right, cross_fade)"""
        self._transition_type = transition_type

    def animated_set_current_index(self, index):
        """Switch to page with animation"""
        if index == self.currentIndex() or self._is_animating:
            return

        self._is_animating = True
        self._current_index = self.currentIndex()
        self._next_index = index

        if self._transition_type == "fade":
            self._fade_transition(index)
        elif self._transition_type == "slide_left":
            self._slide_transition(index, direction="left")
        elif self._transition_type == "slide_right":
            self._slide_transition(index, direction="right")
        elif self._transition_type == "cross_fade":
            self._cross_fade_transition(index)
        else:
            # No animation, just switch
            self.setCurrentIndex(index)
            self._is_animating = False
            self.transition_finished.emit()

    def _fade_transition(self, index):
        """Simple instant page switch - avoids QPainter conflicts with graphics effects"""
        # Just switch pages instantly to avoid QGraphicsOpacityEffect conflicts
        # with child widgets that have QGraphicsDropShadowEffect
        self.setCurrentIndex(index)
        self._animation_finished()

    def _slide_transition(self, index, direction="left"):
        """Slide current page out, next page in"""
        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        # Position next widget off-screen
        if direction == "left":
            next_widget.setGeometry(self.width(), 0, self.width(), self.height())
            slide_in_end = 0
            slide_out_end = -self.width()
        else:  # right
            next_widget.setGeometry(-self.width(), 0, self.width(), self.height())
            slide_in_end = 0
            slide_out_end = self.width()

        # Show next widget
        self.setCurrentIndex(index)

        # Slide animations
        slide_out = QPropertyAnimation(current_widget, b"geometry")
        slide_out.setDuration(300)
        slide_out.setStartValue(current_widget.geometry())
        slide_out.setEndValue(QRect(slide_out_end, 0, self.width(), self.height()))
        slide_out.setEasingCurve(QEasingCurve.OutCubic)

        slide_in = QPropertyAnimation(next_widget, b"geometry")
        slide_in.setDuration(300)
        slide_in.setStartValue(next_widget.geometry())
        slide_in.setEndValue(QRect(slide_in_end, 0, self.width(), self.height()))
        slide_in.setEasingCurve(QEasingCurve.OutCubic)

        # Parallel animation
        parallel = QParallelAnimationGroup()
        parallel.addAnimation(slide_out)
        parallel.addAnimation(slide_in)
        parallel.finished.connect(self._animation_finished)
        parallel.start()

        self._current_animation = parallel

    def _cross_fade_transition(self, index):
        """Simple instant page switch - avoids QPainter conflicts"""
        # Just switch pages instantly to avoid QGraphicsOpacityEffect conflicts
        self.setCurrentIndex(index)
        self._animation_finished()

    def _animation_finished(self):
        """Called when transition animation finishes"""
        self._is_animating = False
        self.transition_finished.emit()


class SlidingStackedWidget(QStackedWidget):
    """
    Simpler sliding widget for quick left/right transitions
    Auto-detects direction based on index
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._speed = 300
        self._animation = None
        self._current = 0

    def set_speed(self, speed):
        """Set transition speed in milliseconds"""
        self._speed = speed

    def slide_to_index(self, index):
        """Slide to index with auto direction"""
        if index == self.currentIndex():
            return

        direction = "left" if index > self.currentIndex() else "right"
        self._slide(index, direction)

    def _slide(self, index, direction):
        """Perform slide animation"""
        if self._animation and self._animation.state() == QPropertyAnimation.Running:
            return

        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        if not current_widget or not next_widget:
            self.setCurrentIndex(index)
            return

        # Calculate positions
        width = self.width()
        if direction == "left":
            offset_x = width
        else:
            offset_x = -width

        # Position next widget
        next_widget.setGeometry(offset_x, 0, width, self.height())
        next_widget.show()
        next_widget.raise_()

        # Animate current widget
        anim_current = QPropertyAnimation(current_widget, b"geometry")
        anim_current.setDuration(self._speed)
        anim_current.setStartValue(current_widget.geometry())
        anim_current.setEndValue(QRect(-offset_x, 0, width, self.height()))
        anim_current.setEasingCurve(QEasingCurve.OutCubic)

        # Animate next widget
        anim_next = QPropertyAnimation(next_widget, b"geometry")
        anim_next.setDuration(self._speed)
        anim_next.setStartValue(QRect(offset_x, 0, width, self.height()))
        anim_next.setEndValue(QRect(0, 0, width, self.height()))
        anim_next.setEasingCurve(QEasingCurve.OutCubic)

        # Group animations
        group = QParallelAnimationGroup()
        group.addAnimation(anim_current)
        group.addAnimation(anim_next)
        group.finished.connect(lambda: self.setCurrentIndex(index))
        group.start()

        self._animation = group
        self._current = index


class FadingStackedWidget(QStackedWidget):
    """
    Simple fading transition between pages
    Lightweight alternative to full PageTransitionManager
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._speed = 250

    def fade_to_index(self, index):
        """Fade to index"""
        if index == self.currentIndex():
            return

        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        if not current_widget or not next_widget:
            self.setCurrentIndex(index)
            return

        # Opacity effect
        effect = QGraphicsOpacityEffect()
        current_widget.setGraphicsEffect(effect)

        # Fade out
        fade = QPropertyAnimation(effect, b"opacity")
        fade.setDuration(self._speed)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        fade.finished.connect(lambda: self.setCurrentIndex(index))
        fade.start()

        # Keep reference
        self._current_animation = fade
