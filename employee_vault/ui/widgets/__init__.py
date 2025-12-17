"""
UI Widgets Package - Modern Animated Widgets
Includes smooth animations, modern effects, and CSS-like styling
"""

from .widgets import (
    ValidatedLineEdit, UserFriendlyMessageBox, DataIntegrityChecker,
    IntegrityCheckDialog, PaginationWidget, WheelEventFilter,
    PasswordRequirementsWidget, CollapsibleSection, FormSection, WheelGuard,
    ModernCalendarWidget, ModernDateEdit, CalendarPopup, DatePicker, db_latest_mtime,
    LoadingSpinner, ToastNotification, show_toast, SimpleProgressDialog,
    AnimatedButton, LoadingOverlay, create_circular_pixmap,
    PageTransitionWidget, CollapsibleSidebar, SkeletonLoader, RippleButton,
    SlideInWidget, SimpleChartWidget, titlecase, normalize_ph_phone,
    NoCursorEventFilter, disable_cursor_changes, remove_focus_rectangle, apply_table_fixes,
    safe_file_path, WheelColumn, WheelDatePickerPopup
)

# New modern animated widgets
from .animated_button import (
    AnimatedButton as ModernAnimatedButton, PulseButton, IconButton,
    GradientGlowButton, NeumorphicButton
)
from .animated_input import (
    FloatingLabelLineEdit, ShakeLineEdit, GlowLineEdit, SuccessLineEdit,
    ModernValidatedInput, NeumorphicGradientLineEdit, NeumorphicGradientPasswordInput,
    NeumorphicGradientComboBox, NeumorphicGradientTextEdit, NeumorphicGradientSpinBox,
    NeumorphicGradientDateEdit
)
from .skeleton_loader import (
    SkeletonWidget, SkeletonLine, SkeletonCircle, SkeletonBlock,
    SkeletonEmployeeRow, SkeletonEmployeeList, SkeletonCard,
    SkeletonDashboard, SkeletonForm, SkeletonProfile, PulsingDot
)
from .glassmorphism import (
    GlassPanel, GlassPanelDark, AnimatedGlassPanel, GlassCard,
    NeumorphicButton, GlassToast, GlassmorphicButton
)
from .animated_dialog import (
    AnimatedDialog, ScaleDialog, SlideUpDialog, FadeDialog, BounceDialog,
    AnimatedDialogBase, QuickAnimatedDialog, SmoothAnimatedDialog
)
from .page_transitions import (
    PageTransitionManager, SlidingStackedWidget, FadingStackedWidget
)
from .image_viewer import ModernImageViewer
from .modern_id_templates import (
    ModernIDCardTemplate, GoogleStyleTemplate, AppleStyleTemplate, get_template
)
from .advanced_reports import (
    PieChartWidget, BarChartWidget, LineChartWidget, AdvancedReportsDialog
)
from .contract_expiry_checker import (
    ContractExpiryChecker, ContractExpiryNotificationDialog, ContractExpiryWidget
)
from .notification_center import (
    NotificationCenter, NotificationBell, NotificationItem, 
    NotificationBadge, FloatingNotificationPanel
)
from .thumbnail_cache import (
    ThumbnailCache, get_thumbnail_cache, load_employee_thumbnail,
    create_circular_thumbnail, ThumbnailLoader
)
from .animated_login_card import AnimatedLoginCard
from .animated_background import AnimatedGradientBackground, AnimatedBackgroundContainer
from .stacked_card_gallery import StackedCardGallery, StackedCard, GalleryPreviewDialog

# New animation system imports
try:
    from employee_vault.ui.widgets.advanced_effects import (
        RippleButton as AdvancedRippleButton, CountUpLabel, 
        ElevatedCard, ShineEffect, PulseWidget,
        GlowPulseLineEdit, BounceCheckBox, HoverScaleWidget
    )
    from employee_vault.ui.widgets.loading_effects import (
        ShimmerSkeleton, ModernSpinner, BreathingDots, ProgressBar as ModernProgressBar
    )
