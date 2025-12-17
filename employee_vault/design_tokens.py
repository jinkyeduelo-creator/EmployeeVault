"""
Design Tokens for Employee Vault
================================
Centralized design system with colors, typography, spacing, shadows, and animations.
This file defines all visual constants used throughout the application.

Usage:
    from employee_vault.design_tokens import TOKENS, get_semantic_color
"""

# ============================================================================
# COLOR PALETTE - Professional, Muted Tones
# ============================================================================

# Base colors - Dark grey (not pure black) for reduced eye strain
COLORS = {
    # Background hierarchy (darkest to lightest)
    "bg_darkest": "#121418",      # Deepest background
    "bg_dark": "#1a1d23",         # Main app background  
    "bg_base": "#22262e",         # Card/surface background
    "bg_elevated": "#2a2f38",     # Elevated surfaces (modals, dropdowns)
    "bg_hover": "#323842",        # Hover state background
    
    # Text colors with proper contrast ratios
    "text_primary": "#e8eaed",    # Primary text (high contrast)
    "text_secondary": "#9aa0a6",  # Secondary/muted text
    "text_tertiary": "#6e7681",   # Hints, placeholders
    "text_disabled": "#484f58",   # Disabled text
    
    # Border colors
    "border_subtle": "#2d333b",   # Subtle borders
    "border_default": "#373e47",  # Default borders
    "border_strong": "#444c56",   # Emphasized borders
    
    # Primary accent - Muted professional blue
    "primary": "#4a8fd9",         # Main accent (desaturated from #4a9eff)
    "primary_hover": "#5a9fe9",
    "primary_muted": "#3a7fc9",
    "primary_subtle": "rgba(74, 143, 217, 0.15)",
    
    # Sidebar section colors - Muted, professional
    "section_main": "#5b8ec9",    # Blue - Main (desaturated from #4a9eff)
    "section_docs": "#5a9a6a",    # Green - Documents (desaturated from #4caf50)
    "section_data": "#c9943a",    # Amber - Data (desaturated from #ff9800)
    "section_admin": "#c95a5a",   # Red - Admin (desaturated from #f44336)
    "section_settings": "#8a5aaa", # Purple - Settings (desaturated from #9c27b0)
    
    # Semantic status colors
    "success": "#3d9a5f",         # Green - Active, Success
    "success_subtle": "rgba(61, 154, 95, 0.15)",
    
    "warning": "#c9943a",         # Amber - Expiring Soon, Warnings
    "warning_subtle": "rgba(201, 148, 58, 0.15)",
    
    "error": "#c95a5a",           # Red - Expired, Errors, Destructive
    "error_subtle": "rgba(201, 90, 90, 0.15)",
    
    "info": "#5b8ec9",            # Blue - Information
    "info_subtle": "rgba(91, 142, 201, 0.15)",
    
    # Special status colors for employee statuses
    "status_active": "#3d9a5f",        # Still working - Green
    "status_expiring": "#c9943a",      # Expiring soon - Amber (NOT red)
    "status_expired": "#c95a5a",       # Expired - Red
    "status_resigned": "#6e7681",      # Resigned - Grey
    "status_probation": "#5b8ec9",     # Probation - Blue
    # Button text on primary
    "text_on_primary": "#ffffff",
    # Error dialog text
    "text_on_error": "#ffffff",
}

# ============================================================================
# TYPOGRAPHY SCALE
# ============================================================================

TYPOGRAPHY = {
    # Font family
    "font_family": "'Segoe UI', 'Inter', 'SF Pro Display', -apple-system, sans-serif",
    
    # Size scale (in pixels)
    "size_xxs": "10px",       # Tiny labels, badges
    "size_xs": "11px",        # Helper text, hints, timestamps
    "size_sm": "12px",        # Secondary labels, table meta
    "size_base": "13px",      # Body text, form labels, table rows
    "size_md": "14px",        # Card titles, menu items
    "size_lg": "16px",        # Section headers, dialog titles
    "size_xl": "18px",        # Page titles
    "size_xxl": "20px",       # Main headings
    
    # Font weights
    "weight_normal": "400",
    "weight_medium": "500",
    "weight_semibold": "600",
    "weight_bold": "700",
    
    # Line heights
    "line_height_tight": "1.25",
    "line_height_normal": "1.45",
    "line_height_relaxed": "1.6",
    
    # Letter spacing
    "letter_spacing_tight": "-0.01em",
    "letter_spacing_normal": "0",
    "letter_spacing_wide": "0.02em",
}

