#!/usr/bin/env python3
"""
Employee Vault - Main Entry Point
Fully modularized version
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
import os
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QLockFile, QDir

# Import from modular packages
from employee_vault.app_config import (
    APP_QSS, DB_FILE, resource_path, guard_or_exit, USE_NETWORK_DB
)
from employee_vault.database import DB
from employee_vault.ui.dialogs.login import LoginDialog
from employee_vault.ui.main_window import MainWindow
from employee_vault.ui.theme_manager import get_theme_manager

# PHASE 5: Enhanced logging with file rotation
# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with both file and console handlers
log_file = os.path.join(logs_dir, 'employee_vault.log')

# Create formatters
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

# Create file handler with rotation (10MB max, keep 5 backups)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Log startup
logging.info("="*80)
logging.info("Employee Vault Application Starting")
logging.info(f"Log file: {log_file}")
logging.info("="*80)


def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler for crash logging"""
    import traceback

    # Log the exception
    logging.critical("Unhandled exception occurred!", exc_info=(exc_type, exc_value, exc_traceback))

    # Auto-export crash log to file
    try:
        import os
        from datetime import datetime
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        crash_log_path = os.path.join(logs_dir, f"crash_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(crash_log_path, 'w') as f:
            f.write(f"Crash Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        logging.info(f"Crash log auto-exported to: {crash_log_path}")
    except Exception as e:
        logging.error(f"Failed to auto-export crash log: {e}")

    # Call default exception handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def main():
    """Main application entry point"""

    # Install global exception hook for crash logging
    sys.excepthook = exception_hook

    # Enforce network share deployment (configurable via settings.json)
    try:
        import json
        # Use resource_path to find settings.json (works for both dev and .exe)
        settings_file = resource_path("settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
                if settings.get("enable_network_guard", False):
                    logging.info("Network guard enabled via settings.json")
                    guard_or_exit()
                else:
                    logging.info("Network guard disabled via settings.json")
        else:
            logging.info(f"settings.json not found at {settings_file}, network guard disabled")
    except Exception as e:
        logging.warning(f"Could not check network guard setting: {e}")

    # Single instance check - prevent multiple instances per user
    lock_file_path = os.path.join(QDir.tempPath(), "employee_vault.lock")
    lock_file = QLockFile(lock_file_path)
    
    if not lock_file.tryLock(100):
        # Another instance is already running
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Application Already Running",
            "EmployeeVault is already running.\n\n"
            "Only one instance can run at a time per user.\n\n"
            "Please close the existing instance before opening a new one."
        )
        sys.exit(1)

    # Create Qt application
    app = QApplication(sys.argv)

    # FORCE DARK MODE: Set Fusion style and dark palette to prevent light mode issues
    # This ensures the app uses dark colors even if Windows is in light mode
    app.setStyle("Fusion")
    
    # Create dark palette
    from PySide6.QtGui import QPalette, QColor
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(25, 25, 35))
    dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 40))
    dark_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 45))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(40, 40, 50))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Button, QColor(40, 40, 50))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(dark_palette)

    # Set application icon
    app_icon = QIcon(resource_path("assets/apruva.ico"))
    app.setWindowIcon(app_icon)

    # Initialize database (using network or local based on availability)
    try:
        db = DB(DB_FILE)
    except RuntimeError as e:
        # Database is locked or corrupted - show user-friendly error
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Database Error")
        msg.setText("Cannot open database")
        msg.setInformativeText(str(e))
        msg.setDetailedText(
            "This usually happens when:\n"
            "1. Another instance is running on this or another PC\n"
            "2. The database file is corrupted\n"
            "3. Network connection is unstable\n\n"
            "Solution:\n"
            "1. Close ALL EmployeeVault windows on ALL computers\n"
            "2. Delete the .db-wal and .db-shm files if they exist\n"
            "3. Try again"
        )
        msg.exec()
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Database Error")
        msg.setText(f"Failed to open database:\n{e}")
        msg.exec()
        sys.exit(1)

    # PHASE 5: Check database integrity on startup
    logging.info("Performing database integrity check...")
    is_healthy, issues = db.check_database_integrity()
    if not is_healthy:
        logging.error(f"Database integrity check failed with {len(issues)} issue(s)")
        for issue in issues:
            logging.error(f"  - {issue}")
    else:
        logging.info("Database integrity check: PASSED")
    
    # v5.2: Migrate employee files to new folder structure (photos/ and files/ subdirs)
    try:
        from employee_vault.database.db import migrate_employee_files_structure
        migrated = migrate_employee_files_structure()
        if migrated > 0:
            logging.info(f"Migrated {migrated} files to new folder structure")
    except Exception as e:
        logging.warning(f"File structure migration skipped or failed: {e}")

    # Graceful database shutdown on app quit
    def on_app_quit():
        """Closes the database connection when the app exits."""
        logging.info("Application quitting, closing database connection...")
        try:
            # Backup network database to local before closing (with timeout to prevent hang)
            if USE_NETWORK_DB and hasattr(db, 'conn'):
                try:
                    logging.info("Backing up network database to local...")
                    from employee_vault.app_config import backup_database_on_close
                    import threading

                    # Run backup with timeout to prevent hang
                    backup_thread = threading.Thread(target=lambda: backup_database_on_close(db.conn))
                    backup_thread.daemon = True
                    backup_thread.start()
                    backup_thread.join(timeout=3.0)  # 3 second timeout

                    if backup_thread.is_alive():
                        logging.warning("Database backup timed out after 3 seconds, proceeding with close")
                    else:
                        logging.info("Database backup completed successfully")
                except Exception as backup_err:
                    logging.error(f"Failed to backup database on close: {backup_err}")

            if hasattr(db, 'conn'):
                db.conn.close()
                logging.info("Database connection closed successfully.")
        except Exception as e:
            logging.error(f"Error closing database on quit: {e}")

    app.aboutToQuit.connect(on_app_quit)

    # Initialize and apply theme
    theme_manager = get_theme_manager()
    theme_manager.apply_theme()
    logging.info(f"Applied theme: {theme_manager.get_active_theme()}")

    # Show login dialog
    login = LoginDialog(db, app_icon)
    if login.exec() != QDialog.Accepted:
        sys.exit(0)

    # Get logged-in username
    if hasattr(login, 'actual_username'):
        username = login.actual_username
    else:
        username = login.username.text().strip()

    # Get user data
    user_row = db.get_user(username)
    if not user_row:
        logging.error(f"User {username} not found after login")
        sys.exit(1)
    
    # Convert sqlite3.Row to dict to ensure proper attribute access
    user_row = dict(user_row)
    logging.info(f"User logged in: {username}, Role: {user_row.get('role', 'unknown')}")

    # Create and show main window
    main_window = MainWindow(db, username, user_row, app_icon)

    # Store reference in app to prevent garbage collection
    app.main_window = main_window

    main_window.showMaximized()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
