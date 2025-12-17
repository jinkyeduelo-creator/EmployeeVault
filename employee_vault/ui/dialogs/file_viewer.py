"""
File Viewer Dialog
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import *
from employee_vault.database import DB
from employee_vault.validators import *
from employee_vault.utils import *
from employee_vault.models import *
from employee_vault.ui.widgets import *
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase

class FileViewerDialog(AnimatedDialogBase):
    def __init__(self, path, parent=None):
        # v4.4.1: Use fade animation for file viewer
        super().__init__(parent, animation_style="fade"); self.setWindowTitle(f"File Viewer — {os.path.basename(path)}"); self.resize(900,700); v=QVBoxLayout(self)
        head=QLabel(f"<b>{os.path.basename(path)}</b> &nbsp; <span style='color:gray'>Size: {os.path.getsize(path)/1024:.1f} KB</span>"); v.addWidget(head)
        self.path=path; ext=os.path.splitext(path)[1].lower()
        if ext=='.pdf' and PDF_AVAILABLE:
            self.doc=QPdfDocument(self); self.view=QPdfView(self); self.view.setDocument(self.doc); self.view.setZoomMode(QPdfView.ZoomMode.FitInView); self.doc.load(path)
            tb=QToolBar(); prev=tb.addAction("◀ Prev"); nxt=tb.addAction("Next ▶"); tb.addSeparator(); zin=tb.addAction("Zoom +"); zout=tb.addAction("Zoom −"); self.page_lbl=QLabel("Page"); tb.addWidget(QWidget()); tb.addWidget(self.page_lbl); v.addWidget(tb)
            def upd(): self.page_lbl.setText(f"Page {self.view.pageNavigation().currentPage()+1}/{self.doc.pageCount()}")
            prev.triggered.connect(lambda:(self.view.pageNavigation().goToPreviousPage(),upd())); nxt.triggered.connect(lambda:(self.view.pageNavigation().goToNextPage(),upd()))
            zin.triggered.connect(lambda:self.view.setZoomFactor(self.view.zoomFactor()*1.2)); zout.triggered.connect(lambda:self.view.setZoomFactor(self.view.zoomFactor()/1.2))
            v.addWidget(self.view,1); upd()
        elif ext in {'.txt','.log','.json','.xml','.csv','.py','.html','.css','.js'}:
            text=QTextEdit(); text.setReadOnly(True)
            try: text.setPlainText(Path(path).read_text(encoding="utf-8"))
            except Exception: text.setPlainText("Could not read file as text.")
            v.addWidget(text,1)
        elif ext in {'.png','.jpg','.jpeg','.gif','.bmp'}:
            lbl=QLabel(alignment=Qt.AlignCenter); pix=QPixmap(path); lbl.setPixmap(pix.scaled(QSize(820,620),Qt.KeepAspectRatio,Qt.SmoothTransformation) if not pix.isNull() else QPixmap()); v.addWidget(lbl,1)
        else:
            info=QLabel("This file type cannot be previewed directly.\n\nClick 'Open Externally'.");
            if ext=='.pdf' and not PDF_AVAILABLE: info.setText(info.text()+"\n\nPDF preview requires PySide6 QtPdf.")
            v.addWidget(info,1)
        row=QHBoxLayout(); open_ext=ModernAnimatedButton("🔗 Open Externally"); reveal=ModernAnimatedButton("📂 Reveal in Folder"); download_btn=ModernAnimatedButton("💾 Download"); close_btn=ModernAnimatedButton("❌ Close")
        row.addStretch(1); row.addWidget(download_btn); row.addWidget(open_ext); row.addWidget(reveal); row.addWidget(close_btn); v.addLayout(row)
        download_btn.clicked.connect(self._download_file); open_ext.clicked.connect(self._open_external); reveal.clicked.connect(self._reveal); close_btn.clicked.connect(self.close)
    def _download_file(self):
        """Download/save file to user's chosen location"""
        import shutil
        filename = os.path.basename(self.path)
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            filename,
            "All Files (*.*)"
        )
        if save_path:
            try:
                shutil.copy2(self.path, save_path)
                from employee_vault.ui.modern_ui_helper import show_success_toast
                show_success_toast(self, f"File saved successfully!\n\n{save_path}")
            except Exception as e:
                from employee_vault.ui.modern_ui_helper import show_error_toast
                show_error_toast(self, f"Failed to save file:\n{str(e)}")
    def _open_external(self):
        from PySide6.QtCore import QUrl; QDesktopServices.openUrl(QUrl.fromLocalFile(self.path))
    def _reveal(self):
        folder=os.path.dirname(self.path)
        try:
            if sys.platform.startswith("win"): os.startfile(folder)
            elif sys.platform=="darwin": os.system(f'open "{folder}"')
            else: os.system(f'xdg-open "{folder}"')
        except Exception: pass


# ============================================================================
# NOTE: CollapsibleSection, WheelGuard, create_circular_pixmap, 
# ModernCalendarWidget, and ModernDateEdit are all imported from 
# employee_vault.ui.widgets - duplicate definitions removed.
# ============================================================================
