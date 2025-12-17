"""
Stacked Card Gallery - 3D Animated Photo Preview
A visually appealing gallery widget with perspective stacked cards.
Supports swipe/click navigation and integrates with ModernImageViewer.
"""

import os
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect, QSizePolicy, QDialog, QApplication
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QSize,
    QPoint, QRect, Signal, QTimer, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QPixmap, QColor, QPen, QBrush, QPainterPath,
    QLinearGradient, QTransform, QCursor, QImage, QFont
)

# Use centralized design tokens for colors and typography
from employee_vault.design_tokens import TOKENS


class StackedCard(QWidget):
    """Individual card in the gallery with 3D perspective effect"""
    
    clicked = Signal()
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._pixmap = None
        self._scale = 1.0
        self._x_offset = 0
        self._y_offset = 0
        self._z_index = 0
        self._opacity = 1.0
        self._rotation_y = 0.0  # Y-axis rotation for 3D effect

        # Card dimensions
        self.card_width = 280
        self.card_height = 200
        self.setFixedSize(self.card_width + 40, self.card_height + 40)  # Extra space for shadow

        # Performance optimizations for ultra-smooth animations
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # Load and cache the image
        self._load_image()

        # Cursor
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def _load_image(self):
        """Load and scale the image"""
        if os.path.exists(self.image_path):
            img = QImage(self.image_path)
            if not img.isNull():
                # Scale to fit card while maintaining aspect ratio
                scaled = img.scaled(
                    self.card_width - 20, self.card_height - 20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._pixmap = QPixmap.fromImage(scaled)
        
        if self._pixmap is None:
            # Create placeholder using theme color
            self._pixmap = QPixmap(self.card_width - 20, self.card_height - 20)
            self._pixmap.fill(QColor(TOKENS['colors'].get('bg_dark', '#3C4150')))
            
    # Properties for animation
    def get_scale(self):
        return self._scale
    def set_scale(self, v):
        self._scale = v
        self.update()
    scale = Property(float, get_scale, set_scale)
    
    def get_x_offset(self):
        return self._x_offset
    def set_x_offset(self, v):
        self._x_offset = v
        self.update()
    x_offset = Property(int, get_x_offset, set_x_offset)
    
    def get_y_offset(self):
        return self._y_offset
    def set_y_offset(self, v):
        self._y_offset = v
        self.update()
    y_offset = Property(int, get_y_offset, set_y_offset)
    
    def get_opacity(self):
        return self._opacity
    def set_opacity(self, v):
        self._opacity = v
        self.update()
    opacity = Property(float, get_opacity, set_opacity)
    
    def get_rotation_y(self):
        return self._rotation_y
    def set_rotation_y(self, v):
        self._rotation_y = v
        self.update()
    rotation_y = Property(float, get_rotation_y, set_rotation_y)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        if self._rotation_y != 0:
            center = self.rect().center()
            t = QTransform()
            t.translate(center.x(), center.y())
            t.rotate(self._rotation_y, Qt.YAxis) # Rotate around Y axis
            t.translate(-center.x(), -center.y())
            painter.setTransform(t)
        
        # Apply opacity
        painter.setOpacity(self._opacity)
        
        # Calculate card rect with offset and scale
        cw = int(self.card_width * self._scale)
        ch = int(self.card_height * self._scale)
        cx = (self.width() - cw) // 2 + self._x_offset
        cy = (self.height() - ch) // 2 + self._y_offset
        card_rect = QRect(cx, cy, cw, ch)
        
        # === DROP SHADOW ===
        shadow_offset = int(TOKENS['spacing']['sm'][:-2])
        shadow_rect = card_rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset)
        painter.setBrush(QColor(TOKENS['colors'].get('shadow_card', '#000000')))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, int(TOKENS['radii']['md'][:-2]), int(TOKENS['radii']['md'][:-2]))
        
        # === CARD BACKGROUND (Glassmorphism) ===
        bg_gradient = QLinearGradient(card_rect.topLeft(), card_rect.bottomRight())
        bg_gradient.setColorAt(0.0, QColor(TOKENS['colors'].get('card_gradient_start', '#2D3241')))
        bg_gradient.setColorAt(1.0, QColor(TOKENS['colors'].get('card_gradient_end', '#232837')))
        painter.setBrush(bg_gradient)
        painter.setPen(QPen(QColor(TOKENS['colors'].get('border_subtle', '#FFFFFF')), 1))
        painter.drawRoundedRect(card_rect, int(TOKENS['radii']['lg'][:-2]), int(TOKENS['radii']['lg'][:-2]))
        
        # === IMAGE ===
        if self._pixmap:
            # Center image in card
            img_x = cx + (cw - self._pixmap.width() * self._scale) / 2
            img_y = cy + (ch - self._pixmap.height() * self._scale) / 2
            
            # Scale pixmap
            scaled_pm = self._pixmap.scaled(
                int(self._pixmap.width() * self._scale),
                int(self._pixmap.height() * self._scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Draw with rounded corners
            path = QPainterPath()
            img_rect = QRect(int(img_x), int(img_y), scaled_pm.width(), scaled_pm.height())
            path.addRoundedRect(img_rect, 12, 12)
            painter.setClipPath(path)
            painter.drawPixmap(int(img_x), int(img_y), scaled_pm)
            painter.setClipping(False)
        
        # === BORDER HIGHLIGHT ===
        painter.setBrush(Qt.BrushStyle.NoBrush)
        highlight_pen = QPen(QColor(TOKENS['colors'].get('highlight', '#FFFFFF')), 1.5)
        painter.setPen(highlight_pen)
        painter.drawRoundedRect(card_rect.adjusted(1, 1, -1, -1), 15, 15)


class StackedCardGallery(QWidget):
    """
    A 3D stacked card gallery widget for previewing images.
    Shows 3-5 cards with perspective effect, swipe/click to navigate.
    """
    
    image_clicked = Signal(int, str)  # Index and path of clicked image
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self._images = []  # List of image paths
        self._current_index = 0
        self._cards = []
        self._is_animating = False

        # Gallery dimensions
        self.gallery_width = 800
        self.gallery_height = 450
        self.setMinimumSize(self.gallery_width, self.gallery_height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Performance optimizations for smooth gallery animations
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # Card positions (relative to center)
        # Format: (x_offset, scale, opacity, z_index)
        self._positions = [
            (-180, 0.7, 0.4, 1),   # Far left
            (-90, 0.85, 0.7, 2),   # Left
            (0, 1.0, 1.0, 3),      # Center (front)
            (90, 0.85, 0.7, 2),    # Right
            (180, 0.7, 0.4, 1),    # Far right
        ]

        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(int(TOKENS['spacing']['md'][:-2]))
        
        self.header = QLabel("Photo Preview Gallery", self)
        self.header.setFont(QFont(TOKENS['typography']['font_family'], int(TOKENS['typography']['size_lg'][:-2]), QFont.Bold))
        self.header.setStyleSheet(f"color: {TOKENS['colors']['text_primary']}; padding: {TOKENS['spacing']['lg']};")
        layout.addWidget(self.header)
        
        # Card container
        self._card_container = QWidget()
        self._card_container.setMinimumHeight(280)
        self._card_container.setStyleSheet(f"background: {TOKENS['colors']['bg_dark']}; border-radius: {TOKENS['radii']['lg']};")
        # Performance optimization for smooth card animations
        self._card_container.setAttribute(Qt.WA_OpaquePaintEvent, False)
        layout.addWidget(self._card_container, 1)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(int(TOKENS['spacing']['lg'][:-2]))
        
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(28, 28)
        self._prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._prev_btn.clicked.connect(self._go_prev)
        self._prev_btn.setStyleSheet(f"background: {TOKENS['colors']['primary']}; color: {TOKENS['colors']['text_on_primary']}; border-radius: {TOKENS['radii']['md']}; font-size: 11px;")

        # Page indicator
        self._page_label = QLabel("1 / 1")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setStyleSheet(f"color: {TOKENS['colors']['text_secondary']}; font-size: {TOKENS['typography']['size_sm']};")

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(28, 28)
        self._next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._next_btn.clicked.connect(self._go_next)
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        
        nav_layout.addStretch()
        nav_layout.addWidget(self._prev_btn)
        nav_layout.addWidget(self._page_label)
        nav_layout.addWidget(self._next_btn)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
    def set_images(self, image_paths: list):
        """Set the list of images to display"""
        # Filter to only valid image files
        valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        self._images = [
            p for p in image_paths 
            if os.path.exists(p) and os.path.splitext(p)[1].lower() in valid_extensions
        ]
        self._current_index = 0
        self._rebuild_cards()
        self._update_page_label()
        
    def _rebuild_cards(self):
        """Create/recreate card widgets"""
        # Clear existing cards
        for card in self._cards:
            card.deleteLater()
        self._cards = []
        
        if not self._images:
            return
            
        # Create cards for visible images (5 at most)
        visible_count = min(5, len(self._images))
        center = visible_count // 2
        
        for i in range(visible_count):
            # Calculate which image this card shows
            img_index = (self._current_index - center + i) % len(self._images)
            
            card = StackedCard(self._images[img_index], self._card_container)
            card.clicked.connect(lambda idx=img_index: self._on_card_clicked(idx))
            
            # Apply position
            if i < len(self._positions):
                x_off, scale, opacity, z = self._positions[i]
                card._x_offset = x_off
                card._scale = scale
                card._opacity = opacity
                card._z_index = z
                
            self._cards.append(card)
            
        # Position and show cards
        self._layout_cards()
        
    def _layout_cards(self):
        """Position cards in the container"""
        if not self._cards:
            return
            
        container_w = self._card_container.width()
        container_h = self._card_container.height()
        
        # Sort by z-index for proper layering
        sorted_cards = sorted(self._cards, key=lambda c: c._z_index)
        
        for card in sorted_cards:
            # Center position plus offset
            x = (container_w - card.width()) // 2 + card._x_offset
            y = (container_h - card.height()) // 2 + card._y_offset
            card.move(x, y)
            card.raise_()
            card.show()
            
    def _animate_to_index(self, new_index: int):
        """Animate cards to show new current image - Ultra smooth modern gallery style"""
        if self._is_animating or not self._images:
            return

        self._is_animating = True
        old_index = self._current_index
        self._current_index = new_index % len(self._images)

        # Create animation group
        anim_group = QParallelAnimationGroup(self)

        visible_count = min(5, len(self._images))
        center = visible_count // 2

        for i, card in enumerate(self._cards):
            # Calculate new position for this card
            new_pos_idx = i
            if new_index > old_index:  # Moving right
                new_pos_idx = (i - 1) % visible_count
            else:  # Moving left
                new_pos_idx = (i + 1) % visible_count

            if new_pos_idx < len(self._positions):
                x_off, scale, opacity, _ = self._positions[new_pos_idx]

                # Modern gallery smooth animation: longer duration + OutQuint easing
                duration = 400  # Slightly longer for smoother feel

                # Animate x_offset
                x_anim = QPropertyAnimation(card, b"x_offset")
                x_anim.setDuration(duration)
                x_anim.setEndValue(x_off)
                x_anim.setEasingCurve(QEasingCurve.Type.OutQuint)  # Smooth deceleration
                anim_group.addAnimation(x_anim)

                # Animate scale
                scale_anim = QPropertyAnimation(card, b"scale")
                scale_anim.setDuration(duration)
                scale_anim.setEndValue(scale)
                scale_anim.setEasingCurve(QEasingCurve.Type.OutQuint)
                anim_group.addAnimation(scale_anim)

                # Animate opacity - slightly faster for crisp transitions
                opacity_anim = QPropertyAnimation(card, b"opacity")
                opacity_anim.setDuration(int(duration * 0.85))  # 340ms
                opacity_anim.setEndValue(opacity)
                opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim_group.addAnimation(opacity_anim)

        def on_finished():
            self._is_animating = False
            self._rebuild_cards()  # Rebuild with correct images

        anim_group.finished.connect(on_finished)
        anim_group.start()

        self._update_page_label()
        
    def _go_prev(self):
        """Go to previous image"""
        if self._images:
            new_idx = (self._current_index - 1) % len(self._images)
            self._animate_to_index(new_idx)
            
    def _go_next(self):
        """Go to next image"""
        if self._images:
            new_idx = (self._current_index + 1) % len(self._images)
            self._animate_to_index(new_idx)
            
    def _on_card_clicked(self, img_index: int):
        """Handle card click"""
        if img_index == self._current_index:
            # Center card clicked - emit signal to open full viewer
            self.image_clicked.emit(img_index, self._images[img_index])
        else:
            # Side card clicked - navigate to it
            self._current_index = img_index
            self._rebuild_cards()
            self._update_page_label()
            
    def _update_page_label(self):
        """Update the page indicator"""
        if self._images:
            self._page_label.setText(f"{self._current_index + 1} / {len(self._images)}")
        else:
            self._page_label.setText("No images")
            
    def resizeEvent(self, event):
        """Re-layout cards when resized"""
        super().resizeEvent(event)
        self._layout_cards()

    def show_error(self, message):
        if hasattr(self, 'error_dialog') and self.error_dialog:
            self.error_dialog.close()
        self.error_dialog = QDialog(self)
        self.error_dialog.setWindowTitle("Error")
        self.error_dialog.setStyleSheet(f"background: {TOKENS['colors']['error']}; color: {TOKENS['colors']['text_on_error']}; border-radius: {TOKENS['radii']['md']};")
        layout = QVBoxLayout(self.error_dialog)
        label = QLabel(message, self.error_dialog)
        label.setStyleSheet(f"color: {TOKENS['colors']['text_on_error']}; font-size: {TOKENS['typography']['size_base']}; padding: {TOKENS['spacing']['md']};")
        layout.addWidget(label)
        btn = QPushButton("OK", self.error_dialog)
        btn.setStyleSheet(f"background: {TOKENS['colors']['primary']}; color: {TOKENS['colors']['text_on_primary']}; border-radius: {TOKENS['radii']['sm']}; padding: {TOKENS['spacing']['sm']} {TOKENS['spacing']['lg']};")
        btn.clicked.connect(self.error_dialog.accept)
        layout.addWidget(btn)
        self.error_dialog.exec()


class GalleryPreviewDialog(QDialog):
    """
    A dialog that shows the StackedCardGallery for employee photos.
    Integrates with ModernImageViewer for fullscreen preview.
    """
    
    def __init__(self, image_paths: list, parent=None, title="Photo Gallery"):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {TOKENS['colors'].get('bg_base', 'rgba(25, 30, 45, 0.98)')},
                    stop:1 {TOKENS['colors'].get('bg_dark', 'rgba(35, 40, 55, 0.98)')});
                border-radius: {TOKENS['radii']['lg']};
            }}
        """)
        
        # Store image paths
        self._image_paths = image_paths
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: {TOKENS['typography']['size_lg']};
            font-weight: {TOKENS['typography']['weight_bold']};
            color: {TOKENS['colors']['text_primary']};
            padding: {TOKENS['spacing']['md']};
        """)
        layout.addWidget(title_label)
        
        # Gallery
        self._gallery = StackedCardGallery()
        self._gallery.set_images(image_paths)
        self._gallery.image_clicked.connect(self._open_fullscreen)
        layout.addWidget(self._gallery, 1)
        
        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # Download current photo button
        download_btn = QPushButton("💾 Download Photo")
        download_btn.setFixedSize(180, 45)
        download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TOKENS['colors']['primary']};
                border: 1px solid {TOKENS['colors']['border_default']};
                border-radius: {TOKENS['radii']['md']};
                color: {TOKENS['colors']['text_on_primary']};
                padding: {TOKENS['spacing']['md']} {TOKENS['spacing']['lg']};
                font-size: {TOKENS['typography']['size_base']};
            }}
            QPushButton:hover {{
                background: {TOKENS['colors'].get('primary_hover', TOKENS['colors']['primary'])};
            }}
        """)
        download_btn.clicked.connect(self._download_current_photo)
        btn_layout.addWidget(download_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(180, 45)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TOKENS['colors']['bg_base']};
                border: 1px solid {TOKENS['colors']['border_subtle']};
                border-radius: {TOKENS['radii']['md']};
                color: {TOKENS['colors']['text_primary']};
                padding: {TOKENS['spacing']['md']} {TOKENS['spacing']['lg']};
                font-size: {TOKENS['typography']['size_base']};
            }}
            QPushButton:hover {{
                background: {TOKENS['colors']['bg_dark']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _download_current_photo(self):
        """Download the currently displayed photo"""
        import shutil
        import os
        
        if not self._image_paths:
            return
        
        # Get current index from gallery
        current_index = self._gallery._current_index if hasattr(self._gallery, '_current_index') else 0
        if current_index >= len(self._image_paths):
            current_index = 0
        
        current_path = self._image_paths[current_index]
        filename = os.path.basename(current_path)
        
        from PySide6.QtWidgets import QFileDialog
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Photo As",
            filename,
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*.*)"
        )
        
        if save_path:
            try:
                shutil.copy2(current_path, save_path)
                from employee_vault.ui.modern_ui_helper import show_success_toast
                show_success_toast(self, f"Photo saved successfully!\n\n{save_path}")
            except Exception as e:
                from employee_vault.ui.modern_ui_helper import show_error_toast
                show_error_toast(self, f"Failed to save photo:\n{str(e)}")
        
    def _open_fullscreen(self, index: int, path: str):
        """Open full image viewer"""
        try:
            from employee_vault.ui.widgets.image_viewer import ModernImageViewer
            viewer = ModernImageViewer(self._image_paths, start_index=index, parent=self)
            viewer.exec()
        except ImportError:
            # Fallback - just show the image
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Image", f"Opening: {path}")
