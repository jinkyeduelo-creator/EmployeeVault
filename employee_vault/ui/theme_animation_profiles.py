"""
Theme-Specific Animation Profiles
Each theme has unique animation characteristics, effects, and transitions
that match its visual style and personality.
"""

from PySide6.QtCore import QEasingCurve


class ThemeAnimationProfile:
    """Base class for theme animation profiles"""

    def __init__(self):
        # Base animation properties
        self.transition_duration = 350
        self.hover_duration = 200
        self.click_duration = 150
        self.easing_curve = QEasingCurve.InOutQuad

        # Effect properties
        self.glow_enabled = False
        self.glow_intensity = 0.5
        self.ripple_enabled = True
        self.ripple_color = (255, 255, 255, 100)
        self.particle_enabled = False

        # Transition effects
        self.page_transition = "slide"  # slide, fade, scale, flip
        self.button_effect = "standard"  # standard, bounce, pulse, glow
        self.card_animation = "lift"  # lift, scale, glow


# ============================================================================
# THEME ANIMATION PROFILES
# ============================================================================

class DefaultThemeAnimation(ThemeAnimationProfile):
    """🌙 Dark Blue (Default) - Smooth, professional, Material Design inspired"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 350
        self.hover_duration = 200
        self.easing_curve = QEasingCurve.InOutQuad

        self.glow_enabled = False
        self.ripple_enabled = True
        self.ripple_color = (33, 150, 243, 120)  # Blue ripple

        self.page_transition = "slide"
        self.button_effect = "standard"
        self.card_animation = "lift"


class CyberpunkThemeAnimation(ThemeAnimationProfile):
    """⚡ Cyberpunk Neon - Fast, glitchy, electric effects"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 200  # Faster, snappier
        self.hover_duration = 100
        self.easing_curve = QEasingCurve.OutBack  # Overshoot effect

        self.glow_enabled = True
        self.glow_intensity = 1.0  # Maximum glow
        self.glow_colors = [(255, 0, 255), (0, 255, 255)]  # Neon magenta/cyan
        self.ripple_enabled = True
        self.ripple_color = (255, 0, 255, 180)  # Neon magenta ripple
        self.particle_enabled = True
        self.particle_color = (0, 255, 255, 200)  # Neon cyan particles

        self.page_transition = "glitch"  # Custom glitch effect
        self.button_effect = "pulse"  # Pulsing glow
        self.card_animation = "glow"  # Glowing edges
        self.scan_line_effect = True  # Cyberpunk scanlines
        self.chromatic_aberration = True  # RGB split effect


class NordThemeAnimation(ThemeAnimationProfile):
    """❄️ Nord Aurora - Smooth, calm, minimalist transitions"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 400  # Slower, more deliberate
        self.hover_duration = 250
        self.easing_curve = QEasingCurve.InOutCubic  # Smooth cubic

        self.glow_enabled = True
        self.glow_intensity = 0.4  # Subtle glow
        self.glow_colors = [(136, 192, 208), (163, 190, 140)]  # Nord frost colors
        self.ripple_enabled = True
        self.ripple_color = (136, 192, 208, 80)  # Soft cyan ripple

        self.page_transition = "fade"  # Gentle fade
        self.button_effect = "standard"
        self.card_animation = "lift"
        self.frost_effect = True  # Frosted glass blur on hover


class DraculaThemeAnimation(ThemeAnimationProfile):
    """🧛 Dracula Purple - Dramatic, elegant, gothic animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 450  # Dramatic timing
        self.hover_duration = 300
        self.easing_curve = QEasingCurve.OutElastic  # Bouncy, playful

        self.glow_enabled = True
        self.glow_intensity = 0.7
        self.glow_colors = [(189, 147, 249), (255, 121, 198)]  # Purple/pink glow
        self.ripple_enabled = True
        self.ripple_color = (189, 147, 249, 150)  # Purple ripple
        self.particle_enabled = True
        self.particle_color = (255, 121, 198, 180)  # Pink particles

        self.page_transition = "fade_scale"  # Fade + scale
        self.button_effect = "bounce"  # Bouncy click
        self.card_animation = "glow"
        self.shadow_intensity = 1.2  # Stronger shadows


