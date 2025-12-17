"""
Standalone demo: modern, smooth image gallery UI (PySide6/Qt Widgets).

Purpose:
  - Preview the "video-style" gallery interaction: main preview + animated thumbnail grid.
  - This file does NOT integrate into EmployeeVault yet.

Run:
  python modern_gallery_demo.py

Requires:
  PySide6 (same environment as EmployeeVault)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from PySide6.QtCore import QEasingCurve, QPoint, QRect, Qt, QPropertyAnimation, QParallelAnimationGroup, Signal
from PySide6.QtGui import QGuiApplication, QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)


QSS = """
QMainWindow { background: #0b0f1a; }

QFrame#Card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(22, 28, 55, 0.98),
        stop:1 rgba(12, 16, 34, 0.98));
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
}

QLabel#Title {
    color: rgba(240, 245, 255, 0.95);
    font-size: 22px;
    font-weight: 800;
}

QLabel#Subtitle {
    color: rgba(240, 245, 255, 0.65);
    font-size: 12px;
}

QFrame#DropZone {
    background: rgba(255, 255, 255, 0.04);
    border: 2px dashed rgba(120, 140, 200, 0.35);
    border-radius: 14px;
}

QPushButton#Primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(76, 110, 255, 0.95),
        stop:1 rgba(120, 76, 255, 0.85));
    color: rgba(255, 255, 255, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 700;
}
QPushButton#Primary:hover { background: rgba(92, 126, 255, 0.98); }
QPushButton#Primary:pressed { background: rgba(56, 92, 230, 1.0); }

QPushButton#Ghost {
    background: rgba(255, 255, 255, 0.06);
    color: rgba(240, 245, 255, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 600;
}
QPushButton#Ghost:hover { background: rgba(255, 255, 255, 0.10); }
QPushButton#Ghost:pressed { background: rgba(255, 255, 255, 0.14); }

QLabel#SectionTitle {
    color: rgba(240, 245, 255, 0.85);
    font-size: 12px;
    font-weight: 700;
}

QFrame#Preview {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
}

ThumbnailTile {
    background: rgba(255, 255, 255, 0.02);
    border: 2px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
}
ThumbnailTile:hover { border-color: rgba(255, 255, 255, 0.18); }
ThumbnailTile[selected=\"true\"] { border-color: rgba(76, 110, 255, 0.9); }

QToolButton#Remove {
    background: rgba(255, 60, 90, 0.85);
    color: white;
    border: none;
    border-radius: 9px;
    padding: 0px;
    font-weight: 900;
}
QToolButton#Remove:hover { background: rgba(255, 60, 90, 1.0); }

QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.12); border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""


@dataclass(frozen=True)
class Motion:
    duration_ms: int = 260
    easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic


def _read_pixmap(path: Path, target_px: int) -> Optional[QPixmap]:
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    image = reader.read()
    if image.isNull():
        return None
    scaled = image.scaled(
        target_px,
        target_px,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    return QPixmap.fromImage(scaled)


class PreviewWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Preview")

        self._label = QLabel("Select images to preview", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: rgba(240,245,255,0.55); font-size: 12px;")
        self._label.setScaledContents(False)

        self._opacity = QGraphicsOpacityEffect(self._label)
        self._opacity.setOpacity(1.0)
        self._label.setGraphicsEffect(self._opacity)

        self._fade_anim: Optional[QPropertyAnimation] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self._label, 1)

    def set_preview_pixmap(self, pixmap: Optional[QPixmap]):
        if self._fade_anim:
            self._fade_anim.stop()
            self._fade_anim.deleteLater()
            self._fade_anim = None

        def _swap_and_fade_in():
            if pixmap is None:
                self._label.setPixmap(QPixmap())
                self._label.setText("Select images to preview")
            else:
                self._label.setText("")
                self._label.setPixmap(pixmap)
                self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self._fade_anim = QPropertyAnimation(self._opacity, b"opacity", self)
            self._fade_anim.setDuration(220)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._fade_anim.start()

        self._fade_anim = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_anim.setDuration(140)
        self._fade_anim.setStartValue(float(self._opacity.opacity()))
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.finished.connect(_swap_and_fade_in)
        self._fade_anim.start()


class ThumbnailTile(QWidget):
    clicked = Signal(object)  # Path
    remove_requested = Signal(object)  # Path

    def __init__(self, image_path: Path, thumb_px: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "ThumbnailTile")
        self._path = image_path
        self._thumb_px = thumb_px
        self._selected = False

        self._thumb_btn = QPushButton(self)
        self._thumb_btn.setFlat(True)
        self._thumb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._thumb_btn.clicked.connect(lambda: self.clicked.emit(self._path))
        self._thumb_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")

        self._remove_btn = QToolButton(self)
        self._remove_btn.setObjectName("Remove")
        self._remove_btn.setText("×")
        self._remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_btn.setFixedSize(18, 18)
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self._path))

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self._pixmap = _read_pixmap(self._path, target_px=self._thumb_px)
        if self._pixmap:
            self._thumb_btn.setIcon(QIcon(self._pixmap))
            self._thumb_btn.setIconSize(self._pixmap.size())

        self.set_selected(False)

    def image_path(self) -> Path:
        return self._path

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_tile_rect(self, rect: QRect):
        self.setGeometry(rect)
        self._thumb_btn.setGeometry(10, 10, rect.width() - 20, rect.height() - 20)
        self._remove_btn.move(rect.width() - self._remove_btn.width() - 8, 8)

    def opacity_effect(self) -> QGraphicsOpacityEffect:
        return self._opacity


