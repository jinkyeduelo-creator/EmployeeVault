"""
Scroll Animation System for EmployeeVault
Reveal, parallax, and scroll-triggered effects
"""

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QObject, QEvent, QPoint
)
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QGraphicsOpacityEffect, QVBoxLayout
)
from PySide6.QtGui import QPainter, QPaintEvent


class ScrollAnimationManager(QObject):
    """Manages scroll-triggered animations for widgets"""
    
    def __init__(self, scroll_area: QScrollArea):
        super().__init__()
        self.scroll_area = scroll_area
        self.animated_widgets = {}  # widget -> animation_data
        self.reveal_threshold = 0.2  # Trigger when 20% visible
        
        # Install event filter to track scroll
        scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
    
    def register_widget(self, widget: QWidget, animation_type: str = "fade_up",
                       duration: int = 500, delay: int = 0):
        """
        Register widget for scroll animation
        
        Args:
            widget: Widget to animate
            animation_type: "fade_up", "fade_in", "slide_left", "slide_right", "scale_in"
            duration: Animation duration in ms
            delay: Delay before animation starts in ms
        """
        self.animated_widgets[widget] = {
            'type': animation_type,
            'duration': duration,
            'delay': delay,
            'triggered': False,
            'animation': None
        }
        
        # Initially hide widget based on animation type
        if 'fade' in animation_type or 'scale' in animation_type:
            opacity = QGraphicsOpacityEffect()
            opacity.setOpacity(0.0)
            widget.setGraphicsEffect(opacity)
    
    def on_scroll(self, value):
        """Handle scroll event and trigger animations"""
        viewport = self.scroll_area.viewport()
        viewport_rect = viewport.rect()
        
        for widget, data in self.animated_widgets.items():
            if data['triggered']:
                continue
            
            # Get widget position relative to viewport
            widget_pos = widget.mapTo(self.scroll_area.widget(), QPoint(0, 0))
            widget_rect = widget.rect()
            widget_rect.moveTo(widget_pos)
            
            # Check if widget is visible enough
            if self._is_visible(widget_rect, viewport_rect):
                self._trigger_animation(widget, data)
    
    def _is_visible(self, widget_rect, viewport_rect):
        """Check if widget is sufficiently visible in viewport"""
        if not widget_rect.intersects(viewport_rect):
            return False
        
        intersection = widget_rect.intersected(viewport_rect)
        visible_ratio = intersection.height() / widget_rect.height()
        
        return visible_ratio >= self.reveal_threshold
    
    def _trigger_animation(self, widget: QWidget, data: dict):
        """Trigger animation for widget"""
        data['triggered'] = True
        
        anim_type = data['type']
        duration = data['duration']
        
        if anim_type == "fade_up":
            self._animate_fade_up(widget, duration, data['delay'])
        elif anim_type == "fade_in":
            self._animate_fade_in(widget, duration, data['delay'])
        elif anim_type == "slide_left":
            self._animate_slide(widget, duration, data['delay'], direction="left")
        elif anim_type == "slide_right":
            self._animate_slide(widget, duration, data['delay'], direction="right")
        elif anim_type == "scale_in":
            self._animate_scale_in(widget, duration, data['delay'])
    
    def _animate_fade_up(self, widget: QWidget, duration: int, delay: int):
        """Fade in while sliding up"""
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect:
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
        
        # Opacity animation
        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Position animation
        original_pos = widget.pos()
        offset_pos = QPoint(original_pos.x(), original_pos.y() + 30)
        widget.move(offset_pos)
        
        pos_anim = QPropertyAnimation(widget, b"pos")
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(offset_pos)
        pos_anim.setEndValue(original_pos)
        pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        if delay > 0:
            opacity_anim.setStartDelay(delay)
            pos_anim.setStartDelay(delay)
        
        opacity_anim.start()
        pos_anim.start()
    
    def _animate_fade_in(self, widget: QWidget, duration: int, delay: int):
        """Simple fade in"""
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect:
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
        
        anim = QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        
        if delay > 0:
            anim.setStartDelay(delay)
        
        anim.start()
    
    def _animate_slide(self, widget: QWidget, duration: int, delay: int, direction: str):
        """Slide in from direction"""
        original_pos = widget.pos()
        
        if direction == "left":
            offset_pos = QPoint(original_pos.x() + 50, original_pos.y())
        else:  # right
            offset_pos = QPoint(original_pos.x() - 50, original_pos.y())
        
        widget.move(offset_pos)
        
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(offset_pos)
        anim.setEndValue(original_pos)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        
        if delay > 0:
            anim.setStartDelay(delay)
        
        anim.start()
    
    def _animate_scale_in(self, widget: QWidget, duration: int, delay: int):
        """Scale in with fade"""
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect:
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
        
        anim = QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutBack)
        
        if delay > 0:
            anim.setStartDelay(delay)
        
        anim.start()
    
    def reset_widget(self, widget: QWidget):
        """Reset widget animation state"""
        if widget in self.animated_widgets:
            self.animated_widgets[widget]['triggered'] = False
    
    def reset_all(self):
        """Reset all widget animations"""
        for data in self.animated_widgets.values():
            data['triggered'] = False


