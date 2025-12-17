"""
Page Transition Manager for EmployeeVault
Smooth transitions between different views/pages
"""

from enum import Enum
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QPoint
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QStackedWidget
from PySide6.QtGui import QPixmap, QPainter


class TransitionType(Enum):
    """Available page transition types"""
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    BLUR_FADE = "blur_fade"
    CROSSFADE = "crossfade"
    PUSH_LEFT = "push_left"
    PUSH_RIGHT = "push_right"


class PageTransitionManager:
    """Manages smooth transitions between pages in QStackedWidget"""
    
    def __init__(self, stacked_widget: QStackedWidget):
        self.stacked_widget = stacked_widget
        self.is_animating = False
        self.current_transition = TransitionType.FADE
        self.transition_duration = 350
        
        # Store original geometry
        self.original_geometry = None
    
    def set_transition_type(self, transition_type: TransitionType):
        """Set the transition effect type"""
        self.current_transition = transition_type
    
    def set_duration(self, duration: int):
        """Set transition duration in milliseconds"""
        self.transition_duration = duration
    
    def transition_to(self, index: int, transition_override: TransitionType = None):
        """Transition to page at index with animation"""
        if self.is_animating:
            return
        
        if index == self.stacked_widget.currentIndex():
            return
        
        transition = transition_override or self.current_transition
        
        current_widget = self.stacked_widget.currentWidget()
        next_widget = self.stacked_widget.widget(index)
        
        if not current_widget or not next_widget:
            self.stacked_widget.setCurrentIndex(index)
            return
        
        self.is_animating = True
        
        # Execute transition based on type
        if transition == TransitionType.FADE:
            self._fade_transition(current_widget, next_widget, index)
        elif transition == TransitionType.SLIDE_LEFT:
            self._slide_transition(current_widget, next_widget, index, direction="left")
        elif transition == TransitionType.SLIDE_RIGHT:
            self._slide_transition(current_widget, next_widget, index, direction="right")
        elif transition == TransitionType.SLIDE_UP:
            self._slide_transition(current_widget, next_widget, index, direction="up")
        elif transition == TransitionType.SLIDE_DOWN:
            self._slide_transition(current_widget, next_widget, index, direction="down")
        elif transition == TransitionType.ZOOM_IN:
            self._zoom_transition(current_widget, next_widget, index, zoom_in=True)
        elif transition == TransitionType.ZOOM_OUT:
            self._zoom_transition(current_widget, next_widget, index, zoom_in=False)
        elif transition == TransitionType.CROSSFADE:
            self._crossfade_transition(current_widget, next_widget, index)
        elif transition == TransitionType.PUSH_LEFT:
            self._push_transition(current_widget, next_widget, index, direction="left")
        elif transition == TransitionType.PUSH_RIGHT:
            self._push_transition(current_widget, next_widget, index, direction="right")
        else:
            # Fallback to instant switch
            self.stacked_widget.setCurrentIndex(index)
            self.is_animating = False
    
    def _fade_transition(self, current_widget: QWidget, next_widget: QWidget, next_index: int):
        """Simple fade transition"""
        # Setup opacity effects
        current_opacity = QGraphicsOpacityEffect()
        next_opacity = QGraphicsOpacityEffect()
        
        current_widget.setGraphicsEffect(current_opacity)
        next_widget.setGraphicsEffect(next_opacity)
        
        # Start with next widget invisible
        next_opacity.setOpacity(0.0)
        self.stacked_widget.setCurrentWidget(next_widget)
        
        # Create animations
        current_anim = QPropertyAnimation(current_opacity, b"opacity")
        current_anim.setDuration(self.transition_duration)
        current_anim.setStartValue(1.0)
        current_anim.setEndValue(0.0)
        current_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        next_anim = QPropertyAnimation(next_opacity, b"opacity")
        next_anim.setDuration(self.transition_duration)
        next_anim.setStartValue(0.0)
        next_anim.setEndValue(1.0)
        next_anim.setEasingCurve(QEasingCurve.InCubic)
        
        # Group animations
        group = QParallelAnimationGroup()
        group.addAnimation(current_anim)
        group.addAnimation(next_anim)
        
        def on_finished():
            current_widget.setGraphicsEffect(None)
            next_widget.setGraphicsEffect(None)
            self.is_animating = False
        
        group.finished.connect(on_finished)
        group.start()
    
    def _slide_transition(self, current_widget: QWidget, next_widget: QWidget, next_index: int, direction: str):
        """Slide transition in specified direction"""
        width = self.stacked_widget.width()
        height = self.stacked_widget.height()
        
        # Calculate start positions
        if direction == "left":
            next_start = QPoint(width, 0)
            current_end = QPoint(-width, 0)
        elif direction == "right":
            next_start = QPoint(-width, 0)
            current_end = QPoint(width, 0)
        elif direction == "up":
            next_start = QPoint(0, height)
            current_end = QPoint(0, -height)
        else:  # down
            next_start = QPoint(0, -height)
            current_end = QPoint(0, height)
        
        # Move next widget to start position
        next_widget.move(next_start)
        next_widget.show()
        next_widget.raise_()
        
        # Animate both widgets
        current_anim = QPropertyAnimation(current_widget, b"pos")
        current_anim.setDuration(self.transition_duration)
        current_anim.setStartValue(current_widget.pos())
        current_anim.setEndValue(current_end)
        current_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        next_anim = QPropertyAnimation(next_widget, b"pos")
        next_anim.setDuration(self.transition_duration)
        next_anim.setStartValue(next_start)
        next_anim.setEndValue(QPoint(0, 0))
        next_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        group = QParallelAnimationGroup()
        group.addAnimation(current_anim)
        group.addAnimation(next_anim)
        
        def on_finished():
            self.stacked_widget.setCurrentIndex(next_index)
            next_widget.move(0, 0)
            current_widget.move(0, 0)
            self.is_animating = False
        
        group.finished.connect(on_finished)
        group.start()
    
    def _zoom_transition(self, current_widget: QWidget, next_widget: QWidget, next_index: int, zoom_in: bool):
        """Zoom in/out transition"""
        current_opacity = QGraphicsOpacityEffect()
        next_opacity = QGraphicsOpacityEffect()
        
        current_widget.setGraphicsEffect(current_opacity)
        next_widget.setGraphicsEffect(next_opacity)
        
        next_opacity.setOpacity(0.0)
        self.stacked_widget.setCurrentWidget(next_widget)
        
        # Opacity animations
        current_fade = QPropertyAnimation(current_opacity, b"opacity")
        current_fade.setDuration(self.transition_duration)
        current_fade.setStartValue(1.0)
        current_fade.setEndValue(0.0)
        current_fade.setEasingCurve(QEasingCurve.OutCubic)
        
        next_fade = QPropertyAnimation(next_opacity, b"opacity")
        next_fade.setDuration(self.transition_duration)
        next_fade.setStartValue(0.0)
        next_fade.setEndValue(1.0)
        next_fade.setEasingCurve(QEasingCurve.InCubic)
        
        # Note: Scale animations would require custom widget wrapper with transform support
        # For now, using fade as approximation
        
        group = QParallelAnimationGroup()
        group.addAnimation(current_fade)
        group.addAnimation(next_fade)
        
        def on_finished():
            current_widget.setGraphicsEffect(None)
            next_widget.setGraphicsEffect(None)
            self.is_animating = False
        
        group.finished.connect(on_finished)
        group.start()
    
    def _crossfade_transition(self, current_widget: QWidget, next_widget: QWidget, next_index: int):
        """Crossfade with longer duration"""
        original_duration = self.transition_duration
        self.transition_duration = int(self.transition_duration * 1.5)
        self._fade_transition(current_widget, next_widget, next_index)
        self.transition_duration = original_duration
    
    def _push_transition(self, current_widget: QWidget, next_widget: QWidget, next_index: int, direction: str):
        """Push transition - new page pushes old page out"""
        self._slide_transition(current_widget, next_widget, next_index, direction)


class AnimatedStackedWidget(QStackedWidget):
    """QStackedWidget with built-in transition support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transition_manager = PageTransitionManager(self)
        self.default_transition = TransitionType.FADE
    
    def setCurrentIndex(self, index: int, animated: bool = True, transition: TransitionType = None):
        """Override to add animation support"""
        if animated:
            transition_type = transition or self.default_transition
            self.transition_manager.transition_to(index, transition_type)
        else:
            super().setCurrentIndex(index)
    
    def setCurrentWidget(self, widget: QWidget, animated: bool = True, transition: TransitionType = None):
        """Override to add animation support"""
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index, animated, transition)
    
    def set_default_transition(self, transition: TransitionType):
        """Set default transition type"""
        self.default_transition = transition
        self.transition_manager.set_transition_type(transition)
    
    def set_transition_duration(self, duration: int):
        """Set transition duration"""
        self.transition_manager.set_duration(duration)
