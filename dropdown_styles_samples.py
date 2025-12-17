"""
DROPDOWN STYLING OPTIONS - SAMPLE FILE
Copy the desired style block into animated_input.py NeumorphicGradientComboBox.__init__()
Replace the self.combo_box.setStyleSheet() section with your chosen option.
"""

# =============================================================================
# OPTION 1: GLASSMORPHISM BACKDROP (Most Modern - Recommended)
# =============================================================================
OPTION_1_GLASSMORPHISM = """
            QComboBox#neumorphicInnerComboBox {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QComboBox#neumorphicInnerComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox#neumorphicInnerComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox#neumorphicInnerComboBox:focus {
                color: #FFFFFF;
            }
            QComboBox#neumorphicInnerComboBox:disabled {
                color: rgba(255, 255, 255, 0.6);
            }

            /* Glassmorphism Popup - Frosted Glass Effect */
            QComboBox QAbstractItemView {
                background: rgba(28, 28, 35, 0.75);   /* Semi-transparent dark background */
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-top: 2px solid rgba(74, 158, 255, 0.5);   /* Blue accent top */
                border-radius: 12px;
                padding: 8px;
                outline: none;
                margin-top: 4px;
            }

            /* Individual Item Styling */
            QComboBox QAbstractItemView::item {
                min-height: 36px;
                padding: 8px 12px;
                border-radius: 8px;
                color: white;
                background: transparent;
                margin: 2px 4px;
            }

            /* Hover Effect - Glassmorphic Glow */
            QComboBox QAbstractItemView::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.15),
                    stop:0.5 rgba(74, 158, 255, 0.25),
                    stop:1 rgba(74, 158, 255, 0.15));
                border-left: 3px solid rgba(74, 158, 255, 0.8);
            }

            /* Selected Effect - Blue Highlight */
            QComboBox QAbstractItemView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.3),
                    stop:0.5 rgba(74, 158, 255, 0.5),
                    stop:1 rgba(74, 158, 255, 0.3));
                border-left: 3px solid #4a9eff;
            }

            /* Modern Scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: rgba(45, 45, 52, 0.3);
                width: 10px;
                border-radius: 5px;
                margin: 4px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.6),
                    stop:1 rgba(156, 39, 176, 0.6));
                border-radius: 5px;
                min-height: 30px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff,
                    stop:1 #9c27b0);
            }

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
"""


# =============================================================================
# OPTION 2: LAYERED NEUMORPHIC DEPTH (Subtle 3D Effect)
# =============================================================================
OPTION_2_NEUMORPHIC = """
            QComboBox#neumorphicInnerComboBox {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QComboBox#neumorphicInnerComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox#neumorphicInnerComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox#neumorphicInnerComboBox:focus {
                color: #FFFFFF;
            }
            QComboBox#neumorphicInnerComboBox:disabled {
                color: rgba(255, 255, 255, 0.6);
            }

            /* Neumorphic Popup - Extruded Effect */
            QComboBox QAbstractItemView {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(35, 35, 42, 0.98),
                    stop:0.5 rgba(28, 28, 35, 0.98),
                    stop:1 rgba(32, 32, 39, 0.98));
                border: 2px solid rgba(74, 158, 255, 0.4);
                border-radius: 12px;
                padding: 6px;
                outline: none;
                margin-top: 4px;
            }

            /* Individual Item Styling */
            QComboBox QAbstractItemView::item {
                min-height: 36px;
                padding: 8px 16px;
                border-radius: 8px;
                color: white;
                background: transparent;
                margin: 2px;
            }

            /* Hover Effect - Raised Surface */
            QComboBox QAbstractItemView::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(45, 48, 55, 0.9),
                    stop:1 rgba(35, 38, 45, 0.9));
                border-left: 4px solid rgba(74, 158, 255, 0.7);
            }

            /* Selected Effect - Pressed Surface */
            QComboBox QAbstractItemView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(28, 31, 38, 0.9),
                    stop:1 rgba(38, 41, 48, 0.9));
                border-left: 4px solid #4a9eff;
                color: #4a9eff;
            }

            /* Scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: rgba(35, 35, 42, 0.5);
                width: 8px;
                border-radius: 4px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: rgba(74, 158, 255, 0.5);
                border-radius: 4px;
                min-height: 30px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: rgba(74, 158, 255, 0.8);
            }

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
"""


