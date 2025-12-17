"""
Photo Editor Dialog
Crop, rotate, and position photos for circular avatar display
v4.6.0: New photo editing capabilities
"""

import os
import math
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class CircularCropWidget(QWidget):
    """Widget for cropping and positioning image within a circular area"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
        
        self.original_pixmap = None
        self.display_pixmap = None
        self.rotation = 0
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        
        # Dragging state
        self.dragging = False
        self.last_pos = QPointF()
        
        # Circle properties
        self.circle_radius = 150
        
        self.setStyleSheet("background-color: #1a1a2e;")
        self.setCursor(Qt.OpenHandCursor)
    
    def set_image(self, pixmap: QPixmap):
        """Set the image to edit"""
        self.original_pixmap = pixmap
        self._update_display()
        self._fit_image_to_circle()
        self.update()
    
    def _fit_image_to_circle(self):
        """Scale image to fit within the circle initially"""
        if not self.original_pixmap:
            return
        
        # Calculate scale to fit the smaller dimension to circle diameter
        img_size = min(self.original_pixmap.width(), self.original_pixmap.height())
        target_size = self.circle_radius * 2
        self.scale = target_size / img_size * 1.1  # Slightly larger for adjustment room
        self.offset = QPointF(0, 0)
        self._update_display()
    
    def _update_display(self):
        """Update the display pixmap with current transforms"""
        if not self.original_pixmap:
            return
        
        # Apply rotation
        transform = QTransform()
        transform.rotate(self.rotation)
        rotated = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        # Apply scale
        new_width = int(rotated.width() * self.scale)
        new_height = int(rotated.height() * self.scale)
        self.display_pixmap = rotated.scaled(
            new_width, new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.update()
    
    def rotate_image(self, degrees: int):
        """Rotate image by specified degrees"""
        self.rotation = (self.rotation + degrees) % 360
        self._update_display()
    
    def zoom_in(self):
        """Zoom in"""
        self.scale = min(5.0, self.scale * 1.2)
        self._update_display()
    
    def zoom_out(self):
        """Zoom out"""
        self.scale = max(0.1, self.scale / 1.2)
        self._update_display()
    
    def reset_transform(self):
        """Reset all transforms"""
        self.rotation = 0
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        self._fit_image_to_circle()
    
    def get_cropped_image(self, size: int = 400) -> QPixmap:
        """Get the cropped circular image"""
        if not self.display_pixmap:
            return QPixmap()
        
        # Create result image with transparency
        result = QImage(size, size, QImage.Format_ARGB32)
        result.fill(Qt.transparent)
        
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Create circular clipping path
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        # Calculate source rect from the view
        center = QPointF(self.width() / 2, self.height() / 2)
        
        # Map the circle area to the image
        if self.display_pixmap:
            img_center = QPointF(
                center.x() + self.offset.x(),
                center.y() + self.offset.y()
            )
            
            # Calculate scale ratio for output
            output_scale = size / (self.circle_radius * 2)
            
            # Source rectangle in display pixmap coordinates
            src_x = self.display_pixmap.width() / 2 - self.circle_radius + self.offset.x()
            src_y = self.display_pixmap.height() / 2 - self.circle_radius + self.offset.y()
            
            # Adjust for the offset from center of widget
            widget_center_x = self.width() / 2
            widget_center_y = self.height() / 2
            img_offset_x = widget_center_x - self.display_pixmap.width() / 2
            img_offset_y = widget_center_y - self.display_pixmap.height() / 2
            
            src_rect = QRectF(
                -self.offset.x() + self.display_pixmap.width() / 2 - self.circle_radius,
                -self.offset.y() + self.display_pixmap.height() / 2 - self.circle_radius,
                self.circle_radius * 2,
                self.circle_radius * 2
            )
            
            dest_rect = QRectF(0, 0, size, size)
            
            painter.drawPixmap(dest_rect, self.display_pixmap, src_rect)
        
        painter.end()
        return QPixmap.fromImage(result)
    
    def paintEvent(self, event):
        """Paint the widget"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Fill background
        painter.fillRect(self.rect(), QColor("#1a1a2e"))
        
        center = QPointF(self.width() / 2, self.height() / 2)
        
        # Draw the image
        if self.display_pixmap:
            img_x = center.x() - self.display_pixmap.width() / 2 + self.offset.x()
            img_y = center.y() - self.display_pixmap.height() / 2 + self.offset.y()
            painter.drawPixmap(int(img_x), int(img_y), self.display_pixmap)
        
        # Draw overlay (darken area outside circle)
        overlay_path = QPainterPath()
        overlay_path.addRect(QRectF(self.rect()))
        circle_path = QPainterPath()
        circle_path.addEllipse(
            center.x() - self.circle_radius,
            center.y() - self.circle_radius,
            self.circle_radius * 2,
            self.circle_radius * 2
        )
        overlay_path = overlay_path.subtracted(circle_path)
        
        painter.fillPath(overlay_path, QColor(0, 0, 0, 180))
        
        # Draw circle border
        painter.setPen(QPen(QColor("#4a9eff"), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            center.x() - self.circle_radius,
            center.y() - self.circle_radius,
            self.circle_radius * 2,
            self.circle_radius * 2
        )
        
        # Draw center crosshair
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1, Qt.DashLine))
        painter.drawLine(int(center.x() - 20), int(center.y()), int(center.x() + 20), int(center.y()))
        painter.drawLine(int(center.x()), int(center.y() - 20), int(center.x()), int(center.y() + 20))
    
    def mousePressEvent(self, event):
        """Start dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """Handle dragging to move image"""
        if self.dragging:
            delta = event.position() - self.last_pos
            self.offset += QPointF(delta.x(), delta.y())
            self.last_pos = event.position()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """End dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.OpenHandCursor)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()


