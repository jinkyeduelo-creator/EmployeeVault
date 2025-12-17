"""
Glassmorphism Theme Constants
Shared styling values for consistent iOS-style frosted glass UI elements
"""

from PySide6.QtGui import QColor

# === BORDER COLORS ===
# Primary gradient colors for animated borders and accents
GLASS_BORDER_PRIMARY = QColor(74, 158, 255)      # Blue (#4a9eff)
GLASS_BORDER_ACCENT = QColor(156, 39, 176)       # Purple (#9c27b0)

# === BACKGROUND COLORS ===
# Dual-layer background for depth effect
GLASS_BG_OUTER = QColor(20, 25, 45, 235)         # Dark blue-gray, semi-transparent
GLASS_BG_INNER = QColor(30, 35, 50, 200)         # Slightly lighter, more transparent

# === BORDER PROPERTIES ===
GLASS_BORDER_WIDTH = 2.5                          # Border thickness in pixels
GLASS_BORDER_OPACITY = 0.85                       # Border color opacity (85%)

# === CORNER RADIUS ===
GLASS_CARD_RADIUS = 24                            # Border radius for cards
GLASS_INPUT_RADIUS = 20                           # Border radius for input fields
GLASS_BUTTON_RADIUS = 22                          # Border radius for buttons

# === SPACING & LAYOUT ===
GLASS_CARD_PADDING = 20                           # Inner padding for cards
GLASS_CARD_MARGIN = 15                            # Margin between cards

# === STATUS COLORS ===
# Color palette for different card types and states
GLASS_COLOR_INFO = QColor(33, 150, 243)          # Blue - informational (#2196F3)
GLASS_COLOR_SUCCESS = QColor(76, 175, 80)        # Green - success/active (#4CAF50)
GLASS_COLOR_WARNING = QColor(255, 152, 0)        # Orange - warning/expiring (#FF9800)
GLASS_COLOR_ERROR = QColor(244, 67, 54)          # Red - error/critical (#F44336)

# === RGBA STRING HELPERS ===
# Pre-formatted RGBA strings for use in stylesheets

def glass_rgba(color: QColor, alpha: float = None) -> str:
    """Convert QColor to rgba() string for stylesheets"""
    if alpha is not None:
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"
    else:
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alphaF()})"

# Background layers
BG_OUTER_RGBA = glass_rgba(GLASS_BG_OUTER)
BG_INNER_RGBA = glass_rgba(GLASS_BG_INNER)

# Border colors at standard opacity
BORDER_PRIMARY_RGBA = glass_rgba(GLASS_BORDER_PRIMARY, GLASS_BORDER_OPACITY)
BORDER_ACCENT_RGBA = glass_rgba(GLASS_BORDER_ACCENT, GLASS_BORDER_OPACITY)

# Status colors with various opacities for backgrounds
INFO_BG_LIGHT = glass_rgba(GLASS_COLOR_INFO, 0.15)
INFO_BG_MID = glass_rgba(GLASS_COLOR_INFO, 0.25)
INFO_BG_DARK = glass_rgba(GLASS_COLOR_INFO, 0.35)
INFO_BORDER = glass_rgba(GLASS_COLOR_INFO, 0.5)

SUCCESS_BG_LIGHT = glass_rgba(GLASS_COLOR_SUCCESS, 0.15)
SUCCESS_BG_MID = glass_rgba(GLASS_COLOR_SUCCESS, 0.25)
SUCCESS_BG_DARK = glass_rgba(GLASS_COLOR_SUCCESS, 0.35)
SUCCESS_BORDER = glass_rgba(GLASS_COLOR_SUCCESS, 0.5)

WARNING_BG_LIGHT = glass_rgba(GLASS_COLOR_WARNING, 0.15)
WARNING_BG_MID = glass_rgba(GLASS_COLOR_WARNING, 0.25)
WARNING_BG_DARK = glass_rgba(GLASS_COLOR_WARNING, 0.35)
WARNING_BORDER = glass_rgba(GLASS_COLOR_WARNING, 0.5)

ERROR_BG_LIGHT = glass_rgba(GLASS_COLOR_ERROR, 0.15)
ERROR_BG_MID = glass_rgba(GLASS_COLOR_ERROR, 0.25)
ERROR_BG_DARK = glass_rgba(GLASS_COLOR_ERROR, 0.35)
ERROR_BORDER = glass_rgba(GLASS_COLOR_ERROR, 0.5)

# === COMMON STYLESHEET SNIPPETS ===

