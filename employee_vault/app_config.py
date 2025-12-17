"""
Employee Vault Configuration Module
Contains all constants, settings, themes, and helper functions
"""

import os
import re
import sys
import pathlib
import logging
from typing import Tuple
from datetime import datetime
from pathlib import Path
import bcrypt

# ============================================================================
# PATH RESOLUTION FOR PYINSTALLER
# ============================================================================

def get_app_root() -> Path:
    """
    Returns the folder where EmployeeVault.exe lives when frozen,
    or the project root when running from source.
    """
    if getattr(sys, "frozen", False):
        # Running from PyInstaller exe - return exe directory
        return Path(sys.executable).resolve().parent
    else:
        # Running from source: config.py is at employee_vault/config.py
        # Go up one level to project root
        return Path(__file__).resolve().parent.parent

# Application root directory
APP_ROOT = get_app_root()

# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

APP_TITLE = "Cuddly Employees Information"

# Database configuration - Network and Local paths
NETWORK_DB_PATH = r"\\extra\EmployeeVault\employee_vault.db"
LOCAL_DB_PATH = str(APP_ROOT / "employee_vault.db")

# Auto-detect which database to use
if os.path.exists(os.path.dirname(NETWORK_DB_PATH)):
    DB_FILE = NETWORK_DB_PATH
    USE_NETWORK_DB = True
    logging.info(f"Using NETWORK database: {NETWORK_DB_PATH}")
else:
    DB_FILE = LOCAL_DB_PATH
    USE_NETWORK_DB = False
    logging.info(f"Using LOCAL database: {LOCAL_DB_PATH}")

JSON_FALLBACK = str(APP_ROOT / "employees_data.json")
FILES_DIR = str(APP_ROOT / "employee_files")
PHOTOS_DIR = str(APP_ROOT / "employee_photos")
LETTERS_DIR = str(APP_ROOT / "employee_letters")
BACKUPS_DIR = str(APP_ROOT / "backups")
ALERT_DAYS = 30

VERSION = "4.6.0 - PIN Authentication + Network Sync"
BUILD_DATE = "2025-01-13"
DATABASE_VERSION = 7  # v7: Added unique constraints for government IDs

# Table headers for employee list (Photo column added)
HEADERS = ["#", "Photo", "Emp ID", "Name", "Salary", "SSS #", "Department", "Position", "Hire Date", "Agency", "Contract Expiry", "Resign Date", "Status"]

# ID Card Generator availability
ID_CARD_GEN_AVAILABLE = True

# Security questions for password recovery
SECURITY_QUESTIONS = [
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was the name of your first pet?",
    "What is your favorite color?",
    "What was the name of your elementary school?",
    "What is your favorite food?",
    "What was your childhood nickname?",
    "What is the name of your favorite teacher?",
    "What street did you grow up on?",
    "What is your father's middle name?"
]

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_FAILED_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 15

# Database optimization settings
DB_TIMEOUT_SECONDS = 30
DB_MAX_RETRIES = 3
DB_RETRY_DELAYS = [0.1, 0.2, 0.4]

# ============================================================================
# NETWORK/SECURITY GUARD SETTINGS
# ============================================================================

EXPECTED_UNC_PREFIX = r"\\Extra\EmployeeVault"  # Change to your real share

# ============================================================================
# UI CONSTANTS
# ============================================================================

INVALID_QSS = "border: 1px solid #ff4d4f; background: #2b1f1f; border-radius: 10px;"
VALID_QSS = ""

SEED_AGENCIES = ["SUN WU", "PEOPLES LINK", "TDEVS", "VITASTAR", "MHAX RADIANT", "NEXUS"]
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# Theme preference storage
THEME_PREFERENCE_FILE = "theme_preference.txt"

# ============================================================================
# ANIMATION TIMING CONSTANTS (Modernized UX)
# ============================================================================

# Animation Duration (in milliseconds)
ANIMATION_FAST = 150      # Quick feedback (button clicks, hover states)
ANIMATION_NORMAL = 250    # Standard interactions (dialogs, menus, transitions)
ANIMATION_SLOW = 400      # Page transitions, complex animations

# Shadow Elevation Levels (Material Design inspired)
SHADOW_ELEVATIONS = {
    0: {"blur": 0, "offset": 0, "opacity": 0},
    1: {"blur": 3, "offset": 1, "opacity": 0.12},
    2: {"blur": 6, "offset": 2, "opacity": 0.16},
    3: {"blur": 10, "offset": 4, "opacity": 0.19},
    4: {"blur": 14, "offset": 6, "opacity": 0.25},
    5: {"blur": 20, "offset": 8, "opacity": 0.30}
}

# Spacing System (4px grid for consistent layouts)
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 20
SPACING_XXL = 24

# Border Radius (consistency across components)
RADIUS_SMALL = 8
RADIUS_MEDIUM = 12
RADIUS_LARGE = 16
RADIUS_XLARGE = 20
RADIUS_PILL = 24

# Typography Scale
FONT_SIZE_XS = 10
FONT_SIZE_SM = 11
FONT_SIZE_MD = 12
FONT_SIZE_LG = 14
FONT_SIZE_XL = 16
FONT_SIZE_XXL = 18

# Button Heights (consistent across all buttons)
BUTTON_HEIGHT_SMALL = 36
BUTTON_HEIGHT_MEDIUM = 44
BUTTON_HEIGHT_LARGE = 50
BUTTON_HEIGHT_XLARGE = 56

# Input Heights (consistent across all input fields)
INPUT_HEIGHT_SMALL = 36
INPUT_HEIGHT_MEDIUM = 44
INPUT_HEIGHT_LARGE = 50

# Dialog/Window Sizes
DIALOG_WIDTH_SMALL = 400
DIALOG_WIDTH_MEDIUM = 600
DIALOG_WIDTH_LARGE = 800
DIALOG_HEIGHT_SMALL = 300
DIALOG_HEIGHT_MEDIUM = 500
DIALOG_HEIGHT_LARGE = 700

# Calendar Widget Dimensions
CALENDAR_MIN_WIDTH = 380
CALENDAR_MIN_HEIGHT = 350

# Icon Sizes
ICON_SIZE_SMALL = 16
ICON_SIZE_MEDIUM = 24
ICON_SIZE_LARGE = 32
ICON_SIZE_XLARGE = 48

# Opacity Levels
OPACITY_DISABLED = 0.4
OPACITY_MUTED = 0.6
OPACITY_SUBTLE = 0.8
OPACITY_FULL = 1.0