class PhotoEditorDialog(QDialog):
    """
    Photo Editor Dialog with crop, rotate, and positioning for circular avatar
    
    Features:
    - Circular crop area for avatar
    - Drag to position image
    - Rotate left/right
    - Zoom in/out
    - Preview result
    - Optional background removal
    """
    
    def __init__(self, image_path: str = None, pixmap: QPixmap = None, parent=None, show_remove_bg: bool = False):
        super().__init__(parent)
        
        self.result_pixmap = None
        self.original_path = image_path
        self.show_remove_bg = show_remove_bg
        self.remove_bg_checked = False
        
        self._setup_ui()
        
        # Load image
        if pixmap and not pixmap.isNull():
            self.crop_widget.set_image(pixmap)
        elif image_path and os.path.exists(image_path):
            pix = QPixmap(image_path)
            if not pix.isNull():
                self.crop_widget.set_image(pix)
    
    def _setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("📷 Edit Photo")
        self.setModal(True)
        
        # Calculate appropriate size (fit within screen with margin)
        screen = QApplication.primaryScreen().availableGeometry()
        dialog_width = min(700, screen.width() - 100)
        dialog_height = min(650, screen.height() - 100)
        self.setFixedSize(dialog_width, dialog_height)
        
        # Center on screen
        self.move(
            (screen.width() - dialog_width) // 2,
            (screen.height() - dialog_height) // 2
        )
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #1a1a2e,
                                           stop:1 #16213e);
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(74, 158, 255, 0.3),
                                           stop:1 rgba(33, 150, 243, 0.5));
                border: 1px solid rgba(74, 158, 255, 0.5);
                border-top: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(74, 158, 255, 0.5),
                                           stop:1 rgba(33, 150, 243, 0.7));
                border: 1px solid rgba(100, 181, 246, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(33, 150, 243, 0.5),
                                           stop:1 rgba(25, 118, 210, 0.7));
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📷 Edit Photo for Avatar")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "🖱️ Drag to position  •  🔄 Rotate buttons  •  🔍 Scroll to zoom"
        )
        instructions.setStyleSheet("color: #9e9e9e; font-size: 12px;")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Crop widget
        self.crop_widget = CircularCropWidget()
        layout.addWidget(self.crop_widget, 1)
        
        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(10)
        
        # Rotate left
        rotate_left = QPushButton("↺ Rotate Left")
        rotate_left.clicked.connect(lambda: self.crop_widget.rotate_image(-90))
        controls.addWidget(rotate_left)
        
        # Rotate right
        rotate_right = QPushButton("↻ Rotate Right")
        rotate_right.clicked.connect(lambda: self.crop_widget.rotate_image(90))
        controls.addWidget(rotate_right)
        
        controls.addStretch()
        
        # Zoom out
        zoom_out = QPushButton("🔍−")
        zoom_out.setFixedWidth(50)
        zoom_out.clicked.connect(self.crop_widget.zoom_out)
        controls.addWidget(zoom_out)
        
        # Zoom in
        zoom_in = QPushButton("🔍+")
        zoom_in.setFixedWidth(50)
        zoom_in.clicked.connect(self.crop_widget.zoom_in)
        controls.addWidget(zoom_in)
        
        controls.addStretch()
        
        # Reset
        reset = QPushButton("↩ Reset")
        reset.clicked.connect(self.crop_widget.reset_transform)
        controls.addWidget(reset)
        
        layout.addLayout(controls)
        
        # Optional: Remove background checkbox
        if self.show_remove_bg:
            bg_row = QHBoxLayout()
            bg_row.setContentsMargins(0, 5, 0, 5)
            
            self.remove_bg_checkbox = QCheckBox("🎨 Remove Background (AI-powered)")
            self.remove_bg_checkbox.setStyleSheet("""
                QCheckBox {
                    color: white;
                    font-size: 13px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid rgba(74, 158, 255, 0.6);
                    background: rgba(30, 40, 60, 0.8);
                }
                QCheckBox::indicator:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                               stop:0 rgba(76, 175, 80, 0.9),
                                               stop:1 rgba(56, 142, 60, 0.8));
                    border: 2px solid rgba(76, 175, 80, 0.8);
                }
                QCheckBox::indicator:hover {
                    border: 2px solid rgba(100, 181, 246, 0.9);
                }
            """)
            self.remove_bg_checkbox.setToolTip(
                "Automatically remove the background from your photo\n"
                "for a clean, professional avatar look."
            )
            bg_row.addStretch()
            bg_row.addWidget(self.remove_bg_checkbox)
            bg_row.addStretch()
            layout.addLayout(bg_row)
        
        # Buttons row
        buttons = QHBoxLayout()
        buttons.setSpacing(15)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.1),
                                           stop:0.5 rgba(158, 158, 158, 0.2),
                                           stop:1 rgba(97, 97, 97, 0.3));
                border: 1px solid rgba(158, 158, 158, 0.5);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.2),
                                           stop:0.5 rgba(158, 158, 158, 0.4),
                                           stop:1 rgba(97, 97, 97, 0.5));
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        buttons.addStretch()
        
        apply_btn = QPushButton("✓ Apply")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.15),
                                           stop:0.5 rgba(76, 175, 80, 0.5),
                                           stop:1 rgba(56, 142, 60, 0.7));
                border: 1px solid rgba(76, 175, 80, 0.7);
                border-top: 1px solid rgba(255, 255, 255, 0.3);
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(255, 255, 255, 0.25),
                                           stop:0.5 rgba(76, 175, 80, 0.7),
                                           stop:1 rgba(56, 142, 60, 0.9));
            }
        """)
        apply_btn.clicked.connect(self._apply)
        buttons.addWidget(apply_btn)
        
        layout.addLayout(buttons)
    
    def _apply(self):
        """Apply changes and close"""
        self.result_pixmap = self.crop_widget.get_cropped_image(400)
        # Store checkbox state if shown
        if self.show_remove_bg and hasattr(self, 'remove_bg_checkbox'):
            self.remove_bg_checked = self.remove_bg_checkbox.isChecked()
        self.accept()
    
    def get_result(self) -> QPixmap:
        """Get the resulting cropped pixmap"""
        return self.result_pixmap
    
    def should_remove_background(self) -> bool:
        """Check if user wants background removed"""
        return self.remove_bg_checked


class PhotoPreviewDialog(QDialog):
    """
    Simple photo preview dialog that fits within screen bounds
    """
    
    def __init__(self, image_path: str = None, pixmap: QPixmap = None, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("📷 Photo Preview")
        self.setModal(True)
        
        # Get screen size
        screen = QApplication.primaryScreen().availableGeometry()
        max_width = screen.width() - 100
        max_height = screen.height() - 100
        
        # Load image
        if pixmap and not pixmap.isNull():
            pix = pixmap
        elif image_path and os.path.exists(image_path):
            pix = QPixmap(image_path)
        else:
            pix = QPixmap()
        
        if pix.isNull():
            self.close()
            return
        
        # Scale image to fit screen
        scaled_pix = pix.scaled(
            max_width, max_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Set dialog size based on scaled image
        dialog_width = scaled_pix.width() + 40
        dialog_height = scaled_pix.height() + 80
        
        self.setFixedSize(dialog_width, dialog_height)
        
        # Center on screen
        self.move(
            (screen.width() - dialog_width) // 2,
            (screen.height() - dialog_height) // 2
        )
        
        self.setStyleSheet("""
            QDialog {
                background: rgba(0, 0, 0, 0.95);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Image label
        img_label = QLabel()
        img_label.setPixmap(scaled_pix)
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)
        
        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(244, 67, 54, 0.8);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background: rgba(244, 67, 54, 1.0);
            }
        """)
        close_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
