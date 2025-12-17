"""
Database module for Employee Vault
Contains the DB class with all database operations
"""

import os
import re
import json
import time
import sqlite3
import shutil
import logging
import hashlib
import threading
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Import from config module
from employee_vault.config import (
    DB_FILE, JSON_FALLBACK, SEED_AGENCIES, DATABASE_VERSION,
    BACKUPS_DIR, _hash_pwd, _hash_pin, _verify_pin
)
from employee_vault.utils import retry_on_lock, check_permission

class DB:
    def __init__(self, path: str):
        # Log database path for debugging
        logging.info(f"Initializing database: {path}")

        # Ensure database directory exists and is writable
        db_dir = os.path.dirname(path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logging.info(f"Created database directory: {db_dir}")
            except (PermissionError, OSError) as e:
                logging.warning(f"Could not create database directory {db_dir}: {e}")
                pass  # Directory may exist or be created by another user

        newdb = not os.path.exists(path)

        # MULTI-USER OPTIMIZATION: Enhanced connection settings for 5-7 concurrent users
        try:
            self.conn = sqlite3.connect(
                path,
                check_same_thread=False,  # Allow multi-threading
                isolation_level="DEFERRED",  # Proper transaction mode for data integrity
                timeout=60.0,              # Increased to 60 seconds for network share reliability
                uri=True if path.startswith('file:') else False  # Support URI paths
            )
            logging.info(f"✓ Database connection successful: {path}")
        except sqlite3.OperationalError as e:
            # If direct path fails, try with absolute path
            abs_path = os.path.abspath(path)
            logging.warning(f"✗ Database connection failed with path: {path}")
            logging.info(f"Trying absolute path: {abs_path}")
            try:
                self.conn = sqlite3.connect(
                    abs_path,
                    check_same_thread=False,
                    isolation_level="DEFERRED",
                    timeout=60.0
                )
                logging.info(f"✓ Database connection successful with absolute path: {abs_path}")
            except sqlite3.OperationalError as e2:
                logging.error(f"✗ Failed to connect to database at both paths")
                logging.error(f"  Original path: {path}")
                logging.error(f"  Absolute path: {abs_path}")
                logging.error(f"  Error: {e2}")
                raise  # Re-raise the exception to show the error to user

        self.conn.row_factory = sqlite3.Row

        # QUICK WIN #4: Cache for reference data (reduces DB queries)
        self._agencies_cache = None
        self._agencies_cache_time = None
        self._cache_ttl = 300  # Cache time-to-live: 5 minutes
        self._cache_lock = threading.Lock()  # Thread safety for cache access

        # Detect if database is on a network drive
        is_network_path = path.startswith('\\\\') or path.startswith('//')
        if is_network_path:
            logging.info("Network path detected - using DELETE journal mode for reliability")

        # PRAGMA optimizations for multi-user performance
        try:
            self.conn.execute("PRAGMA foreign_keys=ON;")
            
            if is_network_path:
                # Network drives: Use DELETE mode (more reliable, but slower)
                # WAL mode is NOT supported on network drives and causes "disk I/O error"
                self.conn.execute("PRAGMA journal_mode=DELETE;")
                self.conn.execute("PRAGMA synchronous=FULL;")    # Full sync for data safety
                self.conn.execute("PRAGMA busy_timeout=60000;")  # Wait up to 60s for locks
                self.conn.execute("PRAGMA locking_mode=NORMAL;") # Normal locking
                logging.info("Using DELETE journal mode for network drive")
            else:
                # Local drives: Use WAL mode (faster, better concurrency)
                self.conn.execute("PRAGMA journal_mode=WAL;")
                self.conn.execute("PRAGMA synchronous=NORMAL;")
                self.conn.execute("PRAGMA busy_timeout=30000;")
                self.conn.execute("PRAGMA wal_autocheckpoint=1000;")
                logging.info("Using WAL journal mode for local drive")
            
            self.conn.execute("PRAGMA cache_size=-64000;")       # 64MB cache for better performance
            self.conn.execute("PRAGMA temp_store=MEMORY;")       # Use memory for temp tables (faster)
            
            # Store the mode for later use
            self._is_network_path = is_network_path
            
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error during PRAGMA setup: {e}")
            logging.error(f"File: {path}")
            
            # Don't try to delete/move the file if it's locked - just fail gracefully
            if "disk I/O error" in str(e) or "locked" in str(e).lower():
                logging.error("Database is locked or has I/O issues. Please close all other instances.")
                self.conn.close()
                raise RuntimeError(
                    f"Database is locked or corrupted.\n\n"
                    f"Please:\n"
                    f"1. Close ALL EmployeeVault windows on ALL computers\n"
                    f"2. Wait 10 seconds\n"
                    f"3. Try again\n\n"
                    f"If problem persists, delete the .db-wal and .db-shm files."
                )
            
            # For other errors, try recovery
            self.conn.close()
            self._handle_corrupted_database(path)
            
            # Reconnect to fixed database
            self.conn = sqlite3.connect(
                path,
                check_same_thread=False,
                isolation_level="DEFERRED",
                timeout=60.0
            )
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys=ON;")
            self.conn.execute("PRAGMA journal_mode=DELETE;")
            self.conn.execute("PRAGMA synchronous=FULL;")
            self.conn.execute("PRAGMA busy_timeout=60000;")
            self.conn.execute("PRAGMA cache_size=-64000;")
            self.conn.execute("PRAGMA temp_store=MEMORY;")
            self._is_network_path = True  # Force network mode after recovery
            logging.info(f"✓ Database recovered and reconnected")

        self._ensure_schema()
        self._migrate_password_to_pin()  # Run PIN migration
        if newdb: self._maybe_import_json()

    def _profile_query(self, query, params=None):
        """
        Performance instrumentation (Phase 0) - Profile database queries
        Logs queries that take longer than 50ms
        """
        start = time.perf_counter()
        if params:
            cursor = self.conn.execute(query, params)
        else:
            cursor = self.conn.execute(query)

        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 50:  # Log queries >50ms
            query_preview = query[:100].replace('\n', ' ')
            print(f"[PERF] SLOW QUERY ({elapsed:.2f}ms): {query_preview}")

        return cursor

    def checkpoint_database(self):
        """
        Force WAL checkpoint to merge changes from WAL file to main database.
        Only applies to WAL mode (local drives). For network drives using DELETE mode,
        this is a no-op since there's no WAL file.
        """
        # Skip checkpoint for network paths (DELETE mode doesn't use WAL)
        if getattr(self, '_is_network_path', False):
            # For DELETE mode, just commit any pending transaction
            try:
                self.conn.commit()
            except:
                pass
            return True
            
        try:
            # Force all WAL changes into main database
            result = self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            checkpoint_result = result.fetchone()
            if checkpoint_result:
                busy, log, checkpointed = checkpoint_result
                if busy == 0 and checkpointed > 0:
                    logging.info(f"✓ WAL checkpoint completed: {checkpointed} pages checkpointed")
                elif busy != 0:
                    logging.warning(f"WAL checkpoint partial: database was busy, {checkpointed} pages done")
            return True
        except sqlite3.Error as e:
            logging.warning(f"WAL checkpoint failed: {e}")
            return False

    def close(self):
        """
        Properly close the database connection with checkpoint.
        Always checkpoint before closing to ensure all changes are in main DB.
        """
        try:
            # Checkpoint before closing to merge WAL to main database
            self.checkpoint_database()
            self.conn.close()
            logging.info("✓ Database connection closed with checkpoint")
        except sqlite3.Error as e:
            logging.error(f"Error closing database: {e}")
            try:
                self.conn.close()
            except:
                pass

    def commit_and_checkpoint(self):
        """
        Commit current transaction AND force checkpoint.
        Use this after important changes to ensure visibility across PCs.
        """
        try:
            self.conn.commit()
            self.checkpoint_database()
            return True
        except sqlite3.Error as e:
            logging.error(f"Commit and checkpoint failed: {e}")
            return False

    @staticmethod
    def row_to_dict(row):
        """Convert sqlite3.Row to dictionary properly"""
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}

    def log_action(self, action: str, emp_id: str, username: str, details: str = ""):
        """Log all important actions"""
        self.conn.execute(
            "INSERT INTO audit_log (action, emp_id, username, details, timestamp) VALUES (?, ?, ?, ?, ?)",
            (action, emp_id, username, details, datetime.now().isoformat())
        )

    def _handle_corrupted_database(self, corrupted_path: str):
        """
        Handle corrupted database by attempting recovery from local backup or creating new.
        
        Recovery strategy:
        1. Rename corrupted file as backup
        2. Try to restore from local backup if available
        3. If no backup, create fresh database
        """
        import shutil
        from pathlib import Path
        
        logging.warning("=" * 80)
        logging.warning("DATABASE CORRUPTION DETECTED - Attempting recovery...")
        logging.warning("=" * 80)
        
        # Rename corrupted file
        corrupted_backup = f"{corrupted_path}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.move(corrupted_path, corrupted_backup)
            logging.info(f"Corrupted file backed up to: {corrupted_backup}")
        except Exception as e:
            logging.error(f"Failed to backup corrupted file: {e}")
            # If can't move, just delete it
            try:
                os.remove(corrupted_path)
                logging.warning(f"Deleted corrupted file: {corrupted_path}")
            except Exception as e2:
                logging.error(f"Failed to delete corrupted file: {e2}")
                raise
        
        # Try to restore from local backup
        from employee_vault.app_config import LOCAL_DB_PATH, NETWORK_DB_PATH
        
        if corrupted_path == NETWORK_DB_PATH and os.path.exists(LOCAL_DB_PATH):
            # Network DB corrupted, restore from local
            try:
                shutil.copy2(LOCAL_DB_PATH, NETWORK_DB_PATH)
                logging.info(f"✓ Restored from local backup: {LOCAL_DB_PATH} → {NETWORK_DB_PATH}")
                return
            except Exception as e:
                logging.error(f"Failed to restore from local backup: {e}")
        
        # No backup available - create fresh database
        logging.warning("No backup available - creating fresh database")
        logging.warning("You will need to restore data from backups or re-enter information")
        
        # Create empty file - _ensure_schema() will initialize it
        Path(corrupted_path).touch()
        logging.info(f"Created fresh database file: {corrupted_path}")

    # Update schema to include:
    """
    CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        emp_id TEXT,
        username TEXT NOT NULL,
        details TEXT,
        timestamp TEXT NOT NULL
    );
    """

    def _ensure_schema(self):
        """
        Ensure all required database tables exist with proper schema.

        Creates tables for: users, security_questions, employees, agencies,
        audit_log, and user_sessions with appropriate constraints and indexes.
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password TEXT,
            pin TEXT,
            pin_change_required INTEGER DEFAULT 1,
            role TEXT NOT NULL DEFAULT 'user',
            name TEXT NOT NULL
        );""")

        # Security questions table for password recovery
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS security_questions(
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer_hash TEXT NOT NULL,
            PRIMARY KEY(username, question_id),
            FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
        );""")

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS employees(
            emp_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT,
            department TEXT, position TEXT, hire_date TEXT NOT NULL, resign_date TEXT,
            salary REAL, notes TEXT, modified TEXT, modified_by TEXT, contract_expiry TEXT, agency TEXT,
            sss_number TEXT, emergency_contact_name TEXT, emergency_contact_phone TEXT,
            contract_start_date TEXT, contract_months INTEGER
        );""")
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS employee_files(
            emp_id TEXT NOT NULL, filename TEXT NOT NULL, added_at TEXT NOT NULL,
            PRIMARY KEY(emp_id,filename),
            FOREIGN KEY(emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
        );""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS agencies(name TEXT PRIMARY KEY);""")

        # Audit log table for tracking all changes
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id TEXT,
            old_value TEXT,
            new_value TEXT,
            details TEXT
        );""")

        # Settings table for network configuration
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );""")

        # Login attempts tracking table for throttling
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            attempt_time TEXT NOT NULL,
            success INTEGER NOT NULL DEFAULT 0,
            ip_address TEXT
        );""")

        # Create index for faster login attempts lookup
        self.conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_attempts_username 
        ON login_attempts(username, attempt_time);
        """)

        # Archived employees table for soft delete (Priority #2)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS archived_employees(
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            hire_date TEXT NOT NULL,
            resign_date TEXT,
            salary REAL,
            notes TEXT,
            modified TEXT,
            modified_by TEXT,
            contract_expiry TEXT,
            agency TEXT,
            sss_number TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            contract_start_date TEXT,
            contract_months INTEGER,
            tin_number TEXT,
            pagibig_number TEXT,
            philhealth_number TEXT,
            archived_date TEXT NOT NULL,
            archived_by TEXT NOT NULL,
            archive_reason TEXT
        );""")

        # QUICK WIN #1: Enhanced indexes for 50-80% faster queries
        indexes = [
            # Phase 3.2: CRITICAL - emp_id is used in WHERE clauses 100+ times
            "CREATE INDEX IF NOT EXISTS idx_emp_id ON employees(emp_id);",

            # Phase 3.2: status index for active/inactive filtering
            "CREATE INDEX IF NOT EXISTS idx_emp_status ON employees(status);",

            # Original indexes
            "CREATE INDEX IF NOT EXISTS idx_emp_name ON employees(name);",
            "CREATE INDEX IF NOT EXISTS idx_emp_department ON employees(department);",
            "CREATE INDEX IF NOT EXISTS idx_emp_contract ON employees(contract_expiry);",

            # NEW: Composite indexes for common filter combinations
            "CREATE INDEX IF NOT EXISTS idx_emp_dept_status ON employees(department, resign_date);",
            "CREATE INDEX IF NOT EXISTS idx_emp_agency_status ON employees(agency, resign_date);",
            "CREATE INDEX IF NOT EXISTS idx_emp_position ON employees(position);",

            # NEW: Audit log indexes for faster reports
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log(username, timestamp);",

            # PHASE 5: Additional indexes for improved search performance
            "CREATE INDEX IF NOT EXISTS idx_emp_hire_date ON employees(hire_date);",
            "CREATE INDEX IF NOT EXISTS idx_emp_first_name ON employees(first_name);",
            "CREATE INDEX IF NOT EXISTS idx_emp_last_name ON employees(last_name);",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, timestamp);",
        ]
        for idx in indexes:
            try:
                self.conn.execute(idx)
            except sqlite3.Error:
                # Index may already exist, skip silently
                pass
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(employees)").fetchall()}
        if "contract_expiry" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN contract_expiry TEXT;")
        if "agency" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN agency TEXT;")
        if "sss_number" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN sss_number TEXT;")
        if "emergency_contact_name" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN emergency_contact_name TEXT;")
        if "emergency_contact_phone" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN emergency_contact_phone TEXT;")
        if "contract_start_date" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN contract_start_date TEXT;")
        if "contract_months" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN contract_months INTEGER;")
        # Add government ID columns
        if "tin_number" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN tin_number TEXT;")
        if "pagibig_number" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN pagibig_number TEXT;")
        if "philhealth_number" not in cols: self.conn.execute("ALTER TABLE employees ADD COLUMN philhealth_number TEXT;")
        
        # v5.1: Add file_type column to employee_files for separating photos from documents
        file_cols = {r[1] for r in self.conn.execute("PRAGMA table_info(employee_files)").fetchall()}
        if "file_type" not in file_cols: 
            self.conn.execute("ALTER TABLE employee_files ADD COLUMN file_type TEXT DEFAULT 'document';")
            logging.info("Added file_type column to employee_files table")
        
        if self.conn.execute("SELECT COUNT(*) FROM agencies").fetchone()[0]==0:
            self.conn.executemany("INSERT OR IGNORE INTO agencies(name) VALUES(?)", [(a,) for a in SEED_AGENCIES])
        # Create default admin user ONLY if users table is empty
        # Check if pin column exists first (for migration compatibility)
        if self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:
            cols = {r[1] for r in self.conn.execute("PRAGMA table_info(users)").fetchall()}
            if "pin" in cols:
                # v4.6.0: Default admin now uses PIN instead of password
                # Default PIN for admin is "123456" - MUST be changed on first login
                # Note: password field set to empty string (legacy databases may have NOT NULL constraint)
                self.conn.execute("INSERT INTO users(username, password, pin, pin_change_required, role, name) VALUES(?,?,?,?,?,?)",
                                  ("admin", "", _hash_pin("123456"), 1, "admin", "Administrator"))
                logging.info("Created default admin user with PIN: 123456 (must be changed on first login)")
            else:
                # Fallback: pin column doesn't exist yet (will be added by migration)
                logging.info("Skipping default admin creation - pin column will be added by migration")

        # v2.0: Add new tables and perform migration
        self._v2_schema_additions()


    def _maybe_import_json(self):
        if not os.path.exists(JSON_FALLBACK): return
        try:
            data = json.loads(Path(JSON_FALLBACK).read_text(encoding="utf-8"))
            if not isinstance(data, list): return
            for e in data:
                if not isinstance(e, dict): continue
                emp_id = e.get("emp_id"); name = (e.get("name","") or "").strip(); hire=e.get("hire_date","").strip()
                if not (emp_id and name and hire): continue
                self.conn.execute("""
                    INSERT OR REPLACE INTO employees(emp_id,name,email,phone,department,position,hire_date,resign_date,salary,notes,modified,modified_by,contract_expiry,agency)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (emp_id, name, e.get("email",""), e.get("phone",""), e.get("department",""),
                     e.get("position",""), hire, e.get("resign_date") or None, float(e.get("salary") or 0),
                     e.get("notes",""), e.get("modified",""), e.get("modified_by",""), e.get("contract_expiry","") or "", e.get("agency") or None))
        except Exception: pass

    # ==================== v2.0 DATABASE METHODS ====================

    def _v2_schema_additions(self):
        """Create v2.0 tables and perform migration"""
        # User permissions table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS user_permissions(
            username TEXT PRIMARY KEY,
            permissions TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
        );""")

        # Stores/Branches table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS stores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            address TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")

        # Letter templates table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS letter_templates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            template_type TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")

        # Letter history table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS letter_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            letter_type TEXT,
            letter_date TEXT,
            store_id INTEGER,
            reason TEXT,
            supervisor_name TEXT,
            supervisor_title TEXT,
            file_path TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(employee_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
            FOREIGN KEY(store_id) REFERENCES stores(id)
        );""")

        # Active sessions table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS active_sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_activity TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            computer_name TEXT
        );""")

        # Database version table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS db_version(
            version INTEGER PRIMARY KEY,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")

        # Record locks table for multi-user concurrent editing
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS record_locks(
            record_id TEXT PRIMARY KEY,
            locked_by TEXT NOT NULL,
            locked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            computer_name TEXT,
            lock_expires_at TEXT NOT NULL
        );""")
        
        # Security audit table with tamper detection (hash chain)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS security_audit(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            computer_name TEXT,
            details TEXT,
            severity TEXT DEFAULT 'INFO',
            previous_hash TEXT,
            entry_hash TEXT NOT NULL
        );""")

        # Create indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_letter_history_employee ON letter_history(employee_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_letter_history_date ON letter_history(letter_date)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_active_sessions_username ON active_sessions(username)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_record_locks_locked_by ON record_locks(locked_by)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_record_locks_expires ON record_locks(lock_expires_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_security_audit_timestamp ON security_audit(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_security_audit_event_type ON security_audit(event_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_security_audit_username ON security_audit(username)")

        # Perform migration if needed
        self._check_and_migrate()

    def _check_and_migrate(self):
        """Check database version and perform migrations if needed"""
        try:
            cursor = self.conn.execute("SELECT MAX(version) FROM db_version")
            row = cursor.fetchone()
            current_version = row[0] if row and row[0] else 0

            TARGET_VERSION = DATABASE_VERSION

            if current_version < TARGET_VERSION:
                logging.info(f"Migrating database from version {current_version} to {TARGET_VERSION}")

                # Create automatic backup
                import shutil
                backup_path = f"backups/auto_migration_v{current_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                os.makedirs("backups", exist_ok=True)
                try:
                    shutil.copy2(DB_FILE, backup_path)
                    logging.info(f"Created migration backup: {backup_path}")
                except Exception as e:
                    logging.warning(f"Could not create backup: {e}")

                # Perform migrations
                if current_version < 1:
                    self._migrate_to_v1()
                if current_version < 2:
                    self._migrate_to_v2()
                if current_version < 7:
                    self._migrate_to_v7()

                # Update version
                self.conn.execute("INSERT OR REPLACE INTO db_version (version) VALUES (?)", (TARGET_VERSION,))
                self.conn.commit()
                logging.info("Database migration completed successfully")

        except Exception as e:
            logging.error(f"Database migration error: {e}")

    def _migrate_to_v1(self):
        """Migrate to version 1"""
        pass  # Placeholder for future v1 migrations

    def _migrate_to_v2(self):
        """Migrate to version 2 - Add permissions and default data"""
        try:
            # Set default permissions for existing users
            default_user_perms = json.dumps({
                "dashboard": True, "employees": True, "add_employee": True,
                "edit_employee": True, "delete_employee": True, "print_system": True,
                "bulk_operations": True, "reports": True, "letters": True,
                "user_management": False, "settings": True, "audit_log": True,
                "backup_restore": True, "archive": True
            })

            admin_perms = json.dumps({
                "dashboard": True, "employees": True, "add_employee": True,
                "edit_employee": True, "delete_employee": True, "print_system": True,
                "bulk_operations": True, "reports": True, "letters": True,
                "user_management": True, "settings": True, "audit_log": True,
                "backup_restore": True, "archive": True
            })

            # Insert default permissions
            cursor = self.conn.execute("SELECT username, role FROM users")
            for row in cursor.fetchall():
                perms = admin_perms if row['role'] == 'admin' else default_user_perms
                self.conn.execute("INSERT OR REPLACE INTO user_permissions (username, permissions) VALUES (?, ?)",
                                (row['username'], perms))

            # Add default letter template
            cursor = self.conn.execute("SELECT COUNT(*) FROM letter_templates")
            if cursor.fetchone()[0] == 0:
                template = """[DATE]

The Store Manager
[COMPANY_NAME]
[BRANCH_NAME]
[ADDRESS]

Dear Sir/Madam,


This is to inform you that [EMPLOYEE_NAME] was unable to report for work on [LETTER_DATE] due to [REASON].

We kindly request your understanding regarding this matter.

Thank you for your consideration.

Respectfully yours,

[SUPERVISOR_NAME]
[SUPERVISOR_TITLE]
"""

                self.conn.execute("""
                    INSERT INTO letter_templates (name, template_type, content)
                    VALUES (?, ?, ?)
                """, ("Default Excuse Letter", "excuse", template))

            # No default stores - users can add their own stores
            # Removed sample stores per user request

            self.conn.commit()
            logging.info("v2.0 migration completed: permissions, templates, and stores added")

        except Exception as e:
            logging.error(f"Error in v2 migration: {e}")

    def _migrate_to_v7(self):
        """
        PHASE 1 FIX: Migrate to version 7 - Add unique constraints for government IDs
        Prevents duplicate SSS, TIN, PhilHealth, and Pag-IBIG numbers
        """
        try:
            logging.info("Starting v7 migration: Adding unique constraints for government IDs")

            # Check for existing duplicates before adding constraints
            duplicates_found = []

            # Check SSS duplicates
            sss_dups = self.conn.execute("""
                SELECT sss_number, COUNT(*) as cnt
                FROM employees
                WHERE sss_number IS NOT NULL AND sss_number != ''
                GROUP BY sss_number
                HAVING cnt > 1
            """).fetchall()
            if sss_dups:
                duplicates_found.append(f"SSS: {len(sss_dups)} duplicates")

            # Check TIN duplicates
            tin_dups = self.conn.execute("""
                SELECT tin_number, COUNT(*) as cnt
                FROM employees
                WHERE tin_number IS NOT NULL AND tin_number != ''
                GROUP BY tin_number
                HAVING cnt > 1
            """).fetchall()
            if tin_dups:
                duplicates_found.append(f"TIN: {len(tin_dups)} duplicates")

            # Check PhilHealth duplicates
            philhealth_dups = self.conn.execute("""
                SELECT philhealth_number, COUNT(*) as cnt
                FROM employees
                WHERE philhealth_number IS NOT NULL AND philhealth_number != ''
                GROUP BY philhealth_number
                HAVING cnt > 1
            """).fetchall()
            if philhealth_dups:
                duplicates_found.append(f"PhilHealth: {len(philhealth_dups)} duplicates")

            # Check Pag-IBIG duplicates
            pagibig_dups = self.conn.execute("""
                SELECT pagibig_number, COUNT(*) as cnt
                FROM employees
                WHERE pagibig_number IS NOT NULL AND pagibig_number != ''
                GROUP BY pagibig_number
                HAVING cnt > 1
            """).fetchall()
            if pagibig_dups:
                duplicates_found.append(f"Pag-IBIG: {len(pagibig_dups)} duplicates")

            if duplicates_found:
                logging.warning(f"⚠️ Duplicate government IDs found: {', '.join(duplicates_found)}")
                logging.warning("⚠️ Unique constraints NOT added. Please fix duplicates first.")
                logging.warning("⚠️ Run audit log to find and fix duplicate IDs, then re-run migration.")
                # Still mark as migrated to v7, but without constraints
                return

            # No duplicates found - safe to add unique indexes
            logging.info("✓ No duplicates found. Adding unique indexes...")

            # Add unique indexes for government IDs
            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_sss
                ON employees(sss_number)
                WHERE sss_number IS NOT NULL AND sss_number != ''
            """)

            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_tin
                ON employees(tin_number)
                WHERE tin_number IS NOT NULL AND tin_number != ''
            """)

            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_philhealth
                ON employees(philhealth_number)
                WHERE philhealth_number IS NOT NULL AND philhealth_number != ''
            """)

            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_pagibig
                ON employees(pagibig_number)
                WHERE pagibig_number IS NOT NULL AND pagibig_number != ''
            """)

            self.conn.commit()
            logging.info("✓ v7 migration completed: Unique constraints added for government IDs")

        except Exception as e:
            logging.error(f"Error in v7 migration: {e}")
            # Don't fail - just log the error

    def _migrate_password_to_pin(self):
        """
        Migrate from password to PIN system.
        Adds pin and pin_change_required columns to users table.
        Also removes NOT NULL constraint from password column.
        """
        try:
            # Check if migration is needed
            cols = {r[1] for r in self.conn.execute("PRAGMA table_info(users)").fetchall()}
            
            # Get table info to check NOT NULL constraint on password
            table_info = self.conn.execute("PRAGMA table_info(users)").fetchall()
            password_col = next((col for col in table_info if col[1] == 'password'), None)
            
            # Column index: 0=cid, 1=name, 2=type, 3=notnull, 4=dflt_value, 5=pk
            # Check if password has NOT NULL constraint (notnull=1)
            if password_col and password_col[3] == 1:  # notnull=1 means NOT NULL constraint exists
                logging.info("Detected NOT NULL constraint on password column - migrating schema...")
                
                # Recreate users table without NOT NULL on password
                # Step 1: Create new table with correct schema
                self.conn.execute("""
                CREATE TABLE users_new(
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    pin TEXT,
                    pin_change_required INTEGER DEFAULT 1,
                    role TEXT NOT NULL DEFAULT 'user',
                    name TEXT NOT NULL
                );""")
                
                # Step 2: Copy data from old table (handle missing pin columns)
                if "pin" in cols:
                    self.conn.execute("""
                    INSERT INTO users_new (username, password, pin, pin_change_required, role, name)
                    SELECT username, password, pin, 
                           COALESCE(pin_change_required, 1), 
                           role, name
                    FROM users;
                    """)
                else:
                    # Old table doesn't have pin column yet
                    self.conn.execute("""
                    INSERT INTO users_new (username, password, pin, pin_change_required, role, name)
                    SELECT username, password, NULL, 1, role, name
                    FROM users;
                    """)
                
                # Step 3: Drop old table and rename new one
                self.conn.execute("DROP TABLE users;")
                self.conn.execute("ALTER TABLE users_new RENAME TO users;")
                
                self.conn.commit()
                logging.info("✓ Successfully removed NOT NULL constraint from password column")
                
                # Refresh column list after migration
                cols = {r[1] for r in self.conn.execute("PRAGMA table_info(users)").fetchall()}

            if "pin" not in cols:
                logging.info("Starting password-to-PIN migration...")

                # Add PIN column
                self.conn.execute("ALTER TABLE users ADD COLUMN pin TEXT;")
                logging.info("✓ Added 'pin' column to users table")

                # Add pin_change_required flag
                self.conn.execute("ALTER TABLE users ADD COLUMN pin_change_required INTEGER DEFAULT 1;")
                logging.info("✓ Added 'pin_change_required' column to users table")

                # For any existing users with password, set pin_change_required=1
                # They will be forced to set PIN on next login
                self.conn.execute("""
                    UPDATE users
                    SET pin_change_required = 1
                    WHERE password IS NOT NULL AND pin IS NULL
                """)

                # Create default admin if no users exist
                if self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                    from employee_vault.config import _hash_pin
                    self.conn.execute("INSERT INTO users(username, password, pin, pin_change_required, role, name) VALUES(?,?,?,?,?,?)",
                                      ("admin", None, _hash_pin("123456"), 1, "admin", "Administrator"))
                    logging.info("Created default admin user with PIN: 123456 (must be changed on first login)")

                self.conn.commit()
                logging.info("✓ Password-to-PIN migration completed successfully")
                logging.info("ℹ️ Existing users will be prompted to set a PIN on next login")

        except Exception as e:
            logging.error(f"Error in PIN migration: {e}")
            # Don't fail - just log the error

    # User Permission Methods
    def get_user_permissions(self, username: str) -> Dict[str, bool]:
        """Get user permissions"""
        try:
            # Check if user is admin first
            user = self.get_user(username)
            logging.info(f"get_user_permissions for {username}: user={user}, role={user.get('role') if user else None}")
            if user and user.get('role') == 'admin':
                # Admin has all permissions
                logging.info(f"Returning admin permissions for {username}")
                return {
                    "dashboard": True,
                    "employees": True,
                    "add_employee": True,
                    "edit_employee": True,
                    "delete_employee": True,
                    "print_system": True,
                    "bulk_operations": True,
                    "reports": True,
                    "letters": True,
                    "user_management": True,
                    "settings": True,
                    "audit_log": True,
                    "backup_restore": True,
                    "archive": True
                }

            cursor = self.conn.execute("SELECT permissions FROM user_permissions WHERE username=?", (username,))
            row = cursor.fetchone()
            if row:
                return json.loads(row['permissions'])
            else:
                # v3.1: Return default permissions for regular users (limited access)
                # Users can only see: Main menu, Backup, Change Theme, About, Logout
                return {
                    "dashboard": True,
                    "employees": True,
                    "add_employee": True,
                    "edit_employee": True,
                    "delete_employee": False,
                    "print_system": False,
                    "bulk_operations": False,
                    "reports": True,
                    "letters": False,
                    "user_management": False,
                    "settings": False,
                    "audit_log": False,
                    "backup_restore": True,  # Can backup
                    "archive": False
                }
        except Exception as e:
            logging.error(f"Error fetching permissions: {e}")
            return {}

    def update_user_permissions(self, username: str, permissions: Dict[str, bool]) -> bool:
        """Update user permissions"""
        try:
            perms_json = json.dumps(permissions)
            self.conn.execute("INSERT OR REPLACE INTO user_permissions (username, permissions) VALUES (?, ?)",
                            (username, perms_json))
            self.conn.commit()
            logging.info(f"Updated permissions for {username}")
            return True
        except Exception as e:
            logging.error(f"Error updating permissions: {e}")
            return False

    def reset_all_users_to_default_permissions(self) -> int:
        """Reset all existing users to default permissions. Returns count of users updated."""
        try:
            # Default permissions for regular users
            default_user_perms = {
                "dashboard": True,
                "employees": True,
                "add_employee": True,
                "edit_employee": True,
                "delete_employee": False,  # Delete disabled by default for safety
                "print_system": True,
                "bulk_operations": True,
                "reports": True,
                "letters": True,
                "user_management": False,  # Regular users cannot manage users
                "settings": True,
                "audit_log": False,  # Audit log is admin-only
                "backup_restore": False,  # Backup is admin-only
                "archive": False,  # Archive is admin-only
            }

            # Admin permissions (full access)
            admin_perms = {
                "dashboard": True,
                "employees": True,
                "add_employee": True,
                "edit_employee": True,
                "delete_employee": True,
                "print_system": True,
                "bulk_operations": True,
                "reports": True,
                "letters": True,
                "user_management": True,
                "settings": True,
                "audit_log": True,
                "backup_restore": True,
                "archive": True,
            }

            cursor = self.conn.execute("SELECT username, role FROM users")
            users = cursor.fetchall()
            count = 0

            for row in users:
                username = row['username']
                role = row['role']
                perms = admin_perms if role == 'admin' else default_user_perms
                perms_json = json.dumps(perms)
                self.conn.execute("INSERT OR REPLACE INTO user_permissions (username, permissions) VALUES (?, ?)",
                                (username, perms_json))
                count += 1
                logging.info(f"Reset permissions for {username} ({role})")

            self.conn.commit()
            logging.info(f"Reset permissions for {count} users to defaults")
            return count

        except Exception as e:
            logging.error(f"Error resetting user permissions: {e}")
            return 0

    # Store Management Methods
    def get_all_stores(self) -> List[Dict]:
        """Get all stores (including inactive)"""
        try:
            cursor = self.conn.execute("SELECT * FROM stores ORDER BY company_name, branch_name")
            return [self.row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching stores: {e}")
            return []

    def get_active_stores(self) -> List[Dict]:
        """Get only active stores"""
        try:
            cursor = self.conn.execute("SELECT * FROM stores WHERE active=1 ORDER BY company_name, branch_name")
            return [self.row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching active stores: {e}")
            return []

    def add_store(self, company_name: str, branch_name: str, address: str = "") -> bool:
        """Add new store"""
        try:
            self.conn.execute("""
                INSERT INTO stores (company_name, branch_name, address, active)
                VALUES (?, ?, ?, 1)
            """, (company_name, branch_name, address))
            self.conn.commit()
            logging.info(f"Added store: {company_name} - {branch_name}")
            return True
        except Exception as e:
            logging.error(f"Error adding store: {e}")
            return False

    def update_store(self, store_id: int, company_name: str, branch_name: str, address: str = "") -> bool:
        """Update store"""
        try:
            self.conn.execute("""
                UPDATE stores SET company_name=?, branch_name=?, address=?
                WHERE id=?
            """, (company_name, branch_name, address, store_id))
            self.conn.commit()
            logging.info(f"Updated store {store_id}")
            return True
        except Exception as e:
            logging.error(f"Error updating store: {e}")
            return False

    def toggle_store_active(self, store_id: int, active: bool) -> bool:
        """Activate/deactivate store"""
        try:
            self.conn.execute("UPDATE stores SET active=? WHERE id=?", (1 if active else 0, store_id))
            self.conn.commit()
            logging.info(f"Store {store_id} {'activated' if active else 'deactivated'}")
            return True
        except Exception as e:
            logging.error(f"Error toggling store: {e}")
            return False

    # Letter System Methods
    def get_letter_template(self, template_id: int = 1) -> str:
        """Get letter template"""
        try:
            cursor = self.conn.execute("SELECT content FROM letter_templates WHERE id=?", (template_id,))
            row = cursor.fetchone()
            return row['content'] if row else ""
        except Exception as e:
            logging.error(f"Error fetching template: {e}")
            return ""

    def save_letter_history(self, employee_id: str, letter_type: str, letter_date: str,
                           store_id: int, reason: str, supervisor_name: str,
                           supervisor_title: str, file_path: str, created_by: str) -> bool:
        """Save letter history"""
        try:
            self.conn.execute("""
                INSERT INTO letter_history
                (employee_id, letter_type, letter_date, store_id, reason,
                 supervisor_name, supervisor_title, file_path, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (employee_id, letter_type, letter_date, store_id, reason,
                  supervisor_name, supervisor_title, file_path, created_by))
            self.conn.commit()
            logging.info(f"Saved letter history for {employee_id}")
            return True
        except Exception as e:
            logging.error(f"Error saving letter history: {e}")
            return False

    def get_employee_letters(self, employee_id: str) -> List[Dict]:
        """Get employee letters"""
        try:
            cursor = self.conn.execute("""
                SELECT lh.*, s.company_name, s.branch_name
                FROM letter_history lh
                LEFT JOIN stores s ON lh.store_id = s.id
                WHERE lh.employee_id = ?
                ORDER BY lh.created_at DESC
            """, (employee_id,))
            return [self.row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching employee letters: {e}")
            return []

    # Session Tracking Methods
    def create_session(self, username: str, ip_address: str = "", computer_name: str = ""):
        """Create session"""
        try:
            self.conn.execute("INSERT INTO active_sessions (username, ip_address, computer_name) VALUES (?, ?, ?)",
                            (username, ip_address, computer_name))
            self.conn.commit()
            logging.info(f"Session created for {username}")
        except Exception as e:
            logging.error(f"Error creating session: {e}")

    def update_session_activity(self, username: str):
        """Update session activity"""
        try:
            self.conn.execute("""
                UPDATE active_sessions SET last_activity = CURRENT_TIMESTAMP
                WHERE username = ? AND id = (SELECT MAX(id) FROM active_sessions WHERE username = ?)
            """, (username, username))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error updating session: {e}")

    def close_session(self, username: str):
        """Close session"""
        try:
            self.conn.execute("""
                DELETE FROM active_sessions
                WHERE username = ? AND id = (SELECT MAX(id) FROM active_sessions WHERE username = ?)
            """, (username, username))
            self.conn.commit()
            logging.info(f"Session closed for {username}")
        except Exception as e:
            logging.error(f"Error closing session: {e}")

    def get_active_sessions(self) -> List[Dict]:
        """Get active sessions (clean up old ones first)"""
        try:
            # Clean up sessions older than 1 hour
            self.conn.execute("DELETE FROM active_sessions WHERE datetime(last_activity) < datetime('now', '-1 hour')")
            cursor = self.conn.execute("SELECT * FROM active_sessions ORDER BY last_activity DESC")
            return [self.row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching sessions: {e}")
            return []

    def force_logout_user(self, username: str):
        """Force logout a user by deleting all their sessions"""
        try:
            self.conn.execute("DELETE FROM active_sessions WHERE username = ?", (username,))
            self.conn.commit()
            logging.info(f"Force logged out user: {username}")
        except Exception as e:
            logging.error(f"Error force logging out user {username}: {e}")

    # ==================== END v2.0 DATABASE METHODS ====================

    # ==================== RECORD LOCKING METHODS ====================

    def acquire_lock(self, record_id: str, username: str) -> bool:
        """
        Attempt to acquire exclusive lock on record.
        Returns True if lock acquired, False if already locked by someone else.
        Auto-expires locks older than 30 minutes.
        """
        try:
            import socket
            from datetime import datetime, timedelta

            # Clean up expired locks first
            self.cleanup_expired_locks()

            # Check if record is already locked
            lock_info = self.get_lock_info(record_id)
            if lock_info and lock_info['locked']:
                # Check if it's locked by the same user
                if lock_info['locked_by'] == username:
                    # Refresh existing lock
                    return self.refresh_lock(record_id, username)
                else:
                    # Locked by someone else
                    return False

            # Acquire new lock (30 minute expiry)
            computer_name = socket.gethostname()
            lock_expires_at = (datetime.now() + timedelta(minutes=30)).isoformat()

            self.conn.execute("""
                INSERT OR REPLACE INTO record_locks (record_id, locked_by, locked_at, computer_name, lock_expires_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (record_id, username, computer_name, lock_expires_at))
            self.conn.commit()

            logging.info(f"Lock acquired: {record_id} by {username}")
            return True

        except Exception as e:
            logging.error(f"Error acquiring lock for {record_id}: {e}")
            return False

    def release_lock(self, record_id: str, username: str) -> bool:
        """Release lock (on form close or save)"""
        try:
            self.conn.execute("""
                DELETE FROM record_locks
                WHERE record_id = ? AND locked_by = ?
            """, (record_id, username))
            self.conn.commit()

            logging.info(f"Lock released: {record_id} by {username}")
            return True

        except Exception as e:
            logging.error(f"Error releasing lock for {record_id}: {e}")
            return False

    def get_lock_info(self, record_id: str) -> Dict[str, Any]:
        """Returns {locked: bool, locked_by: str, locked_at: str, computer_name: str} or None"""
        try:
            row = self.conn.execute("""
                SELECT locked_by, locked_at, computer_name, lock_expires_at
                FROM record_locks
                WHERE record_id = ? AND datetime(lock_expires_at) > datetime('now')
            """, (record_id,)).fetchone()

            if row:
                return {
                    'locked': True,
                    'locked_by': row['locked_by'],
                    'locked_at': row['locked_at'],
                    'computer_name': row['computer_name'] if 'computer_name' in row.keys() else None,
                    'lock_expires_at': row['lock_expires_at']
                }
            else:
                return {'locked': False}

        except Exception as e:
            logging.error(f"Error getting lock info for {record_id}: {e}")
            return {'locked': False}

    def refresh_lock(self, record_id: str, username: str) -> bool:
        """Update lock_expires_at timestamp (call every 5 min)"""
        try:
            from datetime import datetime, timedelta

            lock_expires_at = (datetime.now() + timedelta(minutes=30)).isoformat()

            self.conn.execute("""
                UPDATE record_locks
                SET lock_expires_at = ?, locked_at = CURRENT_TIMESTAMP
                WHERE record_id = ? AND locked_by = ?
            """, (lock_expires_at, record_id, username))
            self.conn.commit()

            logging.debug(f"Lock refreshed: {record_id} by {username}")
            return True

        except Exception as e:
            logging.error(f"Error refreshing lock for {record_id}: {e}")
            return False

    def cleanup_expired_locks(self):
        """Remove locks older than 30 minutes (background task)"""
        try:
            result = self.conn.execute("""
                DELETE FROM record_locks
                WHERE datetime(lock_expires_at) <= datetime('now')
            """)
            self.conn.commit()

            if result.rowcount > 0:
                logging.info(f"Cleaned up {result.rowcount} expired locks")

        except Exception as e:
            logging.error(f"Error cleaning up expired locks: {e}")

    def get_all_locks(self) -> List[Dict[str, Any]]:
        """Get all active locks (for debugging/monitoring)"""
        try:
            cursor = self.conn.execute("""
                SELECT record_id, locked_by, locked_at, computer_name, lock_expires_at
                FROM record_locks
                WHERE datetime(lock_expires_at) > datetime('now')
                ORDER BY locked_at DESC
            """)
            return [self.row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching locks: {e}")
            return []

    # ==================== END RECORD LOCKING METHODS ====================

    def closeEvent(self, event):
        """Add to MainWindow class"""
        if hasattr(self, 'auto_refresh_timer'):
            self.auto_refresh_timer.stop()
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except (sqlite3.Error, AttributeError):
                # Database may already be closed or not have close method
                pass
        event.accept()
    def get_user(self, username):
        """Get user by username, returns dict"""
        row = self.conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None

    def all_users(self):
        """Get all users"""
        return [dict(r) for r in self.conn.execute("SELECT username, name, role FROM users ORDER BY username").fetchall()]

    def create_user(self, username, name, pin, role="user"):
        """Create a new user with PIN authentication (bcrypt hashed)"""
        # Retry logic for concurrent access on network shares
        max_retries = 5
        retry_delay = 0.1  # Start with 100ms
        
        for attempt in range(max_retries):
            try:
                self.conn.execute(
                    "INSERT INTO users(username, password, pin, pin_change_required, role, name) VALUES(?, ?, ?, ?, ?, ?)",
                    (username, None, _hash_pin(pin), 0, role, name)  # password=None, pin_change_required=0 for new users
                )

                # Set permissions based on role
                if role == "admin":
                    # Admin gets full permissions
                    default_permissions = {
                        "dashboard": True,
                        "employees": True,
                        "add_employee": True,
                        "edit_employee": True,
                        "delete_employee": True,
                        "print_system": True,
                        "bulk_operations": True,
                        "reports": True,
                        "letters": True,
                        "user_management": True,  # Admin can manage users
                        "settings": True,
                        "audit_log": True,
                        "backup_restore": True,
                        "archive": True,
                    }
                else:
                    # Regular user gets limited permissions
                    default_permissions = {
                        "dashboard": True,
                        "employees": True,
                        "add_employee": True,
                        "edit_employee": True,
                        "delete_employee": False,  # Delete disabled by default for safety
                        "print_system": True,
                        "bulk_operations": True,
                        "reports": True,
                        "letters": True,
                        "user_management": False,  # Regular users cannot manage users
                        "settings": True,
                        "audit_log": True,
                        "backup_restore": True,
                        "archive": True,
                    }

                # Apply default permissions
                import json
                perms_json = json.dumps(default_permissions)
                self.conn.execute("INSERT OR REPLACE INTO user_permissions (username, permissions) VALUES (?, ?)",
                                (username, perms_json))
                self.conn.commit()
                logging.info(f"Created {role} user {username} with appropriate permissions")
                return  # Success - exit retry loop
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    import time
                    logging.warning(f"Database locked on create_user attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise  # Re-raise if not a lock error or max retries reached
            except sqlite3.IntegrityError:
                # Username already exists - don't retry, just raise
                raise

    def update_user(self, username, name, role):
        """Update user details (name and role)"""
        self.conn.execute("UPDATE users SET name=?, role=? WHERE username=?", (name, role, username))

    def update_user_password(self, username, new_password):
        """
        Update user password with bcrypt hashing
        NOTE: This is kept for backwards compatibility during migration.
        Use update_user_pin() for new PIN-based authentication.
        """
        self.conn.execute("UPDATE users SET password=? WHERE username=?",
                         (_hash_pwd(new_password), username))

    def update_user_pin(self, username, new_pin):
        """Update user PIN with bcrypt hashing"""
        self.conn.execute(
            "UPDATE users SET pin=?, pin_change_required=0 WHERE username=?",
            (_hash_pin(new_pin), username)
        )
        self.conn.commit()
        logging.info(f"Updated PIN for user: {username}")

    def user_needs_pin_setup(self, username) -> bool:
        """Check if user needs to set up their PIN"""
        row = self.conn.execute(
            "SELECT pin, pin_change_required FROM users WHERE username=?",
            (username,)
        ).fetchone()
        if not row:
            return False
        return row['pin'] is None or row['pin_change_required'] == 1

    def delete_user(self, username):
        """Delete a user"""
        self.conn.execute("DELETE FROM users WHERE username=?", (username,))

    def user_exists(self, username):
        """Check if username exists"""
        return bool(self.conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone())

    # ============================================================================
    # SECURITY QUESTIONS FOR PASSWORD RECOVERY - REMOVED IN PIN MIGRATION
    # ============================================================================
    # Security questions have been removed in favor of admin-only PIN resets
    # The security_questions table is kept for backwards compatibility but is no longer used

    # ============================================================================
    # v2.1: DATABASE BACKUP AND MAINTENANCE
    # ============================================================================

    def check_database_integrity(self) -> Tuple[bool, List[str]]:
        """
        Check database integrity and report any issues

        Returns:
            Tuple of (is_healthy, list_of_issues)
        """
        issues = []

        try:
            # 1. Run SQLite integrity check
            result = self.conn.execute("PRAGMA integrity_check").fetchone()
            if result and result[0] != 'ok':
                issues.append(f"Database integrity check failed: {result[0]}")

            # 2. Check that all required tables exist
            required_tables = [
                'users', 'employees', 'employee_files', 'agencies',
                'audit_log', 'settings', 'archived_employees',
                'user_permissions', 'stores', 'active_sessions'
            ]

            existing_tables = {
                row[0] for row in self.conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }

            for table in required_tables:
                if table not in existing_tables:
                    issues.append(f"Missing required table: {table}")

            # 3. Check for orphaned records
            try:
                # Check for employee_files with no matching employee
                orphaned_files = self.conn.execute("""
                    SELECT COUNT(*) FROM employee_files ef
                    WHERE NOT EXISTS (
                        SELECT 1 FROM employees e WHERE e.emp_id = ef.emp_id
                    )
                """).fetchone()[0]

                if orphaned_files > 0:
                    issues.append(f"Found {orphaned_files} orphaned file records")
            except sqlite3.Error:
                # Table might not exist in older versions
                pass

            # 4. Check for duplicate primary keys (shouldn't happen, but good to verify)
            try:
                duplicates = self.conn.execute("""
                    SELECT emp_id, COUNT(*) as cnt
                    FROM employees
                    GROUP BY emp_id
                    HAVING cnt > 1
                """).fetchall()

                if duplicates:
                    issues.append(f"Found {len(duplicates)} duplicate employee IDs")
            except sqlite3.Error:
                # Query execution failed
                pass

            # 5. Verify critical indexes exist
            try:
                indexes = {
                    row[1] for row in self.conn.execute(
                        "SELECT * FROM sqlite_master WHERE type='index'"
                    ).fetchall()
                }

                critical_indexes = ['idx_emp_name', 'idx_emp_department']
                for idx in critical_indexes:
                    if idx not in indexes:
                        issues.append(f"Missing critical index: {idx}")
            except sqlite3.Error:
                # Index query failed
                pass

            # Log results
            if issues:
                logging.warning(f"Database integrity check found {len(issues)} issue(s):")
                for issue in issues:
                    logging.warning(f"  - {issue}")
            else:
                logging.info("Database integrity check passed: OK")

            return (len(issues) == 0, issues)

        except Exception as e:
            logging.error(f"Error during database integrity check: {e}")
            return (False, [f"Integrity check error: {str(e)}"])

    @retry_on_lock(max_attempts=3, delay=0.5)
    def backup_database(self, backup_dir=BACKUPS_DIR):
        """
        Create timestamped database backup with automatic cleanup.

        Args:
            backup_dir: Directory to store backups

        Returns:
            Path to backup file or None on failure
        """
        try:
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"employee_vault_{timestamp}.db")

            # Note: WAL checkpoint removed as we use DELETE journal mode for network compatibility
            # DELETE mode doesn't use WAL files, so no checkpoint needed

            # Copy database file
            shutil.copy2(DB_FILE, backup_path)

            # Also backup WAL and SHM files if they exist
            for ext in ['-wal', '-shm']:
                src = DB_FILE + ext
                if os.path.exists(src):
                    shutil.copy2(src, backup_path + ext)

            logging.info(f"Database backed up to: {backup_path}")

            # Keep only last 10 backups
            self._cleanup_old_backups(backup_dir, keep_count=10)

            return backup_path

        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return None

    def _cleanup_old_backups(self, backup_dir, keep_count=10):
        """Remove old backups, keeping only the most recent ones"""
        try:
            from pathlib import Path
            backups = sorted(Path(backup_dir).glob("employee_vault_*.db"),
                           key=lambda p: p.stat().st_mtime,
                           reverse=True)

            for old_backup in backups[keep_count:]:
                try:
                    old_backup.unlink()
                    # Also remove WAL/SHM files
                    for ext in ['-wal', '-shm']:
                        wal_file = Path(str(old_backup) + ext)
                        if wal_file.exists():
                            wal_file.unlink()
                    logging.info(f"Removed old backup: {old_backup.name}")
                except Exception as e:
                    logging.warning(f"Could not remove old backup {old_backup}: {e}")

        except Exception as e:
            logging.error(f"Backup cleanup failed: {e}")

    # ============================================================================
    # ENCRYPTED BACKUP FUNCTIONS
    # ============================================================================

    def _get_encryption_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        import base64
        from hashlib import pbkdf2_hmac
        # Use a fixed salt (stored with backup) for key derivation
        salt = b'EmployeeVault_Backup_Salt_v1'
        key = pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=32)
        return base64.urlsafe_b64encode(key)

    def backup_database_encrypted(self, password: str, backup_dir: str = None) -> Optional[str]:
        """
        Create an encrypted backup of the database.
        
        Args:
            password: Password to encrypt the backup
            backup_dir: Directory to store backup (defaults to BACKUPS_DIR)
        
        Returns:
            Path to encrypted backup file or None on failure
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            logging.error("cryptography package not installed. Run: pip install cryptography")
            return None
        
        backup_dir = backup_dir or BACKUPS_DIR
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"employee_vault_{timestamp}.db.enc")
            
            # Read the database file
            with open(DB_FILE, 'rb') as f:
                db_data = f.read()
            
            # Encrypt
            key = self._get_encryption_key(password)
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(db_data)
            
            # Write encrypted backup with header
            with open(backup_path, 'wb') as f:
                # Write header for identification
                f.write(b'EVAULT_ENC_V1\n')
                f.write(encrypted_data)
            
            logging.info(f"Encrypted backup created: {backup_path}")
            
            # Log security event
            self.log_security_event(
                event_type="BACKUP_CREATED",
                details=f"Encrypted backup created: {os.path.basename(backup_path)}",
                severity="INFO"
            )
            
            return backup_path
            
        except Exception as e:
            logging.error(f"Encrypted backup failed: {e}")
            return None

    def restore_from_encrypted_backup(self, backup_path: str, password: str, 
                                       create_backup_first: bool = True) -> Tuple[bool, str]:
        """
        Restore database from encrypted backup.
        
        Args:
            backup_path: Path to encrypted backup file
            password: Password to decrypt the backup
            create_backup_first: If True, backup current DB before restore
        
        Returns:
            Tuple of (success, message)
        """
        try:
            from cryptography.fernet import Fernet, InvalidToken
        except ImportError:
            return False, "cryptography package not installed"
        
        try:
            # Read encrypted backup
            with open(backup_path, 'rb') as f:
                header = f.readline()
                if header != b'EVAULT_ENC_V1\n':
                    return False, "Invalid encrypted backup format"
                encrypted_data = f.read()
            
            # Decrypt
            key = self._get_encryption_key(password)
            fernet = Fernet(key)
            
            try:
                db_data = fernet.decrypt(encrypted_data)
            except InvalidToken:
                return False, "Invalid password or corrupted backup"
            
            # Verify decrypted data is a valid SQLite database
            if not db_data.startswith(b'SQLite format 3'):
                return False, "Decrypted data is not a valid SQLite database"
            
            # Create safety backup
            if create_backup_first:
                safety_backup = self.backup_database()
                if not safety_backup:
                    return False, "Could not create safety backup"
            
            # Close current connection
            self.conn.close()
            
            # Write decrypted database
            with open(DB_FILE, 'wb') as f:
                f.write(db_data)
            
            # Reconnect
            self.__init__(DB_FILE)
            
            # Log security event
            self.log_security_event(
                event_type="BACKUP_RESTORED",
                details=f"Restored from encrypted backup: {os.path.basename(backup_path)}",
                severity="WARNING"
            )
            
            return True, "✅ Database restored from encrypted backup!"
            
        except Exception as e:
            return False, f"Restore failed: {e}"

    # ============================================================================
    # WEEK 2 FEATURE #2: BACKUP RESTORE & VERIFY
    # ============================================================================

    def test_backup_restore(self, backup_path: str) -> Tuple[bool, str]:
        """
        Test restore from backup without affecting current database.

        Args:
            backup_path: Path to backup file to test

        Returns:
            Tuple of (success, message)
        """
        import tempfile

        try:
            # Create temporary directory for test
            with tempfile.TemporaryDirectory() as temp_dir:
                test_db_path = os.path.join(temp_dir, "test_restore.db")

                # Copy backup to temp location
                shutil.copy2(backup_path, test_db_path)

                # Try to open database
                test_conn = sqlite3.connect(test_db_path, timeout=5.0)
                test_conn.row_factory = sqlite3.Row

                # Run integrity check
                result = test_conn.execute("PRAGMA integrity_check").fetchone()
                if result[0] != "ok":
                    test_conn.close()
                    return False, f"Integrity check failed: {result[0]}"

                # Try to read data
                count = test_conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
                users_count = test_conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

                test_conn.close()

                return True, f"✅ Backup verified successfully!\n\nEmployees: {count}\nUsers: {users_count}"

        except Exception as e:
            return False, f"Restore test failed: {e}"

    def restore_from_backup(self, backup_path: str, create_backup_first: bool = True) -> Tuple[bool, str]:
        """
        Restore database from backup file.

        CRITICAL: This will replace the current database!

        Args:
            backup_path: Path to backup file
            create_backup_first: If True, backup current DB before restore

        Returns:
            Tuple of (success, message)
        """
        try:
            # First verify the backup is good
            is_valid, msg = self.test_backup_restore(backup_path)
            if not is_valid:
                return False, f"Backup validation failed:\n{msg}"

            # Create safety backup of current database
            if create_backup_first:
                safety_backup = self.backup_database()
                if not safety_backup:
                    return False, "Could not create safety backup of current database"
                logging.info(f"Safety backup created: {safety_backup}")

            # Close current connection
            self.conn.close()

            # Replace database file
            shutil.copy2(backup_path, DB_FILE)

            # Copy WAL and SHM files if they exist
            for ext in ['-wal', '-shm']:
                backup_extra = backup_path + ext
                if os.path.exists(backup_extra):
                    shutil.copy2(backup_extra, DB_FILE + ext)

            # Reconnect
            self.__init__(DB_FILE)

            return True, "✅ Database restored successfully from backup!"

        except Exception as e:
            logging.error(f"Restore failed: {e}")
            return False, f"Restore failed: {e}"

    def verify_database_integrity(self) -> Tuple[bool, str]:
        """
        Run comprehensive database integrity checks.

        Returns:
            Tuple of (is_healthy, report)
        """
        try:
            issues = []

            # PRAGMA integrity_check
            result = self.conn.execute("PRAGMA integrity_check").fetchone()
            if result[0] != "ok":
                issues.append(f"Integrity check: {result[0]}")

            # Check foreign keys
            fk_errors = self.conn.execute("PRAGMA foreign_key_check").fetchall()
            if fk_errors:
                issues.append(f"Foreign key violations: {len(fk_errors)}")

            # Quick check
            quick = self.conn.execute("PRAGMA quick_check").fetchone()
            if quick[0] != "ok":
                issues.append(f"Quick check: {quick[0]}")

            if issues:
                return False, "⚠️ Database issues found:\n" + "\n".join(issues)
            else:
                stats = self.get_database_stats()
                return True, (
                    f"✅ Database is healthy!\n\n"
                    f"Employees: {stats.get('total_employees', 0)}\n"
                    f"Users: {stats.get('total_users', 0)}\n"
                    f"Size: {stats.get('db_size_mb', 0):.2f} MB"
                )

        except Exception as e:
            return False, f"Integrity check failed: {e}"

    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {}
            stats['total_employees'] = self.conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            stats['active_employees'] = self.conn.execute("SELECT COUNT(*) FROM employees WHERE resign_date IS NULL OR resign_date = ''").fetchone()[0]
            stats['total_users'] = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            stats['total_agencies'] = self.conn.execute("SELECT COUNT(*) FROM agencies").fetchone()[0]

            # Get database file size
            if os.path.exists(DB_FILE):
                stats['db_size_mb'] = os.path.getsize(DB_FILE) / (1024 * 1024)
            else:
                stats['db_size_mb'] = 0

            return stats
        except Exception as e:
            logging.error(f"Failed to get database stats: {e}")
            return {}

    # Agencies
    def get_agencies(self, force_refresh=False):
        """QUICK WIN #4: Get agencies with caching (5-minute TTL) - Thread-safe"""
        import time

        with self._cache_lock:
            # Check cache validity
            if not force_refresh and self._agencies_cache is not None:
                if self._agencies_cache_time and (time.time() - self._agencies_cache_time < self._cache_ttl):
                    return self._agencies_cache

            # Fetch fresh data and update cache
            self._agencies_cache = [r[0] for r in self.conn.execute("SELECT name FROM agencies ORDER BY name").fetchall()]
            self._agencies_cache_time = time.time()
            return self._agencies_cache

    def add_agency(self, name):
        """Add agency and invalidate cache - Thread-safe"""
        self.conn.execute("INSERT OR IGNORE INTO agencies(name) VALUES(?)", (name,))
        # Invalidate cache when data changes
        with self._cache_lock:
            self._agencies_cache = None
            self._agencies_cache_time = None

    # Employees
    def all_employees(self, limit: int = None, offset: int = 0, search: str = None, 
                      filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get employees with optional pagination and filtering.
        
        Args:
            limit: Maximum number of records to return (None = all)
            offset: Number of records to skip
            search: Search term for name/emp_id
            filters: Dict of field:value filters
            
        Returns:
            List of employee dictionaries
        """
        query = "SELECT * FROM employees"
        params = []
        where_clauses = []
        
        # Search filter
        if search:
            where_clauses.append("(name LIKE ? OR emp_id LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Additional filters
        if filters:
            if filters.get('department'):
                where_clauses.append("department = ?")
                params.append(filters['department'])
            if filters.get('agency'):
                where_clauses.append("agency = ?")
                params.append(filters['agency'])
            if filters.get('active_only'):
                where_clauses.append("(resign_date IS NULL OR resign_date = '')")
            if filters.get('resigned_only'):
                where_clauses.append("resign_date IS NOT NULL AND resign_date != ''")
        
        # Build WHERE clause
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Add ORDER BY for consistent pagination
        query += " ORDER BY name ASC"
        
        # Pagination
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]
    
    def count_employees(self, search: str = None, filters: Dict[str, Any] = None) -> int:
        """Get total count of employees matching criteria (for pagination)."""
        query = "SELECT COUNT(*) FROM employees"
        params = []
        where_clauses = []
        
        if search:
            where_clauses.append("(name LIKE ? OR emp_id LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if filters:
            if filters.get('department'):
                where_clauses.append("department = ?")
                params.append(filters['department'])
            if filters.get('agency'):
                where_clauses.append("agency = ?")
                params.append(filters['agency'])
            if filters.get('active_only'):
                where_clauses.append("(resign_date IS NULL OR resign_date = '')")
            if filters.get('resigned_only'):
                where_clauses.append("resign_date IS NOT NULL AND resign_date != ''")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        return self.conn.execute(query, params).fetchone()[0]

    @check_permission('add_employee')
    @retry_on_lock(max_attempts=3, delay=0.5)
    def insert_employee(self, data: Dict[str, Any]) -> None:
        self.conn.execute("""INSERT INTO employees(emp_id,name,email,phone,department,position,hire_date,resign_date,salary,notes,modified,modified_by,contract_expiry,agency,sss_number,emergency_contact_name,emergency_contact_phone,contract_start_date,contract_months,tin_number,pagibig_number,philhealth_number)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (data["emp_id"], data["name"], data.get("email",""), data.get("phone",""),
                           data.get("department",""), data.get("position",""), data["hire_date"], data.get("resign_date"),
                           float(data.get("salary") or 0), data.get("notes",""), data.get("modified",""),
                           data.get("modified_by",""), data.get("contract_expiry",""), data.get("agency"),
                           data.get("sss_number"), data.get("emergency_contact_name"), data.get("emergency_contact_phone"),
                           data.get("contract_start_date"), data.get("contract_months"),
                           data.get("tin_number"), data.get("pagibig_number"), data.get("philhealth_number"))) # <-- ADDED 3 NEW FIELDS
        # Log the action
        self.log_action(
            username=data.get("modified_by", "system"),
            action="ADDED",
            table_name="employees",
            record_id=data["emp_id"],
            details=f"Added employee: {data['name']}"
        )

    @check_permission('edit_employee')
    @retry_on_lock(max_attempts=3, delay=0.5)
    def update_employee(self, emp_id: str, data: Dict[str, Any]) -> None:
        # Get old data for comparison
        old_data = self.conn.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,)).fetchone()

        self.conn.execute("""UPDATE employees SET
                             name=?,email=?,phone=?,department=?,position=?,hire_date=?,resign_date=?,salary=?,notes=?,modified=?,modified_by=?,contract_expiry=?,agency=?,sss_number=?,emergency_contact_name=?,emergency_contact_phone=?,contract_start_date=?,contract_months=?,tin_number=?,pagibig_number=?,philhealth_number=?
                             WHERE emp_id=?""",
                          (data["name"], data.get("email",""), data.get("phone",""), data.get("department",""),
                           data.get("position",""), data["hire_date"], data.get("resign_date"),
                           float(data.get("salary") or 0), data.get("notes",""), data.get("modified",""),
                           data.get("modified_by",""), data.get("contract_expiry",""), data.get("agency"),
                           data.get("sss_number"), data.get("emergency_contact_name"), data.get("emergency_contact_phone"),
                           data.get("contract_start_date"), data.get("contract_months"),
                           data.get("tin_number"), data.get("pagibig_number"), data.get("philhealth_number"), emp_id))

        # Log the action with changed fields
        if old_data:
            # Convert sqlite3.Row to dict properly
            old_dict = {key: old_data[key] for key in old_data.keys()}
            changes = []
            if old_dict.get('name') != data['name']:
                changes.append(f"name: {old_dict.get('name')} → {data['name']}")
            if old_dict.get('department') != data.get('department'):
                changes.append(f"department: {old_dict.get('department')} → {data.get('department')}")
            if old_dict.get('position') != data.get('position'):
                changes.append(f"position: {old_dict.get('position')} → {data.get('position')}")
            # Fix salary comparison to handle None and 0 properly
            old_salary = float(old_dict.get('salary') or 0)
            new_salary = float(data.get('salary') or 0)
            if old_salary != new_salary:
                changes.append(f"salary: ₱{old_salary:.2f} → ₱{new_salary:.2f}")

            details = f"Updated employee: {data['name']}"
            if changes:
                details += " | Changes: " + "; ".join(changes[:5])  # Limit to 5 changes

            self.log_action(
                username=data.get("modified_by", "system"),
                action="EDITED",
                table_name="employees",
                record_id=emp_id,
                details=details
            )

    @check_permission('delete_employee')
    def delete_employees(self, emp_ids: List[str], username: str = "system") -> None:
        # Get employee names before deleting
        names = {}
        for emp_id in emp_ids:
            row = self.conn.execute("SELECT name FROM employees WHERE emp_id=?", (emp_id,)).fetchone()
            if row:
                names[emp_id] = row[0]

        self.conn.executemany("DELETE FROM employees WHERE emp_id=?", [(i,) for i in emp_ids])

        # Log deletions
        for emp_id in emp_ids:
            self.log_action(
                username=username,
                action="DELETED",
                table_name="employees",
                record_id=emp_id,
                details=f"Deleted employee: {names.get(emp_id, 'Unknown')}"
            )
    def employee_exists(self, emp_id): return bool(self.conn.execute("SELECT 1 FROM employees WHERE emp_id=?", (emp_id,)).fetchone())

    def get_employee(self, emp_id):
        """Get employee by ID, returns dict or None"""
        row = self.conn.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def delete_employee_file(self, emp_id: str, filename: str) -> bool:
        """
        Delete file record from employee_files table.

        Args:
            emp_id: Employee ID
            filename: Name of the file to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.conn.execute(
                "DELETE FROM employee_files WHERE emp_id=? AND filename=?",
                (emp_id, filename)
            )
            logging.info(f"Deleted file record: {filename} for employee {emp_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete file record: {e}")
            return False

    # Archive/Restore Methods (Priority #2 - Delete Protection)
    def archive_employee(self, emp_id, username, reason=""):
        """Archive (soft delete) an employee"""
        # Get employee data
        emp = self.conn.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,)).fetchone()
        if not emp:
            return False

        emp_dict = dict(emp)

        # Insert into archived_employees
        self.conn.execute("""
            INSERT INTO archived_employees(
                emp_id, name, email, phone, department, position, hire_date, resign_date,
                salary, notes, modified, modified_by, contract_expiry, agency, sss_number,
                emergency_contact_name, emergency_contact_phone, contract_start_date, contract_months,
                tin_number, pagibig_number, philhealth_number,
                archived_date, archived_by, archive_reason
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            emp_dict.get('emp_id'), emp_dict.get('name'), emp_dict.get('email'), emp_dict.get('phone'),
            emp_dict.get('department'), emp_dict.get('position'), emp_dict.get('hire_date'),
            emp_dict.get('resign_date'), emp_dict.get('salary'), emp_dict.get('notes'),
            emp_dict.get('modified'), emp_dict.get('modified_by'), emp_dict.get('contract_expiry'),
            emp_dict.get('agency'), emp_dict.get('sss_number'), emp_dict.get('emergency_contact_name'),
            emp_dict.get('emergency_contact_phone'), emp_dict.get('contract_start_date'),
            emp_dict.get('contract_months'), emp_dict.get('tin_number'), emp_dict.get('pagibig_number'),
            emp_dict.get('philhealth_number'),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, reason
        ))

        # Delete from active employees
        self.conn.execute("DELETE FROM employees WHERE emp_id=?", (emp_id,))

        # Log the action
        self.log_action(
            username=username,
            action="ARCHIVED",
            table_name="employees",
            record_id=emp_id,
            details=f"Archived employee: {emp_dict.get('name')} - Reason: {reason or 'None specified'}"
        )

        return True

    def restore_employee(self, emp_id, username):
        """Restore an archived employee"""
        # Get archived employee data
        emp = self.conn.execute("SELECT * FROM archived_employees WHERE emp_id=?", (emp_id,)).fetchone()
        if not emp:
            return False

        emp_dict = dict(emp)

        # Insert back into employees
        self.conn.execute("""
            INSERT INTO employees(
                emp_id, name, email, phone, department, position, hire_date, resign_date,
                salary, notes, modified, modified_by, contract_expiry, agency, sss_number,
                emergency_contact_name, emergency_contact_phone, contract_start_date, contract_months,
                tin_number, pagibig_number, philhealth_number
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            emp_dict.get('emp_id'), emp_dict.get('name'), emp_dict.get('email'), emp_dict.get('phone'),
            emp_dict.get('department'), emp_dict.get('position'), emp_dict.get('hire_date'),
            emp_dict.get('resign_date'), emp_dict.get('salary'), emp_dict.get('notes'),
            datetime.now().strftime("%m-%d-%Y %H:%M"), username,
            emp_dict.get('contract_expiry'), emp_dict.get('agency'), emp_dict.get('sss_number'),
            emp_dict.get('emergency_contact_name'), emp_dict.get('emergency_contact_phone'),
            emp_dict.get('contract_start_date'), emp_dict.get('contract_months'),
            emp_dict.get('tin_number'), emp_dict.get('pagibig_number'), emp_dict.get('philhealth_number') # <-- ADDED 3 NEW FIELDS
        ))

        # Delete from archive
        self.conn.execute("DELETE FROM archived_employees WHERE emp_id=?", (emp_id,))

        # Log the action
        self.log_action(
            username=username,
            action="RESTORED",
            table_name="employees",
            record_id=emp_id,
            details=f"Restored employee: {emp_dict.get('name')}"
        )

        return True

    def get_archived_employees(self):
        """Get all archived employees"""
        return [dict(r) for r in self.conn.execute("SELECT * FROM archived_employees ORDER BY archived_date DESC").fetchall()]

    def permanently_delete_archived(self, emp_id, username):
        """Permanently delete an archived employee"""
        emp = self.conn.execute("SELECT name FROM archived_employees WHERE emp_id=?", (emp_id,)).fetchone()
        if emp:
            name = emp[0]
            self.conn.execute("DELETE FROM archived_employees WHERE emp_id=?", (emp_id,))
            self.log_action(
                username=username,
                action="PERMANENTLY_DELETED",
                table_name="archived_employees",
                record_id=emp_id,
                details=f"Permanently deleted archived employee: {name}"
            )
            return True
        return False

    # Audit Trail Methods
    def log_action(self, username, action, table_name=None, record_id=None, old_value=None, new_value=None, details=None):
        """Log user action to audit trail"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("""
            INSERT INTO audit_log(timestamp, username, action, table_name, record_id, old_value, new_value, details)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, username, action, table_name, record_id, old_value, new_value, details))

    def get_audit_log(self, limit=100, username=None, action=None, record_id=None):
        """Get audit log entries with optional filters"""
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if username:
            query += " AND username = ?"
            params.append(username)
        if action:
            query += " AND action = ?"
            params.append(action)
        if record_id:
            query += " AND record_id = ?"
            params.append(record_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return [self.row_to_dict(row) for row in self.conn.execute(query, params).fetchall()]

    def get_employee_history(self, emp_id):
        """Get complete history for an employee"""
        return [self.row_to_dict(row) for row in self.conn.execute(
            "SELECT * FROM audit_log WHERE record_id = ? ORDER BY timestamp DESC",
            (emp_id,)
        ).fetchall()]

    # Security Audit Methods with Tamper Detection
    def _get_computer_name(self) -> str:
        """Get the current computer name"""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    def _get_last_security_hash(self) -> Optional[str]:
        """Get the hash of the last security audit entry"""
        row = self.conn.execute(
            "SELECT entry_hash FROM security_audit ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    def _compute_entry_hash(self, timestamp: str, event_type: str, username: Optional[str],
                            details: Optional[str], previous_hash: Optional[str]) -> str:
        """Compute SHA-256 hash for audit entry (hash chain for tamper detection)"""
        data = f"{timestamp}|{event_type}|{username or ''}|{details or ''}|{previous_hash or 'GENESIS'}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def log_security_event(self, event_type: str, username: Optional[str] = None,
                           details: Optional[str] = None, severity: str = "INFO",
                           ip_address: Optional[str] = None) -> bool:
        """
        Log a security event with tamper detection using hash chain.
        
        Args:
            event_type: Type of event (LOGIN_SUCCESS, LOGIN_FAILED, PIN_RESET, etc.)
            username: Username associated with the event
            details: Additional details about the event
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            ip_address: IP address of the user
        
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            computer_name = self._get_computer_name()
            previous_hash = self._get_last_security_hash()
            entry_hash = self._compute_entry_hash(timestamp, event_type, username, details, previous_hash)
            
            self.conn.execute("""
                INSERT INTO security_audit(timestamp, event_type, username, ip_address, 
                                          computer_name, details, severity, previous_hash, entry_hash)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, event_type, username, ip_address, computer_name, 
                  details, severity, previous_hash, entry_hash))
            self.conn.commit()
            logging.debug(f"Security event logged: {event_type} by {username}")
            return True
        except Exception as e:
            logging.error(f"Failed to log security event: {e}")
            return False

    def verify_security_audit_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the security audit log using hash chain.
        
        Returns:
            Dict with 'valid' boolean and 'details' with any issues found
        """
        try:
            rows = self.conn.execute(
                "SELECT id, timestamp, event_type, username, details, previous_hash, entry_hash "
                "FROM security_audit ORDER BY id ASC"
            ).fetchall()
            
            if not rows:
                return {"valid": True, "details": "Audit log is empty"}
            
            issues = []
            expected_previous = None
            
            for row in rows:
                row_id, timestamp, event_type, username, details, previous_hash, entry_hash = row
                
                # Check if previous_hash matches expected
                if expected_previous is not None and previous_hash != expected_previous:
                    issues.append(f"Entry {row_id}: Previous hash mismatch (chain broken)")
                
                # Recompute hash and verify
                computed_hash = self._compute_entry_hash(timestamp, event_type, username, details, previous_hash)
                if computed_hash != entry_hash:
                    issues.append(f"Entry {row_id}: Hash verification failed (entry tampered)")
                
                expected_previous = entry_hash
            
            return {
                "valid": len(issues) == 0,
                "total_entries": len(rows),
                "details": "Audit log integrity verified" if not issues else issues
            }
        except Exception as e:
            return {"valid": False, "details": f"Verification error: {e}"}

    def get_security_audit(self, limit: int = 100, event_type: Optional[str] = None,
                          username: Optional[str] = None, severity: Optional[str] = None,
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        Get security audit entries with optional filters.
        
        Args:
            limit: Maximum number of entries to return
            event_type: Filter by event type
            username: Filter by username
            severity: Filter by severity level
            start_date: Filter entries after this date (YYYY-MM-DD)
            end_date: Filter entries before this date (YYYY-MM-DD)
        
        Returns:
            List of audit entries as dictionaries
        """
        query = "SELECT * FROM security_audit WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if username:
            query += " AND username = ?"
            params.append(username)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date + " 23:59:59")
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        return [self.row_to_dict(row) for row in self.conn.execute(query, params).fetchall()]

    # Settings Methods
    def get_setting(self, key, default=None):
        """Get a setting value"""
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        """Set a setting value"""
        self.conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, value))

    def set_force_close(self, requested_by: str, message: str = ""):
        """Admin triggers force close for all users (for updates)"""
        data = json.dumps({
            'active': True,
            'requested_by': requested_by,
            'message': message or 'Application update in progress. Please restart.',
            'timestamp': datetime.now().isoformat()
        })
        self.conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", ('force_close', data))
        self.conn.commit()
        logging.info(f"Force close requested by {requested_by}")

    def clear_force_close(self):
        """Clear the force close flag after update is complete"""
        self.conn.execute("DELETE FROM settings WHERE key = ?", ('force_close',))
        self.conn.commit()
        logging.info("Force close flag cleared")

    def check_force_close(self) -> dict:
        """Check if force close is active. Returns dict with status or None"""
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", ('force_close',)).fetchone()
        if row and row[0]:
            try:
                data = json.loads(row[0])
                if data.get('active'):
                    return data
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    # Login Throttling Methods
    def record_login_attempt(self, username: str, success: bool, ip_address: str = None):
        """Record a login attempt for throttling"""
        timestamp = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO login_attempts(username, attempt_time, success, ip_address)
            VALUES(?, ?, ?, ?)
        """, (username, timestamp, 1 if success else 0, ip_address))
        self.conn.commit()

    def get_recent_failed_attempts(self, username: str, minutes: int = 15) -> int:
        """Get count of failed login attempts in last N minutes"""
        from datetime import timedelta
        cutoff_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        result = self.conn.execute("""
            SELECT COUNT(*) FROM login_attempts
            WHERE username = ? 
            AND success = 0 
            AND attempt_time > ?
        """, (username, cutoff_time)).fetchone()
        
        return result[0] if result else 0

    def get_last_failed_attempt_time(self, username: str):
        """Get timestamp of last failed login attempt"""
        result = self.conn.execute("""
            SELECT attempt_time FROM login_attempts
            WHERE username = ? AND success = 0
            ORDER BY attempt_time DESC
            LIMIT 1
        """, (username,)).fetchone()
        
        if result:
            try:
                return datetime.fromisoformat(result[0])
            except:
                return None
        return None

    def is_account_locked(self, username: str, max_attempts: int = 5, lockout_minutes: int = 15) -> Tuple[bool, int]:
        """
        Check if account is locked due to too many failed attempts
        
        Returns:
            Tuple[bool, int]: (is_locked, remaining_lockout_seconds)
        """
        failed_count = self.get_recent_failed_attempts(username, lockout_minutes)
        
        if failed_count >= max_attempts:
            last_attempt_time = self.get_last_failed_attempt_time(username)
            if last_attempt_time:
                from datetime import timedelta
                lockout_end = last_attempt_time + timedelta(minutes=lockout_minutes)
                now = datetime.now()
                
                if now < lockout_end:
                    remaining_seconds = int((lockout_end - now).total_seconds())
                    return (True, remaining_seconds)
        
        return (False, 0)

    def auto_reset_pin_on_lockout(self, username: str, max_attempts: int = 5) -> bool:
        """
        Auto-reset PIN when max failed attempts is reached.
        Instead of locking the account, reset the PIN so user can set a new one.
        
        Args:
            username: Username to check and reset
            max_attempts: Number of failed attempts before reset
            
        Returns:
            True if PIN was reset, False otherwise
        """
        failed_count = self.get_recent_failed_attempts(username, minutes=60)  # Check last hour
        
        if failed_count >= max_attempts:
            try:
                # Clear the PIN to force user to set a new one
                self.conn.execute("""
                    UPDATE users SET pin = NULL, pin_change_required = 1
                    WHERE username = ?
                """, (username,))
                self.conn.commit()
                
                # Clear the failed attempts
                self.clear_login_attempts(username)
                
                logging.info(f"PIN auto-reset for user {username} after {failed_count} failed attempts")
                return True
            except Exception as e:
                logging.error(f"Failed to auto-reset PIN for {username}: {e}")
                return False
        
        return False

    def clear_login_attempts(self, username: str):
        """Clear failed login attempts for a user (after successful login)"""
        import time
        max_retries = 5
        retry_delay = 0.1  # Start with 100ms
        
        for attempt in range(max_retries):
            try:
                self.conn.execute("""
                    DELETE FROM login_attempts
                    WHERE username = ? AND success = 0
                """, (username,))
                self.conn.commit()
                return  # Success, exit
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    logging.warning(f"Database locked, retry {attempt + 1}/{max_retries} in {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logging.error(f"Failed to clear login attempts after {max_retries} retries: {e}")
                    # Non-critical operation, just log and continue
                    return

    def cleanup_old_login_attempts(self, days: int = 30):
        """Clean up old login attempts older than N days"""
        from datetime import timedelta
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        self.conn.execute("""
            DELETE FROM login_attempts
            WHERE attempt_time < ?
        """, (cutoff_time,))
        self.conn.commit()

    def next_sequence(self):
        used = set()
        for (emp_id,) in self.conn.execute("SELECT emp_id FROM employees").fetchall():
            m = re.match(r"^[A-Z]-([0-9]{3})-(\d{2}|\d{4})$", emp_id or "")
            if m:
                used.add(int(m.group(1)))
        n = 1
        while n in used:
            n += 1
        return n


def migrate_employee_files_structure():
    """
    Migrate employee files from old structure to new structure:
    
    OLD:
        employee_files/{emp_id}/... (all files mixed)
        employee_photos/{emp_id}.png (single photo)
    
    NEW:
        employee_files/{emp_id}/
            photos/   (all photos including migrated profile photo)
            files/    (all documents)
    
    This function should be called once at startup to migrate existing files.
    """
    import os
    import shutil
    from employee_vault.config import FILES_DIR, PHOTOS_DIR, get_employee_folder
    
    migrated_count = 0
    
    # 1. Migrate files from old flat structure to new subfolders
    if os.path.exists(FILES_DIR):
        for emp_id in os.listdir(FILES_DIR):
            emp_folder = os.path.join(FILES_DIR, emp_id)
            
            # Skip if not a directory or already has new structure
            if not os.path.isdir(emp_folder):
                continue
            
            # Check if already migrated (has photos/ and files/ subdirs)
            photos_subfolder = os.path.join(emp_folder, 'photos')
            files_subfolder = os.path.join(emp_folder, 'files')
            
            if os.path.exists(photos_subfolder) and os.path.exists(files_subfolder):
                continue  # Already migrated
            
            # Create new structure
            os.makedirs(photos_subfolder, exist_ok=True)
            os.makedirs(files_subfolder, exist_ok=True)
            
            # Move existing files to appropriate subfolders
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
            
            for filename in os.listdir(emp_folder):
                file_path = os.path.join(emp_folder, filename)
                
                # Skip subdirectories we just created
                if os.path.isdir(file_path):
                    continue
                
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in image_extensions:
                    # Move to photos subfolder
                    dest_path = os.path.join(photos_subfolder, filename)
                    if not os.path.exists(dest_path):
                        shutil.move(file_path, dest_path)
                        logging.info(f"Migrated photo: {filename} -> photos/")
                        migrated_count += 1
                else:
                    # Move to files subfolder
                    dest_path = os.path.join(files_subfolder, filename)
                    if not os.path.exists(dest_path):
                        shutil.move(file_path, dest_path)
                        logging.info(f"Migrated file: {filename} -> files/")
                        migrated_count += 1
    
    # 2. Migrate photos from legacy employee_photos/ folder
    if os.path.exists(PHOTOS_DIR):
        for filename in os.listdir(PHOTOS_DIR):
            photo_path = os.path.join(PHOTOS_DIR, filename)
            
            if not os.path.isfile(photo_path):
                continue
            
            # Extract emp_id from filename (e.g., "O-001-24.png" -> "O-001-24")
            emp_id = os.path.splitext(filename)[0]
            
            try:
                # Get or create new photos folder
                photos_folder = get_employee_folder(emp_id, 'photos')
                
                # Copy photo to new location (keep original for safety)
                dest_path = os.path.join(photos_folder, f"profile_{filename}")
                if not os.path.exists(dest_path):
                    shutil.copy2(photo_path, dest_path)
                    logging.info(f"Migrated legacy photo: {filename} -> {emp_id}/photos/")
                    migrated_count += 1
            except ValueError:
                # Invalid emp_id, skip
                logging.warning(f"Skipped invalid legacy photo: {filename}")
                continue
    
    if migrated_count > 0:
        logging.info(f"File structure migration complete: {migrated_count} files migrated")
    
    return migrated_count