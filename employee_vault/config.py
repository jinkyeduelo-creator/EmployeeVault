"""
Employee Vault Configuration Module
Contains all constants, settings, themes, and helper functions
"""

import os
import re
import sys
import json
import pathlib
import logging
from typing import Tuple
from datetime import datetime
from pathlib import Path
from functools import lru_cache
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
# CONFIGURABLE PATHS (loaded from network_config.json)
# ============================================================================

def load_network_config() -> dict:
    """
    Load network configuration from network_config.json file.
    This allows changing network paths without modifying code.
    """
    config_file = APP_ROOT / "network_config.json"
    default_config = {
        "network_db_path": r"\\extra\EmployeeVault\employee_vault.db",
        "network_enabled": True,
        "fallback_to_local": True
    }
    
    try:
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                default_config.update(user_config)
    except Exception as e:
        logging.warning(f"Could not load network_config.json: {e}")
    
    return default_config

# Load network config
_network_config = load_network_config()

# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

APP_TITLE = "Cuddly Employees Information"

# Database Configuration: Network + Local Backup
# Paths are now configurable via network_config.json
NETWORK_DB_PATH = _network_config.get("network_db_path", r"\\extra\EmployeeVault\employee_vault.db")
LOCAL_DB_PATH = str(APP_ROOT / "employee_vault.db")

# Try network first, fallback to local if network unavailable
import os
if _network_config.get("network_enabled", True) and os.path.exists(os.path.dirname(NETWORK_DB_PATH) if os.path.dirname(NETWORK_DB_PATH) else NETWORK_DB_PATH):
    DB_FILE = NETWORK_DB_PATH
    USE_NETWORK_DB = True
else:
    DB_FILE = LOCAL_DB_PATH
    USE_NETWORK_DB = False

JSON_FALLBACK = str(APP_ROOT / "employees_data.json")
FILES_DIR = str(APP_ROOT / "employee_files")
PHOTOS_DIR = str(APP_ROOT / "employee_photos")  # Legacy - kept for migration
LETTERS_DIR = str(APP_ROOT / "employee_letters")
BACKUPS_DIR = str(APP_ROOT / "backups")
ALERT_DAYS = 30


def get_employee_folder(emp_id: str, subfolder: str = None) -> str:
    """
    Get or create the employee's folder with new structure:
    employee_files/{emp_id}/
        photos/
        files/
    
    Args:
        emp_id: Employee ID
        subfolder: Optional subfolder ('photos' or 'files')
    
    Returns:
        Path to the employee folder or subfolder
    """
    import os
    import re
    
    # Sanitize employee ID to prevent directory traversal
    safe_emp_id = re.sub(r'[^a-zA-Z0-9_-]', '', emp_id)
    if not safe_emp_id:
        raise ValueError("Invalid employee ID")
    
    base_folder = os.path.join(FILES_DIR, safe_emp_id)
    
    # Create base folder and subfolders
    photos_folder = os.path.join(base_folder, "photos")
    files_folder = os.path.join(base_folder, "files")
    
    os.makedirs(photos_folder, exist_ok=True)
    os.makedirs(files_folder, exist_ok=True)
    
    if subfolder == 'photos':
        return photos_folder
    elif subfolder == 'files':
        return files_folder
    else:
        return base_folder


def get_employee_photos(emp_id: str) -> list:
    """
    Get all photos for an employee from their photos folder.
    
    Args:
        emp_id: Employee ID
    
    Returns:
        List of photo file paths
    """
    import os
    
    photos_folder = get_employee_folder(emp_id, 'photos')
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}
    
    photos = []
    if os.path.exists(photos_folder):
        for file in os.listdir(photos_folder):
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                photos.append(os.path.join(photos_folder, file))
    
    return sorted(photos)  # Sort for consistent ordering

VERSION = "4.7.0 - Multi-User Record Locking + Enhanced Animations"
BUILD_DATE = "2025-12-01"
DATABASE_VERSION = 8  # v8: Added record_locks table for multi-user concurrent editing

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

# PIN Authentication Settings
PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 6
PASSWORD_MAX_FAILED_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 15

# Weak PIN patterns to reject
WEAK_PIN_PATTERNS = [
    '0000', '00000', '000000',
    '1111', '11111', '111111',
    '2222', '22222', '222222',
    '3333', '33333', '333333',
    '4444', '44444', '444444',
    '5555', '55555', '555555',
    '6666', '66666', '666666',
    '7777', '77777', '777777',
    '8888', '88888', '888888',
    '9999', '99999', '999999',
    '1234', '12345', '123456',
    '4321', '54321', '654321',
    '0123', '01234', '012345',
    '3210', '43210', '543210'
]