# =============================================================================
# OPTION 3: ANIMATED GRADIENT SHIMMER (Dynamic Border)
# =============================================================================
OPTION_3_GRADIENT_SHIMMER = """
            QComboBox#neumorphicInnerComboBox {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QComboBox#neumorphicInnerComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox#neumorphicInnerComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox#neumorphicInnerComboBox:focus {
                color: #FFFFFF;
            }
            QComboBox#neumorphicInnerComboBox:disabled {
                color: rgba(255, 255, 255, 0.6);
            }

            /* Gradient Popup - Shifting Colors */
            QComboBox QAbstractItemView {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(28, 28, 35, 0.95),
                    stop:0.3 rgba(35, 40, 48, 0.95),
                    stop:0.6 rgba(28, 28, 35, 0.95),
                    stop:1 rgba(32, 36, 42, 0.95));
                border: 3px solid;
                border-image: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a9eff,
                    stop:0.25 #9c27b0,
                    stop:0.5 #00c8ff,
                    stop:0.75 #ff4081,
                    stop:1 #4a9eff);
                border-radius: 12px;
                padding: 6px;
                outline: none;
                margin-top: 4px;
            }

            /* Individual Item Styling */
            QComboBox QAbstractItemView::item {
                min-height: 36px;
                padding: 8px 14px;
                border-radius: 8px;
                color: white;
                background: transparent;
                margin: 2px 3px;
            }

            /* Hover Effect - Gradient Highlight */
            QComboBox QAbstractItemView::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.2),
                    stop:0.5 rgba(156, 39, 176, 0.3),
                    stop:1 rgba(74, 158, 255, 0.2));
                border-left: 3px solid transparent;
                border-image: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a9eff,
                    stop:1 #9c27b0);
            }

            /* Selected Effect - Full Gradient */
            QComboBox QAbstractItemView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.4),
                    stop:0.5 rgba(156, 39, 176, 0.5),
                    stop:1 rgba(74, 158, 255, 0.4));
                border-left: 3px solid #4a9eff;
                color: white;
            }

            /* Gradient Scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: rgba(35, 35, 42, 0.4);
                width: 10px;
                border-radius: 5px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a9eff,
                    stop:0.5 #9c27b0,
                    stop:1 #00c8ff);
                border-radius: 5px;
                min-height: 30px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66b5ff,
                    stop:0.5 #b855d4,
                    stop:1 #33d4ff);
            }

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
"""


# =============================================================================
# OPTION 4: DUAL-LAYER SHADOW (Clean & Professional)
# =============================================================================
OPTION_4_DUAL_SHADOW = """
            QComboBox#neumorphicInnerComboBox {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QComboBox#neumorphicInnerComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox#neumorphicInnerComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox#neumorphicInnerComboBox:focus {
                color: #FFFFFF;
            }
            QComboBox#neumorphicInnerComboBox:disabled {
                color: rgba(255, 255, 255, 0.6);
            }

            /* Shadow Popup - Professional Look */
            QComboBox QAbstractItemView {
                background-color: #1c1c23;
                border: 2px solid #4a9eff;
                border-radius: 12px;
                padding: 6px;
                outline: none;
                margin-top: 4px;
            }

            /* Individual Item Styling */
            QComboBox QAbstractItemView::item {
                min-height: 36px;
                padding: 8px 14px;
                border-radius: 8px;
                color: white;
                background: transparent;
                margin: 2px;
            }

            /* Hover Effect - Subtle Highlight */
            QComboBox QAbstractItemView::item:hover {
                background: rgba(74, 158, 255, 0.2);
                border-left: 3px solid rgba(74, 158, 255, 0.8);
            }

            /* Selected Effect - Blue Accent */
            QComboBox QAbstractItemView::item:selected {
                background: rgba(74, 158, 255, 0.4);
                border-left: 3px solid #4a9eff;
                color: white;
            }

            /* Simple Scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: rgba(45, 45, 52, 0.4);
                width: 8px;
                border-radius: 4px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: #4a9eff;
                border-radius: 4px;
                min-height: 30px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: #66b5ff;
            }

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
"""