# Z-Index Layers
Z_INDEX_BASE = 0
Z_INDEX_DROPDOWN = 100
Z_INDEX_MODAL = 200
Z_INDEX_POPOVER = 300
Z_INDEX_TOOLTIP = 400
Z_INDEX_NOTIFICATION = 500

# ============================================================================
# THEME SYSTEM
# ============================================================================
# All previous themes removed per user request
# User will provide custom theme definitions later

MODERN_THEMES = {
    "default": {
        "name": "🌙 Dark Blue (Default)",
        "primary": "#2196F3",
        "primary_dark": "#1976D2",
        "primary_light": "#64B5F6",
        "secondary": "#FF9800",
        "accent": "#4CAF50",
        "background": "#1a1a1a",
        "surface": "#242424",
        "surface_variant": "#2d2d2d",
        "bg_primary": "#ffffff",
        "text_primary": "#ffffff",
        "text_secondary": "#b0b0b0",
        "border": "#3a3a3a",
        "hover": "#333333",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
    },
    "cyberpunk": {
        "name": "⚡ Cyberpunk Neon",
        "primary": "#FF00FF",  # Neon magenta
        "primary_dark": "#CC00CC",
        "primary_light": "#FF66FF",
        "secondary": "#00FFFF",  # Neon cyan
        "accent": "#FFFF00",  # Neon yellow
        "background": "#0a0a0a",
        "surface": "#1a1a2e",
        "surface_variant": "#16213e",
        "bg_primary": "#ffffff",
        "text_primary": "#00FFFF",
        "text_secondary": "#FF00FF",
        "border": "#FF00FF",
        "hover": "#2a2a3e",
        "success": "#00FF00",
        "warning": "#FFFF00",
        "error": "#FF0080",
        "info": "#00FFFF",
    },
    "nord": {
        "name": "❄️ Nord Aurora",
        "primary": "#88C0D0",  # Nord frost cyan
        "primary_dark": "#5E81AC",
        "primary_light": "#8FBCBB",
        "secondary": "#EBCB8B",  # Nord aurora yellow
        "accent": "#A3BE8C",  # Nord aurora green
        "background": "#2E3440",  # Nord polar night
        "surface": "#3B4252",
        "surface_variant": "#434C5E",
        "bg_primary": "#ffffff",
        "text_primary": "#ECEFF4",  # Nord snow storm
        "text_secondary": "#D8DEE9",
        "border": "#4C566A",
        "hover": "#434C5E",
        "success": "#A3BE8C",
        "warning": "#EBCB8B",
        "error": "#BF616A",  # Nord aurora red
        "info": "#88C0D0",
    },
    "dracula": {
        "name": "🧛 Dracula Purple",
        "primary": "#BD93F9",  # Dracula purple
        "primary_dark": "#9966CC",
        "primary_light": "#D4B3FF",
        "secondary": "#FF79C6",  # Dracula pink
        "accent": "#50FA7B",  # Dracula green
        "background": "#282A36",  # Dracula background
        "surface": "#343746",
        "surface_variant": "#44475A",
        "bg_primary": "#ffffff",
        "text_primary": "#F8F8F2",  # Dracula foreground
        "text_secondary": "#BFBFBF",
        "border": "#6272A4",  # Dracula comment
        "hover": "#44475A",
        "success": "#50FA7B",
        "warning": "#FFB86C",  # Dracula orange
        "error": "#FF5555",  # Dracula red
        "info": "#8BE9FD",  # Dracula cyan
    },
    "ocean": {
        "name": "🌊 Ocean Breeze",
        "primary": "#0077BE",  # Deep ocean blue
        "primary_dark": "#005580",
        "primary_light": "#3399CC",
        "secondary": "#00BCD4",  # Turquoise
        "accent": "#4DD0E1",  # Light cyan
        "background": "#0D1117",
        "surface": "#161B22",
        "surface_variant": "#21262D",
        "bg_primary": "#ffffff",
        "text_primary": "#C9D1D9",
        "text_secondary": "#8B949E",
        "border": "#30363D",
        "hover": "#21262D",
        "success": "#26A69A",  # Teal
        "warning": "#FFA726",
        "error": "#EF5350",
        "info": "#0077BE",
    },
    "sunset": {
        "name": "🌅 Sunset Glow",
        "primary": "#FF6B6B",  # Coral red
        "primary_dark": "#D94545",
        "primary_light": "#FF8E8E",
        "secondary": "#FFB347",  # Sunset orange
        "accent": "#FFDD57",  # Golden yellow
        "background": "#1A1423",
        "surface": "#2D1B38",
        "surface_variant": "#3E2444",
        "bg_primary": "#ffffff",
        "text_primary": "#FFE5E5",
        "text_secondary": "#E0B0C0",
        "border": "#4A2C57",
        "hover": "#3E2444",
        "success": "#95E1D3",
        "warning": "#FFB347",
        "error": "#FF6B6B",
        "info": "#A78BFA",
    },
    "forest": {
        "name": "🌲 Forest Green",
        "primary": "#4CAF50",  # Material green
        "primary_dark": "#388E3C",
        "primary_light": "#81C784",
        "secondary": "#8BC34A",  # Light green
        "accent": "#66BB6A",
        "background": "#0F1419",
        "surface": "#1A1F24",
        "surface_variant": "#252A2E",
        "bg_primary": "#ffffff",
        "text_primary": "#E6EDF3",
        "text_secondary": "#B0B0B0",
        "border": "#2D3238",
        "hover": "#252A2E",
        "success": "#66BB6A",
        "warning": "#FFC107",
        "error": "#EF5350",
        "info": "#4CAF50",
    },
    "lavender": {
        "name": "💜 Lavender Dreams",
        "primary": "#9C27B0",  # Material purple
        "primary_dark": "#7B1FA2",
        "primary_light": "#BA68C8",
        "secondary": "#E1BEE7",  # Light purple
        "accent": "#CE93D8",
        "background": "#1C1520",
        "surface": "#2A1F2D",
        "surface_variant": "#362838",
        "bg_primary": "#ffffff",
        "text_primary": "#F5E6FA",
        "text_secondary": "#D0B0D8",
        "border": "#4A3550",
        "hover": "#362838",
        "success": "#AB47BC",
        "warning": "#FFB74D",
        "error": "#EC407A",
        "info": "#9C27B0",
    },
    "cherry": {
        "name": "🍒 Cherry Blossom",
        "primary": "#E91E63",  # Pink
        "primary_dark": "#C2185B",
        "primary_light": "#F06292",
        "secondary": "#FF4081",  # Accent pink
        "accent": "#F8BBD0",  # Light pink
        "background": "#1A0A11",
        "surface": "#2A1520",
        "surface_variant": "#3A1F2D",
        "bg_primary": "#ffffff",
        "text_primary": "#FFE5EE",
        "text_secondary": "#E0B0C5",
        "border": "#4A2535",
        "hover": "#3A1F2D",
        "success": "#EC407A",
        "warning": "#FFB74D",
        "error": "#F44336",
        "info": "#E91E63",
    },
    "midnight": {
        "name": "🌃 Midnight Blue",
        "primary": "#3F51B5",  # Indigo
        "primary_dark": "#303F9F",
        "primary_light": "#7986CB",
        "secondary": "#536DFE",  # Indigo accent
        "accent": "#8C9EFF",
        "background": "#0A0E1A",
        "surface": "#141829",
        "surface_variant": "#1E2333",
        "bg_primary": "#ffffff",
        "text_primary": "#E8EAED",
        "text_secondary": "#B0B0B0",
        "border": "#2A2E3D",
        "hover": "#1E2333",
        "success": "#5C6BC0",
        "warning": "#FFA726",
        "error": "#EF5350",
        "info": "#3F51B5",
    },
    "amber": {
        "name": "🔥 Amber Fire",
        "primary": "#FF9800",  # Orange
        "primary_dark": "#F57C00",
        "primary_light": "#FFB74D",
        "secondary": "#FFC107",  # Amber
        "accent": "#FFCA28",
        "background": "#1A1008",
        "surface": "#2A1810",
        "surface_variant": "#3A2218",
        "bg_primary": "#ffffff",
        "text_primary": "#FFF8E1",
        "text_secondary": "#E0D0B0",
        "border": "#4A3020",
        "hover": "#3A2218",
        "success": "#FFB74D",
        "warning": "#FFC107",
        "error": "#FF5722",
        "info": "#FF9800",
    },
    "mint": {
        "name": "🌿 Mint Fresh",
        "primary": "#00BCD4",  # Cyan
        "primary_dark": "#0097A7",
        "primary_light": "#4DD0E1",
        "secondary": "#26A69A",  # Teal
        "accent": "#80CBC4",
        "background": "#0A1414",
        "surface": "#152323",
        "surface_variant": "#1F2E2E",
        "bg_primary": "#ffffff",
        "text_primary": "#E0F7FA",
        "text_secondary": "#B0D8DA",
        "border": "#2A3838",
        "hover": "#1F2E2E",
        "success": "#26A69A",
        "warning": "#FFB74D",
        "error": "#EF5350",
        "info": "#00BCD4",
    },
    "simple": {
        "name": "✨ Simple & Clean",
        "primary": "#5E6C84",  # Muted slate blue
        "primary_dark": "#42526E",
        "primary_light": "#7A869A",
        "secondary": "#8993A4",
        "accent": "#6554C0",
        "background": "#1c1c1c",
        "surface": "#252525",
        "surface_variant": "#2e2e2e",
        "bg_primary": "#ffffff",
        "text_primary": "#f0f0f0",
        "text_secondary": "#a0a0a0",
        "border": "#3d3d3d",
        "hover": "#333333",
        "success": "#36B37E",
        "warning": "#FFAB00",
        "error": "#DE350B",
        "info": "#0065FF",
    },
    "glassmorphism": {
        "name": "💎 Glassmorphism",
        "primary": "#667eea",
        "primary_dark": "#4c63d2",
        "primary_light": "#8099f2",
        "secondary": "#764ba2",
        "accent": "#f093fb",
        "background": "rgba(10, 10, 30, 0.8)",
        "surface": "rgba(30, 30, 60, 0.4)",
        "surface_variant": "rgba(40, 40, 80, 0.6)",
        "bg_primary": "#ffffff",
        "text_primary": "#ffffff",
        "text_secondary": "#b8b8d0",
        "border": "rgba(255, 255, 255, 0.1)",
        "hover": "rgba(102, 126, 234, 0.2)",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "info": "#60a5fa",
    },
    "neumorphic": {
        "name": "🎨 Neumorphic",
        "primary": "#5865F2",
        "primary_dark": "#4752C4",
        "primary_light": "#7289DA",
        "secondary": "#99AAB5",
        "accent": "#ED4245",
        "background": "#2C2F33",
        "surface": "#36393F",
        "surface_variant": "#40444B",
        "bg_primary": "#ffffff",
        "text_primary": "#DCDDDE",
        "text_secondary": "#96989D",
        "border": "#202225",
        "hover": "#40444B",
        "success": "#3BA55D",
        "warning": "#FAA81A",
        "error": "#ED4245",
        "info": "#5865F2",
    }
}