# Keep old PASSWORD_MIN_LENGTH for backwards compatibility during migration
PASSWORD_MIN_LENGTH = 8

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
# iOS FROSTED GLASS INPUT FIELD STYLE
# ============================================================================
# Login-inspired styling for all input fields (no glow effects)
IOS_INPUT_STYLE = """
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background: rgba(255, 255, 255, 0.08);
        border: 1.5px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 10px 16px;
        font-size: 13px;
        color: white;
        selection-background-color: rgba(74, 158, 255, 0.5);
        selection-color: white;
    }
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
        background: rgba(255, 255, 255, 0.12);
        border: 1.5px solid rgba(255, 255, 255, 0.3);
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 2px solid rgba(74, 158, 255, 0.6);
        background: rgba(74, 158, 255, 0.15);
        outline: none;
    }
    QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {
        color: rgba(255, 255, 255, 0.35);
    }
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {
        background: rgba(255, 255, 255, 0.03);
        border: 1.5px solid rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.3);
    }
    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 8px;
        width: 20px;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
        background: rgba(74, 158, 255, 0.3);
    }
    QComboBox::drop-down {
        border: none;
        border-radius: 8px;
        width: 30px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid rgba(255, 255, 255, 0.7);
        margin-right: 10px;
    }
"""

# ============================================================================
# THEME SYSTEM
# ============================================================================
# All previous themes removed per user request
# User will provide custom theme definitions later

