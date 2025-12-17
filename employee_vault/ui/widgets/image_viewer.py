"""
Modern Image Viewer with Carousel/Slider
Lightbox-style fullscreen image viewer with navigation and zoom
"""

import os
from typing import List, Optional
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class ModernImageViewer(QDialog):
    """
    Professional Lightbox-style Image Viewer with Gallery Features

    Features:
    - Fullscreen overlay with dark background
    - Image carousel with smooth transitions
    - Zoom and pan controls
    - Keyboard navigation (arrows, ESC)
    - Thumbnail strip
    - Touch-friendly controls
    - File information display
    """

    def __init__(self, parent=None, image_paths: List[str] = None, current_index: int = 0):
        """
        Initialize Modern Image Viewer

        Args:
            parent: Parent widget
            image_paths: List of image file paths to display
            current_index: Index of image to show first (default: 0)
        """
        super().__init__(parent)

        self.image_paths = image_paths or []
        self.current_index = current_index if current_index < len(self.image_paths) else 0
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.dragging = False
        self.last_mouse_pos = QPoint(0, 0)
        self.is_panning = False  # Track if user is panning vs clicking

        self._setup_ui()
        self._load_current_image()

    def _setup_ui(self):
        """Setup the user interface"""
        # Fullscreen dialog with dark background
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(0, 0, 0, 230);
            }
        """)

        # Make fullscreen
        if self.parent():
            self.setGeometry(self.parent().geometry())
        else:
            screen = QApplication.primaryScreen().geometry()
            self.setGeometry(screen)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === TOP BAR: Title and Controls ===
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)

        # === CENTRAL AREA: Image Display ===
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent;")
        self.image_label.setScaledContents(False)
        self.image_label.setCursor(Qt.ArrowCursor)  # Will change to hand when zoomed

        # Enable mouse tracking for pan
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)

        layout.addWidget(self.image_label, 1)

        # === BOTTOM BAR: Navigation and Thumbnails ===
        bottom_bar = self._create_bottom_bar()
        layout.addWidget(bottom_bar)

        # === NAVIGATION ARROWS (Overlayed on Image) ===
        self._create_navigation_arrows()

    def _create_top_bar(self) -> QWidget:
        """Create top bar with title and controls"""
        top_widget = QWidget()
        top_widget.setFixedHeight(60)
        top_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
            }
        """)

        layout = QHBoxLayout(top_widget)
        layout.setContentsMargins(20, 10, 20, 10)

        # Title/Caption
        self.title_label = QLabel("Image Viewer")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Image counter
        self.counter_label = QLabel(f"1 / {len(self.image_paths)}")
        self.counter_label.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 14px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 20);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.counter_label)

        # Download button
        download_btn = self._create_icon_button("💾", "Download Photo")
        download_btn.clicked.connect(self._download_current_photo)
        layout.addWidget(download_btn)

        # Zoom controls
        zoom_out_btn = self._create_icon_button("🔍−", "Zoom Out")
        zoom_out_btn.clicked.connect(self._zoom_out)
        layout.addWidget(zoom_out_btn)

        zoom_reset_btn = self._create_icon_button("100%", "Reset Zoom")
        zoom_reset_btn.clicked.connect(self._zoom_reset)
        layout.addWidget(zoom_reset_btn)

        zoom_in_btn = self._create_icon_button("🔍+", "Zoom In")
        zoom_in_btn.clicked.connect(self._zoom_in)
        layout.addWidget(zoom_in_btn)

        # Close button
        close_btn = self._create_icon_button("✕", "Close (ESC)")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 180);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 220);
            }
        """)
        layout.addWidget(close_btn)

        return top_widget
    
    def _download_current_photo(self):
        """Download/save current photo to user's chosen location"""
        import shutil
        import os
        
        if not self.image_paths or self.current_index >= len(self.image_paths):
            return
        
        current_path = self.image_paths[self.current_index]
        filename = os.path.basename(current_path)
        
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

    def _create_bottom_bar(self) -> QWidget:
        """Create bottom bar with navigation and thumbnails"""
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(140)
        bottom_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
            }
        """)

        layout = QVBoxLayout(bottom_widget)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # File information
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                color: #BDBDBD;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.info_label)

        # Thumbnail strip
        thumb_scroll = QScrollArea()
        thumb_scroll.setWidgetResizable(True)
        thumb_scroll.setFixedHeight(80)
        thumb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        thumb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        thumb_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        thumb_widget = QWidget()
        self.thumb_layout = QHBoxLayout(thumb_widget)
        self.thumb_layout.setContentsMargins(0, 0, 0, 0)
        self.thumb_layout.setSpacing(10)

        # Create thumbnails
        self.thumb_buttons = []
        for i, img_path in enumerate(self.image_paths):
            thumb_btn = self._create_thumbnail_button(img_path, i)
            self.thumb_layout.addWidget(thumb_btn)
            self.thumb_buttons.append(thumb_btn)

        self.thumb_layout.addStretch()
        thumb_scroll.setWidget(thumb_widget)
        layout.addWidget(thumb_scroll)

        return bottom_widget

    def _create_navigation_arrows(self):
        """Create previous/next navigation arrows"""
        # Previous button
        self.prev_btn = QPushButton("◀", self)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(33, 33, 33, 180);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
                padding: 8px;
                min-width: 36px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: rgba(66, 66, 66, 220);
            }
            QPushButton:disabled {
                color: #666666;
                background-color: rgba(33, 33, 33, 100);
            }
        """)
        self.prev_btn.clicked.connect(self._show_previous)
        # Cursor removed per user request
        # self.prev_btn.setCursor(Qt.PointingHandCursor)

        # Next button
        self.next_btn = QPushButton("▶", self)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(33, 33, 33, 180);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
                padding: 8px;
                min-width: 36px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: rgba(66, 66, 66, 220);
            }
            QPushButton:disabled {
                color: #666666;
                background-color: rgba(33, 33, 33, 100);
            }
        """)
        self.next_btn.clicked.connect(self._show_next)
        # Cursor removed per user request
        # self.next_btn.setCursor(Qt.PointingHandCursor)

        # Position arrows
        self._position_navigation_arrows()

    def _create_icon_button(self, text: str, tooltip: str = "") -> QPushButton:
        """Create a styled icon button"""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
            }
        """)
        # Cursor removed per user request
        # btn.setCursor(Qt.PointingHandCursor)
        return btn

    def _create_thumbnail_button(self, img_path: str, index: int) -> QPushButton:
        """Create thumbnail button"""
        btn = QPushButton()
        btn.setFixedSize(70, 70)
        # Cursor removed per user request
        # btn.setCursor(Qt.PointingHandCursor)

        # Load thumbnail
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(70, 70, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Crop to center
            x = (scaled_pixmap.width() - 70) // 2
            y = (scaled_pixmap.height() - 70) // 2
            cropped = scaled_pixmap.copy(x, y, 70, 70)

            icon = QIcon(cropped)
            btn.setIcon(icon)
            btn.setIconSize(QSize(70, 70))

        # Style
        btn.setStyleSheet("""
            QPushButton {
                border: 3px solid transparent;
                border-radius: 6px;
                background-color: #333333;
            }
            QPushButton:hover {
                border-color: rgba(255, 255, 255, 100);
            }
        """)

        btn.clicked.connect(lambda: self._show_image(index))
        return btn

    def _position_navigation_arrows(self):
        """Position navigation arrows on sides of image"""
        if not self.image_label:
            return

        # Calculate positions (20px from edges, vertically centered)
        label_rect = self.image_label.geometry()
        y = label_rect.top() + (label_rect.height() // 2) - 18  # Half of button height (36/2)

        self.prev_btn.move(20, y)
        self.next_btn.move(self.width() - 56, y)  # 36px button + 20px margin

        # Disable buttons at boundaries
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_paths) - 1)

    def _load_current_image(self):
        """Load and display current image"""
        if not self.image_paths or self.current_index >= len(self.image_paths):
            return

        img_path = self.image_paths[self.current_index]

        # Load image
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            self.title_label.setText("Error loading image")
            return

        # Store original pixmap
        self.original_pixmap = pixmap

        # Display with current zoom
        self._update_image_display()

        # Update UI
        filename = os.path.basename(img_path)
        self.title_label.setText(filename)
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.image_paths)}")

        # Update file info
        file_size = os.path.getsize(img_path) / 1024  # KB
        self.info_label.setText(
            f"{filename} • {pixmap.width()}×{pixmap.height()}px • {file_size:.1f} KB"
        )

        # Update thumbnail highlights
        self._update_thumbnail_highlights()

        # Reset zoom and pan
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)

        # Position arrows
        self._position_navigation_arrows()

    def _update_image_display(self):
        """Update image display with current zoom and pan"""
        if not hasattr(self, 'original_pixmap') or self.original_pixmap.isNull():
            return

        # Calculate display size
        label_size = self.image_label.size()
        pixmap = self.original_pixmap

        # Scale to fit with zoom
        scaled_pixmap = pixmap.scaled(
            int(label_size.width() * self.zoom_level),
            int(label_size.height() * self.zoom_level),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Apply pan offset when zoomed in
        if self.zoom_level > 1.0:
            # Create a larger canvas to hold the zoomed/panned image
            canvas = QPixmap(label_size)
            canvas.fill(Qt.transparent)
            
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Calculate centered position with pan offset
            x = (label_size.width() - scaled_pixmap.width()) // 2 + self.pan_offset.x()
            y = (label_size.height() - scaled_pixmap.height()) // 2 + self.pan_offset.y()
            
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
            
            self.image_label.setPixmap(canvas)
        else:
            # No panning when not zoomed
            self.image_label.setPixmap(scaled_pixmap)

    def _update_thumbnail_highlights(self):
        """Highlight current thumbnail"""
        for i, btn in enumerate(self.thumb_buttons):
            if i == self.current_index:
                btn.setStyleSheet("""
                    QPushButton {
                        border: 3px solid #2196F3;
                        border-radius: 6px;
                        background-color: #333333;
                    }
                    QPushButton:hover {
                        border-color: #2196F3;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        border: 3px solid transparent;
                        border-radius: 6px;
                        background-color: #333333;
                    }
                    QPushButton:hover {
                        border-color: rgba(255, 255, 255, 100);
                    }
                """)

    def _show_image(self, index: int):
        """Show image at specific index"""
        if 0 <= index < len(self.image_paths):
            self.current_index = index
            self._load_current_image()

    def _show_previous(self):
        """Show previous image"""
        if self.current_index > 0:
            self._show_image(self.current_index - 1)

    def _show_next(self):
        """Show next image"""
        if self.current_index < len(self.image_paths) - 1:
            self._show_image(self.current_index + 1)

    def _zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(self.zoom_level * 1.2, 3.0)  # Max 3x zoom
        # Change cursor to show pan is available
        if self.zoom_level > 1.0:
            self.image_label.setCursor(Qt.OpenHandCursor)
        self._update_image_display()

    def _zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.5)  # Min 0.5x zoom
        # Reset pan when zooming out to 1.0 or less
        if self.zoom_level <= 1.0:
            self.pan_offset = QPoint(0, 0)
            self.image_label.setCursor(Qt.ArrowCursor)
        self._update_image_display()

    def _zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.image_label.setCursor(Qt.ArrowCursor)
        self._update_image_display()

    # === EVENT HANDLERS ===

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts"""
        key = event.key()

        if key == Qt.Key_Escape:
            self.close()
        elif key in (Qt.Key_Left, Qt.Key_A):
            self._show_previous()
        elif key in (Qt.Key_Right, Qt.Key_D):
            self._show_next()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self._zoom_in()
        elif key == Qt.Key_Minus:
            self._zoom_out()
        elif key == Qt.Key_0:
            self._zoom_reset()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        """Handle window resize"""
        super().resizeEvent(event)
        self._position_navigation_arrows()
        self._update_image_display()

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zoom"""
        if event.angleDelta().y() > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for closing on background click"""
        # Close if clicked outside the image area (on dark background)
        if event.button() == Qt.LeftButton:
            if not self.image_label.geometry().contains(event.pos()):
                self.close()
        super().mousePressEvent(event)

    def eventFilter(self, obj, event: QEvent) -> bool:
        """Event filter for image label - implements click-and-drag panning when zoomed"""
        if obj == self.image_label and self.zoom_level > 1.0:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.dragging = True
                    self.is_panning = False
                    self.last_mouse_pos = event.pos()
                    self.image_label.setCursor(Qt.ClosedHandCursor)
                    return True
            
            elif event.type() == QEvent.MouseMove:
                if self.dragging:
                    self.is_panning = True
                    # Calculate pan delta
                    delta = event.pos() - self.last_mouse_pos
                    self.pan_offset += delta
                    self.last_mouse_pos = event.pos()
                    
                    # Constrain panning to prevent image from going too far off screen
                    max_pan = 500  # Maximum pan distance in pixels
                    self.pan_offset.setX(max(-max_pan, min(max_pan, self.pan_offset.x())))
                    self.pan_offset.setY(max(-max_pan, min(max_pan, self.pan_offset.y())))
                    
                    self._update_image_display()
                    return True
            
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.dragging = False
                    self.image_label.setCursor(Qt.OpenHandCursor if self.zoom_level > 1.0 else Qt.ArrowCursor)
                    # If user didn't drag much, it was a click (not implemented here)
                    return True
        
        return super().eventFilter(obj, event)