# Light mode variants of all themes
MODERN_THEMES_LIGHT = {
    "default": {
        "name": "🌙 Light Blue",
        "primary": "#2196F3",
        "primary_dark": "#1976D2",
        "primary_light": "#64B5F6",
        "secondary": "#FF9800",
        "accent": "#4CAF50",
        "background": "#f5f5f5",
        "surface": "#ffffff",
        "surface_variant": "#fafafa",
        "bg_primary": "#ffffff",
        "text_primary": "#000000",
        "text_secondary": "#666666",
        "border": "#e0e0e0",
        "hover": "#f0f0f0",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
    },
    "cyberpunk": {
        "name": "⚡ Cyberpunk Neon (Light)",
        "primary": "#C000C0",  # Darker magenta for light mode
        "primary_dark": "#A000A0",
        "primary_light": "#D040D0",
        "secondary": "#00A0A0",  # Darker cyan
        "accent": "#C0C000",  # Darker yellow
        "background": "#fafafa",
        "surface": "#ffffff",
        "surface_variant": "#f5f5f5",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#e0c0ff",
        "hover": "#f0e8ff",
        "success": "#00A000",
        "warning": "#C0C000",
        "error": "#C00050",
        "info": "#00A0A0",
    },
    "nord": {
        "name": "❄️ Nord Aurora (Light)",
        "primary": "#5E81AC",
        "primary_dark": "#5172A5",
        "primary_light": "#729FCF",
        "secondary": "#EBCB8B",
        "accent": "#A3BE8C",
        "background": "#ECEFF4",
        "surface": "#E5E9F0",
        "surface_variant": "#D8DEE9",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#D8DEE9",
        "hover": "#E5E9F0",
        "success": "#A3BE8C",
        "warning": "#EBCB8B",
        "error": "#BF616A",
        "info": "#5E81AC",
    },
    "dracula": {
        "name": "🧛 Dracula Purple (Light)",
        "primary": "#9966CC",
        "primary_dark": "#8855BB",
        "primary_light": "#AA77DD",
        "secondary": "#FF79C6",
        "accent": "#50FA7B",
        "background": "#F8F8F2",
        "surface": "#FFFFFF",
        "surface_variant": "#F5F5F5",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#E0E0F0",
        "hover": "#F0F0F8",
        "success": "#50FA7B",
        "warning": "#FFB86C",
        "error": "#FF5555",
        "info": "#8BE9FD",
    },
    "ocean": {
        "name": "🌊 Ocean Breeze (Light)",
        "primary": "#0077BE",
        "primary_dark": "#005A90",
        "primary_light": "#3399CC",
        "secondary": "#00BCD4",
        "accent": "#4DD0E1",
        "background": "#F5F8FA",
        "surface": "#FFFFFF",
        "surface_variant": "#EDF2F7",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#E2E8F0",
        "hover": "#EDF2F7",
        "success": "#26A69A",
        "warning": "#FFA726",
        "error": "#EF5350",
        "info": "#0077BE",
    },
    "sunset": {
        "name": "🌅 Sunset Glow (Light)",
        "primary": "#D94545",
        "primary_dark": "#C03535",
        "primary_light": "#FF6B6B",
        "secondary": "#FFB347",
        "accent": "#FFDD57",
        "background": "#FFF8F0",
        "surface": "#FFFFFF",
        "surface_variant": "#FFF0E5",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#FFE0D0",
        "hover": "#FFF0E5",
        "success": "#95E1D3",
        "warning": "#FFB347",
        "error": "#FF6B6B",
        "info": "#A78BFA",
    },
    "forest": {
        "name": "🌲 Forest Green (Light)",
        "primary": "#4CAF50",
        "primary_dark": "#388E3C",
        "primary_light": "#81C784",
        "secondary": "#8BC34A",
        "accent": "#66BB6A",
        "background": "#F1F8F4",
        "surface": "#FFFFFF",
        "surface_variant": "#E8F5E9",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#C8E6C9",
        "hover": "#E8F5E9",
        "success": "#66BB6A",
        "warning": "#FFC107",
        "error": "#EF5350",
        "info": "#4CAF50",
    },
    "lavender": {
        "name": "💜 Lavender Dreams (Light)",
        "primary": "#9C27B0",
        "primary_dark": "#7B1FA2",
        "primary_light": "#BA68C8",
        "secondary": "#E1BEE7",
        "accent": "#CE93D8",
        "background": "#FAF5FF",
        "surface": "#FFFFFF",
        "surface_variant": "#F3E5F5",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#E1BEE7",
        "hover": "#F3E5F5",
        "success": "#AB47BC",
        "warning": "#FFB74D",
        "error": "#EC407A",
        "info": "#9C27B0",
    },
    "cherry": {
        "name": "🍒 Cherry Blossom (Light)",
        "primary": "#C2185B",
        "primary_dark": "#AD1457",
        "primary_light": "#E91E63",
        "secondary": "#FF4081",
        "accent": "#F8BBD0",
        "background": "#FFF5F7",
        "surface": "#FFFFFF",
        "surface_variant": "#FCE4EC",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#F8BBD0",
        "hover": "#FCE4EC",
        "success": "#EC407A",
        "warning": "#FFB74D",
        "error": "#F44336",
        "info": "#E91E63",
    },
    "midnight": {
        "name": "🌃 Midnight Blue (Light)",
        "primary": "#3F51B5",
        "primary_dark": "#303F9F",
        "primary_light": "#7986CB",
        "secondary": "#536DFE",
        "accent": "#8C9EFF",
        "background": "#F5F7FA",
        "surface": "#FFFFFF",
        "surface_variant": "#E8EAF6",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#C5CAE9",
        "hover": "#E8EAF6",
        "success": "#5C6BC0",
        "warning": "#FFA726",
        "error": "#EF5350",
        "info": "#3F51B5",
    },
    "amber": {
        "name": "🔥 Amber Fire (Light)",
        "primary": "#FF9800",
        "primary_dark": "#F57C00",
        "primary_light": "#FFB74D",
        "secondary": "#FFC107",
        "accent": "#FFCA28",
        "background": "#FFF8F0",
        "surface": "#FFFFFF",
        "surface_variant": "#FFF3E0",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#FFE0B2",
        "hover": "#FFF3E0",
        "success": "#FFB74D",
        "warning": "#FFC107",
        "error": "#FF5722",
        "info": "#FF9800",
    },
    "mint": {
        "name": "🌿 Mint Fresh (Light)",
        "primary": "#00BCD4",
        "primary_dark": "#0097A7",
        "primary_light": "#4DD0E1",
        "secondary": "#26A69A",
        "accent": "#80CBC4",
        "background": "#F0FAFA",
        "surface": "#FFFFFF",
        "surface_variant": "#E0F7FA",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#B2EBF2",
        "hover": "#E0F7FA",
        "success": "#26A69A",
        "warning": "#FFB74D",
        "error": "#EF5350",
        "info": "#00BCD4",
    },
    "simple": {
        "name": "✨ Simple & Clean (Light)",
        "primary": "#5E6C84",
        "primary_dark": "#42526E",
        "primary_light": "#7A869A",
        "secondary": "#8993A4",
        "accent": "#6554C0",
        "background": "#fafbfc",
        "surface": "#ffffff",
        "surface_variant": "#f4f5f7",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "border": "#dfe1e6",
        "hover": "#f4f5f7",
        "success": "#36B37E",
        "warning": "#FFAB00",
        "error": "#DE350B",
        "info": "#0065FF",
    },
    "glassmorphism": {
        "name": "💎 Glassmorphism (Light)",
        "primary": "#667eea",
        "primary_dark": "#4c63d2",
        "primary_light": "#8099f2",
        "secondary": "#764ba2",
        "accent": "#f093fb",
        "background": "rgba(255, 255, 255, 0.7)",
        "surface": "rgba(255, 255, 255, 0.4)",
        "surface_variant": "rgba(255, 255, 255, 0.6)",
        "bg_primary": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#5a5a5a",
        "border": "rgba(255, 255, 255, 0.3)",
        "hover": "rgba(102, 126, 234, 0.1)",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "info": "#60a5fa",
    },
    "neumorphic": {
        "name": "🎨 Neumorphic (Light)",
        "primary": "#5865F2",
        "primary_dark": "#4752C4",
        "primary_light": "#7289DA",
        "secondary": "#99AAB5",
        "accent": "#ED4245",
        "background": "#E3E5E8",
        "surface": "#E3E5E8",
        "surface_variant": "#D4D7DC",
        "bg_primary": "#ffffff",
        "text_primary": "#2C2F33",
        "text_secondary": "#5C5E66",
        "border": "#C4C7CC",
        "hover": "#D4D7DC",
        "success": "#3BA55D",
        "warning": "#FAA81A",
        "error": "#ED4245",
        "info": "#5865F2",
    }
}