MODERN_THEMES = {
    "default": {
        "name": "🌙 Dark Professional",
        "primary": "#4a8fd9",          # Muted professional blue
        "primary_dark": "#3a7fc9",
        "primary_light": "#5a9fe9",
        "secondary": "#c9943a",         # Muted amber
        "accent": "#5a9a6a",            # Muted green
        "background": "#1a1d23",        # Dark grey (not pure black)
        "surface": "#22262e",           # Card background
        "surface_variant": "#2a2f38",   # Elevated surfaces
        "bg_primary": "#ffffff",
        "text_primary": "#e8eaed",      # High contrast text
        "text_secondary": "#9aa0a6",    # Muted text
        "border": "#373e47",            # Subtle borders
        "hover": "#323842",             # Hover state
        "success": "#3d9a5f",           # Muted green
        "warning": "#c9943a",           # Amber for warnings
        "error": "#c95a5a",             # Muted red for errors
        "info": "#5b8ec9",              # Muted blue for info
    },
    "dark": {
        "name": "🌑 Dark Mode",
        "primary": "#4a8fd9",
        "primary_dark": "#3a7fc9",
        "primary_light": "#5a9fe9",
        "secondary": "#c9943a",
        "accent": "#5a9a6a",
        "background": "#121418",        # Darker variant
        "surface": "#1a1d23",
        "surface_variant": "#22262e",
        "bg_primary": "#ffffff",
        "text_primary": "#e8eaed",
        "text_secondary": "#9aa0a6",
        "border": "#2d333b",
        "hover": "#2a2f38",
        "success": "#3d9a5f",
        "warning": "#c9943a",
        "error": "#c95a5a",
        "info": "#5b8ec9",
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
    "glass_frost": {
        "name": "🧊 Glass Frost",
        "primary": "#7AC0FF",
        "primary_dark": "#4D8FE8",
        "primary_light": "#A6D8FF",
        "secondary": "#9EF2D9",
        "accent": "#C7E9FF",
        "background": "#0F1626",
        "surface": "#161D2E",
        "surface_variant": "#1F283A",
        "bg_primary": "#ffffff",
        "text_primary": "#E7F5FF",
        "text_secondary": "#B8C4D8",
        "border": "#24334A",
        "hover": "#1A2538",
        "success": "#7FE0C2",
        "warning": "#F0C27B",
        "error": "#E88888",
        "info": "#7AC0FF",
    },
    "warm_clay": {
        "name": "🌅 Warm Clay",
        "primary": "#C46A3D",
        "primary_dark": "#A95530",
        "primary_light": "#E58C5D",
        "secondary": "#F0C27B",
        "accent": "#E8B197",
        "background": "#1F130F",
        "surface": "#2A1A14",
        "surface_variant": "#33211B",
        "bg_primary": "#ffffff",
        "text_primary": "#F5E9E0",
        "text_secondary": "#D3B8A7",
        "border": "#3D2922",
        "hover": "#3A241C",
        "success": "#7FB77E",
        "warning": "#F2C14E",
        "error": "#D75D5D",
        "info": "#F0C27B",
    },
    "midnight_wave": {
        "name": "🌌 Midnight Wave",
        "primary": "#5C6FF7",
        "primary_dark": "#2F3BB8",
        "primary_light": "#8EA0FF",
        "secondary": "#1EC8FF",
        "accent": "#22D2A0",
        "background": "#0B1021",
        "surface": "#0F152B",
        "surface_variant": "#121A33",
        "bg_primary": "#ffffff",
        "text_primary": "#E8ECFF",
        "text_secondary": "#A3B1D7",
        "border": "#1E2740",
        "hover": "#1A2340",
        "success": "#2ED8A3",
        "warning": "#F5B759",
        "error": "#FF6B7A",
        "info": "#6AA8FF",
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
    "glass_frost": {
        "name": "🧊 Glass Frost (Light)",
        "primary": "#4D8FE8",
        "primary_dark": "#3A6EC4",
        "primary_light": "#7AC0FF",
        "secondary": "#58E1C1",
        "accent": "#A8DEFF",
        "background": "#F5F8FF",
        "surface": "#FFFFFF",
        "surface_variant": "#ECF3FF",
        "bg_primary": "#ffffff",
        "text_primary": "#0F172A",
        "text_secondary": "#4B5568",
        "border": "#D6E4FF",
        "hover": "#E7F0FF",
        "success": "#36C9A4",
        "warning": "#F0C27B",
        "error": "#E88888",
        "info": "#4D8FE8",
    },
    "warm_clay": {
        "name": "🌅 Warm Clay (Light)",
        "primary": "#D27A48",
        "primary_dark": "#B56439",
        "primary_light": "#E9A36F",
        "secondary": "#F3C58A",
        "accent": "#EAC2A8",
        "background": "#FFF8F3",
        "surface": "#FFFFFF",
        "surface_variant": "#F7E8DE",
        "bg_primary": "#ffffff",
        "text_primary": "#2F1A14",
        "text_secondary": "#6A4A3A",
        "border": "#E6D2C6",
        "hover": "#F4E2D6",
        "success": "#7FB77E",
        "warning": "#F2C14E",
        "error": "#D75D5D",
        "info": "#D27A48",
    },
    "midnight_wave": {
        "name": "🌌 Midnight Wave (Light)",
        "primary": "#4658D8",
        "primary_dark": "#3340A8",
        "primary_light": "#6F80FF",
        "secondary": "#1AA9E5",
        "accent": "#25C79C",
        "background": "#F4F6FF",
        "surface": "#FFFFFF",
        "surface_variant": "#E7EBFF",
        "bg_primary": "#ffffff",
        "text_primary": "#0F172A",
        "text_secondary": "#4B5568",
        "border": "#D8DEFF",
        "hover": "#E9EDFF",
        "success": "#2ED8A3",
        "warning": "#F5B759",
        "error": "#FF6B7A",
        "info": "#6AA8FF",
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


def validate_pin_strength(pin: str) -> Tuple[bool, list]:
    """
    Validate PIN against security requirements.
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check length
    if len(pin) < PIN_MIN_LENGTH or len(pin) > PIN_MAX_LENGTH:
        errors.append(f"PIN must be {PIN_MIN_LENGTH}-{PIN_MAX_LENGTH} digits")
        return (False, errors)
    
    # Check if all digits
    if not pin.isdigit():
        errors.append("PIN must contain only numbers")
        return (False, errors)
    
    # Check for weak patterns
    if pin in WEAK_PIN_PATTERNS:
        errors.append("PIN is too simple - avoid repeated digits or sequences")
        return (False, errors)
    
    return (True, [])


def validate_password_strength(password: str) -> Tuple[bool, list]:
    """
    Validate password against security requirements.
    Returns: (is_valid, list_of_missing_requirements)
    
    NOTE: This is kept for backwards compatibility during migration.
    New accounts should use validate_pin_strength() instead.
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


# Theme preference cache - invalidated when theme is saved
_theme_cache_valid = True

def load_theme_preference() -> str:
    """Load saved theme or return default (cached for performance)"""
    return _load_theme_preference_cached()

@lru_cache(maxsize=1)
def _load_theme_preference_cached() -> str:
    """Internal cached theme loader"""
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
    """Save theme preference to file and invalidate cache"""
    try:
        with open(THEME_PREFERENCE_FILE, 'w') as f:
            f.write(theme_name)
        # Invalidate cache when theme is saved
        _load_theme_preference_cached.cache_clear()
    except Exception as e:
        logging.error(f"Could not save theme preference: {e}")


@lru_cache(maxsize=4)
def get_modern_stylesheet(theme_name="default", is_light_mode=False) -> str:
    """
    Generate modern stylesheet with selected theme - ULTRA STYLISH v5.0
    Cached for performance (maxsize=4 for dark/light variants of 2 themes)
    
    MODERN CSS EFFECTS:
    - Dark themes: Colored glow effects on hover/focus using theme accent colors
    - Light themes: Soft neumorphic shadows for depth
    - All buttons: 22px pill-shaped with trendy modern effects
    - Noticeable hover/focus transitions throughout

    Args:
        theme_name: Name of the color theme (default, cyberpunk, nord, etc.)
        is_light_mode: If True, use light theme variants; if False, use dark variants
    """
    # Select theme dict based on light/dark mode
    theme_dict = MODERN_THEMES_LIGHT if is_light_mode else MODERN_THEMES
    c = theme_dict.get(theme_name, theme_dict["default"])
    
    # Helper function to extract RGB from hex for rgba() usage
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Get RGB values for glow/shadow effects
    primary_rgb = hex_to_rgb(c['primary'])
    accent_rgb = hex_to_rgb(c.get('accent', c['primary']))
    
    # Theme-adaptive effects
    if is_light_mode:
        # LIGHT MODE: Neumorphic soft shadows
        input_focus_effect = f"border: 2px solid {c['primary']}; background-color: {c['surface']};"
        button_hover_effect = f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['primary_light']}, stop:1 {c['primary']});
            border: 2px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.4);
        """
        card_shadow = f"border: 1px solid {c['border']}; background-color: {c['surface']};"
        glow_border_hover = f"border: 2px solid {c['primary']};"
        input_glow = f"border: 2px solid {c['primary']};"
    else:
        # DARK MODE: Colored glow effects
        input_focus_effect = f"""
            border: 2px solid {c['primary']};
            background-color: {c['surface_variant']};
        """
        button_hover_effect = f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.15),
                stop:0.5 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.5),
                stop:1 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.7));
            border: 2px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.6);
            border-top: 2px solid rgba(255, 255, 255, 0.3);
        """
        card_shadow = f"border: 1px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.3);"
        glow_border_hover = f"border: 2px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.7);"
        input_glow = f"border: 2px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.8);"

    return f"""
    /* ====== MODERN UI v5.0 - TRENDY EFFECTS ====== */
    * {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
        letter-spacing: 0.2px;
    }}

    QMainWindow, QDialog, QWidget {{
        background-color: {c['background']};
        color: {c['text_primary']};
    }}

    /* ====== MODERN INPUT FIELDS - FROSTED / SOFT ====== */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
        background: {'rgba(255, 255, 255, 0.08)' if not is_light_mode else c['surface']};
        color: {'white' if not is_light_mode else c['text_primary']};
        border: {'1px solid rgba(255, 255, 255, 0.18)' if not is_light_mode else '1px solid ' + c['border']};
        border-radius: 14px;
        padding: 10px 14px;
        min-height: 44px;
        font-size: 13px;
        selection-background-color: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.5);
        selection-color: white;
    }}

    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QDateEdit:hover {{
        background: {'rgba(255, 255, 255, 0.12)' if not is_light_mode else c['surface_variant']};
        border: 1px solid {c['primary']};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
        border: 2px solid {c['primary']};
        background: {'rgba(' + str(primary_rgb[0]) + ', ' + str(primary_rgb[1]) + ', ' + str(primary_rgb[2]) + ', 0.15)' if not is_light_mode else c['surface_variant']};
        color: {c['text_primary']};
        outline: none;
    }}

    QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {{
        color: {'rgba(255, 255, 255, 0.35)' if not is_light_mode else c['text_secondary']};
    }}

    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled, QDateEdit:disabled {{
        background: {'rgba(255, 255, 255, 0.03)' if not is_light_mode else c['surface_variant']};
        border: {'1px solid rgba(255, 255, 255, 0.1)' if not is_light_mode else '1px solid ' + c['border']};
        color: {'rgba(255, 255, 255, 0.3)' if not is_light_mode else c['text_secondary']};
    }}

    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background: {'rgba(255, 255, 255, 0.1)' if not is_light_mode else c['surface_variant']};
        border: none;
        border-radius: 8px;
        width: 20px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.3);
    }}

    QComboBox QAbstractItemView {{
        background: {c['surface']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        selection-background-color: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.2);
        selection-color: {c['text_primary']};
        outline: none;
        padding: 6px;
    }}

    /* ====== MODERN BUTTONS - 22px PILL SHAPE + EFFECTS ====== */
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {'rgba(255, 255, 255, 0.08)' if not is_light_mode else c['primary_light']},
            stop:0.5 {c['primary']},
            stop:1 {c['primary_dark']});
        color: {c['bg_primary']};
        border: {'1px solid rgba(255, 255, 255, 0.18)' if not is_light_mode else '1px solid ' + c['border']};
        border-top: {'1px solid rgba(255, 255, 255, 0.25)' if not is_light_mode else '1px solid ' + c['border']};
        border-radius: 16px;
        padding: 10px 18px;
        font-weight: 600;
        font-size: 13px;
        min-height: 40px;
    }}

    QPushButton:hover {{
        {button_hover_effect}
    }}

    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary_dark']},
            stop:1 rgba({primary_rgb[0]//2}, {primary_rgb[1]//2}, {primary_rgb[2]//2}, 0.9));
        border: 1px solid {c['primary_dark']};
    }}

    QPushButton:focus {{
        outline: none;
        border: 2px solid {c['primary']};
    }}

    QPushButton:checked {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        border: 2px solid {c['primary_dark']};
        color: {c['bg_primary']};
    }}

    QPushButton:disabled {{
        background-color: {c['surface_variant']};
        color: {c['text_secondary']};
        border: 1px solid {c['border']};
    }}

    /* ====== MODERN COMBOBOX - iOS STYLE ====== */
    QComboBox::drop-down {{
        border: none;
        width: 30px;
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {'rgba(255, 255, 255, 0.7)' if not is_light_mode else c['text_secondary']};
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(' + str(primary_rgb[0]) + ', ' + str(primary_rgb[1]) + ', ' + str(primary_rgb[2]) + ', 0.4)'};
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
        outline: none;
        border-radius: 12px;
        padding: 6px;
    }}

    QComboBox QAbstractItemView::item {{
        padding: 8px 12px;
        border-radius: 8px;
        margin: 2px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background-color: {c['hover']};
    }}

    /* ====== ENHANCED TABLES - MODERN GLOW/SHADOW ====== */
    QTableView {{
        background-color: {c['surface']};
        alternate-background-color: {c['surface_variant']};
        color: {c['text_primary']};
        gridline-color: transparent;
        border: none;
        border-radius: 12px;
        selection-background-color: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.3);
    }}

    QTableView::item {{
        padding: 10px 12px;
        border: none;
        border-bottom: 1px solid {'rgba(0, 0, 0, 0.08)' if is_light_mode else 'rgba(255, 255, 255, 0.05)'};
    }}

    QTableView::item:hover {{
        background-color: {'rgba(' + str(primary_rgb[0]) + ', ' + str(primary_rgb[1]) + ', ' + str(primary_rgb[2]) + ', 0.1)' if is_light_mode else 'rgba(' + str(primary_rgb[0]) + ', ' + str(primary_rgb[1]) + ', ' + str(primary_rgb[2]) + ', 0.15)'};
    }}

    QTableView::item:selected {{
        background-color: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.25);
        color: {c['text_primary']};
        border-left: 4px solid {c['primary']};
    }}

    QHeaderView::section {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']},
            stop:1 {c['surface']});
        color: {c['text_primary']};
        padding: 12px 10px;
        border: none;
        border-right: 1px solid {'rgba(0, 0, 0, 0.1)' if is_light_mode else 'rgba(255, 255, 255, 0.08)'};
        border-bottom: 3px solid {c['primary']};
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    QHeaderView::section:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.15),
            stop:1 {c['surface_variant']});
    }}

    /* ====== MODERN GROUP BOXES - CARD STYLE ====== */
    QGroupBox {{
        background-color: {c['surface']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.08)'};
        border-radius: 16px;
        margin-top: 16px;
        padding: 16px 12px 12px 12px;
        font-weight: 600;
        color: {c['text_primary']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 6px 16px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        color: {c['bg_primary']};
        border-radius: 12px;
        font-weight: 700;
        font-size: 13px;
        margin-left: 8px;
    }}

    /* ====== HIDDEN SCROLLBARS - iOS STYLE ====== */
    QScrollBar:vertical {{
        background: transparent;
        width: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: transparent;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: transparent;
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}

    /* ====== MODERN TABS - PILL STYLE ====== */
    QTabWidget::pane {{
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.08)'};
        background-color: {c['surface']};
        border-radius: 12px;
        margin-top: -1px;
    }}

    QTabBar::tab {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']},
            stop:1 {c['surface']});
        color: {c['text_secondary']};
        padding: 10px 22px;
        margin-right: 4px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        font-weight: 500;
        font-size: 13px;
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.05)'};
        border-bottom: none;
    }}

    QTabBar::tab:selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        color: {c['bg_primary']};
        font-weight: 700;
        border: 1px solid {c['primary']};
        border-bottom: none;
    }}

    QTabBar::tab:hover:!selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.15),
            stop:1 {c['surface_variant']});
        color: {c['text_primary']};
    }}

    /* ====== MODERN PROGRESS BAR - GRADIENT ====== */
    QProgressBar {{
        background-color: {c['surface_variant']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        border-radius: 10px;
        text-align: center;
        height: 22px;
        font-size: 11px;
        font-weight: 600;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']},
            stop:0.5 {c['primary_light']},
            stop:1 {c['primary']});
        border-radius: 8px;
    }}

    /* ====== MODERN SLIDER - TRENDY ====== */
    QSlider::groove:horizontal {{
        background: {'rgba(0, 0, 0, 0.1)' if is_light_mode else 'rgba(255, 255, 255, 0.1)'};
        height: 8px;
        border-radius: 4px;
        border: none;
    }}

    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary_light']},
            stop:1 {c['primary']});
        width: 20px;
        height: 20px;
        margin: -6px 0;
        border-radius: 10px;
        border: 3px solid {c['surface']};
    }}

    QSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 1),
            stop:1 {c['primary_light']});
        border: 3px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.3);
    }}

    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']},
            stop:1 {c['primary_light']});
        border-radius: 4px;
    }}

    QSlider::groove:vertical {{
        background: {'rgba(0, 0, 0, 0.1)' if is_light_mode else 'rgba(255, 255, 255, 0.1)'};
        width: 8px;
        border-radius: 4px;
        border: none;
    }}

    QSlider::handle:vertical {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary_light']},
            stop:1 {c['primary']});
        height: 20px;
        width: 20px;
        margin: 0 -6px;
        border-radius: 10px;
        border: 3px solid {c['surface']};
    }}

    QSlider::handle:vertical:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 1),
            stop:1 {c['primary_light']});
        border: 3px solid rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.3);
    }}

    /* ====== MODERN CALENDAR - TRENDY STYLE ====== */
    QCalendarWidget {{
        background-color: {c['surface']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        border-radius: 16px;
        padding: 8px;
    }}

    QCalendarWidget QWidget {{
        background-color: {c['surface']};
        color: {c['text_primary']};
    }}

    QCalendarWidget QToolButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']},
            stop:1 {c['surface']});
        border-radius: 12px;
        padding: 10px 16px;
        color: {c['text_primary']};
        font-weight: 600;
        font-size: 13px;
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        margin: 3px;
        min-width: 75px;
    }}

    QCalendarWidget QToolButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        color: {c['bg_primary']};
        border-color: {c['primary']};
    }}

    QCalendarWidget QToolButton:pressed {{
        background: {c['primary_dark']};
        color: {c['bg_primary']};
    }}

    QCalendarWidget QToolButton::menu-indicator {{
        image: none;
        width: 0px;
    }}

    QCalendarWidget QMenu {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.15)'};
        border-radius: 12px;
        padding: 6px;
    }}

    QCalendarWidget QMenu::item {{
        padding: 8px 18px;
        border-radius: 8px;
    }}

    QCalendarWidget QMenu::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        color: {c['bg_primary']};
    }}

    QCalendarWidget QSpinBox {{
        background-color: {c['surface_variant']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        border-radius: 10px;
        padding: 8px 14px;
        font-weight: 600;
        font-size: 13px;
        min-width: 100px;
        selection-background-color: {c['primary']};
    }}

    QCalendarWidget QSpinBox:hover {{
        border-color: {c['primary']};
    }}

    QCalendarWidget QSpinBox:focus {{
        border: 2px solid {c['primary']};
        background-color: {c['surface_variant']};
    }}

    QCalendarWidget QSpinBox::up-button,
    QCalendarWidget QSpinBox::down-button {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        border-radius: 6px;
        width: 22px;
        height: 14px;
        border: none;
        margin: 2px;
    }}

    QCalendarWidget QSpinBox::up-button:hover,
    QCalendarWidget QSpinBox::down-button:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary_light']},
            stop:1 {c['primary']});
    }}

    QCalendarWidget QSpinBox::up-button:pressed,
    QCalendarWidget QSpinBox::down-button:pressed {{
        background: {c['primary_dark']};
    }}

    /* Make the arrows more visible */
    QCalendarWidget QSpinBox::up-arrow {{
        width: 10px;
        height: 10px;
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 6px solid white;
    }}

    QCalendarWidget QSpinBox::down-arrow {{
        width: 10px;
        height: 10px;
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid white;
    }}

    QCalendarWidget QAbstractItemView {{
        color: {c['text_primary']};
        background-color: {c['surface']};
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
        outline: none;
        border: none;
        border-radius: 10px;
        padding: 6px;
    }}

    QCalendarWidget QAbstractItemView:enabled {{
        color: {c['text_primary']};
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
        font-size: 12px;
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
            stop:0 {c['surface_variant']},
            stop:1 {c['surface']});
        border-bottom: 3px solid {c['primary']};
        border-radius: 12px 12px 0 0;
        padding: 8px;
    }}

    /* Day names header styling */
    QCalendarWidget QAbstractItemView::item {{
        padding: 8px;
        border-radius: 8px;
    }}

    /* ====== MODERN CHECKBOXES & RADIO - TRENDY ====== */
    QCheckBox, QRadioButton {{
        color: {c['text_primary']};
        spacing: 10px;
        font-size: 13px;
    }}

    QCheckBox::indicator, QRadioButton::indicator {{
        width: 22px;
        height: 22px;
        border: 2px solid {'rgba(0, 0, 0, 0.2)' if is_light_mode else 'rgba(255, 255, 255, 0.2)'};
        border-radius: 6px;
        background-color: {c['surface']};
    }}

    QRadioButton::indicator {{
        border-radius: 11px;
    }}

    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        border-color: {c['primary']};
    }}

    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {c['primary']};
        background-color: {'rgba(' + str(primary_rgb[0]) + ', ' + str(primary_rgb[1]) + ', ' + str(primary_rgb[2]) + ', 0.1)'};
    }}

    /* ====== MODERN TOOLTIPS - FLOATING ====== */
    QToolTip {{
        background-color: {c['surface_variant']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.15)'};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 500;
    }}

    /* Labels */
    QLabel {{
        color: {c['text_primary']};
        background: transparent;
    }}

    /* Status Bar */
    QStatusBar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface']},
            stop:1 {c['surface_variant']});
        color: {c['text_secondary']};
        border-top: 2px solid {c['primary']};
        padding: 4px;
        font-size: 12px;
    }}

    /* ====== MENU & CONTEXT MENUS - MODERN ====== */
    QMenu {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.12)'};
        border-radius: 12px;
        padding: 8px;
    }}

    QMenu::item {{
        padding: 10px 24px 10px 16px;
        border-radius: 8px;
        margin: 2px 4px;
    }}

    QMenu::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.2),
            stop:1 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.1));
        color: {c['primary']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {'rgba(0, 0, 0, 0.1)' if is_light_mode else 'rgba(255, 255, 255, 0.1)'};
        margin: 6px 12px;
    }}

    QMenuBar {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border-bottom: 2px solid {c['primary']};
        padding: 4px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 8px 16px;
        border-radius: 8px;
    }}

    QMenuBar::item:selected {{
        background: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.2);
    }}

    /* ====== SPINBOX - MODERN ====== */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        border-radius: 12px;
        padding: 8px 12px;
        min-height: 32px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c['primary']};
    }}

    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary']},
            stop:1 {c['primary_dark']});
        border-radius: 6px;
        width: 22px;
        margin: 2px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['primary_light']},
            stop:1 {c['primary']});
    }}

    /* ====== SPLITTER - SUBTLE ====== */
    QSplitter::handle {{
        background: {'rgba(0, 0, 0, 0.1)' if is_light_mode else 'rgba(255, 255, 255, 0.1)'};
    }}

    QSplitter::handle:hover {{
        background: {c['primary']};
    }}

    QSplitter::handle:horizontal {{
        width: 3px;
    }}

    QSplitter::handle:vertical {{
        height: 3px;
    }}

    /* ====== LIST VIEW & TREE VIEW - MODERN ====== */
    QListView, QTreeView {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.08)'};
        border-radius: 12px;
        padding: 6px;
        outline: none;
    }}

    QListView::item, QTreeView::item {{
        padding: 10px 12px;
        border-radius: 8px;
        margin: 2px 0;
    }}

    QListView::item:hover, QTreeView::item:hover {{
        background: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.1);
    }}

    QListView::item:selected, QTreeView::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.25),
            stop:1 rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.15));
        color: {c['text_primary']};
        border-left: 4px solid {c['primary']};
    }}

    /* ====== DOCK WIDGET - MODERN ====== */
    QDockWidget {{
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
    }}

    QDockWidget::title {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['surface_variant']},
            stop:1 {c['surface']});
        padding: 10px;
        border-bottom: 2px solid {c['primary']};
    }}

    /* ====== TOOL BUTTON - PILL ====== */
    QToolButton {{
        background: transparent;
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        border-radius: 12px;
        padding: 8px 14px;
        color: {c['text_primary']};
    }}

    QToolButton:hover {{
        background: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.15);
        border-color: {c['primary']};
    }}

    QToolButton:pressed {{
        background: rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.25);
    }}

    /* ====== FRAME - SUBTLE BORDER ====== */
    QFrame {{
        border-radius: 8px;
    }}

    QFrame[frameShape="4"], QFrame[frameShape="5"] {{
        background: {'rgba(0, 0, 0, 0.08)' if is_light_mode else 'rgba(255, 255, 255, 0.08)'};
        max-height: 1px;
    }}

    /* ====== TEXT BROWSER - MODERN ====== */
    QTextBrowser {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: {'1px solid ' + c['border'] if is_light_mode else '1px solid rgba(255, 255, 255, 0.1)'};
        border-radius: 12px;
        padding: 12px;
        selection-background-color: {c['primary']};
        selection-color: {c['bg_primary']};
    }}

    /* ====== PROGRESS BAR (Modern style) ====== */
    QProgressBar {{
        border: 2px solid {'rgba(0, 0, 0, 0.1)' if is_light_mode else 'rgba(255, 255, 255, 0.1)'};
        border-radius: 12px;
        background-color: {c['surface']};
        text-align: center;
        color: {c['text_primary']};
        font-weight: bold;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']}, stop:1 {c['primary_light']});
        border-radius: 10px;
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
        font-size: 13px;
    }}

    QMessageBox QPushButton {{
        min-width: 90px;
        padding: 10px 20px;
        border-radius: 22px;
    }}

    /* ====== DIALOG BUTTONS - CONSISTENT ====== */
    QDialogButtonBox QPushButton {{
        min-width: 90px;
        padding: 10px 20px;
        border-radius: 22px;
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

def _hash_pin(pin: str) -> str:
    """
    Hash PIN using bcrypt with automatic salt generation.
    PINs are hashed just like passwords for security.

    Args:
        pin: Plain text PIN (4-6 digits)

    Returns:
        Bcrypt hashed PIN (includes salt)
    """
    try:
        return bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        logging.error(f"PIN hashing failed: {e}")
        raise


def _verify_pin(pin: str, hashed: str) -> bool:
    """
    Verify PIN against bcrypt hash.

    Args:
        pin: Plain text PIN to verify
        hashed: Bcrypt hashed PIN from database

    Returns:
        True if PIN matches, False otherwise
    """
    try:
        # Normal bcrypt verification
        return bcrypt.checkpw(pin.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logging.error(f"PIN verification failed: {e}")
        return False


def _hash_pwd(password: str) -> str:
    """
    Hash password using bcrypt with automatic salt generation.
    This is the industry standard for secure password storage.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password (includes salt)
        
    NOTE: This is kept for backwards compatibility during migration.
    New accounts should use _hash_pin() instead.
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
        # Reject legacy SHA-256 hashes - they must be reset
        if len(hashed) == 64 and all(c in '0123456789abcdef' for c in hashed.lower()):
            logging.error("Legacy SHA-256 hash detected - user must reset password/PIN")
            return False  # Force password reset for legacy users

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
    Called on app startup if network is available.
    """
    import shutil
    
    if not USE_NETWORK_DB:
        logging.info("Not using network database - sync skipped")
        return False
    
    try:
        if os.path.exists(NETWORK_DB_PATH):
            # Create backup directory if needed
            os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
            
            # Copy network database to local
            shutil.copy2(NETWORK_DB_PATH, LOCAL_DB_PATH)
            logging.info(f"✓ Database synced from network to local: {LOCAL_DB_PATH}")
            return True
        else:
            logging.warning("Network database not found - cannot sync")
            return False
    except Exception as e:
        logging.error(f"Failed to sync database from network: {e}")
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
