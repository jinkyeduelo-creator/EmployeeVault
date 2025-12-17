"""
Notification Center Widget
v5.3.0: Real-time notifications for all users with contract expiry alerts
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QSizePolicy
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QSequentialAnimationGroup, Property, QPoint
)
from PySide6.QtGui import QColor, QFont, QCursor

# Use centralized design tokens for colors and typography
from employee_vault.design_tokens import TOKENS, get_semantic_color

from employee_vault.database import DB


class NotificationItem(QFrame):
    """Individual notification card with animations"""
    
    clicked = Signal(dict)  # Emits notification data when clicked
    dismissed = Signal(object)  # Emits self when dismissed
    
    def __init__(self, notification: dict, parent=None):
        super().__init__(parent)
        self.notification = notification
        self.setObjectName("notificationItem")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Determine notification type and colors
        ntype = notification.get('type', 'info')
        self._setup_style(ntype)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Icon based on type
        icons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅',
            'contract_expired': '❌',
            'contract_expiring': '📅'
        }
        icon_label = QLabel(icons.get(ntype, 'ℹ️'))
        icon_label.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        title = QLabel(notification.get('title', 'Notification'))
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: white; background: transparent;")
        content_layout.addWidget(title)
        
        message = QLabel(notification.get('message', ''))
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.85); background: transparent;")
        content_layout.addWidget(message)
        
        if notification.get('time'):
            time_label = QLabel(notification['time'])
            time_label.setStyleSheet("font-size: 10px; color: rgba(255,255,255,0.6); background: transparent;")
            content_layout.addWidget(time_label)
        
        layout.addLayout(content_layout, 1)
        
        # Dismiss button
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setFixedSize(24, 24)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                border: none;
                border-radius: 12px;
                color: rgba(255,255,255,0.7);
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.2);
                color: white;
            }
        """)
        dismiss_btn.clicked.connect(self._dismiss)
        layout.addWidget(dismiss_btn)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
    def _setup_style(self, ntype: str):
        """Setup style based on notification type"""
        colors = {
            'critical': ('220, 38, 38', '255, 100, 100'),      # Red
            'warning': ('245, 158, 11', '255, 193, 7'),         # Amber
            'info': ('59, 130, 246', '96, 165, 250'),          # Blue
            'success': ('34, 197, 94', '74, 222, 128'),        # Green
            'contract_expired': ('239, 68, 68', '248, 113, 113'),  # Red
            'contract_expiring': ('249, 115, 22', '251, 146, 60')  # Orange
        }
        
        base, light = colors.get(ntype, colors['info'])
        
        self.setStyleSheet(f"""
            #notificationItem {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({base}, 0.95),
                    stop:1 rgba({base}, 0.85));
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                min-height: 60px;
            }}
            #notificationItem:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({light}, 0.98),
                    stop:1 rgba({base}, 0.92));
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
    def _dismiss(self):
        """Animate dismissal"""
        self.anim = QPropertyAnimation(self, b"maximumHeight")
        self.anim.setDuration(200)
        self.anim.setStartValue(self.height())
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.anim.finished.connect(lambda: self.dismissed.emit(self))
        self.anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.notification)
        super().mousePressEvent(event)


class NotificationBadge(QLabel):
    """Badge showing notification count"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(22, 22)
        self._count = 0
        self._update_style()
        
    def set_count(self, count: int):
        self._count = count
        if count > 0:
            self.setText(str(min(count, 99)) if count < 100 else "99+")
            self.show()
            # Pulse animation
            self._pulse()
        else:
            self.hide()
        self._update_style()
            
    def _update_style(self):
        bg_color = "#ef4444" if self._count > 0 else "#6b7280"
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                font-size: 10px;
                font-weight: bold;
                border-radius: 11px;
                border: 2px solid rgba(255,255,255,0.3);
            }}
        """)
        
    def _pulse(self):
        """Pulse animation to draw attention"""
        self.pulse_anim = QPropertyAnimation(self, b"geometry")
        self.pulse_anim.setDuration(300)
        orig = self.geometry()
        expanded = orig.adjusted(-2, -2, 2, 2)
        self.pulse_anim.setKeyValueAt(0, orig)
        self.pulse_anim.setKeyValueAt(0.5, expanded)
        self.pulse_anim.setKeyValueAt(1, orig)
        self.pulse_anim.start()


class NotificationCenter(QWidget):
    """
    Central notification management widget
    Shows real-time notifications for contract expiry and other alerts
    """
    
    notification_clicked = Signal(dict)
    
    def __init__(self, db: DB, parent=None):
        super().__init__(parent)
        self.db = db
        self.notifications: List[dict] = []
        self.setObjectName("notificationCenter")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with badge
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 65, 80, 0.95),
                    stop:1 rgba(45, 50, 60, 0.98));
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title = QLabel("🔔 Notifications")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        header_layout.addWidget(title)
        
        self.badge = NotificationBadge()
        self.badge.hide()
        header_layout.addWidget(self.badge)
        
        header_layout.addStretch()
        
        # Clear all button
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.7);
                border: none;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: white;
                text-decoration: underline;
            }
        """)
        clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        
        # Scroll area for notifications
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        # Container for notification items
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        # Empty state
        self.empty_label = QLabel("No notifications")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: rgba(255,255,255,0.5);
            font-size: 12px;
            padding: 30px;
        """)
        self.container_layout.insertWidget(0, self.empty_label)
        
        # Timer for periodic checks
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_contract_expiry)
        self.check_timer.setInterval(5 * 60 * 1000)  # Check every 5 minutes
        
        # Initial check after 3 seconds
        QTimer.singleShot(3000, self.check_contract_expiry)
        
    def start_monitoring(self):
        """Start monitoring for notifications"""
        self.check_timer.start()
        logging.info("Notification center monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.check_timer.stop()
        
    def check_contract_expiry(self):
        """Check for expiring contracts and create notifications"""
        try:
            today = datetime.now()
            
            # Query employees with contract_expiry dates
            rows = self.db.conn.execute("""
                SELECT emp_id, name, position, department, contract_expiry, agency
                FROM employees
                WHERE contract_expiry IS NOT NULL
                  AND contract_expiry != ''
                  AND resign_date IS NULL
                ORDER BY contract_expiry ASC
            """).fetchall()
            
            expired_count = 0
            expiring_soon = []
            
            for row in rows:
                try:
                    expiry_str = row['contract_expiry']
                    # Try different date formats
                    expiry_date = None
                    for fmt in ["%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y"]:
                        try:
                            expiry_date = datetime.strptime(expiry_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not expiry_date:
                        continue
                        
                    days_left = (expiry_date - today).days
                    
                    if days_left < 0:
                        expired_count += 1
                    elif days_left <= 30:
                        expiring_soon.append({
                            'emp_id': row['emp_id'],
                            'name': row['name'],
                            'days_left': days_left,
                            'expiry_date': expiry_str
                        })
                        
                except Exception as e:
                    logging.warning(f"Date parse error: {e}")
                    continue
            
            # Add notifications
            if expired_count > 0:
                self.add_notification({
                    'type': 'contract_expired',
                    'title': f'🚨 {expired_count} Contract(s) Expired!',
                    'message': f'{expired_count} employee contract(s) have expired and need immediate attention.',
                    'time': datetime.now().strftime('%H:%M'),
                    'data': {'filter': 'expired'}
                })
                
            # Group expiring soon by urgency
            critical = [e for e in expiring_soon if e['days_left'] <= 7]
            warning = [e for e in expiring_soon if 7 < e['days_left'] <= 14]
            notice = [e for e in expiring_soon if 14 < e['days_left'] <= 30]
            
            if critical:
                names = ", ".join([e['name'] for e in critical[:3]])
                if len(critical) > 3:
                    names += f" +{len(critical)-3} more"
                self.add_notification({
                    'type': 'critical',
                    'title': f'⚠️ {len(critical)} Contract(s) Expiring This Week!',
                    'message': f'{names}',
                    'time': datetime.now().strftime('%H:%M'),
                    'data': {'employees': critical}
                })
                
            if warning:
                self.add_notification({
                    'type': 'warning',
                    'title': f'📅 {len(warning)} Contract(s) Expiring in 2 Weeks',
                    'message': 'Review and renew contracts soon.',
                    'time': datetime.now().strftime('%H:%M'),
                    'data': {'employees': warning}
                })
                
            if notice:
                self.add_notification({
                    'type': 'info',
                    'title': f'ℹ️ {len(notice)} Contract(s) Expiring Within 30 Days',
                    'message': 'Plan ahead for contract renewals.',
                    'time': datetime.now().strftime('%H:%M'),
                    'data': {'employees': notice}
                })
                    
        except Exception as e:
            logging.error(f"Error checking contract expiry: {e}")
            
    def add_notification(self, notification: dict):
        """Add a notification to the center"""
        # Check for duplicates (same title in last 5 minutes)
        for existing in self.notifications[-10:]:
            if existing.get('title') == notification.get('title'):
                return  # Skip duplicate
                
        self.notifications.append(notification)
        
        # Create notification item
        item = NotificationItem(notification)
        item.clicked.connect(self._on_notification_clicked)
        item.dismissed.connect(self._on_notification_dismissed)
        
        # Insert at top (before stretch)
        self.container_layout.insertWidget(0, item)
        
        # Update badge
        self.badge.set_count(len(self.notifications))
        
        # Hide empty state
        self.empty_label.hide()
        
        # Animate in
        item.setMaximumHeight(0)
        anim = QPropertyAnimation(item, b"maximumHeight")
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(100)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()
        
    def _on_notification_clicked(self, notification: dict):
        """Handle notification click"""
        self.notification_clicked.emit(notification)
        
    def _on_notification_dismissed(self, item: NotificationItem):
        """Handle notification dismissal"""
        if item.notification in self.notifications:
            self.notifications.remove(item.notification)
        item.deleteLater()
        self.badge.set_count(len(self.notifications))
        
        if not self.notifications:
            self.empty_label.show()
            
    def clear_all(self):
        """Clear all notifications"""
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if isinstance(widget, NotificationItem):
                widget.deleteLater()
                
        self.notifications.clear()
        self.badge.set_count(0)
        self.empty_label.show()


class NotificationBell(QPushButton):
    """
    Bell button with notification badge
    Click to show/hide notification panel
    """
    
    def __init__(self, parent=None):
        super().__init__("🔔", parent)
        self.setFixedSize(28, 28)  # Compact size for header
        self._count = 0
        self._setup_style()
        
        # Badge - smaller to fit on smaller bell
        self.badge = NotificationBadge(self)
        self.badge.setFixedSize(16, 16)  # Smaller badge
        self.badge.move(16, -2)  # Adjusted position for smaller bell
        self.badge.hide()
        
    def _setup_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 14px;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        
    def set_count(self, count: int):
        """Update notification count"""
        self._count = count
        self.badge.set_count(count)


class FloatingNotificationPanel(QFrame):
    """
    Floating panel that appears when bell is clicked
    """
    
    def __init__(self, notification_center: NotificationCenter, parent=None):
        super().__init__(parent)
        # Fix: Remove WA_TranslucentBackground to avoid Windows rendering errors
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFixedSize(350, 450)
        
        # Solid background style (avoids UpdateLayeredWindowIndirect error on Windows)
        self.setStyleSheet("""
            FloatingNotificationPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgb(50, 55, 65),
                    stop:1 rgb(35, 40, 50));
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(notification_center)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
    def show_at(self, global_pos: QPoint):
        """Show panel at specific position, ensuring it stays within screen bounds"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QGuiApplication
        
        # Get the screen that contains the bell button
        screen = QGuiApplication.screenAt(global_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        
        screen_rect = screen.availableGeometry()
        
        # Calculate initial position (below and left of the button)
        x = global_pos.x() - self.width() + 30
        y = global_pos.y() + 10
        
        # Ensure panel stays within screen bounds
        # Check right edge
        if x + self.width() > screen_rect.right():
            x = screen_rect.right() - self.width() - 10
        
        # Check left edge
        if x < screen_rect.left():
            x = screen_rect.left() + 10
        
        # Check bottom edge - if panel would go below screen, show it above the button
        if y + self.height() > screen_rect.bottom():
            y = global_pos.y() - self.height() - 10
        
        # Check top edge
        if y < screen_rect.top():
            y = screen_rect.top() + 10
        
        self.move(x, y)
        self.show()
