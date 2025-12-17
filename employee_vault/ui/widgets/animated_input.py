"""
Modern Animated Input Fields with Floating Labels
Material Design-style input fields for PySide6
Includes Neumorphic Gradient Input with animated borders
"""

import math
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint,
    Property, QTimer, QVariantAnimation, QPointF, QRectF, QEvent
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QLinearGradient, QBrush, QPainterPath, QPalette, QMouseEvent
)
from PySide6.QtWidgets import (
    QLineEdit, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsOpacityEffect, QPushButton, QComboBox, QSpinBox, QDateEdit,
    QSizePolicy, QAbstractItemView, QStyledItemDelegate, QStyle, QApplication
)

from employee_vault.config import IOS_INPUT_STYLE


class FloatingLabelLineEdit(QWidget):
    """
    Line edit with floating label animation
    Label moves up when focused or has text
    """

    class _CustomLineEdit(QLineEdit):
        """Custom QLineEdit with proper focus event overrides"""
        def __init__(self, container_parent):
            super().__init__()
            self.container = container_parent

        def focusInEvent(self, event):
            """Override focus in event properly"""
            super().focusInEvent(event)
            self.container._handle_focus_in()

        def focusOutEvent(self, event):
            """Override focus out event properly"""
            self.deselect()
            self.setCursorPosition(0)
            super().focusOutEvent(event)
            self.container._handle_focus_out()

        def mousePressEvent(self, event):
            """Handle mouse press to ensure proper focus transfer"""
            super().mousePressEvent(event)
            if not self.hasFocus():
                self.setFocus(Qt.FocusReason.MouseFocusReason)

    def __init__(self, label_text="", parent=None, enable_glow=True):
        super().__init__(parent)
        self._label_text = label_text
        self._label_y = 28  
        self._border_width = 0 
        self._glow_opacity = 0.0 
        self._enable_glow = enable_glow 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(0)

        self.line_edit = self._CustomLineEdit(self)
        self.line_edit.setPlaceholderText("")

        self.line_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1.5px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 13px;
                color: white;
                min-height: 24px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1.5px solid rgba(255, 255, 255, 0.3);
            }
            QLineEdit:focus {
                border: 2px solid rgba(74, 158, 255, 0.6);
                background: rgba(74, 158, 255, 0.15);
                outline: none;
            }
            QLineEdit:read-only {
                background: rgba(255, 255, 255, 0.04);
                color: rgba(255, 255, 255, 0.6);
            }
        """)

        if label_text:
            self.line_edit.setAccessibleName(label_text)
            self.line_edit.setAccessibleDescription(f"Input field for {label_text}")

        self.line_edit.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.line_edit)
        self.setMinimumHeight(70) 

        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(100)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        if enable_glow:
            self._glow_anim = QPropertyAnimation(self, b"glow_opacity")
            self._glow_anim.setDuration(1500)
            self._glow_anim.setStartValue(0.15)
            self._glow_anim.setEndValue(0.4)
            self._glow_anim.setEasingCurve(QEasingCurve.InOutSine)
            self._glow_anim.setLoopCount(-1)
        else:
            self._glow_anim = None
    
    def get_glow_opacity(self):
        return self._glow_opacity
    
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    
    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    def get_label_y(self):
        return self._label_y

    def set_label_y(self, value):
        self._label_y = value
        self.update()

    label_y = Property(int, get_label_y, set_label_y)

    def get_border_width(self):
        return self._border_width

    def set_border_width(self, value):
        self._border_width = value
        self.update()

    border_width = Property(int, get_border_width, set_border_width)

    def _handle_focus_in(self):
        self.label_anim.stop()
        self.label_anim.setStartValue(self._label_y)
        self.label_anim.setEndValue(2) 
        self.label_anim.start()

        if self._glow_anim is not None:
            self._glow_anim.start()

    def _handle_focus_out(self):
        if not self.line_edit.text():
            self.label_anim.stop()
            self.label_anim.setStartValue(self._label_y)
            self.label_anim.setEndValue(28) 
            self.label_anim.start()

        if self._glow_anim is not None:
            self._glow_anim.stop()
            self._glow_opacity = 0.0
            self.update()

    def _on_text_changed(self, text):
        if text and self._label_y > 10:
            self.label_anim.stop()
            self.label_anim.setStartValue(self._label_y)
            self.label_anim.setEndValue(2) 
            self.label_anim.start()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._label_text:
            font = QFont()
            if self._label_y < 15:
                font.setPixelSize(11)
                font.setWeight(QFont.Weight.DemiBold)
                painter.setPen(QColor(74, 158, 255)) 
            else: 
                font.setPixelSize(13)
                label_color = QColor(255, 255, 255, 90) 
                painter.setPen(label_color)

            painter.setFont(font)
            painter.drawText(20, int(self._label_y + 12), self._label_text)

    def text(self): return self.line_edit.text()
    def setText(self, text): self.line_edit.setText(text)
    def setPlaceholderText(self, text): self._label_text = text
    def setEchoMode(self, mode): self.line_edit.setEchoMode(mode)
    @property
    def returnPressed(self): return self.line_edit.returnPressed
    def setFocus(self): self.line_edit.setFocus()
    def clear(self): self.line_edit.clear()
    def setReadOnly(self, read_only): self.line_edit.setReadOnly(read_only)
    def setValidator(self, validator): self.line_edit.setValidator(validator)
    def setCompleter(self, completer): self.line_edit.setCompleter(completer)
    def setStyleSheet(self, stylesheet): self.line_edit.setStyleSheet(stylesheet)
    def setToolTip(self, tooltip): self.line_edit.setToolTip(tooltip)
    def cursorPosition(self): return self.line_edit.cursorPosition()
    def setCursorPosition(self, pos): self.line_edit.setCursorPosition(pos)
    def blockSignals(self, block): return self.line_edit.blockSignals(block)
    @property
    def editingFinished(self): return self.line_edit.editingFinished
    @property
    def textChanged(self): return self.line_edit.textChanged


class ShakeLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pos = None
        self.shake_anim = QPropertyAnimation(self, b"geometry")
        self.shake_anim.setDuration(400)
        self.shake_anim.setEasingCurve(QEasingCurve.OutBounce)

    def shake(self):
        if not self._original_pos:
            self._original_pos = self.geometry()
        original = self._original_pos
        self.shake_anim.setKeyValueAt(0, original)
        self.shake_anim.setKeyValueAt(0.2, QRect(original.x() + 10, original.y(), original.width(), original.height()))
        self.shake_anim.setKeyValueAt(0.4, QRect(original.x() - 10, original.y(), original.width(), original.height()))
        self.shake_anim.setKeyValueAt(0.6, QRect(original.x() + 10, original.y(), original.width(), original.height()))
        self.shake_anim.setKeyValueAt(0.8, QRect(original.x() - 10, original.y(), original.width(), original.height()))
        self.shake_anim.setKeyValueAt(1, original)
        self.shake_anim.start()

    def moveEvent(self, event):
        if not self.shake_anim.state():
            self._original_pos = self.geometry()
        super().moveEvent(event)


class GlowLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(IOS_INPUT_STYLE)


class SuccessLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._validation_state = None
        self._indicator_opacity = 0
        self.indicator_anim = QPropertyAnimation(self, b"indicator_opacity")
        self.indicator_anim.setDuration(300)
        self.indicator_anim.setEasingCurve(QEasingCurve.OutBack)

    def get_indicator_opacity(self): return self._indicator_opacity
    def set_indicator_opacity(self, value): self._indicator_opacity = value; self.update()
    indicator_opacity = Property(int, get_indicator_opacity, set_indicator_opacity)

    def show_success(self):
        self._validation_state = 'success'
        self.indicator_anim.stop(); self.indicator_anim.setStartValue(0); self.indicator_anim.setEndValue(100); self.indicator_anim.start()

    def show_error(self):
        self._validation_state = 'error'
        self.indicator_anim.stop(); self.indicator_anim.setStartValue(0); self.indicator_anim.setEndValue(100); self.indicator_anim.start()

    def clear_validation(self):
        self.indicator_anim.stop(); self.indicator_anim.setStartValue(self._indicator_opacity); self.indicator_anim.setEndValue(0)
        self.indicator_anim.finished.connect(lambda: setattr(self, '_validation_state', None))
        self.indicator_anim.start()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._validation_state and self._indicator_opacity > 0:
            painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
            x = self.width() - 30; y = self.height() // 2
            opacity = int(self._indicator_opacity * 2.55)
            if self._validation_state == 'success':
                painter.setPen(QPen(QColor(76, 175, 80, opacity), 3))
                painter.drawLine(x, y, x + 4, y + 4); painter.drawLine(x + 4, y + 4, x + 10, y - 4)
            else:
                painter.setPen(QPen(QColor(244, 67, 54, opacity), 3))
                painter.drawLine(x, y - 4, x + 8, y + 4); painter.drawLine(x, y + 4, x + 8, y - 4)


class ModernValidatedInput(QWidget):
    STATE_NEUTRAL = "neutral"; STATE_VALID = "valid"; STATE_INVALID = "invalid"; STATE_LOADING = "loading"

    def __init__(self, label_text="", validator_func=None, parent=None):
        super().__init__(parent)
        self._label_text = label_text; self._validator_func = validator_func
        self._validation_state = self.STATE_NEUTRAL; self._error_message = ""
        self._label_y = 16; self._glow_intensity = 0

        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(4)
        input_container = QWidget(); input_container.setMinimumHeight(50)
        input_layout = QVBoxLayout(input_container); input_layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit(); self.line_edit.setMinimumHeight(44); self.update_style()
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.focusInEvent = self._focus_in; self.line_edit.focusOutEvent = self._focus_out
        input_layout.addWidget(self.line_edit); layout.addWidget(input_container)

        self.help_label = QLabel(""); self.help_label.setStyleSheet("QLabel { color: #f44336; font-size: 11px; padding: 2px 4px; }")
        self.help_label.setWordWrap(True); self.help_label.hide(); layout.addWidget(self.help_label)

        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(200); self.label_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.glow_anim = QPropertyAnimation(self, b"glow_intensity")
        self.glow_anim.setDuration(250); self.glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.validation_timer = QTimer(); self.validation_timer.setSingleShot(True); self.validation_timer.timeout.connect(self._perform_validation)

    def get_label_y(self): return self._label_y
    def set_label_y(self, value): self._label_y = value; self.update()
    label_y = Property(int, get_label_y, set_label_y)

    def get_glow_intensity(self): return self._glow_intensity
    def set_glow_intensity(self, value): self._glow_intensity = value; self.update_style()
    glow_intensity = Property(int, get_glow_intensity, set_glow_intensity)

    def update_style(self):
        style = IOS_INPUT_STYLE
        if self._validation_state == self.STATE_VALID:
            style += "QLineEdit, QTextEdit, QPlainTextEdit { border: 2px solid rgba(76, 175, 80, 0.8); background: rgba(76, 175, 80, 0.1); }"
        elif self._validation_state == self.STATE_INVALID:
            style += "QLineEdit, QTextEdit, QPlainTextEdit { border: 2px solid rgba(244, 67, 54, 0.8); background: rgba(244, 67, 54, 0.1); }"
        elif self._validation_state == self.STATE_LOADING:
            style += "QLineEdit, QTextEdit, QPlainTextEdit { border: 2px solid rgba(156, 39, 176, 0.8); background: rgba(156, 39, 176, 0.1); }"
        self.line_edit.setStyleSheet(style)

    def _focus_in(self, event):
        if not self.line_edit.text() or self._label_y > 0:
            self.label_anim.stop(); self.label_anim.setStartValue(self._label_y); self.label_anim.setEndValue(-6); self.label_anim.start()
        QLineEdit.focusInEvent(self.line_edit, event)

    def _focus_out(self, event):
        if not self.line_edit.text():
            self.label_anim.stop(); self.label_anim.setStartValue(self._label_y); self.label_anim.setEndValue(16); self.label_anim.start()
        if self._validator_func and self.line_edit.text(): self._perform_validation()
        QLineEdit.focusOutEvent(self.line_edit, event)

    def _on_text_changed(self, text):
        if text and self._label_y > 0:
            self.label_anim.stop(); self.label_anim.setStartValue(self._label_y); self.label_anim.setEndValue(-6); self.label_anim.start()
        if self._validator_func: self.validation_timer.stop(); self.validation_timer.start(500)

    def _perform_validation(self):
        if not self._validator_func: return
        text = self.line_edit.text().strip()
        if not text: self.set_validation_state(self.STATE_NEUTRAL); return
        try:
            is_valid, error_msg = self._validator_func(text)
            if is_valid: self.set_validation_state(self.STATE_VALID); self.help_label.hide()
            else: self.set_validation_state(self.STATE_INVALID, error_msg); self.help_label.setText(f"❌ {error_msg}"); self.help_label.show()
        except Exception as e: self.set_validation_state(self.STATE_INVALID, str(e))

    def set_validation_state(self, state, error_msg=""):
        self._validation_state = state; self._error_message = error_msg; self.update_style(); self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._label_text:
            font = QFont()
            if self.line_edit.hasFocus():
                painter.setPen(QColor(76, 175, 80) if self._validation_state == self.STATE_VALID else QColor(244, 67, 54) if self._validation_state == self.STATE_INVALID else QColor(33, 150, 243))
                font.setPixelSize(11); font.setBold(True)
            elif self._label_y < 10: painter.setPen(QColor(150, 150, 150)); font.setPixelSize(11)
            else: painter.setPen(QColor(120, 120, 120)); font.setPixelSize(14)
            painter.setFont(font)
            label_rect = self.line_edit.geometry(); y_pos = label_rect.top() + int(self._label_y) + 18
            painter.drawText(20, y_pos, self._label_text)
            if self._validation_state in [self.STATE_VALID, self.STATE_INVALID]:
                icon_x = label_rect.right() - 32; icon_y = label_rect.top() + 18
                if self._validation_state == self.STATE_VALID:
                    painter.setPen(QPen(QColor(76, 175, 80), 2))
                    painter.drawLine(icon_x, icon_y, icon_x + 3, icon_y + 3); painter.drawLine(icon_x + 3, icon_y + 3, icon_x + 8, icon_y - 3)
                else:
                    painter.setPen(QPen(QColor(244, 67, 54), 2))
                    painter.drawLine(icon_x, icon_y - 3, icon_x + 6, icon_y + 3); painter.drawLine(icon_x, icon_y + 3, icon_x + 6, icon_y - 3)

    def text(self): return self.line_edit.text()
    def setText(self, text): self.line_edit.setText(text)
    def setPlaceholderText(self, text): self._label_text = text
    def setEchoMode(self, mode): self.line_edit.setEchoMode(mode)
    @property
    def returnPressed(self): return self.line_edit.returnPressed
    def setFocus(self): self.line_edit.setFocus()
    def clear(self): self.line_edit.clear(); self.set_validation_state(self.STATE_NEUTRAL); self.help_label.hide()
    def setReadOnly(self, read_only): self.line_edit.setReadOnly(read_only)
    def setEnabled(self, enabled): self.line_edit.setEnabled(enabled); super().setEnabled(enabled)
    @property
    def textChanged(self): return self.line_edit.textChanged
    @property
    def editingFinished(self): return self.line_edit.editingFinished
    def is_valid(self): return self._validation_state == self.STATE_VALID
    def get_validation_state(self): return self._validation_state


# =============================================================================
# NEUMORPHIC GRADIENT INPUT FIELD
# =============================================================================

class NeumorphicGradientLineEdit(QWidget):
    def setCompleter(self, completer):
        self.line_edit.setCompleter(completer)
    """
    Neumorphic input field with animated rotating gradient border.
    Features:
    - Soft neumorphic shadows
    - Rotating gradient border animation
    - Floating label animation
    """
    
    # === CHANGED: Added float_y, rest_y parameters + NEW customization parameters ===
    def __init__(self, placeholder="", parent=None, float_y=4.0, rest_y=38.0, input_y=8,
                 gradient_colors=None, rotation_duration=3000, enable_rotation=True):
        super().__init__(parent)
        self._placeholder = placeholder
        self._angle = 0.0
        self._border_width = 2.5
        self._is_focused = False

        # === CHANGED: Use parameters instead of hardcoded defaults ===
        self._float_y = float_y  # Position when active (top)
        self._rest_y = rest_y    # Position when empty (middle)
        self._label_y = self._rest_y  # Start at resting position

        self._input_y = input_y # Text input vertical position

        # NEW: Gradient customization
        self.gradient_colors = gradient_colors or [
            "#4a9eff",  # Blue
            "#9c27b0",  # Purple
            "#00c8ff",  # Cyan
            "#ff4081"   # Pink
        ]
        self.rotation_duration = rotation_duration
        self.enable_rotation = enable_rotation

        self._glow_opacity = 0.0
        self._margin = 10
        self._input_height = 36

        self.setMinimumHeight(70)
        self.setMinimumWidth(260)

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("neumorphicInnerLineEdit")
        self.line_edit.setStyleSheet("""
            QLineEdit#neumorphicInnerLineEdit {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 14px;
                padding: 12px 8px 12px 12px;
                selection-background-color: rgba(74, 158, 255, 0.4);
            }
            QLineEdit#neumorphicInnerLineEdit:focus {
                color: #FFFFFF;
            }
            QLineEdit#neumorphicInnerLineEdit:disabled {
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.line_edit.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        margin = self._margin
        self.line_edit.setGeometry(margin, self._input_y, self.width() - margin * 2, self._input_height)
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.installEventFilter(self)

        if placeholder:
            self.line_edit.setAccessibleName(placeholder)
            self.line_edit.setAccessibleDescription(f"Input field for {placeholder}")
        
        self._floating_label = QLabel(placeholder, self)
        self._floating_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._floating_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._floating_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 14px;
                background: transparent;
                padding-left: 12px;
            }
        """)
        
        # === CHANGED: Use rest_y parameter ===
        self._floating_label.setGeometry(margin, int(self._rest_y), self.width() - margin * 2, 20)

        # NEW: Lazy animation initialization - don't create border animation yet
        self.border_anim = None  # Will be created on first focus

        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(150)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self.glow_anim.setDuration(1500)
        self.glow_anim.setLoopCount(-1)
        self.glow_anim.setStartValue(0.3)
        self.glow_anim.setEndValue(0.7)
        self.glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        
        self.setCursor(Qt.IBeamCursor)
        
    def mousePressEvent(self, event):
        self.line_edit.setFocus()
        super().mousePressEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = self._margin
        self.line_edit.setGeometry(margin, self._input_y, self.width() - margin * 2, self._input_height)
        self._floating_label.setGeometry(margin, int(self._label_y), self.width() - margin * 2, 20)

    def eventFilter(self, obj, event):
        if obj == self.line_edit:
            if event.type() == QEvent.Type.FocusIn:
                self._on_focus_in()
            elif event.type() == QEvent.Type.FocusOut:
                self._on_focus_out()
        return super().eventFilter(obj, event)

    def _create_border_animation(self):
        """Lazy initialization - create border animation only when needed"""
        if not self.enable_rotation:
            return  # Don't create animation if rotation disabled

        self.border_anim = QVariantAnimation(self)
        self.border_anim.setStartValue(0.0)
        self.border_anim.setEndValue(360.0)
        self.border_anim.setDuration(self.rotation_duration)
        self.border_anim.setLoopCount(-1)
        self.border_anim.valueChanged.connect(self._on_angle_changed)

    def _on_focus_in(self):
        self._is_focused = True

        # NEW: Lazy animation - create only on first focus
        if self.enable_rotation:
            if self.border_anim is None:
                self._create_border_animation()
            if self.border_anim:
                self.border_anim.start()

        self.glow_anim.start()
        # === CHANGED: Use float_y parameter ===
        self._animate_label(self._float_y)
        self.update()

    def _on_focus_out(self):
        self._is_focused = False

        # Stop border animation if it exists
        if self.border_anim:
            self.border_anim.stop()
            self._angle = 0.0  # Reset to starting position

        self.glow_anim.stop()
        self._glow_opacity = 0.0
        if not self.line_edit.text():
            # === CHANGED: Use rest_y parameter ===
            self._animate_label(self._rest_y)
        self.update()

    def _on_text_changed(self, text):
        if text and not self._is_focused:
            # === CHANGED: Use float_y parameter ===
            self._animate_label(self._float_y)
        elif not text and not self._is_focused:
            # === CHANGED: Use rest_y parameter ===
            self._animate_label(self._rest_y)

    def _animate_label(self, target_y):
        self.label_anim.stop()
        self.label_anim.setStartValue(self._label_y)
        self.label_anim.setEndValue(target_y)
        self.label_anim.start()
        
    def _on_angle_changed(self, value):
        self._angle = value
        self.update()
        
    def get_label_y(self):
        return self._label_y
    
    def set_label_y(self, value):
        self._label_y = value
        margin = self._margin
        width = max(self.width() - margin * 2, 100)
        self._floating_label.setGeometry(margin, int(value), width, 20)
        
        # === CHANGED: Adjust style change threshold to be dynamic ===
        threshold = (self._rest_y + self._float_y) / 2
        
        if value < threshold:
            self._floating_label.setStyleSheet("""
                QLabel {
                    color: rgba(74, 158, 255, 0.9);
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding-left: 12px;
                }
            """)
        else:
            self._floating_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 14px;
                    background: transparent;
                    padding-left: 12px;
                }
            """)
        self.update()
        
    label_y = Property(float, get_label_y, set_label_y)
    
    def get_glow_opacity(self):
        return self._glow_opacity
    
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
        
    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)
    
    def _build_gradient(self, rect):
        rad = math.radians(self._angle)
        cx, cy = rect.center().x(), rect.center().y()
        r = max(rect.width(), rect.height()) / 2

        x1, y1 = cx + r * math.cos(rad), cy + r * math.sin(rad)
        x2, y2 = cx - r * math.cos(rad), cy - r * math.sin(rad)

        grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))

        # NEW: Use custom gradient colors
        colors = [QColor(c) for c in self.gradient_colors]
        if len(colors) >= 4:
            grad.setColorAt(0.0, colors[0])
            grad.setColorAt(0.25, colors[1])
            grad.setColorAt(0.5, colors[2])
            grad.setColorAt(0.75, colors[3])
            grad.setColorAt(1.0, colors[0])  # Loop back to first color
        else:
            # Fallback to default if less than 4 colors provided
            grad.setColorAt(0.0, QColor(74, 158, 255))
            grad.setColorAt(0.25, QColor(156, 39, 176))
            grad.setColorAt(0.5, QColor(0, 200, 255))
            grad.setColorAt(0.75, QColor(255, 64, 129))
            grad.setColorAt(1.0, QColor(74, 158, 255))

        return grad
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        padding = self._margin
        rect = QRectF(self.rect()).adjusted(padding, padding, -padding, -padding)
        radius = 16
        
        shadow_offset = 4
        shadow_rect = rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(10, 10, 15, 80))
        painter.drawRoundedRect(shadow_rect, radius, radius)
        
        highlight_rect = rect.adjusted(-2, -2, -2, -2)
        painter.setBrush(QColor(60, 65, 80, 40))
        painter.drawRoundedRect(highlight_rect, radius, radius)
        
        if self._is_focused and self._glow_opacity > 0:
            glow_rect = rect.adjusted(-4, -4, 4, 4)
            glow_color = QColor(74, 158, 255, int(50 * self._glow_opacity))
            painter.setBrush(glow_color)
            painter.drawRoundedRect(glow_rect, radius + 2, radius + 2)
        
        bg_grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        bg_grad.setColorAt(0, QColor(40, 44, 55, 250))
        bg_grad.setColorAt(1, QColor(30, 34, 45, 250))
        painter.setBrush(bg_grad)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)
        
        inner_shadow = QPainterPath()
        inner_shadow.addRoundedRect(rect, radius, radius)
        painter.setClipPath(inner_shadow)
        
        inset_grad = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 20))
        inset_grad.setColorAt(0, QColor(0, 0, 0, 40))
        inset_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(inset_grad)
        painter.drawRect(rect)
        
        painter.setClipping(False)
        
        if self._is_focused:
            grad = self._build_gradient(rect)
            border_pen = QPen(QBrush(grad), self._border_width)
            border_pen.setCapStyle(Qt.RoundCap)
            border_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(
                self._border_width / 2, self._border_width / 2,
                -self._border_width / 2, -self._border_width / 2
            ), radius - 1, radius - 1)
        else:
            painter.setPen(QPen(QColor(80, 85, 100, 100), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
        
        highlight_path = QPainterPath()
        highlight_rect_top = QRectF(rect.left() + 10, rect.top() + 6, rect.width() - 20, 8)
        highlight_path.addRoundedRect(highlight_rect_top, 6, 6)
        highlight_grad = QLinearGradient(highlight_rect_top.topLeft(), highlight_rect_top.bottomLeft())
        highlight_grad.setColorAt(0, QColor(255, 255, 255, 10))
        highlight_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(highlight_grad)
        painter.drawPath(highlight_path)
        
        painter.end()
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.line_edit.text():
            # === CHANGED: Use float_y parameter ===
            self._label_y = self._float_y
            margin = self._margin
            width = max(self.width() - margin * 2, 100)
            self._floating_label.setGeometry(margin, int(self._float_y), width, 20)
            self._floating_label.setStyleSheet("""
                QLabel {
                    color: rgba(74, 158, 255, 0.9);
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding-left: 12px;
                }
            """)

    def text(self): return self.line_edit.text()
    def setText(self, text):
        self.line_edit.setText(text)
        if text:
            if self.isVisible() and self.width() > 50:
                # === CHANGED: Use float_y parameter ===
                self._animate_label(self._float_y)
            else:
                self._label_y = self._float_y
                margin = self._margin
                width = max(self.width() - margin * 2, 100)
                self._floating_label.setGeometry(margin, int(self._float_y), width, 20)
                self._floating_label.setStyleSheet("""
                    QLabel {
                        color: rgba(74, 158, 255, 0.9);
                        font-size: 11px;
                        font-weight: bold;
                        background: transparent;
                        padding-left: 12px;
                    }
                """)
    def setEchoMode(self, mode): self.line_edit.setEchoMode(mode)
    def setPlaceholderText(self, text): self._placeholder = text; self._floating_label.setText(text)
    def setMaxLength(self, length): self.line_edit.setMaxLength(length)
    def setValidator(self, validator): self.line_edit.setValidator(validator)
    def setReadOnly(self, read_only): self.line_edit.setReadOnly(read_only)
    def setEnabled(self, enabled): self.line_edit.setEnabled(enabled); super().setEnabled(enabled)
    def clear(self): self.line_edit.clear()
    def setFocus(self): self.line_edit.setFocus()
    @property
    def textChanged(self): return self.line_edit.textChanged
    @property
    def returnPressed(self): return self.line_edit.returnPressed
    @property
    def editingFinished(self): return self.line_edit.editingFinished


class NeumorphicGradientComboBox(QWidget):
    """
    Neumorphic combo box with animated rotating gradient border and floating label.
    Similar to NeumorphicGradientLineEdit but for dropdown selections.
    """

    def __init__(self, placeholder="", parent=None, float_y=4.0, rest_y=38.0, input_y=8,
                 gradient_colors=None, rotation_duration=3000, enable_rotation=True):
        super().__init__(parent)
        self._placeholder = placeholder
        self._angle = 0.0
        self._border_width = 2.5
        self._is_focused = False

        self._float_y = float_y
        self._rest_y = rest_y
        self._label_y = self._rest_y
        self._input_y = input_y

        self.gradient_colors = gradient_colors or [
            "#4a9eff", "#9c27b0", "#00c8ff", "#ff4081"
        ]
        self.rotation_duration = rotation_duration
        self.enable_rotation = enable_rotation

        self._glow_opacity = 0.0
        self._margin = 10
        self._input_height = 36
        self._open_popup_on_focus = False

        self.setMinimumHeight(70)
        self.setMinimumWidth(260)

        # Create combo box
        self.combo_box = QComboBox(self)
        self.combo_box.setObjectName("neumorphicInnerComboBox")

        # Enable transparency for rounded corners - deferred to avoid initialization issues
        self._transparency_configured = False

        def configure_popup_transparency():
            """Configure transparency when popup is first shown"""
            if self._transparency_configured:
                return

            try:
                from PySide6.QtCore import Qt
                view = self.combo_box.view()
                if view and not view.isHidden():
                    view.setAttribute(Qt.WA_TranslucentBackground)
                    view.viewport().setAttribute(Qt.WA_TranslucentBackground)

                    # Configure container window if it exists
                    parent = view.parentWidget()
                    if parent:
                        parent.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                        parent.setAttribute(Qt.WA_TranslucentBackground)

                    self._transparency_configured = True
            except RuntimeError:
                pass  # Object already deleted, ignore

        # Store the function to prevent garbage collection
        self._configure_transparency = configure_popup_transparency

        # Connect to combo box events - configure on first popup show
        original_showPopup = self.combo_box.showPopup
        original_hidePopup = self.combo_box.hidePopup

        def showPopup_with_transparency():
            original_showPopup()
            configure_popup_transparency()

        def hidePopup_stop_animation():
            original_hidePopup()

        self.combo_box.showPopup = showPopup_with_transparency
        self.combo_box.hidePopup = hidePopup_stop_animation

        self.combo_box.setStyleSheet("""
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

            /* Popup List Styling - Simple Dark Background (matches Agency dropdown) */
            QComboBox QAbstractItemView {
                background: rgba(30, 35, 45, 0.98);
                border: 2px solid rgba(66, 165, 245, 0.8);
                border-radius: 4px;
                padding: 2px;
                outline: none;
                selection-background-color: rgba(66, 165, 245, 0.3);
                color: white;
            }

            /* Individual Item Styling - With rounded backgrounds */
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 8px 14px;
                border-radius: 8px;
                color: white;
                background: transparent;
                margin: 2px 4px;
            }

            /* Hover Effect - Rounded blue background */
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(66, 165, 245, 0.25);
            }

            /* Selected Effect - Stronger rounded blue background */
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(66, 165, 245, 0.4);
            }
        """)
        margin = self._margin
        self.combo_box.setGeometry(margin, self._input_y, self.width() - margin * 2, self._input_height)
        self.combo_box.currentIndexChanged.connect(self._on_selection_changed)
        self.combo_box.installEventFilter(self)

        if placeholder:
            self.combo_box.setAccessibleName(placeholder)
            self.combo_box.setAccessibleDescription(f"Combo box for {placeholder}")
        
        
        # Floating label
        self._floating_label = QLabel(placeholder, self)
        self._floating_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._floating_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._floating_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 14px;
                background: transparent;
                padding-left: 12px;
            }
        """)
        self._floating_label.setGeometry(margin, int(self._rest_y), self.width() - margin * 2, 20)

        # Lazy animation initialization
        self.border_anim = None

        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(150)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self.glow_anim.setDuration(1500)
        self.glow_anim.setLoopCount(-1)
        self.glow_anim.setStartValue(0.3)
        self.glow_anim.setEndValue(0.7)
        self.glow_anim.setEasingCurve(QEasingCurve.InOutSine)

        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Forward clicks to combo box and handle first-click-to-open"""
        # Flag to open popup if we're gaining focus from this click
        if not self.combo_box.hasFocus():
            self._open_popup_on_focus = True

        if not self.combo_box.geometry().contains(event.pos()):
            # Click was on margin area - focus combo box and let it handle the click naturally
            self.combo_box.setFocus()
            # Create a new mouse event positioned relative to combo box
            combo_pos = event.pos() - self.combo_box.geometry().topLeft()
            new_event = QMouseEvent(
                event.type(),
                combo_pos,
                event.globalPosition(),
                event.button(),
                event.buttons(),
                event.modifiers()
            )
            QApplication.sendEvent(self.combo_box, new_event)
        else:
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = self._margin
        self.combo_box.setGeometry(margin, self._input_y, self.width() - margin * 2, self._input_height)
        self._floating_label.setGeometry(margin, int(self._label_y), self.width() - margin * 2, 20)

    def eventFilter(self, obj, event):
        if obj == self.combo_box:
            if event.type() == QEvent.Type.FocusIn:
                self._on_focus_in()
            elif event.type() == QEvent.Type.FocusOut:
                self._on_focus_out()
            elif event.type() == QEvent.Type.Wheel:
                # Block wheel events on combo box to prevent scroll capture
                event.ignore()
                return True
        return super().eventFilter(obj, event)

    def _create_border_animation(self):
        """Lazy initialization - create border animation only when needed"""
        if not self.enable_rotation:
            return

        self.border_anim = QVariantAnimation(self)
        self.border_anim.setStartValue(0.0)
        self.border_anim.setEndValue(360.0)
        self.border_anim.setDuration(self.rotation_duration)
        self.border_anim.setLoopCount(-1)
        self.border_anim.valueChanged.connect(self._on_angle_changed)

    def _on_focus_in(self):
        self._is_focused = True

        # Don't start animations on focus - only on selection
        self._animate_label(self._float_y)
        self.update()

        # Open popup if this focus was triggered by a mouse click
        if self._open_popup_on_focus:
            self._open_popup_on_focus = False
            # Use singleShot to open popup after event loop finishes processing focus event
            QTimer.singleShot(0, self.combo_box.showPopup)

    def _on_focus_out(self):
        self._is_focused = False

        if self.border_anim:
            self.border_anim.stop()
            self._angle = 0.0

        # Glow animation removed - no glow on dropdowns
        self._glow_opacity = 0.0
        if self.combo_box.currentIndex() < 0:
            self._animate_label(self._rest_y)
        self.update()

    def _on_selection_changed(self, index):
        if index >= 0:
            # Start animations when user selects an item
            if self.enable_rotation:
                if self.border_anim is None:
                    self._create_border_animation()
                if self.border_anim:
                    self.border_anim.start()

            # Glow animation removed - no glow on dropdowns

            if not self._is_focused:
                self._animate_label(self._float_y)
        elif index < 0 and not self._is_focused:
            self._animate_label(self._rest_y)

    def _animate_label(self, target_y):
        self.label_anim.stop()
        self.label_anim.setStartValue(self._label_y)
        self.label_anim.setEndValue(target_y)
        self.label_anim.start()

    def _on_angle_changed(self, value):
        self._angle = value
        self.update()

    def get_label_y(self):
        return self._label_y

    def set_label_y(self, value):
        self._label_y = value
        margin = self._margin
        width = max(self.width() - margin * 2, 100)
        self._floating_label.setGeometry(margin, int(value), width, 20)

        threshold = (self._rest_y + self._float_y) / 2

        if value < threshold:
            self._floating_label.setStyleSheet("""
                QLabel {
                    color: rgba(74, 158, 255, 0.9);
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding-left: 12px;
                }
            """)
        else:
            self._floating_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 14px;
                    background: transparent;
                    padding-left: 12px;
                }
            """)
        self.update()

    label_y = Property(float, get_label_y, set_label_y)

    def get_glow_opacity(self):
        return self._glow_opacity

    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()

    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    def _build_gradient(self, rect):
        rad = math.radians(self._angle)
        cx, cy = rect.center().x(), rect.center().y()
        r = max(rect.width(), rect.height()) / 2

        x1, y1 = cx + r * math.cos(rad), cy + r * math.sin(rad)
        x2, y2 = cx - r * math.cos(rad), cy - r * math.sin(rad)

        grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))

        colors = [QColor(c) for c in self.gradient_colors]
        if len(colors) >= 4:
            grad.setColorAt(0.0, colors[0])
            grad.setColorAt(0.25, colors[1])
            grad.setColorAt(0.5, colors[2])
            grad.setColorAt(0.75, colors[3])
            grad.setColorAt(1.0, colors[0])
        else:
            grad.setColorAt(0.0, QColor(74, 158, 255))
            grad.setColorAt(0.25, QColor(156, 39, 176))
            grad.setColorAt(0.5, QColor(0, 200, 255))
            grad.setColorAt(0.75, QColor(255, 64, 129))
            grad.setColorAt(1.0, QColor(74, 158, 255))

        return grad

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        padding = self._margin
        rect = QRectF(self.rect()).adjusted(padding, padding, -padding, -padding)
        radius = 16

        # Shadow
        shadow_offset = 4
        shadow_rect = rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(10, 10, 15, 80))
        painter.drawRoundedRect(shadow_rect, radius, radius)

        # Highlight
        highlight_rect = rect.adjusted(-2, -2, -2, -2)
        painter.setBrush(QColor(60, 65, 80, 40))
        painter.drawRoundedRect(highlight_rect, radius, radius)

        # Glow when focused
        if self._is_focused and self._glow_opacity > 0:
            glow_rect = rect.adjusted(-4, -4, 4, 4)
            glow_color = QColor(74, 158, 255, int(50 * self._glow_opacity))
            painter.setBrush(glow_color)
            painter.drawRoundedRect(glow_rect, radius + 2, radius + 2)

        # Background gradient
        bg_grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        bg_grad.setColorAt(0, QColor(40, 44, 55, 250))
        bg_grad.setColorAt(1, QColor(30, 34, 45, 250))
        painter.setBrush(bg_grad)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # Inner shadow
        inner_shadow = QPainterPath()
        inner_shadow.addRoundedRect(rect, radius, radius)
        painter.setClipPath(inner_shadow)

        inset_grad = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 20))
        inset_grad.setColorAt(0, QColor(0, 0, 0, 40))
        inset_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(inset_grad)
        painter.drawRect(rect)

        painter.setClipping(False)

        # Rotating gradient border when focused
        if self._is_focused:
            grad = self._build_gradient(rect)
            border_pen = QPen(QBrush(grad), self._border_width)
            border_pen.setCapStyle(Qt.RoundCap)
            border_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(
                self._border_width / 2, self._border_width / 2,
                -self._border_width / 2, -self._border_width / 2
            ), radius - 1, radius - 1)
        else:
            painter.setPen(QPen(QColor(80, 85, 100, 100), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

        # Top highlight
        highlight_path = QPainterPath()
        highlight_rect_top = QRectF(rect.left() + 10, rect.top() + 6, rect.width() - 20, 8)
        highlight_path.addRoundedRect(highlight_rect_top, 6, 6)
        highlight_grad = QLinearGradient(highlight_rect_top.topLeft(), highlight_rect_top.bottomLeft())
        highlight_grad.setColorAt(0, QColor(255, 255, 255, 10))
        highlight_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(highlight_grad)
        painter.drawPath(highlight_path)

        painter.end()

    def showEvent(self, event):
        super().showEvent(event)
        if self.combo_box.currentIndex() >= 0:
            self._label_y = self._float_y
            margin = self._margin
            width = max(self.width() - margin * 2, 100)
            self._floating_label.setGeometry(margin, int(self._float_y), width, 20)
            self._floating_label.setStyleSheet("""
                QLabel {
                    color: rgba(74, 158, 255, 0.9);
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding-left: 12px;
                }
            """)

    # API compatibility methods
    def addItem(self, text, data=None):
        if data is None:
            self.combo_box.addItem(text)
        else:
            self.combo_box.addItem(text, data)

    def addItems(self, texts):
        self.combo_box.addItems(texts)

    def currentIndex(self):
        return self.combo_box.currentIndex()

    def currentText(self):
        return self.combo_box.currentText()

    def currentData(self, role=Qt.UserRole):
        return self.combo_box.currentData(role)

    def setCurrentIndex(self, index):
        self.combo_box.setCurrentIndex(index)

    def setCurrentText(self, text):
        self.combo_box.setCurrentText(text)

    def count(self):
        return self.combo_box.count()

    def itemText(self, index):
        return self.combo_box.itemText(index)

    def clear(self):
        self.combo_box.clear()

    def setEnabled(self, enabled):
        self.combo_box.setEnabled(enabled)
        super().setEnabled(enabled)

    def setFocus(self):
        self.combo_box.setFocus()

    @property
    def currentIndexChanged(self):
        return self.combo_box.currentIndexChanged

    @property
    def currentTextChanged(self):
        return self.combo_box.currentTextChanged


class NeumorphicGradientPasswordInput(NeumorphicGradientLineEdit):
    """Password variant with animated show/hide toggle"""
    
    def __init__(self, placeholder="Password", parent=None, float_y=4.0, rest_y=38.0, input_y=8):
        super().__init__(placeholder, parent, float_y, rest_y, input_y)
        self.line_edit.setEchoMode(QLineEdit.Password)
        
        self.toggle_btn = QPushButton("👁", self)
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFocusPolicy(Qt.NoFocus)  # Prevent Enter key from clicking button
        self.toggle_btn.setAutoDefault(False)  # Not a default button
        self.toggle_btn.setDefault(False)  # Not a default button
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.7);
                font-size: 18px;
                padding: 0px 2px 0px 2px;
                outline: none;
            }
            QPushButton:focus { outline: none; }
            QPushButton:hover { color: rgba(74, 158, 255, 1.0); }
        """)
        self.toggle_btn.clicked.connect(self._toggle_visibility)
        self._password_visible = False
        
        self._toggle_scale = 1.0
        self.toggle_scale_anim = QPropertyAnimation(self, b"toggle_scale")
        self.toggle_scale_anim.setDuration(150)
        self.toggle_scale_anim.setEasingCurve(QEasingCurve.OutBack)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_height = self.toggle_btn.height()
        geom = self.line_edit.geometry()
        btn_y = geom.y() + (geom.height() - btn_height) // 2
        self.toggle_btn.move(self.width() - 50, btn_y - 7)
        margin = self._margin
        self.line_edit.setGeometry(margin, self._input_y, self.width() - margin * 2 - 35, self._input_height)
        
    def _toggle_visibility(self):
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.line_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.line_edit.setEchoMode(QLineEdit.Password)
            self.toggle_btn.setText("👁")
        
    def get_toggle_scale(self): return self._toggle_scale
    def set_toggle_scale(self, value): self._toggle_scale = value
    toggle_scale = Property(float, get_toggle_scale, set_toggle_scale)


