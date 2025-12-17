"""
Advanced Animation Manager for EmployeeVault
Centralized animation system with performance optimization and accessibility support
"""

import os
import logging
from typing import Optional, Callable
from PySide6.QtCore import (
    QObject, Signal, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QSequentialAnimationGroup, QTimer,
    QPoint, QAbstractAnimation, Qt, QSettings
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget
from PySide6.QtGui import QPainter, QColor

# Phase 5: Import design tokens for consistent animation timings
from employee_vault.design_tokens import ANIMATIONS, get_animation_duration


class AnimationManager(QObject):
    """
    Centralized animation management system
    
    Features:
    - Performance mode management (high, balanced, power_saver, reduced)
    - System accessibility preference detection
    - Animation presets with consistent timing
    - GPU acceleration hints
    - FPS limiting
    """
    
    # Animation performance modes
    HIGH_PERFORMANCE = "high"
    BALANCED = "balanced"
    POWER_SAVER = "power_saver"
    REDUCED_MOTION = "reduced"
    
    # Phase 5: Animation durations from design tokens (milliseconds)
    DURATION_INSTANT = int(ANIMATIONS['duration_instant'])
    DURATION_FAST = int(ANIMATIONS['duration_fast'])
    DURATION_NORMAL = int(ANIMATIONS['duration_normal'])
    DURATION_SLOW = int(ANIMATIONS['duration_slow'])
    DURATION_SLOWER = int(ANIMATIONS['duration_slower'])

    # Specific use case durations
    DURATION_HOVER = int(ANIMATIONS['hover'])
    DURATION_PRESS = int(ANIMATIONS['press'])
    DURATION_EXPAND = int(ANIMATIONS['expand'])
    DURATION_DIALOG = int(ANIMATIONS['dialog'])
    DURATION_PAGE = int(ANIMATIONS['page'])
    
    # Easing curves
    EASE_IN_OUT = QEasingCurve.InOutQuad
    EASE_OUT = QEasingCurve.OutCubic
    EASE_IN = QEasingCurve.InCubic
    EASE_BOUNCE = QEasingCurve.OutBounce
    EASE_ELASTIC = QEasingCurve.OutElastic
    EASE_BACK = QEasingCurve.OutBack
    
    animation_started = Signal(str)
    animation_finished = Signal(str)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True

        # Load settings
        self.settings = QSettings("EmployeeVault", "Animations")
        self.performance_mode = self.settings.value("performance_mode", self.BALANCED)
        self.animations_enabled = self.settings.value("animations_enabled", True, type=bool)

        # Detect system preferences
        self.system_reduced_motion = self._detect_reduced_motion()

        # Active animations tracking
        self.active_animations = []

        # FPS limiter
        self.max_fps = 60
        self.frame_time = 1000 / self.max_fps

        # Theme animation profile (will be set by ThemeManager)
        self.theme_profile = None

        logging.info(f"AnimationManager initialized: mode={self.performance_mode}, enabled={self.animations_enabled}, reduced_motion={self.system_reduced_motion}")
    
    def _detect_reduced_motion(self) -> bool:
        """Detect if system has 'Reduce Motion' preference enabled"""
        try:
            # Windows: Check SystemParametersInfo
            import ctypes
            SPI_GETCLIENTAREAANIMATION = 0x1042
            animation_enabled = ctypes.c_int()
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(animation_enabled), 0
            )
            return animation_enabled.value == 0
        except Exception as e:
            logging.debug(f"Could not detect reduced motion preference: {e}")
            return False
    
    def should_animate(self, animation_type: str = "default") -> bool:
        """
        Determine if animation should be played based on settings and performance
        
        Args:
            animation_type: Type of animation (micro, transition, effect, heavy)
        
        Returns:
            True if animation should play
        """
        if not self.animations_enabled:
            return False
        
        if self.system_reduced_motion:
            return False
        
        if self.performance_mode == self.REDUCED_MOTION:
            return False
        
        if self.performance_mode == self.POWER_SAVER:
            # Only allow micro-interactions
            return animation_type == "micro"
        
        if self.performance_mode == self.BALANCED:
            # Skip heavy effects
            if animation_type == "heavy":
                return False
        
        return True
    
    def get_duration(self, base_duration: int) -> int:
        """
        Get animation duration based on performance mode
        
        Args:
            base_duration: Requested duration in milliseconds
        
        Returns:
            Adjusted duration
        """
        if not self.should_animate():
            return 0
        
        if self.performance_mode == self.POWER_SAVER:
            return base_duration // 2
        
        return base_duration
    
    def set_performance_mode(self, mode: str):
        """Set animation performance mode"""
        if mode in [self.HIGH_PERFORMANCE, self.BALANCED, self.POWER_SAVER, self.REDUCED_MOTION]:
            self.performance_mode = mode
            self.settings.setValue("performance_mode", mode)
            logging.info(f"Animation performance mode set to: {mode}")
    
    def set_animations_enabled(self, enabled: bool):
        """Enable or disable all animations"""
        self.animations_enabled = enabled
        self.settings.setValue("animations_enabled", enabled)
        logging.info(f"Animations {'enabled' if enabled else 'disabled'}")

    def set_theme_profile(self, profile):
        """Set the current theme's animation profile"""
        self.theme_profile = profile
        logging.info(f"Animation profile updated for theme")

    def get_theme_duration(self, animation_type: str = "transition") -> int:
        """Get duration from theme profile, fallback to defaults"""
        if not self.theme_profile:
            return self.DURATION_NORMAL

        if animation_type == "transition":
            return self.get_duration(self.theme_profile.transition_duration)
        elif animation_type == "hover":
            return self.get_duration(self.theme_profile.hover_duration)
        elif animation_type == "click":
            return self.get_duration(self.theme_profile.click_duration)
        else:
            return self.DURATION_NORMAL

    def get_theme_easing(self) -> QEasingCurve:
        """Get easing curve from theme profile"""
        if not self.theme_profile:
            return self.EASE_IN_OUT
        return self.theme_profile.easing_curve
    
    def create_fade_animation(self, widget: QWidget, start_opacity: float = 0.0,
                            end_opacity: float = 1.0, duration: int = None) -> QPropertyAnimation:
        """Create fade in/out animation"""
        if duration is None:
            duration = self.get_theme_duration("transition")

        duration = self.get_duration(duration)

        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(self.get_theme_easing())

        return animation
    
    def create_slide_animation(self, widget: QWidget, start_pos: QPoint,
                              end_pos: QPoint, duration: int = None) -> QPropertyAnimation:
        """Create slide animation"""
        if duration is None:
            duration = self.get_theme_duration("transition")

        duration = self.get_duration(duration)

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(self.get_theme_easing())

        return animation
    
    def create_scale_animation(self, widget: QWidget, start_scale: float = 0.8,
                              end_scale: float = 1.0, duration: int = None) -> QPropertyAnimation:
        """Create scale animation (requires geometry changes)"""
        if duration is None:
            duration = self.DURATION_NORMAL
        
        duration = self.get_duration(duration)
        
        # Scale using geometry
        original_geometry = widget.geometry()
        
        start_width = int(original_geometry.width() * start_scale)
        start_height = int(original_geometry.height() * start_scale)
        
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(widget.geometry().adjusted(
            (original_geometry.width() - start_width) // 2,
            (original_geometry.height() - start_height) // 2,
            -(original_geometry.width() - start_width) // 2,
            -(original_geometry.height() - start_height) // 2
        ))
        animation.setEndValue(original_geometry)
        animation.setEasingCurve(self.EASE_OUT)
        
        return animation
    
    def create_parallel_group(self, animations: list) -> QParallelAnimationGroup:
        """Create group of animations that play simultaneously"""
        group = QParallelAnimationGroup()
        for anim in animations:
            if anim:
                group.addAnimation(anim)
        return group
    
    def create_sequential_group(self, animations: list) -> QSequentialAnimationGroup:
        """Create group of animations that play in sequence"""
        group = QSequentialAnimationGroup()
        for anim in animations:
            if anim:
                group.addAnimation(anim)
        return group
    
    def animate_widget_fade_in(self, widget: QWidget, duration: int = None, 
                               delay: int = 0, callback: Callable = None):
        """Convenience method to fade in a widget"""
        if not self.should_animate("transition"):
            widget.show()
            if callback:
                callback()
            return
        
        if duration is None:
            duration = self.DURATION_FAST
        
        animation = self.create_fade_animation(widget, 0.0, 1.0, duration)
        
        if callback:
            animation.finished.connect(callback)
        
        if delay > 0:
            QTimer.singleShot(delay, animation.start)
        else:
            animation.start(QAbstractAnimation.DeleteWhenStopped)
    
    def animate_widget_slide_in(self, widget: QWidget, direction: str = "bottom",
                                distance: int = 50, duration: int = None, callback: Callable = None):
        """
        Slide widget into view
        
        Args:
            widget: Widget to animate
            direction: Direction to slide from (top, bottom, left, right)
            distance: Distance to slide in pixels
            duration: Animation duration
            callback: Function to call when done
        """
        if not self.should_animate("transition"):
            widget.show()
            if callback:
                callback()
            return
        
        if duration is None:
            duration = self.DURATION_NORMAL
        
        end_pos = widget.pos()
        
        if direction == "bottom":
            start_pos = QPoint(end_pos.x(), end_pos.y() + distance)
        elif direction == "top":
            start_pos = QPoint(end_pos.x(), end_pos.y() - distance)
        elif direction == "left":
            start_pos = QPoint(end_pos.x() - distance, end_pos.y())
        else:  # right
            start_pos = QPoint(end_pos.x() + distance, end_pos.y())
        
        widget.move(start_pos)
        animation = self.create_slide_animation(widget, start_pos, end_pos, duration)
        
        if callback:
            animation.finished.connect(callback)
        
        animation.start(QAbstractAnimation.DeleteWhenStopped)
    
    def animate_staggered_list(self, widgets: list, delay_between: int = 50, 
                               animation_type: str = "fade"):
        """
        Animate list of widgets with stagger effect
        
        Args:
            widgets: List of widgets to animate
            delay_between: Delay between each widget animation (ms)
            animation_type: Type of animation (fade, slide)
        """
        if not self.should_animate("transition"):
            for widget in widgets:
                widget.show()
            return
        
        for i, widget in enumerate(widgets):
            delay = i * delay_between
            
            if animation_type == "fade":
                self.animate_widget_fade_in(widget, delay=delay)
            elif animation_type == "slide":
                self.animate_widget_slide_in(widget, delay=delay)
    
    def get_status(self) -> dict:
        """Get current animation manager status"""
        return {
            "enabled": self.animations_enabled,
            "performance_mode": self.performance_mode,
            "system_reduced_motion": self.system_reduced_motion,
            "active_animations": len(self.active_animations),
            "max_fps": self.max_fps
        }


# Global instance
_animation_manager = None

def get_animation_manager() -> AnimationManager:
    """Get global animation manager instance"""
    global _animation_manager
    if _animation_manager is None:
        _animation_manager = AnimationManager()
    return _animation_manager