class OceanThemeAnimation(ThemeAnimationProfile):
    """🌊 Ocean Breeze - Flowing, wave-like, liquid transitions"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 500  # Slow, flowing
        self.hover_duration = 350
        self.easing_curve = QEasingCurve.InOutSine  # Smooth wave

        self.glow_enabled = True
        self.glow_intensity = 0.6
        self.glow_colors = [(0, 119, 190), (77, 208, 225)]  # Ocean blue/cyan
        self.ripple_enabled = True
        self.ripple_color = (0, 188, 212, 100)  # Water ripple
        self.particle_enabled = True
        self.particle_color = (77, 208, 225, 150)  # Bubble particles

        self.page_transition = "wave"  # Wave/liquid transition
        self.button_effect = "ripple_spread"  # Expanding ripple
        self.card_animation = "float"  # Floating effect
        self.wave_effect = True  # Subtle wave distortion


class SunsetThemeAnimation(ThemeAnimationProfile):
    """🌅 Sunset Glow - Warm, gradient transitions, color shifts"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 600  # Slow, atmospheric
        self.hover_duration = 400
        self.easing_curve = QEasingCurve.InOutQuart  # Smooth acceleration

        self.glow_enabled = True
        self.glow_intensity = 0.8
        self.glow_colors = [(255, 107, 107), (255, 179, 71), (255, 221, 87)]  # Sunset gradient
        self.ripple_enabled = True
        self.ripple_color = (255, 179, 71, 130)  # Orange ripple
        self.particle_enabled = True
        self.particle_color = (255, 221, 87, 160)  # Golden particles

        self.page_transition = "fade_gradient"  # Gradient fade
        self.button_effect = "glow"  # Glowing pulse
        self.card_animation = "glow"
        self.gradient_shift = True  # Animated gradient colors
        self.color_bloom = True  # Color bleeding effect


class ForestThemeAnimation(ThemeAnimationProfile):
    """🌲 Forest Green - Natural, organic, growth-inspired animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 450
        self.hover_duration = 300
        self.easing_curve = QEasingCurve.OutCubic  # Natural ease out

        self.glow_enabled = True
        self.glow_intensity = 0.5
        self.glow_colors = [(76, 175, 80), (102, 187, 106)]  # Green glow
        self.ripple_enabled = True
        self.ripple_color = (76, 175, 80, 100)  # Green ripple
        self.particle_enabled = True
        self.particle_color = (102, 187, 106, 120)  # Leaf particles

        self.page_transition = "grow"  # Growing/sprouting effect
        self.button_effect = "standard"
        self.card_animation = "lift"
        self.organic_movement = True  # Slight random variation
        self.leaf_particles = True  # Falling leaf effect


class LavenderThemeAnimation(ThemeAnimationProfile):
    """💜 Lavender Dreams - Soft, dreamy, ethereal animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 550  # Slow, dreamy
        self.hover_duration = 350
        self.easing_curve = QEasingCurve.InOutQuad

        self.glow_enabled = True
        self.glow_intensity = 0.9  # Strong soft glow
        self.glow_colors = [(156, 39, 176), (225, 190, 231)]  # Purple gradient
        self.ripple_enabled = True
        self.ripple_color = (206, 147, 216, 140)  # Lavender ripple
        self.particle_enabled = True
        self.particle_color = (225, 190, 231, 180)  # Sparkle particles

        self.page_transition = "fade_blur"  # Dreamy blur transition
        self.button_effect = "glow"
        self.card_animation = "float_glow"  # Floating with glow
        self.blur_effect = True  # Soft blur on transitions
        self.sparkle_particles = True  # Twinkling sparkles


class CherryThemeAnimation(ThemeAnimationProfile):
    """🍒 Cherry Blossom - Delicate, falling petals, spring-like"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 500
        self.hover_duration = 350
        self.easing_curve = QEasingCurve.InOutSine  # Gentle sine wave

        self.glow_enabled = True
        self.glow_intensity = 0.6
        self.glow_colors = [(233, 30, 99), (248, 187, 208)]  # Pink gradient
        self.ripple_enabled = True
        self.ripple_color = (255, 64, 129, 120)  # Pink ripple
        self.particle_enabled = True
        self.particle_color = (248, 187, 208, 200)  # Petal particles

        self.page_transition = "petal_fall"  # Falling petals transition
        self.button_effect = "standard"
        self.card_animation = "lift"
        self.petal_particles = True  # Cherry blossom petals
        self.wind_effect = True  # Gentle drift/sway


class MidnightThemeAnimation(ThemeAnimationProfile):
    """🌃 Midnight Blue - Deep, starry, cosmic animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 450
        self.hover_duration = 300
        self.easing_curve = QEasingCurve.InOutQuad

        self.glow_enabled = True
        self.glow_intensity = 0.7
        self.glow_colors = [(63, 81, 181), (140, 158, 255)]  # Indigo glow
        self.ripple_enabled = True
        self.ripple_color = (83, 109, 254, 140)  # Indigo ripple
        self.particle_enabled = True
        self.particle_color = (140, 158, 255, 180)  # Star particles

        self.page_transition = "fade"
        self.button_effect = "glow"
        self.card_animation = "glow"
        self.star_particles = True  # Twinkling stars
        self.constellation_lines = True  # Connecting star lines