except ImportError:
    # Fallback if new modules not available
    AdvancedRippleButton = None
    CountUpLabel = None
    ElevatedCard = None
    ShineEffect = None
    GlowPulseLineEdit = None
    BounceCheckBox = None
    HoverScaleWidget = None
    PulseWidget = None
    ShimmerSkeleton = None
    ModernSpinner = None
    BreathingDots = None
    ModernProgressBar = None

__all__ = [
    # Original widgets
    "ValidatedLineEdit", "UserFriendlyMessageBox", "DataIntegrityChecker",
    "IntegrityCheckDialog", "PaginationWidget", "WheelEventFilter",
    "PasswordRequirementsWidget", "CollapsibleSection", "FormSection", "WheelGuard",
    "ModernCalendarWidget", "ModernDateEdit", "CalendarPopup", "DatePicker", "db_latest_mtime",
    "LoadingSpinner", "ToastNotification", "show_toast", "SimpleProgressDialog",
    "AnimatedButton", "LoadingOverlay", "create_circular_pixmap",
    "PageTransitionWidget", "CollapsibleSidebar", "SkeletonLoader", "RippleButton",
    "SlideInWidget", "SimpleChartWidget", "titlecase", "normalize_ph_phone",
    "NoCursorEventFilter", "disable_cursor_changes", "remove_focus_rectangle", "apply_table_fixes",
    "safe_file_path", "WheelColumn", "WheelDatePickerPopup",

    # Modern animated widgets
    "ModernAnimatedButton", "PulseButton", "IconButton",
    "GradientGlowButton", "NeumorphicButton",
    "FloatingLabelLineEdit", "ShakeLineEdit", "GlowLineEdit", "SuccessLineEdit",
    "ModernValidatedInput", "NeumorphicGradientLineEdit", "NeumorphicGradientPasswordInput",
    "NeumorphicGradientComboBox", "NeumorphicGradientTextEdit", "NeumorphicGradientSpinBox",
    "NeumorphicGradientDateEdit",
    "SkeletonWidget", "SkeletonLine", "SkeletonCircle", "SkeletonBlock",
    "SkeletonEmployeeRow", "SkeletonEmployeeList", "SkeletonCard",
    "SkeletonDashboard", "SkeletonForm", "SkeletonProfile", "PulsingDot",
    "GlassPanel", "GlassPanelDark", "AnimatedGlassPanel", "GlassCard",
    "NeumorphicButton", "GlassToast", "GlassmorphicButton",
    "AnimatedDialog", "ScaleDialog", "SlideUpDialog", "FadeDialog", "BounceDialog",
    "AnimatedDialogBase", "QuickAnimatedDialog", "SmoothAnimatedDialog",
    "PageTransitionManager", "SlidingStackedWidget", "FadingStackedWidget",
    "ModernImageViewer",
    "ModernIDCardTemplate", "GoogleStyleTemplate", "AppleStyleTemplate", "get_template",
    "PieChartWidget", "BarChartWidget", "LineChartWidget", "AdvancedReportsDialog",
    "ContractExpiryChecker", "ContractExpiryNotificationDialog", "ContractExpiryWidget",
    "NotificationCenter", "NotificationBell", "NotificationItem", 
    "NotificationBadge", "FloatingNotificationPanel",
    "ThumbnailCache", "get_thumbnail_cache", "load_employee_thumbnail",
    "create_circular_thumbnail", "ThumbnailLoader",
    "AnimatedLoginCard",
    "AnimatedGradientBackground", "AnimatedBackgroundContainer",
    "StackedCardGallery", "StackedCard", "GalleryPreviewDialog",
    
    # New animation system (v4.5.0)
    "AdvancedRippleButton", "CountUpLabel", "ElevatedCard", "ShineEffect", "PulseWidget",
    "ShimmerSkeleton", "ModernSpinner", "BreathingDots", "ModernProgressBar",
]