# =============================================================================
# OPTION 5: RIPPLE EFFECT WITH ANIMATION (Most Interactive)
# =============================================================================
OPTION_5_RIPPLE = """
            QComboBox#neumorphicInnerComboBox {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QComboBox#neumorphicInnerComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox#neumorphicInnerComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox#neumorphicInnerComboBox:focus {
                color: #FFFFFF;
            }
            QComboBox#neumorphicInnerComboBox:disabled {
                color: rgba(255, 255, 255, 0.6);
            }

            /* Ripple Popup - Interactive Feel */
            QComboBox QAbstractItemView {
                background: rgba(28, 28, 35, 0.9);
                border: 2px solid rgba(74, 158, 255, 0.6);
                border-radius: 12px;
                padding: 6px;
                outline: none;
                margin-top: 4px;
            }

            /* Individual Item Styling */
            QComboBox QAbstractItemView::item {
                min-height: 38px;
                padding: 10px 16px;
                border-radius: 10px;
                color: white;
                background: transparent;
                margin: 3px 4px;
            }

            /* Hover Effect - Expanding Ripple */
            QComboBox QAbstractItemView::item:hover {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                    fx:0.5, fy:0.5,
                    stop:0 rgba(74, 158, 255, 0.4),
                    stop:0.5 rgba(74, 158, 255, 0.2),
                    stop:1 rgba(74, 158, 255, 0.05));
                border: 1px solid rgba(74, 158, 255, 0.5);
            }

            /* Selected Effect - Full Ripple Glow */
            QComboBox QAbstractItemView::item:selected {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                    fx:0.5, fy:0.5,
                    stop:0 rgba(74, 158, 255, 0.6),
                    stop:0.4 rgba(74, 158, 255, 0.4),
                    stop:1 rgba(74, 158, 255, 0.1));
                border: 1px solid #4a9eff;
                color: white;
            }

            /* Animated Scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: rgba(35, 35, 42, 0.5);
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.7),
                    stop:1 rgba(156, 39, 176, 0.7));
                border-radius: 5px;
                min-height: 30px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff,
                    stop:1 #9c27b0);
            }

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
"""


# =============================================================================
# OPTION 6: MINIMAL WITH ACCENT (Cleanest)
# =============================================================================
OPTION_6_MINIMAL = """
            QComboBox#neumorphicInnerComboBox {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QComboBox#neumorphicInnerComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox#neumorphicInnerComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox#neumorphicInnerComboBox:focus {
                color: #FFFFFF;
            }
            QComboBox#neumorphicInnerComboBox:disabled {
                color: rgba(255, 255, 255, 0.6);
            }

            /* Minimal Popup - Ultra Clean */
            QComboBox QAbstractItemView {
                background-color: #1c1c23;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-left: 3px solid #4a9eff;  /* Accent bar */
                border-radius: 8px;
                padding: 4px 4px 4px 8px;
                outline: none;
                margin-top: 4px;
            }

            /* Individual Item Styling */
            QComboBox QAbstractItemView::item {
                min-height: 34px;
                padding: 8px 12px;
                border-radius: 6px;
                color: white;
                background: transparent;
                margin: 1px 2px;
            }

            /* Hover Effect - Minimal Accent */
            QComboBox QAbstractItemView::item:hover {
                background: rgba(74, 158, 255, 0.15);
                color: #4a9eff;
            }

            /* Selected Effect - Blue Background */
            QComboBox QAbstractItemView::item:selected {
                background: rgba(74, 158, 255, 0.3);
                color: white;
            }

            /* Minimal Scrollbar */
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border-radius: 3px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: rgba(74, 158, 255, 0.5);
                border-radius: 3px;
                min-height: 25px;
            }

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: #4a9eff;
            }

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
"""


# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
"""
TO APPLY ANY STYLE:

1. Open: employee_vault/ui/widgets/animated_input.py

2. Find the NeumorphicGradientComboBox class __init__ method (around line 817)

3. Find the line: self.combo_box.setStyleSheet('''

4. Replace the entire stylesheet string with your chosen option from above

5. Save and restart the application

EXAMPLE:
    Replace this block:
        self.combo_box.setStyleSheet('''
            ... old styles ...
        ''')

    With:
        self.combo_box.setStyleSheet(OPTION_1_GLASSMORPHISM)

RECOMMENDATIONS:
- OPTION 1 (Glassmorphism): Most modern, works great with dark themes
- OPTION 2 (Neumorphic): Best for subtle depth, matches existing neumorphic fields
- OPTION 3 (Gradient): Most eye-catching, animated feel
- OPTION 4 (Dual Shadow): Most professional, clean business look
- OPTION 5 (Ripple): Most interactive, fun to use
- OPTION 6 (Minimal): Cleanest, least distraction

You can also MIX AND MATCH - take the popup style from one option and
the hover/selected effects from another!
"""