# ============================================================================
# SPACING SCALE (based on 4px grid)
# ============================================================================

SPACING = {
    "xxs": "2px",
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "base": "16px",
    "lg": "20px",
    "xl": "24px",
    "xxl": "32px",
    "xxxl": "48px",
}

# ============================================================================
# BORDER RADIUS
# ============================================================================

RADII = {
    "none": "0",
    "sm": "4px",      # Small elements (chips, badges)
    "md": "6px",      # Buttons, inputs
    "lg": "8px",      # Cards, dialogs
    "xl": "12px",     # Large cards, modals
    "full": "9999px", # Pills, avatars
}

# ============================================================================
# SHADOWS (Subtle, professional)
# ============================================================================

SHADOWS = {
    "none": "none",
    
    # Subtle elevation
    "xs": "0 1px 2px rgba(0, 0, 0, 0.15)",
    
    # Default card shadow
    "sm": "0 2px 4px rgba(0, 0, 0, 0.2)",
    
    # Elevated elements
    "md": "0 4px 8px rgba(0, 0, 0, 0.25)",
    
    # Modals, dropdowns
    "lg": "0 8px 16px rgba(0, 0, 0, 0.3)",
    
    # Focused/Active elements
    "xl": "0 12px 24px rgba(0, 0, 0, 0.35)",
    
    # Inner shadows for pressed states
    "inner_sm": "inset 0 1px 2px rgba(0, 0, 0, 0.2)",
    "inner_md": "inset 0 2px 4px rgba(0, 0, 0, 0.25)",
    
    # Focus ring (subtle glow)
    "focus": "0 0 0 2px rgba(74, 143, 217, 0.4)",
}

# ============================================================================
# ANIMATION TIMING
# ============================================================================

ANIMATIONS = {
    # Durations (in milliseconds) - Optimized for 2025 snappy feel
    "duration_instant": "0",      # Truly instant (was 50ms)
    "duration_fast": "100",       # Snappier (was 150ms)
    "duration_normal": "150",     # Reduced (was 200ms)
    "duration_slow": "250",       # Faster (was 300ms)
    "duration_slower": "350",     # Reduced (was 400ms)
    
    # Easing curves
    "ease_default": "cubic-bezier(0.4, 0, 0.2, 1)",  # Material standard
    "ease_in": "cubic-bezier(0.4, 0, 1, 1)",
    "ease_out": "cubic-bezier(0, 0, 0.2, 1)",
    "ease_in_out": "cubic-bezier(0.4, 0, 0.2, 1)",
    "ease_bounce": "cubic-bezier(0.34, 1.56, 0.64, 1)",
    
    # Specific use cases
    "hover": "150",      # Button/link hover
    "press": "100",      # Button press
    "expand": "200",     # Sidebar expand/collapse
    "dialog": "250",     # Dialog open/close
    "page": "300",       # Page transitions
}

# ============================================================================
# COMPONENT TOKENS
# ============================================================================

COMPONENTS = {
    # Buttons
    "button_height_sm": "28px",
    "button_height_md": "36px",
    "button_height_lg": "44px",
    "button_padding_sm": "8px 12px",
    "button_padding_md": "10px 16px",
    "button_padding_lg": "12px 24px",
    "button_radius": RADII["md"],
    
    # Inputs
    "input_height": "36px",
    "input_padding": "8px 12px",
    "input_radius": RADII["md"],
    
    # Cards
    "card_padding": SPACING["base"],
    "card_radius": RADII["lg"],
    "card_shadow": SHADOWS["sm"],
    
    # Sidebar
    "sidebar_width_expanded": "260px",
    "sidebar_width_collapsed": "64px",
    "sidebar_item_height": "36px",
    "sidebar_item_padding": "8px 16px",
    
    # Table
    "table_row_height": "44px",
    "table_header_height": "40px",
    "table_cell_padding": "12px 16px",
    
    # Status chips
    "chip_height": "24px",
    "chip_padding": "4px 10px",
    "chip_radius": RADII["sm"],
}

# ============================================================================
# CONSOLIDATED TOKENS OBJECT
# ============================================================================

