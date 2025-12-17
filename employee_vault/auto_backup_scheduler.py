"""
Auto-Backup Scheduler for EmployeeVault
Implements scheduled automatic backups with configurable time and retention
"""

import os
import logging
import threading
from datetime import datetime, time as dt_time, timedelta
from typing import Optional
from PySide6.QtCore import QTimer, QObject, Signal


class AutoBackupScheduler(QObject):
    """
    Manages automated daily backups
    
    Features:
    - Scheduled daily backups at specified time
    - Automatic cleanup of old backups based on retention policy
    - Thread-safe background execution
    - Status reporting
    """
    
    backup_started = Signal()
    backup_completed = Signal(bool, str)  # success, message
    
    def __init__(self, db, backup_callback=None):
        """
        Initialize auto-backup scheduler
        
        Args:
            db: Database instance
            backup_callback: Optional callback function for manual backups
        """
        super().__init__()
        self.db = db
        self.backup_callback = backup_callback
        self.timer = None
        self.enabled = False
        self.backup_time = dt_time(2, 0)  # Default 2:00 AM
        self.retention_days = 30
        self.last_backup_date = None
        
        # Load settings
        self._load_settings()
    
    def _load_settings(self):
        """Load auto-backup settings from database"""
        try:
            enabled_str = self.db.get_setting('auto_backup_enabled', 'false')
            self.enabled = enabled_str.lower() == 'true'
            
            time_str = self.db.get_setting('auto_backup_time', '02:00')
            hour, minute = map(int, time_str.split(':'))
            self.backup_time = dt_time(hour, minute)
            
            retention_str = self.db.get_setting('auto_backup_retention', '30')
            self.retention_days = int(retention_str)
            
            self.last_backup_date = self.db.get_setting('last_auto_backup', None)
            
            logging.info(f"Auto-backup settings loaded: enabled={self.enabled}, time={self.backup_time}, retention={self.retention_days} days")
        except Exception as e:
            logging.error(f"Failed to load auto-backup settings: {e}")
    
    def _save_settings(self):
        """Save auto-backup settings to database"""
        try:
            self.db.set_setting('auto_backup_enabled', 'true' if self.enabled else 'false')
            self.db.set_setting('auto_backup_time', self.backup_time.strftime('%H:%M'))
            self.db.set_setting('auto_backup_retention', str(self.retention_days))
            self.db.conn.commit()
            logging.info("Auto-backup settings saved")
        except Exception as e:
            logging.error(f"Failed to save auto-backup settings: {e}")
    
    def enable(self, backup_time: dt_time = None, retention_days: int = None):
        """
        Enable auto-backup scheduler
        
        Args:
            backup_time: Time of day for backups (default: 2:00 AM)
            retention_days: Days to keep backups (default: 30)
        """
        if backup_time:
            self.backup_time = backup_time
        if retention_days:
            self.retention_days = retention_days
        
        self.enabled = True
        self._save_settings()
        self._start_scheduler()
        logging.info(f"Auto-backup enabled: {self.backup_time}, retention={self.retention_days} days")
    
    def disable(self):
        """Disable auto-backup scheduler"""
        self.enabled = False
        self._save_settings()
        self._stop_scheduler()
        logging.info("Auto-backup disabled")
    
    def _start_scheduler(self):
        """Start the backup scheduler timer"""
        if self.timer:
            self.timer.stop()
        
        # Calculate milliseconds until next backup time
        interval_ms = self._calculate_next_backup_interval()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_and_backup)
        self.timer.start(interval_ms)
        
        next_backup = datetime.now() + timedelta(milliseconds=interval_ms)
        logging.info(f"Auto-backup scheduler started. Next backup: {next_backup}")
    
    def _stop_scheduler(self):
        """Stop the backup scheduler timer"""
        if self.timer:
            self.timer.stop()
            self.timer = None
            logging.info("Auto-backup scheduler stopped")
    
    def _calculate_next_backup_interval(self) -> int:
        """
        Calculate milliseconds until next scheduled backup
        
        Returns:
            Milliseconds until next backup time
        """
        now = datetime.now()
        today_backup = datetime.combine(now.date(), self.backup_time)
        
        # If backup time has passed today, schedule for tomorrow
        if now.time() >= self.backup_time:
            next_backup = today_backup + timedelta(days=1)
        else:
            next_backup = today_backup
        
        delta = next_backup - now
        return int(delta.total_seconds() * 1000)
    
    def _check_and_backup(self):
        """Check if backup is due and perform it"""
        if not self.enabled:
            return
        
        now = datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        
        # Skip if already backed up today
        if self.last_backup_date == today_str:
            logging.info("Backup already performed today, skipping")
            # Reschedule for tomorrow
            self._start_scheduler()
            return
        
        # Perform backup in background thread
        self._perform_backup_async()
        
        # Reschedule for next day
        self._start_scheduler()
    
    def _perform_backup_async(self):
        """Perform backup in background thread"""
        def backup_worker():
            try:
                self.backup_started.emit()
                logging.info("Auto-backup started")
                
                # Perform backup
                if self.backup_callback:
                    success = self.backup_callback()
                else:
                    # Use database backup method
                    backup_path = self.db.backup_database()
                    success = backup_path is not None
                
                if success:
                    # Update last backup date
                    today_str = datetime.now().strftime('%Y-%m-%d')
                    self.db.set_setting('last_auto_backup', today_str)
                    self.db.conn.commit()
                    self.last_backup_date = today_str
                    
                    # Cleanup old backups
                    self._cleanup_old_backups()
                    
                    message = "Auto-backup completed successfully"
                    logging.info(message)
                    self.backup_completed.emit(True, message)
                else:
                    message = "Auto-backup failed"
                    logging.error(message)
                    self.backup_completed.emit(False, message)
                    
            except Exception as e:
                message = f"Auto-backup error: {e}"
                logging.error(message)
                self.backup_completed.emit(False, message)
        
        # Run backup in background thread
        thread = threading.Thread(target=backup_worker, daemon=True)
        thread.start()
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            from employee_vault.config import BACKUPS_DIR
            
            if not os.path.exists(BACKUPS_DIR):
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for item in os.listdir(BACKUPS_DIR):
                item_path = os.path.join(BACKUPS_DIR, item)
                
                if os.path.isdir(item_path):
                    # Extract date from folder name (e.g., employee_vault_backup_20251129_100000)
                    try:
                        # Try to parse date from folder name
                        parts = item.split('_')
                        if len(parts) >= 4:
                            date_str = parts[-2]  # YYYYMMDD
                            backup_date = datetime.strptime(date_str, '%Y%m%d')
                            
                            if backup_date < cutoff_date:
                                # Delete old backup
                                import shutil
                                shutil.rmtree(item_path)
                                deleted_count += 1
                                logging.info(f"Deleted old backup: {item}")
                    except Exception as e:
                        logging.warning(f"Could not parse backup date for {item}: {e}")
            
            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} old backup(s)")
                
        except Exception as e:
            logging.error(f"Failed to cleanup old backups: {e}")
    
    def trigger_manual_backup(self):
        """Manually trigger a backup (doesn't update last_backup_date)"""
        self._perform_backup_async()
    
    def get_status(self) -> dict:
        """
        Get current scheduler status
        
        Returns:
            Dictionary with status information
        """
        next_backup = None
        if self.enabled and self.timer:
            remaining_ms = self.timer.remainingTime()
            next_backup = datetime.now() + timedelta(milliseconds=remaining_ms)
        
        return {
            'enabled': self.enabled,
            'backup_time': self.backup_time.strftime('%H:%M'),
            'retention_days': self.retention_days,
            'last_backup': self.last_backup_date,
            'next_backup': next_backup.isoformat() if next_backup else None
        }