# ============================================================================
# VALIDATION ERROR MESSAGES
# ============================================================================

VALIDATION_MESSAGES = {
    # Employee ID validation
    "emp_id_required": "Employee ID is required",
    "emp_id_invalid_format": "Invalid Employee ID format. Expected format: X-NNN-YY (e.g., O-001-23)",
    "emp_id_exists": "Employee ID already exists in the database",

    # Name validation
    "name_required": "Employee name is required",
    "name_too_short": "Name must be at least 2 characters long",
    "name_invalid_chars": "Name contains invalid characters",

    # Date validation
    "hire_date_required": "Hire date is required",
    "hire_date_invalid": "Invalid hire date format. Expected: MM-DD-YYYY",
    "hire_date_future": "Hire date cannot be in the future",
    "resign_date_before_hire": "Resign date cannot be before hire date",
    "contract_date_invalid": "Invalid contract date format",

    # Government ID validation
    "sss_invalid": "Invalid SSS number format",
    "sss_duplicate": "SSS number already exists in the database",
    "tin_invalid": "Invalid TIN format",
    "tin_duplicate": "TIN already exists in the database",
    "philhealth_invalid": "Invalid PhilHealth number format",
    "philhealth_duplicate": "PhilHealth number already exists in the database",
    "pagibig_invalid": "Invalid Pag-IBIG number format",
    "pagibig_duplicate": "Pag-IBIG number already exists in the database",

    # Contact validation
    "email_invalid": "Invalid email address format",
    "phone_invalid": "Invalid phone number format",

    # Salary validation
    "salary_negative": "Salary cannot be negative",
    "salary_invalid": "Invalid salary amount",

    # User management
    "username_required": "Username is required",
    "username_exists": "Username already exists",
    "username_invalid": "Username must be 3-20 characters, letters/numbers only",
    "password_required": "Password is required",
    "password_mismatch": "Passwords do not match",
    "password_weak": "Password does not meet security requirements",

    # General validation
    "field_required": "This field is required",
    "invalid_selection": "Please select a valid option",
    "operation_failed": "Operation failed. Please try again",
    "permission_denied": "You do not have permission to perform this action",

    # Database errors
    "db_connection_error": "Failed to connect to database",
    "db_query_error": "Database query failed",
    "db_integrity_error": "Database integrity constraint violated",
}

