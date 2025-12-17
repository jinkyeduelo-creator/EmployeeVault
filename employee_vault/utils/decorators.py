"""
Database decorators for retry logic and permission checking
"""

import time
import logging
import sqlite3
from functools import wraps


def retry_on_lock(max_attempts=3, delay=0.5):
    """
    Retry database operations if database is locked.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Base delay between retries (exponential backoff)

    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_error = e
                    if "locked" in str(e).lower() and attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logging.warning(f"Database locked, retrying in {wait_time}s... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(wait_time)
                        continue
                    # PHASE 2 FIX: Better error message for database locks
                    elif "locked" in str(e).lower():
                        # Final attempt failed
                        logging.error(f"Database remains locked after {max_attempts} attempts")
                        raise sqlite3.OperationalError(
                            f"Database is busy - another user is currently saving data.\n\n"
                            f"Please wait a moment and try again.\n\n"
                            f"If this persists, contact your system administrator.\n\n"
                            f"Technical details: {str(e)}"
                        ) from e
                    raise
            # Should never reach here, but raise last error if we do
            if last_error:
                raise last_error
        return wrapper
    return decorator


def check_permission(permission_key: str):
    """
    Decorator to enforce permissions at database layer (defense in depth).

    CRITICAL SECURITY: Never trust UI-only checks - always validate at DB layer

    Usage:
        @check_permission('edit_employee')
        def update_employee(self, emp_id, data, username):
            ...

    Args:
        permission_key: Permission to check ('add_employee', 'edit_employee', etc.)

    Returns:
        Decorated function that checks permissions before execution
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get username from kwargs or find in args
            username = kwargs.get('username') or kwargs.get('modified_by')

            if not username:
                # Try to find username in data dict - check first arg after self
                if len(args) > 0 and isinstance(args[0], dict):
                    username = args[0].get('modified_by') or args[0].get('username')
                # Also check second arg (for methods with emp_id as first param)
                elif len(args) > 1 and isinstance(args[1], dict):
                    username = args[1].get('modified_by') or args[1].get('username')

            if not username:
                logging.error(f"Permission check failed: No user context for {func.__name__}")
                raise PermissionError("No user context for permission check")

            # Get user info
            try:
                user = self.get_user(username)
            except:
                logging.error(f"Permission check failed: User {username} not found")
                raise PermissionError(f"User {username} not found")

            # Admin bypass
            # Convert Row to dict if needed
            if user:
                if hasattr(user, 'keys'):  # It's a Row object
                    user_dict = {key: user[key] for key in user.keys()}
                else:
                    user_dict = user

                if user_dict.get('role') == 'admin':
                    return func(self, *args, **kwargs)
            else:
                logging.error(f"Permission check failed: User object is None")
                raise PermissionError("User not found")

            # Check specific permission
            try:
                perms = self.get_user_permissions(username)
            except:
                perms = {}

            if not perms.get(permission_key, False):
                logging.warning(f"SECURITY: Permission denied - {username} attempted {permission_key} via {func.__name__}")
                raise PermissionError(f"User '{username}' lacks permission: {permission_key}")

            return func(self, *args, **kwargs)
        return wrapper
    return decorator
