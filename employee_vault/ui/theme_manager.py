"""
Theme Manager for EmployeeVault
Handles dark/light mode with system theme detection
Integrated with MODERN_THEMES color palette system
Includes theme-specific animation profiles
"""

import os
import json
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from employee_vault.ui.theme_animation_profiles import get_theme_animation_profile


class ThemeManager(QObject):
    """
    Manages application themes with system detection
    Supports light, dark, and auto modes
    Integrates with MODERN_THEMES color palette system
    """

    # Signals
    theme_changed = Signal(str)  # Emitted when theme changes

    # Theme modes
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

    def __init__(self):
        super().__init__()
        self.current_theme = self.load_preference()
        self.current_applied = None
        self.current_color_theme = self.load_color_theme_preference()
        self.sync_with_windows = self.load_sync_preference()
        self.animation_profile = get_theme_animation_profile(self.current_color_theme)

    def load_preference(self):
        """Load theme preference (light/dark/auto) from file"""
        try:
            if os.path.exists("theme_mode_preference.txt"):
                with open("theme_mode_preference.txt", "r") as f:
                    theme = f.read().strip()
                    if theme in [self.LIGHT, self.DARK, self.AUTO]:
                        return theme
        except:
            pass
        return self.AUTO  # Default to auto

    def save_preference(self, theme):
        """Save theme preference to file"""
        try:
            with open("theme_mode_preference.txt", "w") as f:
                f.write(theme)
        except:
            pass

    def load_color_theme_preference(self):
        """Load color theme (default, cyberpunk, etc.) from file"""
        try:
            if os.path.exists("theme_preference.txt"):
                with open("theme_preference.txt", "r") as f:
                    theme = f.read().strip()
                    # Validate theme exists
                    from employee_vault.config import MODERN_THEMES
                    if theme in MODERN_THEMES:
                        return theme
        except:
            pass
        return "default"

    def save_color_theme_preference(self, theme_name):
        """Save color theme preference to file"""
        try:
            with open("theme_preference.txt", "w") as f:
                f.write(theme_name)
        except:
            pass

    def load_sync_preference(self):
        """Load Windows theme sync preference from settings.json"""
        try:
            import json
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    return settings.get("sync_with_windows_theme", True)
        except:
            pass
        return True  # Default to enabled

    def save_sync_preference(self, enabled: bool):
        """Save Windows theme sync preference to settings.json"""
        try:
            import json
            settings = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
            settings["sync_with_windows_theme"] = enabled
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save sync preference: {e}")

    def set_sync_with_windows(self, enabled: bool):
        """Enable/disable Windows theme synchronization"""
        self.sync_with_windows = enabled
        self.save_sync_preference(enabled)
        if enabled:
            # When enabled, switch to AUTO mode
            self.set_theme(self.AUTO)
        self.apply_theme()

    @staticmethod
    def is_system_dark_mode():
        """Detect if system is using dark mode (Windows)"""
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(
                registry,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            return value == 0  # 0 = dark mode, 1 = light mode
        except:
            # Default to dark if can't detect
            return True

    def get_active_theme(self):
        """Get the currently active theme mode (always returns DARK for glassmorphism design)"""
        # FORCE DARK MODE: The app's glassmorphism UI is designed for dark backgrounds
        # Light mode makes white text on white background unreadable
        # Users can still select color themes, but base mode stays dark
        return self.DARK

    def get_current_theme_colors(self):
        """Get the current theme's color dict"""
        from employee_vault.config import MODERN_THEMES, MODERN_THEMES_LIGHT

        is_light = self.get_active_theme() == self.LIGHT
        theme_dict = MODERN_THEMES_LIGHT if is_light else MODERN_THEMES

        return theme_dict.get(self.current_color_theme, theme_dict["default"])

    def set_theme(self, theme):
        """Set theme mode (light/dark/auto) and apply to application"""
        if theme not in [self.LIGHT, self.DARK, self.AUTO]:
            return

        self.current_theme = theme
        self.save_preference(theme)
        self.apply_theme()

    def set_color_theme(self, theme_name):
        """Set color theme (default, cyberpunk, nord, etc.) and apply"""
        from employee_vault.config import MODERN_THEMES

        if theme_name not in MODERN_THEMES:
            return

        self.current_color_theme = theme_name
        self.save_color_theme_preference(theme_name)
        # Update animation profile when theme changes
        self.animation_profile = get_theme_animation_profile(theme_name)
        self.apply_theme()

    def toggle_theme(self):
        """Toggle between light and dark modes"""
        active = self.get_active_theme()
        if active == self.DARK:
            self.set_theme(self.LIGHT)
        else:
            self.set_theme(self.DARK)

    def apply_theme(self):
        """Apply the current theme to the application with smooth transition"""
        from employee_vault.config import get_modern_stylesheet
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve

        active = self.get_active_theme()
        is_light = active == self.LIGHT

        # Use get_modern_stylesheet with current color theme and light/dark mode
        stylesheet = get_modern_stylesheet(self.current_color_theme, is_light)

        # Use theme-specific animation duration and easing curve
        transition_duration = self.animation_profile.transition_duration
        easing = self.animation_profile.easing_curve

        app = QApplication.instance()
        if app:
            # Animate theme transition with fade effect
            # Get all top-level windows
            windows = app.topLevelWidgets()
            
            for window in windows:
                if not window.isVisible():
                    continue
                
                # Create opacity effect if not exists
                if not window.graphicsEffect():
                    opacity_effect = QGraphicsOpacityEffect(window)
                    window.setGraphicsEffect(opacity_effect)
                else:
                    opacity_effect = window.graphicsEffect()
                
                # Create fade out -> change theme -> fade in sequence using theme-specific timing
                fade_out = QPropertyAnimation(opacity_effect, b"opacity")
                fade_out.setDuration(transition_duration // 2)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.7)
                fade_out.setEasingCurve(easing)

                fade_in = QPropertyAnimation(opacity_effect, b"opacity")
                fade_in.setDuration(transition_duration // 2)
                fade_in.setStartValue(0.7)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(easing)
                
                # Apply new stylesheet between animations
                def apply_new_style():
                    app.setStyleSheet(stylesheet)
                    fade_in.start()
                
                fade_out.finished.connect(apply_new_style)
                fade_out.start()
                
                # Only animate first window to avoid performance hit
                break
            
            # If no windows animated, apply directly
            if not windows or not any(w.isVisible() for w in windows):
                app.setStyleSheet(stylesheet)

        self.current_applied = active

    def get_animation_profile(self):
        """Get the current theme's animation profile"""
        return self.animation_profile

    # Legacy methods for backward compatibility (now use MODERN_THEMES)
    def get_dark_stylesheet(self):
        """Legacy: Get dark mode stylesheet (redirects to get_modern_stylesheet)"""
        from employee_vault.config import get_modern_stylesheet
        return get_modern_stylesheet(self.current_color_theme, is_light_mode=False)

    def get_light_stylesheet(self):
        """Legacy: Get light mode stylesheet (redirects to get_modern_stylesheet)"""
        from employee_vault.config import get_modern_stylesheet
        return get_modern_stylesheet(self.current_color_theme, is_light_mode=True)


# Global theme manager instance
_theme_manager = None

def get_theme_manager():
    """Get or create the global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