class AnimatedThumbnailGrid(QWidget):
    image_selected = Signal(object)  # Path

    def __init__(self, motion: Motion, parent: QWidget | None = None):
        super().__init__(parent)
        self._motion = motion
        self._tiles: List[ThumbnailTile] = []
        self._selected: Optional[Path] = None
        self._active_groups: List[QParallelAnimationGroup] = []

        self._tile_w = 140
        self._tile_h = 110
        self._gap = 14
        self._thumb_px = 160

        self.setMinimumHeight(2 * self._tile_h + 3 * self._gap)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_images(self, paths: Iterable[Path]):
        self.clear(animate=False)
        self.add_images(paths)

    def add_images(self, paths: Iterable[Path]):
        added = 0
        for p in paths:
            if not p.exists() or not p.is_file():
                continue
            if p in (t.image_path() for t in self._tiles):
                continue
            tile = ThumbnailTile(p, self._thumb_px, parent=self)
            tile.clicked.connect(self._on_tile_clicked)
            tile.remove_requested.connect(self._on_remove_requested)
            tile.opacity_effect().setOpacity(0.0)
            tile.show()
            self._tiles.append(tile)
            added += 1

        self._relayout(animate=True, fade_in_new=True if added else False)

        if self._selected is None and self._tiles:
            self._set_selected(self._tiles[0].image_path())

    def clear(self, animate: bool = True):
        if not self._tiles:
            return

        if not animate:
            for t in self._tiles:
                t.deleteLater()
            self._tiles.clear()
            self._selected = None
            self.update()
            return

        group = QParallelAnimationGroup(self)
        for t in list(self._tiles):
            fade = QPropertyAnimation(t.opacity_effect(), b"opacity", group)
            fade.setDuration(180)
            fade.setStartValue(float(t.opacity_effect().opacity()))
            fade.setEndValue(0.0)
            fade.setEasingCurve(QEasingCurve.Type.OutCubic)
            group.addAnimation(fade)

        def _finish():
            for t in list(self._tiles):
                t.deleteLater()
            self._tiles.clear()
            self._selected = None
            self.update()

        group.finished.connect(_finish)
        self._active_groups.append(group)
        group.finished.connect(lambda: self._active_groups.remove(group) if group in self._active_groups else None)
        group.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout(animate=False)

    def _on_tile_clicked(self, path: Path):
        self._set_selected(path)
        self.image_selected.emit(path)

    def _set_selected(self, path: Path):
        self._selected = path
        for t in self._tiles:
            t.set_selected(t.image_path() == path)

    def _on_remove_requested(self, path: Path):
        tile = next((t for t in self._tiles if t.image_path() == path), None)
        if tile is None:
            return

        group = QParallelAnimationGroup(self)

        fade = QPropertyAnimation(tile.opacity_effect(), b"opacity", group)
        fade.setDuration(170)
        fade.setStartValue(float(tile.opacity_effect().opacity()))
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(fade)

        shrink_from = tile.geometry()
        center = shrink_from.center()
        shrink_to = QRect(center.x(), center.y(), 0, 0)
        geom = QPropertyAnimation(tile, b"geometry", group)
        geom.setDuration(190)
        geom.setStartValue(shrink_from)
        geom.setEndValue(shrink_to)
        geom.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(geom)

        def _finish():
            was_selected = self._selected == path
            self._tiles.remove(tile)
            tile.deleteLater()
            self._relayout(animate=True, fade_in_new=False)
            if was_selected:
                self._selected = None
                if self._tiles:
                    self._set_selected(self._tiles[0].image_path())
                    self.image_selected.emit(self._tiles[0].image_path())
                else:
                    self.image_selected.emit(None)

        group.finished.connect(_finish)
        self._active_groups.append(group)
        group.finished.connect(lambda: self._active_groups.remove(group) if group in self._active_groups else None)
        group.start()

    def _relayout(self, animate: bool, fade_in_new: bool = False):
        if not self._tiles:
            self.setMinimumHeight(2 * self._tile_h + 3 * self._gap)
            self.update()
            return

        available_w = max(1, self.width())
        cols = max(1, min(4, (available_w - self._gap) // (self._tile_w + self._gap)))
        rows = (len(self._tiles) + cols - 1) // cols
        rows = max(1, rows)

        min_h = rows * self._tile_h + (rows + 1) * self._gap
        self.setMinimumHeight(min_h)

        target_rects: List[QRect] = []
        for i in range(len(self._tiles)):
            r = i // cols
            c = i % cols
            x = self._gap + c * (self._tile_w + self._gap)
            y = self._gap + r * (self._tile_h + self._gap)
            target_rects.append(QRect(x, y, self._tile_w, self._tile_h))

        if not animate:
            for tile, rect in zip(self._tiles, target_rects):
                tile.set_tile_rect(rect)
            return

        group = QParallelAnimationGroup(self)

        for tile, rect in zip(self._tiles, target_rects):
            if tile.geometry().isNull():
                start = QRect(rect.center().x(), rect.center().y(), 0, 0)
                tile.setGeometry(start)
                tile.set_tile_rect(start)
            geom = QPropertyAnimation(tile, b"geometry", group)
            geom.setDuration(self._motion.duration_ms)
            geom.setStartValue(tile.geometry())
            geom.setEndValue(rect)
            geom.setEasingCurve(self._motion.easing)
            group.addAnimation(geom)

            if fade_in_new and float(tile.opacity_effect().opacity()) < 0.05:
                fade = QPropertyAnimation(tile.opacity_effect(), b"opacity", group)
                fade.setDuration(220)
                fade.setStartValue(0.0)
                fade.setEndValue(1.0)
                fade.setEasingCurve(QEasingCurve.Type.OutCubic)
                group.addAnimation(fade)

        def _apply_final_rects():
            for tile, rect in zip(self._tiles, target_rects):
                tile.set_tile_rect(rect)

        group.finished.connect(_apply_final_rects)
        self._active_groups.append(group)
        group.finished.connect(lambda: self._active_groups.remove(group) if group in self._active_groups else None)
        group.start()


class ModernGalleryDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Gallery Demo (Qt/PySide6)")
        self.setMinimumSize(980, 720)

        self._motion = Motion()

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(14)

        title = QLabel("Modern Image Gallery")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        subtitle = QLabel("Upload, preview and manage images with smooth transitions")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        drop = QFrame()
        drop.setObjectName("DropZone")
        drop_layout = QVBoxLayout(drop)
        drop_layout.setContentsMargins(18, 18, 18, 18)
        drop_layout.setSpacing(10)

        choose = QPushButton("Choose Images")
        choose.setObjectName("Primary")
        choose.clicked.connect(self._choose_images)
        choose.setFixedWidth(220)
        choose.setCursor(Qt.CursorShape.PointingHandCursor)

        formats = QLabel("Supported formats: JPG, PNG, GIF, WEBP, BMP")
        formats.setObjectName("Subtitle")
        formats.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        drop_layout.addWidget(choose, 0, Qt.AlignmentFlag.AlignHCenter)
        drop_layout.addWidget(formats, 0, Qt.AlignmentFlag.AlignHCenter)

        card_layout.addWidget(drop)

        self._preview = PreviewWidget()
        self._preview.setFixedHeight(270)
        card_layout.addWidget(self._preview)

        section_row = QHBoxLayout()
        section_row.setContentsMargins(2, 0, 2, 0)

        section_title = QLabel("Your Images")
        section_title.setObjectName("SectionTitle")

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("Ghost")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self._grid.clear(animate=True))

        section_row.addWidget(section_title)
        section_row.addStretch()
        section_row.addWidget(clear_btn)
        card_layout.addLayout(section_row)

        self._grid = AnimatedThumbnailGrid(self._motion)
        self._grid.image_selected.connect(self._on_image_selected)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self._grid)
        scroll.setFixedHeight(2 * 110 + 3 * 14 + 14)  # 2 rows visible by default
        card_layout.addWidget(scroll)

        root_layout.addWidget(card, 1)
        self.setCentralWidget(root)

        self.setStyleSheet(QSS)

    def _choose_images(self):
        start_dir = str(Path.home())
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose images",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.gif *.webp *.bmp);;All Files (*.*)",
        )
        if not files:
            return
        self._grid.add_images(Path(f) for f in files)

    def _on_image_selected(self, path: Optional[Path]):
        if not path:
            self._preview.set_preview_pixmap(None)
            return

        # Fit preview to widget size.
        pix = _read_pixmap(path, target_px=1400)
        if pix is None:
            self._preview.set_preview_pixmap(None)
            return

        target = self._preview.size()
        scaled = pix.scaled(
            target.width() - 36,
            target.height() - 36,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview.set_preview_pixmap(scaled)


def main():
    app = QApplication(sys.argv)

    # Slightly smoother font rendering on some Windows setups.
    QGuiApplication.setFont(app.font())

    w = ModernGalleryDemo()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