TOKENS = {
    "colors": COLORS,
    "typography": TYPOGRAPHY,
    "spacing": SPACING,
    "radii": RADII,
    "shadows": SHADOWS,
    "animations": ANIMATIONS,
    "components": COMPONENTS,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_semantic_color(status: str) -> str:
    """
    Get the appropriate color for a semantic status.
    
    Args:
        status: One of 'success', 'warning', 'error', 'info', 
                'active', 'expiring', 'expired', 'resigned', 'probation'
    
    Returns:
        Hex color string
    """
    status_map = {
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "error": COLORS["error"],
        "info": COLORS["info"],
        "active": COLORS["status_active"],
        "expiring": COLORS["status_expiring"],
        "expired": COLORS["status_expired"],
        "resigned": COLORS["status_resigned"],
        "probation": COLORS["status_probation"],
    }
    return status_map.get(status.lower(), COLORS["text_secondary"])


def get_section_color(section: str) -> str:
    """
    Get the appropriate color for a sidebar section.
    
    Args:
        section: One of 'main', 'documents', 'data', 'admin', 'settings'
    
    Returns:
        Hex color string
    """
    section_map = {
        "main": COLORS["section_main"],
        "documents": COLORS["section_docs"],
        "data": COLORS["section_data"],
        "admin": COLORS["section_admin"],
        "settings": COLORS["section_settings"],
    }
    return section_map.get(section.lower(), COLORS["primary"])


def get_animation_duration(type: str = "normal") -> int:
    """
    Get animation duration in milliseconds.
    
    Args:
        type: One of 'instant', 'fast', 'normal', 'slow', 'slower',
              'hover', 'press', 'expand', 'dialog', 'page'
    
    Returns:
        Duration in milliseconds as integer
    """
    return int(ANIMATIONS.get(f"duration_{type}", ANIMATIONS.get(type, ANIMATIONS["duration_normal"])))


# ============================================================================
# CSS GENERATION HELPERS
# ============================================================================

def generate_button_css(variant: str = "primary") -> str:
    """Generate CSS for a button variant."""
    if variant == "primary":
        return f"""
            background: {COLORS['primary']};
            color: {COLORS['text_primary']};
            border: none;
            border-radius: {RADII['md']};
            padding: {COMPONENTS['button_padding_md']};
            font-size: {TYPOGRAPHY['size_base']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        """
    elif variant == "secondary":
        return f"""
            background: transparent;
            color: {COLORS['primary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADII['md']};
            padding: {COMPONENTS['button_padding_md']};
            font-size: {TYPOGRAPHY['size_base']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        """
    elif variant == "danger":
        return f"""
            background: {COLORS['error']};
            color: {COLORS['text_primary']};
            border: none;
            border-radius: {RADII['md']};
            padding: {COMPONENTS['button_padding_md']};
            font-size: {TYPOGRAPHY['size_base']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        """
    return ""


def generate_card_css() -> str:
    """Generate CSS for a standard card."""
    return f"""
        background: {COLORS['bg_base']};
        border: 1px solid {COLORS['border_subtle']};
        border-radius: {RADII['lg']};
        padding: {SPACING['base']};
        box-shadow: {SHADOWS['sm']};
    """


def generate_input_css() -> str:
    """Generate CSS for an input field."""
    return f"""
        background: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: {RADII['md']};
        padding: {COMPONENTS['input_padding']};
        font-size: {TYPOGRAPHY['size_base']};
    """


# Phase 4: Modern interaction state helpers
def generate_button_states_css(bg_color: str, hover_lightness: float = 1.1, pressed_lightness: float = 0.9) -> str:
    """Generate consistent hover/pressed states for buttons.

    Args:
        bg_color: Base background color (hex)
        hover_lightness: Multiplier for hover (>1 = lighter, <1 = darker)
        pressed_lightness: Multiplier for pressed (typically <1 for darker)

    Returns:
        CSS string with :hover and :pressed states
    """
    return f"""
        QPushButton {{
            transition: all {ANIMATIONS['hover']}ms {ANIMATIONS['ease_default']};
        }}
        QPushButton:hover {{
            transform: translateY(-1px);
            box-shadow: {SHADOWS['md']};
        }}
        QPushButton:pressed {{
            transform: translateY(0px);
            box-shadow: {SHADOWS['inner_sm']};
        }}
        QPushButton:focus {{
            outline: none;
            box-shadow: {SHADOWS['focus']};
        }}
    """


def generate_modern_focus_ring() -> str:
    """Generate modern focus ring styling."""
    return f"""
        outline: none;
        box-shadow: {SHADOWS['focus']};
        border-color: {COLORS['primary']};
    """