# ============================================================================
# INTERNATIONALIZATION (i18n) INFRASTRUCTURE
# ============================================================================

# Current language setting
CURRENT_LANGUAGE = "en"  # Default: English

# Available languages
AVAILABLE_LANGUAGES = {
    "en": "English",
    "fil": "Filipino",
    # Add more languages as needed
}

# Translation strings dictionary
# Structure: TRANSLATIONS[language_code][key] = translated_string
TRANSLATIONS = {
    "en": {
        # Common UI strings
        "app_title": "Cuddly Employees Information",
        "welcome": "Welcome",
        "login": "Login",
        "logout": "Logout",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "add": "Add",
        "search": "Search",
        "close": "Close",
        "ok": "OK",
        "yes": "Yes",
        "no": "No",

        # Menu items
        "dashboard": "Dashboard",
        "employees": "Employees",
        "reports": "Reports",
        "settings": "Settings",
        "about": "About",

        # Employee fields
        "employee_id": "Employee ID",
        "name": "Name",
        "email": "Email",
        "phone": "Phone",
        "department": "Department",
        "position": "Position",
        "hire_date": "Hire Date",
        "salary": "Salary",
        "status": "Status",

        # Buttons
        "add_employee": "Add Employee",
        "edit_employee": "Edit Employee",
        "delete_employee": "Delete Employee",
        "export": "Export",
        "import": "Import",
        "backup": "Backup",

        # Status messages
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "loading": "Loading...",
        "saving": "Saving...",
        "deleting": "Deleting...",
    },
    "fil": {
        # Filipino translations (examples - expand as needed)
        "app_title": "Impormasyon ng mga Empleyado ng Cuddly",
        "welcome": "Maligayang pagdating",
        "login": "Mag-login",
        "logout": "Mag-logout",
        "save": "I-save",
        "cancel": "Kanselahin",
        "delete": "Tanggalin",
        "edit": "I-edit",
        "add": "Magdagdag",
        "search": "Maghanap",
        "close": "Isara",
        "ok": "OK",
        "yes": "Oo",
        "no": "Hindi",

        # Add more Filipino translations as needed
    }
}

def t(key: str, language: str = None) -> str:
    """
    Translate a string key to the current or specified language.

    Args:
        key: Translation key to look up
        language: Language code (uses CURRENT_LANGUAGE if not specified)

    Returns:
        Translated string, or the key itself if translation not found

    Example:
        >>> t("welcome")
        "Welcome"
        >>> t("welcome", "fil")
        "Maligayang pagdating"
    """
    lang = language or CURRENT_LANGUAGE
    return TRANSLATIONS.get(lang, {}).get(key, key)