class ParallaxWidget(QWidget):
    """Widget with parallax scrolling effect"""
    
    def __init__(self, parent=None, parallax_factor: float = 0.5):
        super().__init__(parent)
        self.parallax_factor = parallax_factor  # 0.0 = no parallax, 1.0 = full parallax
        self.original_y = 0
        self.scroll_offset = 0
    
    def set_scroll_offset(self, offset: int):
        """Update parallax based on scroll offset"""
        self.scroll_offset = offset
        parallax_y = int(offset * self.parallax_factor)
        self.move(self.x(), self.original_y + parallax_y)
    
    def showEvent(self, event):
        """Store original position"""
        super().showEvent(event)
        self.original_y = self.y()


class ParallaxScrollArea(QScrollArea):
    """Scroll area with automatic parallax effects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parallax_widgets = []
        
        self.verticalScrollBar().valueChanged.connect(self.update_parallax)
    
    def add_parallax_widget(self, widget: ParallaxWidget):
        """Register widget for parallax effect"""
        self.parallax_widgets.append(widget)
    
    def update_parallax(self, value):
        """Update all parallax widgets"""
        for widget in self.parallax_widgets:
            widget.set_scroll_offset(value)


class ScrollRevealContainer(QWidget):
    """Container that reveals children with staggered animations on scroll"""
    
    def __init__(self, parent=None, scroll_area: QScrollArea = None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        
        self.scroll_manager = None
        if scroll_area:
            self.scroll_manager = ScrollAnimationManager(scroll_area)
    
    def add_widget_animated(self, widget: QWidget, animation_type: str = "fade_up",
                           stagger_delay: int = 0):
        """Add widget with scroll reveal animation"""
        self.layout.addWidget(widget)
        
        if self.scroll_manager:
            # Calculate delay based on widget index for stagger effect
            index = self.layout.count() - 1
            delay = stagger_delay * index
            
            self.scroll_manager.register_widget(
                widget,
                animation_type=animation_type,
                duration=500,
                delay=delay
            )
    
    def set_scroll_area(self, scroll_area: QScrollArea):
        """Set scroll area for animation manager"""
        self.scroll_manager = ScrollAnimationManager(scroll_area)


def create_staggered_reveal(scroll_area: QScrollArea, widgets: list,
                            animation_type: str = "fade_up",
                            stagger_delay: int = 100):
    """
    Create staggered scroll reveal for list of widgets
    
    Args:
        scroll_area: Parent scroll area
        widgets: List of widgets to animate
        animation_type: Animation type
        stagger_delay: Delay between each widget animation in ms
    """
    manager = ScrollAnimationManager(scroll_area)
    
    for i, widget in enumerate(widgets):
        delay = i * stagger_delay
        manager.register_widget(
            widget,
            animation_type=animation_type,
            duration=500,
            delay=delay
        )
    
    return manager
