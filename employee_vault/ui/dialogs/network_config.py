"""
Enhanced Network Configuration Dialog
Comprehensive settings for database, file paths, backup, and email (future)
"""

import os
import json
import logging
from pathlib import Path

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import DB_FILE, FILES_DIR, PHOTOS_DIR, EXPECTED_UNC_PREFIX, IOS_INPUT_STYLE
from employee_vault.ui.widgets import ModernAnimatedButton, AnimatedDialogBase
from employee_vault.ui.modern_ui_helper import show_success_toast, show_error_toast, show_warning_toast
from employee_vault.ui.ios_button_styles import apply_ios_style


class NetworkConfigDialog(AnimatedDialogBase):
    """Enhanced network configuration dialog with tabs"""

    def __init__(self, parent=None):
        super().__init__(parent, animation_style="fade")
        self.setWindowTitle("🌐 Network Configuration")
        self.resize(550, 600)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>🌐 Network Configuration</h2>")
        header.setStyleSheet("color: #4a9eff; padding: 10px;")
        layout.addWidget(header)

        instructions = QLabel(
            "<p>Configure network settings, file paths, and system preferences.</p>"
            "<p><b>Note:</b> This application is designed for 100% offline LAN deployment.</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Tabbed interface
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                background-color: rgba(45, 45, 48, 0.5);
                padding: 16px;
            }
            QTabBar::tab {
                background-color: rgba(45, 45, 48, 0.8);
                color: white;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 rgba(74, 158, 255, 0.5),
                                           stop:1 rgba(25, 118, 210, 0.3));
            }
            QTabBar::tab:hover {
                background-color: rgba(74, 158, 255, 0.3);
            }
        """)

        self._create_database_tab()
        self._create_file_paths_tab()
        self._create_backup_tab()
        self._create_email_tab()

        layout.addWidget(self.tabs, 1)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("padding: 8px; font-size: 12px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = ModernAnimatedButton("💾 Save Configuration")
        apply_ios_style(save_btn, 'green')
        save_btn.clicked.connect(self._save_config)

        test_btn = ModernAnimatedButton("🔍 Test Connections")
        apply_ios_style(test_btn, 'blue')
        test_btn.clicked.connect(self._test_connections)

        close_btn = ModernAnimatedButton("✗ Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # Load current settings
        self._load_settings()

    def _create_database_tab(self):
        """Database settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Database location
        db_group = QGroupBox("Database Settings")
        db_layout = QVBoxLayout(db_group)

        # Current database path
        db_layout.addWidget(QLabel("<b>Database File:</b>"))
        self.db_path = NeumorphicGradientLineEdit("Database File Path")
        self.db_path.setMinimumHeight(70)
        self.db_path.line_edit.setText(str(Path(DB_FILE).resolve()))
        self.db_path.line_edit.setReadOnly(True)
        db_layout.addWidget(self.db_path)

        # Database info
        info_layout = QHBoxLayout()

        if os.path.exists(DB_FILE):
            db_size = os.path.getsize(DB_FILE) / 1024  # KB
            db_layout.addWidget(QLabel(f"<i>Size: {db_size:.2f} KB</i>"))

        db_layout.addLayout(info_layout)
        layout.addWidget(db_group)

        # Network share settings
        net_group = QGroupBox("Network Share Settings")
        net_layout = QVBoxLayout(net_group)

        net_layout.addWidget(QLabel("<b>Expected Network Path:</b>"))
        self.network_path = NeumorphicGradientLineEdit("Network UNC Path")
        self.network_path.setMinimumHeight(70)
        self.network_path.line_edit.setText(EXPECTED_UNC_PREFIX)
        self.network_path.line_edit.setReadOnly(True)
        net_layout.addWidget(self.network_path)

        net_layout.addWidget(QLabel(
            "<i>Note: Network paths are configured for LAN deployment.\n"
            "The application works 100% offline on the local network.</i>"
        ))

        layout.addWidget(net_group)

        # Database actions
        actions_group = QGroupBox("Database Actions")
        actions_layout = QVBoxLayout(actions_group)

        vacuum_btn = ModernAnimatedButton("🗜️ Optimize Database (VACUUM)")
        apply_ios_style(vacuum_btn, 'blue')
        vacuum_btn.clicked.connect(self._vacuum_database)
        actions_layout.addWidget(vacuum_btn)

        actions_layout.addWidget(QLabel(
            "<i>Optimizes database performance by reclaiming unused space.</i>"
        ))

        layout.addWidget(actions_group)

        layout.addStretch(1)
        self.tabs.addTab(tab, "📁 Database")

    def _create_file_paths_tab(self):
        """File paths settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Employee files directory
        files_group = QGroupBox("Employee Files Directory")
        files_layout = QVBoxLayout(files_group)

        files_layout.addWidget(QLabel("<b>Location:</b>"))
        self.files_path = NeumorphicGradientLineEdit("Employee Files Directory")
        self.files_path.setMinimumHeight(70)
        self.files_path.line_edit.setText(str(Path(FILES_DIR).resolve()))
        self.files_path.line_edit.setReadOnly(True)
        files_layout.addWidget(self.files_path)

        if os.path.exists(FILES_DIR):
            file_count = len([f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))])
            files_layout.addWidget(QLabel(f"<i>Files stored: {file_count}</i>"))

        browse_files_btn = ModernAnimatedButton("📂 Open in Explorer")
        apply_ios_style(browse_files_btn, 'blue')
        browse_files_btn.clicked.connect(lambda: os.startfile(FILES_DIR) if os.path.exists(FILES_DIR) else None)
        files_layout.addWidget(browse_files_btn)

        layout.addWidget(files_group)

        # Employee photos directory
        photos_group = QGroupBox("Employee Photos Directory")
        photos_layout = QVBoxLayout(photos_group)

        photos_layout.addWidget(QLabel("<b>Location:</b>"))
        self.photos_path = NeumorphicGradientLineEdit("Employee Photos Directory")
        self.photos_path.setMinimumHeight(70)
        self.photos_path.line_edit.setText(str(Path(PHOTOS_DIR).resolve()))
        self.photos_path.line_edit.setReadOnly(True)
        photos_layout.addWidget(self.photos_path)

        if os.path.exists(PHOTOS_DIR):
            photo_count = len([f for f in os.listdir(PHOTOS_DIR) if f.endswith('.png')])
            photos_layout.addWidget(QLabel(f"<i>Photos stored: {photo_count}</i>"))

        browse_photos_btn = ModernAnimatedButton("📂 Open in Explorer")
        apply_ios_style(browse_photos_btn, 'blue')
        browse_photos_btn.clicked.connect(lambda: os.startfile(PHOTOS_DIR) if os.path.exists(PHOTOS_DIR) else None)
        photos_layout.addWidget(browse_photos_btn)

        layout.addWidget(photos_group)

        # Path info
        info_label = QLabel(
            "<p><b>ℹ️ Path Information:</b></p>"
            "<p>File paths are relative to the application directory and are automatically "
            "created if they don't exist. For network deployment, ensure all client machines "
            "have access to the shared network location.</p>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch(1)
        self.tabs.addTab(tab, "📂 File Paths")

    def _create_backup_tab(self):
        """Backup settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Backup location
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QVBoxLayout(backup_group)

        backup_layout.addWidget(QLabel("<b>Backup Directory:</b>"))
        self.backup_path = NeumorphicGradientLineEdit("Backup Directory")
        self.backup_path.setMinimumHeight(70)
        self.backup_path.line_edit.setText("backups/")
        self.backup_path.line_edit.setReadOnly(True)
        backup_layout.addWidget(self.backup_path)

        if os.path.exists("backups"):
            backup_count = len([d for d in os.listdir("backups") if os.path.isdir(os.path.join("backups", d))])
            backup_layout.addWidget(QLabel(f"<i>Backups available: {backup_count}</i>"))

        browse_backup_btn = ModernAnimatedButton("📂 Open Backup Folder")
        apply_ios_style(browse_backup_btn, 'blue')
        browse_backup_btn.clicked.connect(lambda: os.startfile("backups") if os.path.exists("backups") else None)
        backup_layout.addWidget(browse_backup_btn)

        layout.addWidget(backup_group)

        # Auto-backup settings
        auto_group = QGroupBox("Automatic Backup")
        auto_layout = QVBoxLayout(auto_group)

        self.auto_backup_enabled = QCheckBox("Enable automatic daily backups")
        self.auto_backup_enabled.setEnabled(True)  # Now enabled
        auto_layout.addWidget(self.auto_backup_enabled)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Backup time:"))
        self.backup_time = QTimeEdit()
        self.backup_time.setTime(QTime(2, 0))  # 2:00 AM default
        self.backup_time.setEnabled(True)  # Now enabled
        time_layout.addWidget(self.backup_time)
        time_layout.addStretch(1)
        auto_layout.addLayout(time_layout)

        self.auto_backup_retention = NeumorphicGradientSpinBox("Retention Days")
        self.auto_backup_retention.setMinimumHeight(70)
        self.auto_backup_retention.spin_box.setRange(1, 90)
        self.auto_backup_retention.spin_box.setValue(30)
        self.auto_backup_retention.spin_box.setSuffix(" days")
        self.auto_backup_retention.setEnabled(True)  # Now enabled

        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Keep backups for:"))
        retention_layout.addWidget(self.auto_backup_retention)
        retention_layout.addStretch(1)
        auto_layout.addLayout(retention_layout)

        # Status info
        self.backup_status_label = QLabel("<i>Configure automatic daily backups and retention policy.</i>")
        self.backup_status_label.setWordWrap(True)
        auto_layout.addWidget(self.backup_status_label)

        layout.addWidget(auto_group)

        layout.addStretch(1)
        self.tabs.addTab(tab, "💾 Backup")

    def _create_email_tab(self):
        """Email notification settings tab (future feature)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Email warning
        warning = QLabel(
            "<p><b>⚠️ Email Notifications (Future Feature)</b></p>"
            "<p>Email notifications for contract expiry alerts will be available in a future version. "
            "This requires SMTP server configuration and may need internet access.</p>"
            "<p><b>Note:</b> Since this application is designed for 100% offline LAN deployment, "
            "email features are optional and can be enabled if network email is available.</p>"
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 152, 0, 0.2);
                border: 1px solid rgba(255, 152, 0, 0.5);
                border-radius: 8px;
                padding: 16px;
            }
        """)
        layout.addWidget(warning)

        # SMTP settings (disabled for now)
        smtp_group = QGroupBox("SMTP Server Settings")
        smtp_layout = QFormLayout(smtp_group)

        self.smtp_server = NeumorphicGradientLineEdit("smtp.office365.com")
        self.smtp_server.setMinimumHeight(70)
        self.smtp_server.line_edit.setText("smtp.office365.com")
        self.smtp_server.setEnabled(False)
        smtp_layout.addRow("SMTP Server:", self.smtp_server)

        self.smtp_port = NeumorphicGradientSpinBox("Port")
        self.smtp_port.setMinimumHeight(70)
        self.smtp_port.spin_box.setRange(1, 65535)
        self.smtp_port.spin_box.setValue(587)
        self.smtp_port.setEnabled(False)
        smtp_layout.addRow("Port:", self.smtp_port)

        self.smtp_username = NeumorphicGradientLineEdit("email@company.com")
        self.smtp_username.setMinimumHeight(70)
        self.smtp_username.setEnabled(False)
        smtp_layout.addRow("Username:", self.smtp_username)

        self.smtp_password = NeumorphicGradientPasswordInput("Password")
        self.smtp_password.setMinimumHeight(70)
        self.smtp_password.setEnabled(False)
        smtp_layout.addRow("Password:", self.smtp_password)

        self.smtp_use_tls = QCheckBox("Use TLS")
        self.smtp_use_tls.setChecked(True)
        self.smtp_use_tls.setEnabled(False)
        smtp_layout.addRow("", self.smtp_use_tls)

        layout.addWidget(smtp_group)

        # Notification settings
        notif_group = QGroupBox("Notification Settings")
        notif_layout = QVBoxLayout(notif_group)

        self.notify_enabled = QCheckBox("Enable email notifications")
        self.notify_enabled.setEnabled(False)
        notif_layout.addWidget(self.notify_enabled)

        self.notify_days = NeumorphicGradientSpinBox("Notify Days")
        self.notify_days.setMinimumHeight(70)
        self.notify_days.spin_box.setRange(1, 90)
        self.notify_days.spin_box.setValue(30)
        self.notify_days.spin_box.setSuffix(" days before expiry")
        self.notify_days.setEnabled(False)

        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Send notifications:"))
        days_layout.addWidget(self.notify_days)
        days_layout.addStretch(1)
        notif_layout.addLayout(days_layout)

        layout.addWidget(notif_group)

        layout.addStretch(1)
        self.tabs.addTab(tab, "📧 Email (Future)")

    def _load_settings(self):
        """Load settings from config file"""
        config_file = "settings.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    settings = json.load(f)

                # Load backup settings
                if 'auto_backup' in settings:
                    # Future: load auto backup settings
                    pass

                # Load email settings
                if 'email' in settings:
                    # Future: load email settings
                    pass

                self.status_label.setText("✓ Settings loaded successfully")
                self.status_label.setStyleSheet("color: #4CAF50; padding: 8px;")

            except Exception as e:
                logging.error(f"Error loading settings: {e}")
                self.status_label.setText(f"⚠ Error loading settings: {e}")
                self.status_label.setStyleSheet("color: #ffaa00; padding: 8px;")
        else:
            self.status_label.setText("ℹ Using default settings (no config file found)")
            self.status_label.setStyleSheet("color: #4a9eff; padding: 8px;")

    def _save_config(self):
        """Save configuration to file"""
        config_file = "settings.json"

        try:
            settings = {}

            # Save current settings (future features)
            settings['last_updated'] = QDateTime.currentDateTime().toString(Qt.ISODate)

            # Future: Save backup settings
            # Future: Save email settings

            with open(config_file, 'w') as f:
                json.dump(settings, f, indent=2)

            show_success_toast(self, "Configuration saved successfully!")
            self.status_label.setText("✓ Configuration saved")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 8px;")
            logging.info("Network configuration saved")

        except Exception as e:
            show_error_toast(self, f"Error saving configuration:\n{e}")
            logging.error(f"Config save error: {e}")

    def _test_connections(self):
        """Test network paths and database connections"""
        self.status_label.setText("🔍 Testing connections...")
        self.status_label.setStyleSheet("color: #4a9eff; padding: 8px;")
        QApplication.processEvents()

        results = []

        # Test database
        if os.path.exists(DB_FILE):
            if os.access(DB_FILE, os.R_OK | os.W_OK):
                results.append("✅ Database is accessible (read/write)")
            else:
                results.append("⚠️ Database exists but may have permission issues")
        else:
            results.append("❌ Database file not found")

        # Test files directory
        if os.path.exists(FILES_DIR):
            if os.access(FILES_DIR, os.R_OK | os.W_OK):
                results.append("✅ Files directory is accessible")
            else:
                results.append("⚠️ Files directory has permission issues")
        else:
            results.append("⚠️ Files directory does not exist (will be created)")

        # Test photos directory
        if os.path.exists(PHOTOS_DIR):
            if os.access(PHOTOS_DIR, os.R_OK | os.W_OK):
                results.append("✅ Photos directory is accessible")
            else:
                results.append("⚠️ Photos directory has permission issues")
        else:
            results.append("⚠️ Photos directory does not exist (will be created)")

        # Test backup directory
        if os.path.exists("backups"):
            if os.access("backups", os.R_OK | os.W_OK):
                results.append("✅ Backup directory is accessible")
            else:
                results.append("⚠️ Backup directory has permission issues")
        else:
            results.append("ℹ️ Backup directory will be created on first backup")

        # Show results
        result_text = "\n".join(results)
        self.status_label.setText(result_text)

        if "❌" in result_text:
            self.status_label.setStyleSheet("color: #ff6b6b; padding: 8px;")
            show_error_toast(self, "Connection test found errors:\n\n" + result_text)
        elif "⚠️" in result_text:
            self.status_label.setStyleSheet("color: #ffaa00; padding: 8px;")
            show_warning_toast(self, "Connection test completed with warnings:\n\n" + result_text)
        else:
            self.status_label.setStyleSheet("color: #4CAF50; padding: 8px;")
            show_success_toast(self, "All connections tested successfully!\n\n" + result_text)

        logging.info(f"Connection test results: {result_text}")

    def _vacuum_database(self):
        """Optimize database with VACUUM command"""
        reply = QMessageBox.question(
            self,
            "Optimize Database",
            "This will optimize the database by reclaiming unused space.\n\n"
            "This operation may take a few moments. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                import sqlite3

                self.status_label.setText("🗜️ Optimizing database...")
                QApplication.processEvents()

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                # Get size before
                size_before = os.path.getsize(DB_FILE) / 1024  # KB

                cursor.execute("VACUUM")
                conn.commit()
                conn.close()

                # Get size after
                size_after = os.path.getsize(DB_FILE) / 1024  # KB
                savings = size_before - size_after

                result_msg = (
                    f"Database optimized successfully!\n\n"
                    f"Size before: {size_before:.2f} KB\n"
                    f"Size after: {size_after:.2f} KB\n"
                    f"Space reclaimed: {savings:.2f} KB"
                )

                show_success_toast(self, result_msg)
                self.status_label.setText("✓ Database optimized")
                self.status_label.setStyleSheet("color: #4CAF50; padding: 8px;")
                logging.info(f"Database vacuumed: {savings:.2f} KB reclaimed")

            except Exception as e:
                show_error_toast(self, f"Error optimizing database:\n{e}")
                logging.error(f"Database vacuum error: {e}")