def set_language(language_code: str) -> bool:
    """
    Set the current application language.

    Args:
        language_code: Language code from AVAILABLE_LANGUAGES

    Returns:
        True if language was set successfully, False otherwise
    """
    global CURRENT_LANGUAGE
    if language_code in AVAILABLE_LANGUAGES:
        CURRENT_LANGUAGE = language_code
        logging.info(f"Language changed to: {AVAILABLE_LANGUAGES[language_code]}")
        return True
    else:
        logging.warning(f"Language code '{language_code}' not available")
        return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def validate_password_strength(password: str) -> Tuple[bool, list]:
    """
    Validate password against security requirements.
    Returns: (is_valid, list_of_missing_requirements)
    """
    errors = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"At least {PASSWORD_MIN_LENGTH} characters")
    if not re.search(r'[A-Z]', password):
        errors.append("At least 1 uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("At least 1 lowercase letter")
    if not re.search(r'\d', password):
        errors.append("At least 1 number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("At least 1 special character")
    return (len(errors) == 0, errors)


def load_theme_preference() -> str:
    """Load saved theme or return default"""
    try:
        if os.path.exists(THEME_PREFERENCE_FILE):
            with open(THEME_PREFERENCE_FILE, 'r') as f:
                theme = f.read().strip()
                if theme in MODERN_THEMES:
                    return theme
    except (IOError, OSError):
        # File read error, use default theme
        pass
    return "default"  # Changed from "dark_blue"


def save_theme_preference(theme_name: str):
    """Save theme preference to file"""
    try:
        with open(THEME_PREFERENCE_FILE, 'w') as f:
            f.write(theme_name)
    except Exception as e:
        logging.error(f"Could not save theme preference: {e}")


def get_modern_stylesheet(theme_name="default", is_light_mode=False) -> str:
    """
    Generate modern stylesheet with selected theme - ULTRA STYLISH v3.0

    Args:
        theme_name: Name of the color theme (default, cyberpunk, nord, etc.)
        is_light_mode: If True, use light theme variants; if False, use dark variants
    """
    # Select theme dict based on light/dark mode
    theme_dict = MODERN_THEMES_LIGHT if is_light_mode else MODERN_THEMES
    c = theme_dict.get(theme_name, theme_dict["default"])

    return f"""
    /* ====== MODERN UI v3.0 - ULTRA STYLISH ====== */
    * {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
    }}

    QMainWindow, QDialog, QWidget {{
        background-color: {c['background']};
        color: {c['text_primary']};
    }}

    /* Modern Input Fields - COMPACT */
    QLineEdit, QTextEdit, QComboBox, QDateEdit {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: 2px solid {c['border']};
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 28px;
        max-height: 32px;
    }}

    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
        border: 2px solid {c['primary']};
        background-color: {c['surface_variant']};
    }}

    QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QDateEdit:hover {{
        border-color: {c['primary_light']};
    }}

    /* Modern Gradient Buttons - PILL SHAPE */
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        color: {c['bg_primary']};
        border: none;
        border-radius: 22px;
        padding: 8px 20px;
        font-weight: 600;
        min-height: 36px;
    }}

    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary_light']}, stop:1 {c['primary']});
    }}

    QPushButton:pressed {{
        background-color: {c['primary_dark']};
    }}

    QPushButton:disabled {{
        background-color: {c['surface_variant']};
        color: {c['text_secondary']};
    }}

    /* Modern ComboBox */
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
        outline: none;
        border-radius: 8px;
    }}

    /* Enhanced Tables */
    QTableView {{
        background-color: {c['surface']};
        alternate-background-color: {c['surface_variant']};
        color: {c['text_primary']};
        gridline-color: transparent;
        border: none;
        border-radius: 12px;
        selection-background-color: {c['primary']};
    }}

    QTableView::item {{
        padding: 10px 8px;
        border: none;
        border-bottom: 1px solid {c['border']};
    }}

    QTableView::item:hover {{
        background-color: {c['hover']};
    }}

    QTableView::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(33, 150, 243, 0.3),
            stop:1 rgba(33, 150, 243, 0.5));
        color: {c['text_primary']};
        border-left: 3px solid {c['primary']};
        font-weight: 600;
    }}

    QHeaderView::section {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']}, stop:1 {c['surface']});
        color: {c['text_primary']};
        padding: 12px 8px;
        border: none;
        border-right: 1px solid {c['border']};
        border-bottom: 3px solid {c['primary']};
        font-weight: 600;
        font-size: 13px;
    }}

    QHeaderView::section:hover {{
        background-color: {c['hover']};
    }}

    /* Modern Group Boxes */
    QGroupBox {{
        background-color: {c['surface']};
        border: 2px solid {c['border']};
        border-radius: 12px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: 600;
        color: {c['text_primary']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 12px;
        color: {c['primary']};
        font-weight: 600;
        font-size: 14px;
    }}

    /* Modern Scrollbars */
    QScrollBar:vertical {{
        background: {c['surface']};
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {c['primary']};
        border-radius: 6px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['primary_dark']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {c['surface']};
        height: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['primary']};
        border-radius: 6px;
        min-width: 30px;
    }}

    /* Modern Tabs */
    QTabWidget::pane {{
        border: none;
        background-color: {c['surface']};
        border-radius: 12px;
    }}

    QTabBar::tab {{
        background-color: {c['surface_variant']};
        color: {c['text_secondary']};
        padding: 10px 20px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 600;
    }}

    QTabBar::tab:selected {{
        background-color: {c['primary']};
        color: {c['bg_primary']};
    }}

    QTabBar::tab:hover {{
        background-color: {c['hover']};
    }}

    /* Modern Progress Bar */
    QProgressBar {{
        background-color: {c['surface_variant']};
        color: {c['text_primary']};
        border: none;
        border-radius: 8px;
        text-align: center;
        height: 24px;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        border-radius: 8px;
    }}

    /* Modern Slider - Smooth Rounded Edges */
    QSlider::groove:horizontal {{
        background: {c['surface_variant']};
        height: 8px;
        border-radius: 4px;
        border: none;
    }}

    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        width: 18px;
        height: 18px;
        margin: -5px 0;
        border-radius: 9px;
        border: 2px solid {c['surface']};
    }}

    QSlider::handle:horizontal:hover {{
        background: {c['primary_light']};
    }}

    QSlider::groove:vertical {{
        background: {c['surface_variant']};
        width: 8px;
        border-radius: 4px;
        border: none;
    }}

    QSlider::handle:vertical {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        height: 18px;
        width: 18px;
        margin: 0 -5px;
        border-radius: 9px;
        border: 2px solid {c['surface']};
    }}

    QSlider::handle:vertical:hover {{
        background: {c['primary_light']};
    }}

    /* Modern Calendar - ULTRA ENHANCED WITH DROPDOWN */
    QCalendarWidget {{
        background-color: {c['surface']};
        border: 2px solid {c['primary']};
        border-radius: 12px;
        padding: 5px;
    }}

    QCalendarWidget QWidget {{
        background-color: {c['surface']};
        color: {c['text_primary']};
    }}

    QCalendarWidget QToolButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']}, stop:1 {c['surface']});
        border-radius: 8px;
        padding: 10px 16px;
        color: {c['text_primary']};
        font-weight: 700;
        font-size: 14px;
        border: 1px solid {c['border']};
        margin: 3px;
        min-width: 80px;
    }}

    QCalendarWidget QToolButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary_light']}, stop:1 {c['primary']});
        color: {c['bg_primary']};
        border-color: {c['primary']};
    }}

    QCalendarWidget QToolButton:pressed {{
        background-color: {c['primary_dark']};
        color: {c['bg_primary']};
    }}

    QCalendarWidget QToolButton::menu-indicator {{
        image: none;  /* Remove default arrow */
        width: 0px;
    }}

    QCalendarWidget QMenu {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: 2px solid {c['primary']};
        border-radius: 8px;
        padding: 5px;
    }}

    QCalendarWidget QMenu::item {{
        padding: 8px 20px;
        border-radius: 4px;
    }}

    QCalendarWidget QMenu::item:selected {{
        background-color: {c['primary']};
        color: {c['bg_primary']};
    }}

    QCalendarWidget QSpinBox {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']}, stop:1 {c['surface']});
        color: {c['text_primary']};
        border: 2px solid {c['primary']};
        border-radius: 8px;
        padding: 10px 15px;
        font-weight: 700;
        font-size: 15px;
        min-width: 120px;
        selection-background-color: {c['primary']};
    }}

    QCalendarWidget QSpinBox:hover {{
        border-color: {c['primary_light']};
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary_light']}, stop:1 {c['primary']});
        color: {c['bg_primary']};
    }}

    QCalendarWidget QSpinBox:focus {{
        border: 3px solid {c['primary']};
        background-color: {c['surface_variant']};
    }}

    QCalendarWidget QSpinBox::up-button,
    QCalendarWidget QSpinBox::down-button {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        border-radius: 6px;
        width: 24px;
        height: 18px;
        border: none;
        margin: 2px;
    }}

    QCalendarWidget QSpinBox::up-button:hover,
    QCalendarWidget QSpinBox::down-button:hover {{
        background-color: {c['primary_light']};
    }}

    QCalendarWidget QSpinBox::up-button:pressed,
    QCalendarWidget QSpinBox::down-button:pressed {{
        background-color: {c['primary_dark']};
    }}

    /* Make the arrows more visible */
    QCalendarWidget QSpinBox::up-arrow {{
        width: 12px;
        height: 12px;
        image: none;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-bottom: 8px solid white;
    }}

    QCalendarWidget QSpinBox::down-arrow {{
        width: 12px;
        height: 12px;
        image: none;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 8px solid white;
    }}

    QCalendarWidget QAbstractItemView {{
        color: {c['text_primary']};
        background-color: {c['surface']};
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
        outline: none;
        border: none;
        border-radius: 8px;
        padding: 5px;
    }}

    QCalendarWidget QAbstractItemView:enabled {{
        color: {c['text_primary']};
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
        font-size: 13px;
    }}

    QCalendarWidget QAbstractItemView:disabled {{
        color: {c['text_secondary']};
    }}

    QCalendarWidget QTableView {{
        selection-background-color: {c['primary']};
        alternate-background-color: {c['surface_variant']};
        gridline-color: transparent;
    }}

    /* Calendar header (day names) */
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']}, stop:1 {c['primary_dark']});
        border-bottom: 3px solid {c['primary']};
        border-radius: 10px 10px 0 0;
        padding: 8px;
    }}

    /* Day names header styling */
    QCalendarWidget QAbstractItemView::item {{
        padding: 8px;
    }}

    /* Modern Checkboxes & Radio Buttons */
    QCheckBox, QRadioButton {{
        color: {c['text_primary']};
        spacing: 8px;
    }}

    QCheckBox::indicator, QRadioButton::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {c['border']};
        border-radius: 4px;
        background-color: {c['surface']};
    }}

    QRadioButton::indicator {{
        border-radius: 10px;
    }}

    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {c['primary']};
        border-color: {c['primary']};
    }}

    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {c['primary']};
    }}

    /* Modern Tooltips */
    QToolTip {{
        background-color: {c['surface_variant']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: normal;
    }}

    /* Labels */
    QLabel {{
        color: {c['text_primary']};
        background: transparent;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {c['surface']};
        color: {c['text_secondary']};
        border-top: 1px solid {c['border']};
    }}

    /* ====== MODERN SCROLLBARS (Auto-hiding style) ====== */
    QScrollBar:vertical {{
        background: {c['surface']};
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {c['primary']};
        border-radius: 6px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['primary_dark']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {c['surface']};
        height: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['primary']};
        border-radius: 6px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {c['primary_dark']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ====== PROGRESS BAR (Modern style) ====== */
    QProgressBar {{
        border: 2px solid {c['border']};
        border-radius: 8px;
        background-color: {c['surface']};
        text-align: center;
        color: {c['text_primary']};
        font-weight: bold;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        border-radius: 6px;
    }}

    /* ====== TOOLTIPS (Modern) ====== */
    QToolTip {{
        background-color: {c['surface_variant']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: normal;
    }}

    /* ====== MESSAGE BOXES (Clean & Modern) ====== */
    QMessageBox {{
        background-color: {c['surface']};
        color: {c['text_primary']};
    }}

    QMessageBox QLabel {{
        background: transparent;
        color: {c['text_primary']};
        border: none;
        padding: 0px;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
        padding: 8px 16px;
    }}
    """


# ============================================================================
# NETWORK GUARD FUNCTIONS
# ============================================================================

def _is_frozen():
    """Check if running as PyInstaller executable"""
    return getattr(sys, "frozen", False)


def _exe_path():
    """Get executable path"""
    return pathlib.Path(sys.executable if _is_frozen() else __file__).resolve()


def _to_unc(p: pathlib.Path) -> str:
    """Convert mapped drive to UNC path if possible"""
    try:
        import ctypes
        from ctypes import wintypes
        p_str = str(p)
        drive = os.path.splitdrive(p_str)[0]
        if len(drive) == 2 and drive[1] == ":":
            remote = ctypes.create_unicode_buffer(1024)
            buflen = wintypes.DWORD(len(remote))
            res = ctypes.windll.mpr.WNetGetConnectionW(drive, remote, ctypes.byref(buflen))
            if res == 0:  # success
                return remote.value + p_str[len(drive):]
    except Exception:
        pass
    return str(p)


def guard_or_exit():
    """Guard function to ensure app runs only from network share"""
    exe_unc = _to_unc(_exe_path()).rstrip("\\/")
    if not exe_unc.lower().startswith(EXPECTED_UNC_PREFIX.lower()):
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                "This application can only be run from the official network share:\n\n" + EXPECTED_UNC_PREFIX,
                "= Application Locked",
                0x10  # MB_ICONERROR
            )
        except Exception:
            pass
        sys.exit(1)


# ============================================================================
# PASSWORD HASHING (bcrypt)
# ============================================================================

def _hash_pwd(password: str) -> str:
    """
    Hash password using bcrypt with automatic salt generation.
    This is the industry standard for secure password storage.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password (includes salt)
    """
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        logging.error(f"Password hashing failed: {e}")
        raise


def _verify_pwd(password: str, hashed: str) -> bool:
    """
    Verify password against bcrypt hash.

    Args:
        password: Plain text password to verify
        hashed: Bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        import hashlib
        # Handle legacy SHA-256 hashes during migration
        if len(hashed) == 64 and all(c in '0123456789abcdef' for c in hashed.lower()):
            # This is an old SHA-256 hash - needs migration
            logging.warning("Legacy SHA-256 hash detected - password needs update")
            return hashlib.sha256(password.encode()).hexdigest() == hashed

        # Normal bcrypt verification
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logging.error(f"Password verification failed: {e}")
        return False


def _needs_password_rehash(hashed: str) -> bool:
    """
    Check if password hash needs to be updated (legacy SHA-256).

    Args:
        hashed: Password hash from database

    Returns:
        True if password needs rehashing to bcrypt
    """
    # SHA-256 hashes are exactly 64 hex characters
    return len(hashed) == 64 and all(c in '0123456789abcdef' for c in hashed.lower())


# Backwards compatibility alias
def _check_pwd(password: str, hashed: str) -> bool:
    """Alias for _verify_pwd for backwards compatibility"""
    return _verify_pwd(password, hashed)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def contract_days_left(emp: dict):
    """Calculate days left until contract expiry"""
    ce = (emp.get("contract_expiry") or "").strip()
    if not ce:
        return None
    try:
        dt = datetime.strptime(ce, "%m-%d-%Y").date()
        return (dt - datetime.now().date()).days
    except Exception:
        return None


# ============================================================================
# DATABASE SYNC FUNCTIONS
# ============================================================================

def sync_database_from_network():
    """
    Sync database from network to local for offline backup.
    NOT USED - We work directly on network DB.
    Only kept for potential manual sync scenarios.
    """
    import shutil
    
    if not USE_NETWORK_DB:
        logging.info("Not using network database - sync skipped")
        return False
    
    logging.warning("Direct file sync not recommended while DB is in use. Use backup_database_on_close() instead.")
    return False


def backup_database_on_close(source_conn):
    """
    Backup database using SQLite's backup API.
    This safely copies the database even while it's open.
    Called on app close to create local backup of network database.

    ONLY backs up when app is running from network path (\\extra\EmployeeVault).
    When running locally, no backup is performed.
    """
    import sqlite3
    import signal
    import shutil

    # Check if running from network location
    exe_path = sys.executable if getattr(sys, "frozen", False) else __file__
    exe_location = str(pathlib.Path(exe_path).resolve().parent)

    # Only backup if running FROM network path
    is_running_from_network = exe_location.lower().startswith(r"\\extra\employeevault")

    if not is_running_from_network:
        logging.info("Running from local path - backup skipped")
        return False

    if not USE_NETWORK_DB:
        logging.info("Not using network database - backup skipped")
        return False

    # Backup destination: E:\Documents\MEGA downloads\EmployeeVault\EmployeeVault
    BACKUP_DIR = r"E:\Documents\MEGA downloads\EmployeeVault\EmployeeVault"
    BACKUP_DB_PATH = os.path.join(BACKUP_DIR, "employee_vault.db")

    # Timeout handler to prevent hanging
    def timeout_handler(signum, frame):
        raise TimeoutError("Backup operation timed out")

    try:
        # Create backup directory if needed
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Create timestamped backup of existing file before replacing
        if os.path.exists(BACKUP_DB_PATH):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_backup = os.path.join(BACKUP_DIR, f"employee_vault_backup_{timestamp}.db")
            shutil.copy2(BACKUP_DB_PATH, timestamped_backup)
            logging.info(f"✓ Created timestamped backup: {timestamped_backup}")

        # Open backup database
        backup_conn = sqlite3.connect(BACKUP_DB_PATH, timeout=5.0)

        # Set a 10-second timeout for the backup operation
        if hasattr(signal, 'SIGALRM'):  # Unix-like systems
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)

        try:
            # Use SQLite backup API (safely copies while DB is open)
            source_conn.backup(backup_conn, pages=100, progress=lambda status, remaining, total: None)

            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel timeout

            backup_conn.close()
            logging.info(f"✓ Database backed up from network to: {BACKUP_DB_PATH}")
            return True
        except TimeoutError:
            logging.warning("Backup operation timed out - network may be slow")
            backup_conn.close()
            return False

    except Exception as e:
        logging.error(f"Failed to backup database: {e}")
        return False


def sync_database_to_network():
    """
    Sync database from local to network.
    Called when network becomes available or on manual sync.
    """
    import shutil
    
    if USE_NETWORK_DB:
        logging.info("Already using network database - no need to sync")
        return True
    
    try:
        if os.path.exists(LOCAL_DB_PATH):
            # Ensure network directory exists
            network_dir = os.path.dirname(NETWORK_DB_PATH)
            os.makedirs(network_dir, exist_ok=True)
            
            # Copy local database to network
            shutil.copy2(LOCAL_DB_PATH, NETWORK_DB_PATH)
            logging.info(f"✓ Database synced from local to network: {NETWORK_DB_PATH}")
            return True
        else:
            logging.warning("Local database not found - cannot sync")
            return False
    except Exception as e:
        logging.error(f"Failed to sync database to network: {e}")
        return False


# ============================================================================
# DIRECTORY INITIALIZATION
# ============================================================================

def initialize_directories():
    """Create necessary directories if they don't exist"""
    for directory in [FILES_DIR, PHOTOS_DIR, LETTERS_DIR, BACKUPS_DIR]:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Directories may already exist on network share
            # or may be created by another user
            pass


# Initialize on import
initialize_directories()

# Get default stylesheet for backwards compatibility
APP_QSS = get_modern_stylesheet(load_theme_preference())