class AmberThemeAnimation(ThemeAnimationProfile):
    """🔥 Amber Fire - Warm, flickering, flame-like animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 300  # Quick, energetic
        self.hover_duration = 150
        self.easing_curve = QEasingCurve.OutBack  # Sharp, energetic

        self.glow_enabled = True
        self.glow_intensity = 1.0  # Strong glow
        self.glow_colors = [(255, 152, 0), (255, 193, 7), (255, 202, 40)]  # Fire gradient
        self.ripple_enabled = True
        self.ripple_color = (255, 193, 7, 160)  # Amber ripple
        self.particle_enabled = True
        self.particle_color = (255, 202, 40, 200)  # Ember particles

        self.page_transition = "burn"  # Fire burn effect
        self.button_effect = "pulse"  # Pulsing glow
        self.card_animation = "glow"
        self.flicker_effect = True  # Flame flicker
        self.ember_particles = True  # Rising embers
        self.heat_distortion = True  # Heat wave distortion


class MintThemeAnimation(ThemeAnimationProfile):
    """🌿 Mint Fresh - Crisp, refreshing, clean animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 350
        self.hover_duration = 200
        self.easing_curve = QEasingCurve.OutCubic  # Sharp, clean

        self.glow_enabled = True
        self.glow_intensity = 0.5
        self.glow_colors = [(0, 188, 212), (77, 208, 225)]  # Cyan/mint glow
        self.ripple_enabled = True
        self.ripple_color = (38, 166, 154, 120)  # Teal ripple
        self.particle_enabled = True
        self.particle_color = (128, 203, 196, 150)  # Mint particles

        self.page_transition = "slide"
        self.button_effect = "standard"
        self.card_animation = "lift"
        self.crisp_shadows = True  # Sharp, clean shadows
        self.bubble_particles = True  # Fresh bubble effect


class SimpleThemeAnimation(ThemeAnimationProfile):
    """✨ Simple & Clean - Minimal, functional, no-nonsense"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 250  # Fast, efficient
        self.hover_duration = 150
        self.easing_curve = QEasingCurve.InOutQuad

        self.glow_enabled = False  # No glow
        self.ripple_enabled = True
        self.ripple_color = (94, 108, 132, 80)  # Subtle gray ripple
        self.particle_enabled = False  # No particles

        self.page_transition = "fade"
        self.button_effect = "standard"
        self.card_animation = "lift"
        self.minimal_shadows = True  # Subtle shadows only


class GlassmorphismThemeAnimation(ThemeAnimationProfile):
    """💎 Glassmorphism - Frosted glass, blur, depth effects"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 400
        self.hover_duration = 250
        self.easing_curve = QEasingCurve.InOutQuad

        self.glow_enabled = True
        self.glow_intensity = 0.7
        self.glow_colors = [(102, 126, 234), (118, 75, 162)]  # Purple gradient
        self.ripple_enabled = True
        self.ripple_color = (102, 126, 234, 100)  # Glass ripple
        self.particle_enabled = True
        self.particle_color = (240, 147, 251, 150)  # Light particles

        self.page_transition = "glass_shatter"  # Glass breaking effect
        self.button_effect = "glow"
        self.card_animation = "frost"  # Frosting effect
        self.blur_background = True  # Background blur
        self.glass_refraction = True  # Light refraction
        self.depth_layers = True  # Layered depth


class NeumorphicThemeAnimation(ThemeAnimationProfile):
    """🎨 Neumorphic - Soft, shadow-based, tactile animations"""

    def __init__(self):
        super().__init__()
        self.transition_duration = 350
        self.hover_duration = 200
        self.easing_curve = QEasingCurve.InOutQuad

        self.glow_enabled = False  # No glow (shadows instead)
        self.ripple_enabled = True
        self.ripple_color = (88, 101, 242, 80)  # Subtle indigo ripple
        self.particle_enabled = False

        self.page_transition = "morph"  # Morphing transition
        self.button_effect = "press"  # Physical press effect
        self.card_animation = "press"  # Inset/outset shadows
        self.shadow_morph = True  # Morphing shadows
        self.tactile_feedback = True  # Physical button feel


# ============================================================================
# THEME PROFILE REGISTRY
# ============================================================================

THEME_ANIMATION_PROFILES = {
    "default": DefaultThemeAnimation(),
    "cyberpunk": CyberpunkThemeAnimation(),
    "nord": NordThemeAnimation(),
    "dracula": DraculaThemeAnimation(),
    "ocean": OceanThemeAnimation(),
    "sunset": SunsetThemeAnimation(),
    "forest": ForestThemeAnimation(),
    "lavender": LavenderThemeAnimation(),
    "cherry": CherryThemeAnimation(),
    "midnight": MidnightThemeAnimation(),
    "amber": AmberThemeAnimation(),
    "mint": MintThemeAnimation(),
    "simple": SimpleThemeAnimation(),
    "glassmorphism": GlassmorphismThemeAnimation(),
    "glass_frost": GlassmorphismThemeAnimation(),
    "neumorphic": NeumorphicThemeAnimation(),
    "warm_clay": SunsetThemeAnimation(),
    "midnight_wave": MidnightThemeAnimation(),
}


def get_theme_animation_profile(theme_name: str) -> ThemeAnimationProfile:
    """Get animation profile for a specific theme"""
    return THEME_ANIMATION_PROFILES.get(theme_name.lower(), THEME_ANIMATION_PROFILES["default"])