GLASS_CARD_BASE_STYLE = f"""
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255, 255, 255, 0.12),
        stop:1 rgba(255, 255, 255, 0.08));
    border: {GLASS_BORDER_WIDTH}px solid rgba(255, 255, 255, 0.2);
    border-radius: {GLASS_CARD_RADIUS}px;
    padding: {GLASS_CARD_PADDING}px;
"""

GLASS_HOVER_EFFECT = """
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255, 255, 255, 0.18),
        stop:1 rgba(255, 255, 255, 0.12));
    border: 2px solid rgba(255, 255, 255, 0.4);
"""

# === ANIMATION CONSTANTS ===
GLASS_ANIM_DURATION = 180                         # Animation duration in milliseconds
GLASS_HOVER_SCALE = 1.02                          # Scale factor on hover (2% increase)
GLASS_BORDER_ROTATION_SPEED = 0.8                 # Degrees per frame for rotating border

# === INPUT FIELD STYLES ===
INPUT_BG_BASE = "rgba(255, 255, 255, 0.08)"
INPUT_BG_HOVER = "rgba(255, 255, 255, 0.12)"
INPUT_BG_FOCUS = glass_rgba(GLASS_BORDER_PRIMARY, 0.15)
INPUT_BORDER_BASE = "rgba(255, 255, 255, 0.2)"
INPUT_BORDER_HOVER = "rgba(255, 255, 255, 0.3)"
INPUT_BORDER_FOCUS = glass_rgba(GLASS_BORDER_PRIMARY, 0.8)

# === BUTTON STYLES ===
BUTTON_BG_GRADIENT_START = "rgba(255, 255, 255, 0.18)"
BUTTON_BG_GRADIENT_MID = "rgba(255, 255, 255, 0.12)"
BUTTON_BG_GRADIENT_END = "rgba(255, 255, 255, 0.08)"
BUTTON_BORDER_TOP = "rgba(255, 255, 255, 0.5)"
BUTTON_BORDER_SIDES = "rgba(255, 255, 255, 0.25)"

# === SIDEBAR STYLES ===
SIDEBAR_HEADER_PADDING_V = 12                     # Vertical padding for section headers
SIDEBAR_HEADER_PADDING_H = 16                     # Horizontal padding for section headers
SIDEBAR_ITEM_PADDING_V = 10                       # Vertical padding for child items
SIDEBAR_ITEM_PADDING_L = 32                       # Left padding for child items (indented)
SIDEBAR_ICON_SIZE = 16                            # Icon size in pixels
SIDEBAR_ICON_TEXT_GAP = 12                        # Gap between icon and text
SIDEBAR_LINE_HEIGHT = 1.4                         # Line height multiplier

SIDEBAR_ACTIVE_OPACITY = 1.0                      # Active section gradient opacity
SIDEBAR_INACTIVE_OPACITY = 0.7                    # Inactive section gradient opacity
SIDEBAR_HOVER_OPACITY = 0.85                      # Hover state gradient opacity

# === ACCESSIBILITY ===
WCAG_MIN_CONTRAST = 4.5                          # WCAG AA minimum contrast ratio

def get_glass_card_style(color_type: str = "info", hover: bool = False) -> str:
    """
    Generate a complete glassmorphism card style

    Args:
        color_type: One of "info", "success", "warning", "error"
        hover: Whether to include hover state

    Returns:
        CSS stylesheet string
    """
    color_map = {
        "info": (INFO_BG_LIGHT, INFO_BG_MID, INFO_BG_DARK, INFO_BORDER),
        "success": (SUCCESS_BG_LIGHT, SUCCESS_BG_MID, SUCCESS_BG_DARK, SUCCESS_BORDER),
        "warning": (WARNING_BG_LIGHT, WARNING_BG_MID, WARNING_BG_DARK, WARNING_BORDER),
        "error": (ERROR_BG_LIGHT, ERROR_BG_MID, ERROR_BG_DARK, ERROR_BORDER),
    }

    bg_light, bg_mid, bg_dark, border = color_map.get(color_type, color_map["info"])

    base_style = f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(255, 255, 255, 0.15),
            stop:0.5 {bg_mid},
            stop:1 {bg_dark});
        border: {GLASS_BORDER_WIDTH}px solid rgba(255, 255, 255, 0.3);
        border-radius: {GLASS_CARD_RADIUS}px;
        padding: {GLASS_CARD_PADDING}px;
    """

    if hover:
        hover_style = f"""
        QFrame:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.22),
                stop:0.5 {bg_mid},
                stop:1 {bg_dark});
            border: 2px solid rgba(255, 255, 255, 0.5);
        }}
        """
        return base_style + hover_style

    return base_style
