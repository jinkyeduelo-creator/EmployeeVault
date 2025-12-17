"""
iOS Frosted Glass Button Styles
Theme-adaptive button styling with light/dark mode support
Maintains frosted glass effect while adapting to theme colors
"""

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def darken_color(rgb, factor=0.8):
    """Darken an RGB color"""
    return tuple(int(c * factor) for c in rgb)

def lighten_color(rgb, factor=1.2):
    """Lighten an RGB color"""
    return tuple(min(255, int(c * factor)) for c in rgb)

def get_ios_frosted_glass_style(theme_colors=None, is_light_mode=False, color_type='primary'):
    """
    Generate theme-adaptive iOS frosted glass button style

    Frosted glass effect remains constant:
    - Semi-transparent gradient background
    - Layered border with light/dark edges
    - 22px border radius (pill shape)
    - Hover/press animations

    Theme-adaptive elements:
    - Base color from theme_colors (primary/success/warning/error)
    - Text color adapts to light/dark mode
    - Border opacity adapts to light/dark mode
    - Background gradient uses theme colors with transparency

    Args:
        theme_colors: Dict from MODERN_THEMES or MODERN_THEMES_LIGHT (None = default)
        is_light_mode: If True, use light mode styling; if False, use dark mode
        color_type: 'primary', 'success', 'warning', 'danger'

    Returns:
        QString: Complete stylesheet for QPushButton
    """
    # Fallback to default theme if not provided
    if theme_colors is None:
        from employee_vault.config import MODERN_THEMES, MODERN_THEMES_LIGHT
        theme_colors = MODERN_THEMES_LIGHT["default"] if is_light_mode else MODERN_THEMES["default"]

    # Extract theme color for this button type
    if color_type == 'primary':
        base_color = theme_colors.get('primary', '#2196F3')
    elif color_type == 'success':
        base_color = theme_colors.get('success', '#4CAF50')
    elif color_type == 'warning':
        base_color = theme_colors.get('warning', '#FF9800')
    elif color_type == 'danger':
        base_color = theme_colors.get('error', '#F44336')
    else:
        base_color = theme_colors.get('primary', '#2196F3')

    # Convert hex to RGB
    r, g, b = hex_to_rgb(base_color)

    # Calculate darker/lighter variants
    if is_light_mode:
        dark_r, dark_g, dark_b = darken_color((r, g, b), 0.85)
        darker_r, darker_g, darker_b = darken_color((r, g, b), 0.7)
    else:
        dark_r, dark_g, dark_b = darken_color((r, g, b), 0.8)
        darker_r, darker_g, darker_b = darken_color((r, g, b), 0.65)

    # Light mode uses darker borders and less transparency
    # Dark mode uses lighter borders and more transparency
    if is_light_mode:
        border_opacity_top = 0.4
        border_opacity_sides = 0.3
        border_opacity_bottom = 0.2
        bg_start = 0.12
        bg_mid = 0.35
        bg_end = 0.55
        hover_start = 0.18
        hover_mid = 0.45
        hover_end = 0.65
        text_color = "rgba(255, 255, 255, 0.95)"
        disabled_bg = "rgba(200, 200, 200, 0.4)"
        disabled_text = "rgba(100, 100, 100, 0.6)"
    else:
        border_opacity_top = 0.5
        border_opacity_sides = 0.3
        border_opacity_bottom = 0.1
        bg_start = 0.15
        bg_mid = 0.3
        bg_end = 0.6
        hover_start = 0.25
        hover_mid = 0.4
        hover_end = 0.7
        text_color = "white"
        disabled_bg = "rgba(158, 158, 158, 0.3)"
        disabled_text = "rgba(255, 255, 255, 0.4)"

    return f"""
        QPushButton {{
            text-align: center;
            padding: 10px 24px;
            font-weight: 600;
            font-size: 14px;
            color: {text_color};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 rgba(255, 255, 255, {bg_start}),
                                       stop:0.5 rgba({r}, {g}, {b}, {bg_mid}),
                                       stop:1 rgba({dark_r}, {dark_g}, {dark_b}, {bg_end}));
            border-top: 1.5px solid rgba(255, 255, 255, {border_opacity_top});
            border-left: 1px solid rgba(255, 255, 255, {border_opacity_sides});
            border-right: 1px solid rgba(255, 255, 255, {border_opacity_bottom});
            border-bottom: 1px solid rgba(255, 255, 255, {border_opacity_bottom});
            border-radius: 22px;
            margin: 3px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 rgba(255, 255, 255, {hover_start}),
                                       stop:0.5 rgba({r}, {g}, {b}, {hover_mid}),
                                       stop:1 rgba({dark_r}, {dark_g}, {dark_b}, {hover_end}));
            border-top: 1.5px solid rgba(255, 255, 255, {border_opacity_top + 0.1});
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 rgba({dark_r}, {dark_g}, {dark_b}, 0.5),
                                       stop:1 rgba({darker_r}, {darker_g}, {darker_b}, 0.8));
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }}
        QPushButton:disabled {{
            background: {disabled_bg};
            color: {disabled_text};
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }}
    """

def apply_ios_style(button, color_type='primary', theme_colors=None, is_light_mode=False):
    """
    Apply iOS frosted glass style to a button

    Args:
        button: QPushButton instance
        color_type: 'primary', 'success', 'warning', 'danger'
        theme_colors: Dict from MODERN_THEMES/MODERN_THEMES_LIGHT (None = auto-detect)
        is_light_mode: If True, use light mode; if False, use dark mode
    """
    # Auto-detect theme if not provided
    if theme_colors is None:
        try:
            from employee_vault.ui.theme_manager import get_theme_manager
            theme_mgr = get_theme_manager()
            # Get current theme colors will be implemented in ThemeManager
            # For now, use default
            from employee_vault.config import MODERN_THEMES, MODERN_THEMES_LIGHT
            theme_colors = MODERN_THEMES_LIGHT["default"] if is_light_mode else MODERN_THEMES["default"]
        except:
            from employee_vault.config import MODERN_THEMES, MODERN_THEMES_LIGHT
            theme_colors = MODERN_THEMES_LIGHT["default"] if is_light_mode else MODERN_THEMES["default"]

    button.setStyleSheet(get_ios_frosted_glass_style(theme_colors, is_light_mode, color_type))

# Backward compatibility: support old color parameter
def apply_ios_style_legacy(button, color='blue'):
    """
    Legacy function for backward compatibility
    Maps old color names to new color_type system
    """
    color_map = {
        'blue': 'primary',
        'green': 'success',
        'orange': 'warning',
        'red': 'danger',
        'gray': 'primary',
        'purple': 'primary'
    }
    apply_ios_style(button, color_type=color_map.get(color, 'primary'))