class NeumorphicGradientTextEdit(QWidget):
    """
    Modern multi-line text input with floating label and rotating gradient border.

    Features:
    - Floating label that animates to top-left when text entered
    - Rotating gradient border on focus (lazy initialization)
    - Neumorphic glassmorphism background
    - Rounded corners (12px - suitable for tall boxes)
    - Customizable gradient colors and rotation speed

    API Compatibility:
        text_edit = NeumorphicGradientTextEdit("Notes", min_height=100)
        text_edit.setPlainText("Some text")
        text = text_edit.toPlainText()
        text_edit.textChanged.connect(handler)
    """

    def __init__(
        self,
        placeholder="",
        parent=None,
        min_height=100,
        float_y=4.0,
        rest_y=12.0,  # Top-left position when empty
        input_y=24,
        gradient_colors=None,
        rotation_duration=3000,
        enable_rotation=True
    ):
        super().__init__(parent)
        self._placeholder = placeholder
        self._angle = 0.0
        self._border_width = 2.5
        self._is_focused = False

        self._float_y = float_y  # Position when active (very top)
        self._rest_y = rest_y    # Position when empty (top-left)
        self._label_y = self._rest_y  # Start at resting position
        self._input_y = input_y

        # Gradient customization
        self.gradient_colors = gradient_colors or [
            "#4a9eff",  # Blue
            "#9c27b0",  # Purple
            "#00c8ff",  # Cyan
            "#ff4081"   # Pink
        ]
        self.rotation_duration = rotation_duration
        self.enable_rotation = enable_rotation

        self._glow_opacity = 0.0
        self._margin = 10
        self._min_height = min_height

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Text Edit widget
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("")  # We handle placeholder via label
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.95);
                font-size: 14px;
                padding: 4px 8px;
                selection-background-color: rgba(74, 158, 255, 0.3);
                outline: none;
            }
            QTextEdit:focus {
                outline: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(74, 158, 255, 0.4);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(74, 158, 255, 0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.text_edit.installEventFilter(self)

        # Label (floating)
        self.label = QLabel(placeholder, self)
        self.label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 13px;
                background: transparent;
                padding: 0px 4px;
            }
        """)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Label background for readability when floated
        self.label_bg = QLabel(self)
        self.label_bg.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(28, 28, 35, 0.9),
                    stop:1 rgba(28, 28, 35, 0.0)
                );
                border-radius: 4px;
            }
        """)
        self.label_bg.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.label_bg.hide()

        # Animations - lazy initialization
        self.border_anim = None

        # Label animation
        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(200)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Glow animation
        self.glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self.glow_anim.setDuration(300)
        self.glow_anim.setStartValue(0.0)
        self.glow_anim.setEndValue(0.6)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Signals
        self.text_edit.textChanged.connect(self._on_text_changed)

        self.setMinimumHeight(min_height + 2 * self._margin)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _create_border_animation(self):
        """Lazy initialization - create border animation only when needed"""
        if not self.enable_rotation:
            return

        self.border_anim = QVariantAnimation(self)
        self.border_anim.setStartValue(0.0)
        self.border_anim.setEndValue(360.0)
        self.border_anim.setDuration(self.rotation_duration)
        self.border_anim.setLoopCount(-1)
        self.border_anim.valueChanged.connect(self._on_angle_changed)

    def _on_angle_changed(self, value):
        self._angle = value
        self.update()

    def eventFilter(self, obj, event):
        if obj == self.text_edit:
            if event.type() == QEvent.FocusIn:
                self._on_focus_in()
            elif event.type() == QEvent.FocusOut:
                self._on_focus_out()
        return super().eventFilter(obj, event)

    def _on_focus_in(self):
        self._is_focused = True

        # Lazy animation - create only on first focus
        if self.enable_rotation:
            if self.border_anim is None:
                self._create_border_animation()
            if self.border_anim:
                self.border_anim.start()

        self.glow_anim.start()
        self._animate_label(self._float_y)
        self.label_bg.show()
        self.update()

    def _on_focus_out(self):
        self._is_focused = False

        # Stop border animation if it exists
        if self.border_anim:
            self.border_anim.stop()
            self._angle = 0.0

        self.glow_anim.stop()
        self._glow_opacity = 0.0

        if not self.text_edit.toPlainText():
            self._animate_label(self._rest_y)
            self.label_bg.hide()

        self.update()

    def _on_text_changed(self):
        if self.text_edit.toPlainText() and not self._is_focused:
            self._animate_label(self._float_y)
            self.label_bg.show()
        elif not self.text_edit.toPlainText() and not self._is_focused:
            self._animate_label(self._rest_y)
            self.label_bg.hide()

    def _animate_label(self, target_y):
        self.label_anim.stop()
        self.label_anim.setStartValue(self._label_y)
        self.label_anim.setEndValue(target_y)
        self.label_anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = self._margin
        content_height = self.height() - 2 * margin

        # Position text edit
        self.text_edit.setGeometry(
            margin + 8,
            self._input_y,
            self.width() - 2 * margin - 16,
            content_height - self._input_y + margin
        )

        # Update label position
        self.label.adjustSize()
        self.label.move(margin + 12, int(self._label_y))

        # Position label background
        self.label_bg.setGeometry(
            margin + 8,
            int(self._label_y) - 2,
            self.label.width() + 8,
            20
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        padding = self._margin
        rect = QRectF(self.rect()).adjusted(padding, padding, -padding, -padding)
        radius = 12  # Smaller radius for tall boxes

        # Outer shadow (depth)
        shadow_color = QColor(0, 0, 0, 80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        painter.drawRoundedRect(rect.adjusted(2, 2, 2, 2), radius, radius)

        # Highlight shadow (top-left)
        highlight_color = QColor(255, 255, 255, 8)
        painter.setBrush(highlight_color)
        painter.drawRoundedRect(rect.adjusted(-1, -1, -1, -1), radius, radius)

        # Glow effect when focused
        if self._is_focused and self._glow_opacity > 0:
            glow_color = QColor(74, 158, 255, int(30 * self._glow_opacity))
            painter.setBrush(glow_color)
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), radius + 2, radius + 2)

        # Main background gradient
        bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        bg_gradient.setColorAt(0.0, QColor(40, 40, 50, 180))
        bg_gradient.setColorAt(1.0, QColor(30, 30, 38, 180))
        painter.setBrush(bg_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # Inner shadow (inset effect)
        inner_shadow = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 30))
        inner_shadow.setColorAt(0.0, QColor(0, 0, 0, 40))
        inner_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(inner_shadow)
        painter.drawRoundedRect(rect, radius, radius)

        # Rotating gradient border (only when focused)
        if self._is_focused:
            grad = self._build_gradient(rect)
            border_pen = QPen(QBrush(grad), self._border_width)
            border_pen.setCapStyle(Qt.RoundCap)
            border_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                rect.adjusted(
                    self._border_width / 2, self._border_width / 2,
                    -self._border_width / 2, -self._border_width / 2
                ),
                radius - 1, radius - 1
            )
        else:
            # Subtle static border when not focused
            static_border = QColor(255, 255, 255, 20)
            painter.setPen(QPen(static_border, 1.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

    def _build_gradient(self, rect):
        """Build rotating gradient for border"""
        rad = math.radians(self._angle)
        cx, cy = rect.center().x(), rect.center().y()
        r = max(rect.width(), rect.height()) / 2

        x1, y1 = cx + r * math.cos(rad), cy + r * math.sin(rad)
        x2, y2 = cx - r * math.cos(rad), cy - r * math.sin(rad)

        grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))

        # Use custom gradient colors
        colors = [QColor(c) for c in self.gradient_colors]
        if len(colors) >= 4:
            grad.setColorAt(0.0, colors[0])
            grad.setColorAt(0.25, colors[1])
            grad.setColorAt(0.5, colors[2])
            grad.setColorAt(0.75, colors[3])
            grad.setColorAt(1.0, colors[0])
        else:
            # Fallback
            grad.setColorAt(0.0, QColor(74, 158, 255))
            grad.setColorAt(0.25, QColor(156, 39, 176))
            grad.setColorAt(0.5, QColor(0, 200, 255))
            grad.setColorAt(0.75, QColor(255, 64, 129))
            grad.setColorAt(1.0, QColor(74, 158, 255))

        return grad

    # Property for label animation
    def get_label_y(self): return self._label_y
    def set_label_y(self, value):
        self._label_y = value
        self.label.move(self._margin + 12, int(value))
        self.label_bg.move(self._margin + 8, int(value) - 2)
    label_y = Property(float, get_label_y, set_label_y)

    # Property for glow animation
    def get_glow_opacity(self): return self._glow_opacity
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    # API compatibility methods - proxy to QTextEdit
    def toPlainText(self):
        return self.text_edit.toPlainText()

    def setPlainText(self, text):
        self.text_edit.setPlainText(text)

    def toHtml(self):
        return self.text_edit.toHtml()

    def setHtml(self, html):
        self.text_edit.setHtml(html)

    def insertPlainText(self, text):
        self.text_edit.insertPlainText(text)

    def clear(self):
        self.text_edit.clear()

    def setReadOnly(self, read_only):
        self.text_edit.setReadOnly(read_only)

    def isReadOnly(self):
        return self.text_edit.isReadOnly()

    def setEnabled(self, enabled):
        self.text_edit.setEnabled(enabled)
        super().setEnabled(enabled)

    def setFocus(self):
        self.text_edit.setFocus()

    @property
    def textChanged(self):
        return self.text_edit.textChanged


