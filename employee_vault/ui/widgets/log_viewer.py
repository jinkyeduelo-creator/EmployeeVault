"""
Live Log Viewer Widget
Admin-only widget for viewing application logs in real-time
"""

import logging
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat


class LogSignal(QObject):
    """Qt Signal emitter for log messages"""
    log_message = Signal(str, int)  # message, level


class LogHandler(logging.Handler):
    """Custom logging handler that emits Qt signals"""
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter

    def emit(self, record):
        """Emit log record as Qt signal"""
        try:
            msg = self.format(record)
            self.signal_emitter.log_message.emit(msg, record.levelno)
        except Exception:
            self.handleError(record)


class LogViewerWidget(QWidget):
    """
    Live log viewer with color-coded messages, auto-scroll, and export functionality.
    Only accessible to admin users.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auto_scroll = True
        self.log_buffer = []  # Store all logs for export

        # Setup UI
        self._setup_ui()

        # Setup logging handler
        self.log_signal = LogSignal()
        self.log_handler = LogHandler(self.log_signal)
        self.log_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))

        # Connect signal to slot
        self.log_signal.log_message.connect(self._append_log)

        # Add handler to root logger
        logging.getLogger().addHandler(self.log_handler)

    def _setup_ui(self):
        """Setup the log viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with title and controls
        header = QHBoxLayout()

        title = QLabel("📋 Live Logs (Admin Only)")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.9);
        """)
        header.addWidget(title)

        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        self.auto_scroll_check.toggled.connect(self._toggle_auto_scroll)
        header.addWidget(self.auto_scroll_check)

        # Export button
        self.export_btn = QPushButton("💾 Export Logs")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.4),
                    stop:1 rgba(33, 150, 243, 0.3));
                border: 1.5px solid rgba(74, 158, 255, 0.6);
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.6),
                    stop:1 rgba(33, 150, 243, 0.5));
            }
        """)
        self.export_btn.clicked.connect(self._export_logs)
        header.addWidget(self.export_btn)

        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(244, 67, 54, 0.4),
                    stop:1 rgba(211, 47, 47, 0.3));
                border: 1.5px solid rgba(244, 67, 54, 0.6);
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(244, 67, 54, 0.6),
                    stop:1 rgba(211, 47, 47, 0.5));
            }
        """)
        self.clear_btn.clicked.connect(self._clear_logs)
        header.addWidget(self.clear_btn)

        header.addStretch()
        layout.addLayout(header)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: rgba(20, 25, 30, 0.95);
                border: 2px solid rgba(74, 158, 255, 0.3);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.9);
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)

        # Legend
        legend = QHBoxLayout()
        legend.addWidget(QLabel("<span style='color: #4a9eff;'>ℹ️ INFO</span>"))
        legend.addWidget(QLabel("<span style='color: #ff9800;'>⚠️ WARNING</span>"))
        legend.addWidget(QLabel("<span style='color: #f44336;'>❌ ERROR</span>"))
        legend.addWidget(QLabel("<span style='color: #9c27b0;'>🔴 CRITICAL</span>"))
        legend.addStretch()
        layout.addLayout(legend)

    def _append_log(self, message, level):
        """Append log message with color coding"""
        # Store in buffer
        self.log_buffer.append(message)

        # Color based on level
        if level >= logging.CRITICAL:
            color = QColor(156, 39, 176)  # Purple
            prefix = "🔴 "
        elif level >= logging.ERROR:
            color = QColor(244, 67, 54)  # Red
            prefix = "❌ "
        elif level >= logging.WARNING:
            color = QColor(255, 152, 0)  # Orange
            prefix = "⚠️ "
        else:
            color = QColor(74, 158, 255)  # Blue
            prefix = "ℹ️ "

        # Format and append
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Set color
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.setCharFormat(fmt)

        # Insert text
        cursor.insertText(prefix + message + "\n")

        # Auto-scroll if enabled
        if self.auto_scroll:
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()

    def _toggle_auto_scroll(self, checked):
        """Toggle auto-scroll"""
        self.auto_scroll = checked

    def _clear_logs(self):
        """Clear log display (but keep buffer for export)"""
        self.log_text.clear()

    def _export_logs(self):
        """Export logs to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"employee_vault_logs_{timestamp}.txt"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            default_filename,
            "Text Files (*.txt);;All Files (*.*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"EmployeeVault Logs - Exported at {datetime.now()}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write("\n".join(self.log_buffer))

                logging.info(f"Logs exported to: {filename}")
            except Exception as e:
                logging.error(f"Failed to export logs: {e}")

    def auto_export_on_crash(self):
        """Auto-export logs on application crash"""
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_log = os.path.join(logs_dir, f"crash_log_{timestamp}.txt")

        try:
            with open(crash_log, 'w', encoding='utf-8') as f:
                f.write(f"EmployeeVault Crash Log - {datetime.now()}\n")
                f.write("=" * 80 + "\n\n")
                f.write("\n".join(self.log_buffer))

            return crash_log
        except Exception as e:
            print(f"Failed to auto-export crash log: {e}")
            return None

    def closeEvent(self, event):
        """Auto-export logs when widget is closed"""
        # Remove handler to prevent memory leaks
        logging.getLogger().removeHandler(self.log_handler)
        super().closeEvent(event)