class NeumorphicGradientSpinBox(QWidget):
    """
    Modern numeric input with floating label and rotating gradient border.

    Features:
    - Floating label that animates upward when value is non-zero
    - Rotating gradient border on focus (lazy initialization)
    - Neumorphic glassmorphism background
    - Pill-shaped rounded borders
    - Gradient-styled up/down arrows
    - Customizable gradient colors and rotation speed

    API Compatibility:
        spin_box = NeumorphicGradientSpinBox("Age")
        spin_box.setValue(25)
        value = spin_box.value()
        spin_box.setRange(0, 100)
        spin_box.valueChanged.connect(handler)
    """

    def __init__(
        self,
        placeholder="",
        parent=None,
        float_y=4.0,
        rest_y=38.0,
        input_y=8,
        gradient_colors=None,
        rotation_duration=3000,
        enable_rotation=True
    ):
        super().__init__(parent)
        self._placeholder = placeholder
        self._angle = 0.0
        self._border_width = 2.5
        self._is_focused = False

        self._float_y = float_y  # Position when active (top)
        self._rest_y = rest_y    # Position when empty (middle)
        self._label_y = self._rest_y  # Start at resting position
        self._input_y = input_y

        # Gradient customization
        self.gradient_colors = gradient_colors or [
            "#4a9eff",  # Blue
            "#9c27b0",  # Purple
            "#00c8ff",  # Cyan
            "#ff4081"   # Pink
        ]
        self.rotation_duration = rotation_duration
        self.enable_rotation = enable_rotation

        self._glow_opacity = 0.0
        self._margin = 10
        self._input_height = 36

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # SpinBox widget
        self.spin_box = QSpinBox(self)
        self.spin_box.setStyleSheet("""
            QSpinBox {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.95);
                font-size: 14px;
                padding: 0px 8px;
                selection-background-color: rgba(74, 158, 255, 0.3);
                outline: none;
            }
            QSpinBox:focus {
                outline: none;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border: none;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.3),
                    stop:1 rgba(74, 158, 255, 0.1)
                );
                border-top-right-radius: 18px;
            }
            QSpinBox::up-button:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.5),
                    stop:1 rgba(74, 158, 255, 0.2)
                );
            }
            QSpinBox::up-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid rgba(255, 255, 255, 0.7);
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border: none;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(156, 39, 176, 0.1),
                    stop:1 rgba(156, 39, 176, 0.3)
                );
                border-bottom-right-radius: 18px;
            }
            QSpinBox::down-button:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(156, 39, 176, 0.2),
                    stop:1 rgba(156, 39, 176, 0.5)
                );
            }
            QSpinBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
            }
        """)
        self.spin_box.installEventFilter(self)

        # Label (floating)
        self.label = QLabel(placeholder, self)
        self.label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 13px;
                background: transparent;
            }
        """)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Animations - lazy initialization
        self.border_anim = None

        # Label animation
        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(200)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Glow animation
        self.glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self.glow_anim.setDuration(300)
        self.glow_anim.setStartValue(0.0)
        self.glow_anim.setEndValue(0.6)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Signals
        self.spin_box.valueChanged.connect(self._on_value_changed)

        self.setMinimumHeight(60)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _create_border_animation(self):
        """Lazy initialization - create border animation only when needed"""
        if not self.enable_rotation:
            return

        self.border_anim = QVariantAnimation(self)
        self.border_anim.setStartValue(0.0)
        self.border_anim.setEndValue(360.0)
        self.border_anim.setDuration(self.rotation_duration)
        self.border_anim.setLoopCount(-1)
        self.border_anim.valueChanged.connect(self._on_angle_changed)

    def _on_angle_changed(self, value):
        self._angle = value
        self.update()

    def eventFilter(self, obj, event):
        if obj == self.spin_box:
            if event.type() == QEvent.FocusIn:
                self._on_focus_in()
            elif event.type() == QEvent.FocusOut:
                self._on_focus_out()
        return super().eventFilter(obj, event)

    def _on_focus_in(self):
        self._is_focused = True

        # Lazy animation - create only on first focus
        if self.enable_rotation:
            if self.border_anim is None:
                self._create_border_animation()
            if self.border_anim:
                self.border_anim.start()

        self.glow_anim.start()
        self._animate_label(self._float_y)
        self.update()

    def _on_focus_out(self):
        self._is_focused = False

        # Stop border animation if it exists
        if self.border_anim:
            self.border_anim.stop()
            self._angle = 0.0

        self.glow_anim.stop()
        self._glow_opacity = 0.0

        if self.spin_box.value() == 0:
            self._animate_label(self._rest_y)

        self.update()

    def _on_value_changed(self, value):
        if value != 0 and not self._is_focused:
            self._animate_label(self._float_y)
        elif value == 0 and not self._is_focused:
            self._animate_label(self._rest_y)

    def _animate_label(self, target_y):
        self.label_anim.stop()
        self.label_anim.setStartValue(self._label_y)
        self.label_anim.setEndValue(target_y)
        self.label_anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = self._margin

        # Position spin box
        self.spin_box.setGeometry(
            margin,
            self._input_y,
            self.width() - 2 * margin,
            self._input_height
        )

        # Update label position
        self.label.adjustSize()
        label_x = (self.width() - self.label.width()) // 2
        self.label.move(label_x, int(self._label_y))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        padding = self._margin
        rect = QRectF(self.rect()).adjusted(padding, padding, -padding, -padding)
        radius = 20  # Pill shape

        # Outer shadow (depth)
        shadow_color = QColor(0, 0, 0, 80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        painter.drawRoundedRect(rect.adjusted(2, 2, 2, 2), radius, radius)

        # Highlight shadow (top-left)
        highlight_color = QColor(255, 255, 255, 8)
        painter.setBrush(highlight_color)
        painter.drawRoundedRect(rect.adjusted(-1, -1, -1, -1), radius, radius)

        # Glow effect when focused
        if self._is_focused and self._glow_opacity > 0:
            glow_color = QColor(74, 158, 255, int(30 * self._glow_opacity))
            painter.setBrush(glow_color)
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), radius + 2, radius + 2)

        # Main background gradient
        bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        bg_gradient.setColorAt(0.0, QColor(40, 40, 50, 180))
        bg_gradient.setColorAt(1.0, QColor(30, 30, 38, 180))
        painter.setBrush(bg_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # Inner shadow (inset effect)
        inner_shadow = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 30))
        inner_shadow.setColorAt(0.0, QColor(0, 0, 0, 40))
        inner_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(inner_shadow)
        painter.drawRoundedRect(rect, radius, radius)

        # Rotating gradient border (only when focused)
        if self._is_focused:
            grad = self._build_gradient(rect)
            border_pen = QPen(QBrush(grad), self._border_width)
            border_pen.setCapStyle(Qt.RoundCap)
            border_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                rect.adjusted(
                    self._border_width / 2, self._border_width / 2,
                    -self._border_width / 2, -self._border_width / 2
                ),
                radius - 1, radius - 1
            )
        else:
            # Subtle static border when not focused
            static_border = QColor(255, 255, 255, 20)
            painter.setPen(QPen(static_border, 1.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

    def _build_gradient(self, rect):
        """Build rotating gradient for border"""
        rad = math.radians(self._angle)
        cx, cy = rect.center().x(), rect.center().y()
        r = max(rect.width(), rect.height()) / 2

        x1, y1 = cx + r * math.cos(rad), cy + r * math.sin(rad)
        x2, y2 = cx - r * math.cos(rad), cy - r * math.sin(rad)

        grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))

        # Use custom gradient colors
        colors = [QColor(c) for c in self.gradient_colors]
        if len(colors) >= 4:
            grad.setColorAt(0.0, colors[0])
            grad.setColorAt(0.25, colors[1])
            grad.setColorAt(0.5, colors[2])
            grad.setColorAt(0.75, colors[3])
            grad.setColorAt(1.0, colors[0])
        else:
            # Fallback
            grad.setColorAt(0.0, QColor(74, 158, 255))
            grad.setColorAt(0.25, QColor(156, 39, 176))
            grad.setColorAt(0.5, QColor(0, 200, 255))
            grad.setColorAt(0.75, QColor(255, 64, 129))
            grad.setColorAt(1.0, QColor(74, 158, 255))

        return grad

    # Property for label animation
    def get_label_y(self): return self._label_y
    def set_label_y(self, value):
        self._label_y = value
        label_x = (self.width() - self.label.width()) // 2
        self.label.move(label_x, int(value))
    label_y = Property(float, get_label_y, set_label_y)

    # Property for glow animation
    def get_glow_opacity(self): return self._glow_opacity
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    # API compatibility methods - proxy to QSpinBox
    def value(self):
        return self.spin_box.value()

    def setValue(self, value):
        self.spin_box.setValue(value)

    def setRange(self, minimum, maximum):
        self.spin_box.setRange(minimum, maximum)

    def setMinimum(self, minimum):
        self.spin_box.setMinimum(minimum)

    def setMaximum(self, maximum):
        self.spin_box.setMaximum(maximum)

    def minimum(self):
        return self.spin_box.minimum()

    def maximum(self):
        return self.spin_box.maximum()

    def setSingleStep(self, step):
        self.spin_box.setSingleStep(step)

    def singleStep(self):
        return self.spin_box.singleStep()

    def setPrefix(self, prefix):
        self.spin_box.setPrefix(prefix)

    def setSuffix(self, suffix):
        self.spin_box.setSuffix(suffix)

    def setReadOnly(self, read_only):
        self.spin_box.setReadOnly(read_only)

    def isReadOnly(self):
        return self.spin_box.isReadOnly()

    def setEnabled(self, enabled):
        self.spin_box.setEnabled(enabled)
        super().setEnabled(enabled)

    def setFocus(self):
        self.spin_box.setFocus()

    @property
    def valueChanged(self):
        return self.spin_box.valueChanged


class NeumorphicGradientDateEdit(QWidget):
    """
    Modern date input with floating label and rotating gradient border.

    Features:
    - Floating label that animates upward when date selected
    - Rotating gradient border on focus (lazy initialization)
    - Neumorphic glassmorphism background
    - Pill-shaped rounded borders
    - Glassmorphic calendar popup
    - Calendar icon with gradient hover
    - Customizable gradient colors and rotation speed

    API Compatibility:
        date_edit = NeumorphicGradientDateEdit("Birth Date")
        date_edit.setDate(QDate(1990, 1, 1))
        date = date_edit.date()
        date_edit.dateChanged.connect(handler)
    """

    def __init__(
        self,
        placeholder="",
        parent=None,
        float_y=4.0,
        rest_y=38.0,
        input_y=8,
        gradient_colors=None,
        rotation_duration=3000,
        enable_rotation=True
    ):
        super().__init__(parent)
        self._placeholder = placeholder
        self._angle = 0.0
        self._border_width = 2.5
        self._is_focused = False

        self._float_y = float_y  # Position when active (top)
        self._rest_y = rest_y    # Position when empty (middle)
        self._label_y = self._rest_y  # Start at resting position
        self._input_y = input_y

        # Gradient customization
        self.gradient_colors = gradient_colors or [
            "#4a9eff",  # Blue
            "#9c27b0",  # Purple
            "#00c8ff",  # Cyan
            "#ff4081"   # Pink
        ]
        self.rotation_duration = rotation_duration
        self.enable_rotation = enable_rotation

        self._glow_opacity = 0.0
        self._margin = 10
        self._input_height = 36

        # Track if a date has been explicitly set
        self._has_custom_date = False

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # DateEdit widget
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("MMM dd, yyyy")
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.95);
                font-size: 14px;
                padding: 0px 30px 0px 8px;
                selection-background-color: rgba(74, 158, 255, 0.3);
                outline: none;
            }
            QDateEdit:focus {
                outline: none;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border: none;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.2),
                    stop:1 rgba(156, 39, 176, 0.2)
                );
                border-top-right-radius: 18px;
                border-bottom-right-radius: 18px;
            }
            QDateEdit::drop-down:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.4),
                    stop:1 rgba(156, 39, 176, 0.4)
                );
            }
            QDateEdit::down-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
            }
            QCalendarWidget {
                background: rgba(28, 28, 35, 0.95);
                border: 2px solid rgba(74, 158, 255, 0.3);
                border-radius: 12px;
            }
            QCalendarWidget QToolButton {
                background: rgba(74, 158, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background: rgba(74, 158, 255, 0.4);
            }
            QCalendarWidget QMenu {
                background: rgba(28, 28, 35, 0.95);
                color: white;
                border: 1px solid rgba(74, 158, 255, 0.3);
            }
            QCalendarWidget QSpinBox {
                background: rgba(40, 40, 50, 0.8);
                color: white;
                border: 1px solid rgba(74, 158, 255, 0.3);
                border-radius: 4px;
                padding: 2px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.2),
                    stop:1 rgba(156, 39, 176, 0.2)
                );
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QCalendarWidget QAbstractItemView {
                background: rgba(28, 28, 35, 0.7);
                color: white;
                selection-background-color: rgba(74, 158, 255, 0.5);
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: rgba(255, 255, 255, 0.9);
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.date_edit.installEventFilter(self)

        # Label (floating)
        self.label = QLabel(placeholder, self)
        self.label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 13px;
                background: transparent;
            }
        """)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Animations - lazy initialization
        self.border_anim = None

        # Label animation
        self.label_anim = QPropertyAnimation(self, b"label_y")
        self.label_anim.setDuration(200)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Glow animation
        self.glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self.glow_anim.setDuration(300)
        self.glow_anim.setStartValue(0.0)
        self.glow_anim.setEndValue(0.6)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Signals
        self.date_edit.dateChanged.connect(self._on_date_changed)

        self.setMinimumHeight(60)
        self.setMinimumWidth(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _create_border_animation(self):
        """Lazy initialization - create border animation only when needed"""
        if not self.enable_rotation:
            return

        self.border_anim = QVariantAnimation(self)
        self.border_anim.setStartValue(0.0)
        self.border_anim.setEndValue(360.0)
        self.border_anim.setDuration(self.rotation_duration)
        self.border_anim.setLoopCount(-1)
        self.border_anim.valueChanged.connect(self._on_angle_changed)

    def _on_angle_changed(self, value):
        self._angle = value
        self.update()

    def eventFilter(self, obj, event):
        if obj == self.date_edit:
            if event.type() == QEvent.FocusIn:
                self._on_focus_in()
            elif event.type() == QEvent.FocusOut:
                self._on_focus_out()
        return super().eventFilter(obj, event)

    def _on_focus_in(self):
        self._is_focused = True

        # Lazy animation - create only on first focus
        if self.enable_rotation:
            if self.border_anim is None:
                self._create_border_animation()
            if self.border_anim:
                self.border_anim.start()

        self.glow_anim.start()
        self._animate_label(self._float_y)
        self.update()

    def _on_focus_out(self):
        self._is_focused = False

        # Stop border animation if it exists
        if self.border_anim:
            self.border_anim.stop()
            self._angle = 0.0

        self.glow_anim.stop()
        self._glow_opacity = 0.0

        if not self._has_custom_date:
            self._animate_label(self._rest_y)

        self.update()

    def _on_date_changed(self, date):
        self._has_custom_date = True
        if not self._is_focused:
            self._animate_label(self._float_y)

    def _animate_label(self, target_y):
        self.label_anim.stop()
        self.label_anim.setStartValue(self._label_y)
        self.label_anim.setEndValue(target_y)
        self.label_anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = self._margin

        # Position date edit
        self.date_edit.setGeometry(
            margin,
            self._input_y,
            self.width() - 2 * margin,
            self._input_height
        )

        # Update label position
        self.label.adjustSize()
        label_x = (self.width() - self.label.width()) // 2
        self.label.move(label_x, int(self._label_y))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        padding = self._margin
        rect = QRectF(self.rect()).adjusted(padding, padding, -padding, -padding)
        radius = 20  # Pill shape

        # Outer shadow (depth)
        shadow_color = QColor(0, 0, 0, 80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        painter.drawRoundedRect(rect.adjusted(2, 2, 2, 2), radius, radius)

        # Highlight shadow (top-left)
        highlight_color = QColor(255, 255, 255, 8)
        painter.setBrush(highlight_color)
        painter.drawRoundedRect(rect.adjusted(-1, -1, -1, -1), radius, radius)

        # Glow effect when focused
        if self._is_focused and self._glow_opacity > 0:
            glow_color = QColor(74, 158, 255, int(30 * self._glow_opacity))
            painter.setBrush(glow_color)
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), radius + 2, radius + 2)

        # Main background gradient
        bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        bg_gradient.setColorAt(0.0, QColor(40, 40, 50, 180))
        bg_gradient.setColorAt(1.0, QColor(30, 30, 38, 180))
        painter.setBrush(bg_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # Inner shadow (inset effect)
        inner_shadow = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 30))
        inner_shadow.setColorAt(0.0, QColor(0, 0, 0, 40))
        inner_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(inner_shadow)
        painter.drawRoundedRect(rect, radius, radius)

        # Rotating gradient border (only when focused)
        if self._is_focused:
            grad = self._build_gradient(rect)
            border_pen = QPen(QBrush(grad), self._border_width)
            border_pen.setCapStyle(Qt.RoundCap)
            border_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                rect.adjusted(
                    self._border_width / 2, self._border_width / 2,
                    -self._border_width / 2, -self._border_width / 2
                ),
                radius - 1, radius - 1
            )
        else:
            # Subtle static border when not focused
            static_border = QColor(255, 255, 255, 20)
            painter.setPen(QPen(static_border, 1.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

    def _build_gradient(self, rect):
        """Build rotating gradient for border"""
        rad = math.radians(self._angle)
        cx, cy = rect.center().x(), rect.center().y()
        r = max(rect.width(), rect.height()) / 2

        x1, y1 = cx + r * math.cos(rad), cy + r * math.sin(rad)
        x2, y2 = cx - r * math.cos(rad), cy - r * math.sin(rad)

        grad = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))

        # Use custom gradient colors
        colors = [QColor(c) for c in self.gradient_colors]
        if len(colors) >= 4:
            grad.setColorAt(0.0, colors[0])
            grad.setColorAt(0.25, colors[1])
            grad.setColorAt(0.5, colors[2])
            grad.setColorAt(0.75, colors[3])
            grad.setColorAt(1.0, colors[0])
        else:
            # Fallback
            grad.setColorAt(0.0, QColor(74, 158, 255))
            grad.setColorAt(0.25, QColor(156, 39, 176))
            grad.setColorAt(0.5, QColor(0, 200, 255))
            grad.setColorAt(0.75, QColor(255, 64, 129))
            grad.setColorAt(1.0, QColor(74, 158, 255))

        return grad

    # Property for label animation
    def get_label_y(self): return self._label_y
    def set_label_y(self, value):
        self._label_y = value
        label_x = (self.width() - self.label.width()) // 2
        self.label.move(label_x, int(value))
    label_y = Property(float, get_label_y, set_label_y)

    # Property for glow animation
    def get_glow_opacity(self): return self._glow_opacity
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    # API compatibility methods - proxy to QDateEdit
    def date(self):
        return self.date_edit.date()

    def setDate(self, date):
        self._has_custom_date = True
        self.date_edit.setDate(date)

    def setDateRange(self, min_date, max_date):
        self.date_edit.setDateRange(min_date, max_date)

    def setMinimumDate(self, date):
        self.date_edit.setMinimumDate(date)

    def setMaximumDate(self, date):
        self.date_edit.setMaximumDate(date)

    def minimumDate(self):
        return self.date_edit.minimumDate()

    def maximumDate(self):
        return self.date_edit.maximumDate()

    def setDisplayFormat(self, format_str):
        self.date_edit.setDisplayFormat(format_str)

    def displayFormat(self):
        return self.date_edit.displayFormat()

    def setCalendarPopup(self, enable):
        self.date_edit.setCalendarPopup(enable)

    def calendarPopup(self):
        return self.date_edit.calendarPopup()

    def setReadOnly(self, read_only):
        self.date_edit.setReadOnly(read_only)

    def isReadOnly(self):
        return self.date_edit.isReadOnly()

    def setEnabled(self, enabled):
        self.date_edit.setEnabled(enabled)
        super().setEnabled(enabled)

    def setFocus(self):
        self.date_edit.setFocus()

    @property
    def dateChanged(self):
        return self.date_edit.dateChanged
