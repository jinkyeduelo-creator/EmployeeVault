"""
Modern UI Helper Functions
v4.5.0: Utilities to apply demo-style effects to main program
v4.6.0: Added toast notification queuing system
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from employee_vault.ui.widgets import GlassToast
from typing import List, Tuple
from collections import deque

# Toast queue system - prevents overlapping toasts
_toast_queue: deque = deque()
_current_toast = None
_toast_timer = None
_TOAST_GAP = 300  # ms gap between toasts


def _process_toast_queue():
    """Process the next toast in queue"""
    global _current_toast, _toast_timer
    
    if _toast_queue:
        message, toast_type, parent, duration = _toast_queue.popleft()
        _current_toast = GlassToast(message, toast_type=toast_type, parent=parent, duration=duration)
        
        # Schedule next toast after this one finishes
        if _toast_timer is None:
            _toast_timer = QTimer()
            _toast_timer.setSingleShot(True)
            _toast_timer.timeout.connect(_process_toast_queue)
        _toast_timer.start(duration + _TOAST_GAP)
    else:
        _current_toast = None


def _queue_toast(message: str, toast_type: str, parent: QWidget, duration: int):
    """Add toast to queue and process if not busy"""
    global _current_toast
    
    _toast_queue.append((message, toast_type, parent, duration))
    
    # If no toast is currently showing, start processing
    if _current_toast is None:
        _process_toast_queue()


def show_success_toast(parent: QWidget, message: str, duration: int = 3000):
    """
    Show a success toast notification (green checkmark)
    Replacement for QMessageBox.information()

    Args:
        parent: Parent widget
        message: Success message to display
        duration: How long to show (milliseconds)
    """
    _queue_toast(message, "success", parent, duration)


def show_error_toast(parent: QWidget, message: str, duration: int = 4000):
    """
    Show an error toast notification (red X)
    Replacement for QMessageBox.critical()

    Args:
        parent: Parent widget
        message: Error message to display
        duration: How long to show (milliseconds)
    """
    _queue_toast(message, "error", parent, duration)


def show_warning_toast(parent: QWidget, message: str, duration: int = 3500):
    """
    Show a warning toast notification (yellow warning)
    Replacement for QMessageBox.warning()

    Args:
        parent: Parent widget
        message: Warning message to display
        duration: How long to show (milliseconds)
    """
    _queue_toast(message, "warning", parent, duration)


def show_info_toast(parent: QWidget, message: str, duration: int = 3000):
    """
    Show an info toast notification (blue i)
    Replacement for simple information messages

    Args:
        parent: Parent widget
        message: Info message to display
        duration: How long to show (milliseconds)
    """
    _queue_toast(message, "info", parent, duration)


# ============================================================
# Error Boundary Decorator
# ============================================================

import functools
import logging
import traceback


def error_boundary(fallback_value=None, show_toast=True, log_error=True):
    """
    Decorator to wrap functions with error handling (error boundary pattern).
    
    Catches exceptions, logs them, optionally shows toast, and returns fallback.
    
    Args:
        fallback_value: Value to return if exception occurs
        show_toast: Whether to show error toast to user
        log_error: Whether to log the error
    
    Usage:
        @error_boundary(fallback_value=[], show_toast=True)
        def load_data(self):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logging.error(f"Error in {func.__name__}: {e}")
                    logging.debug(traceback.format_exc())
                
                if show_toast:
                    # Try to find parent widget from args
                    parent = None
                    if args and hasattr(args[0], 'window'):
                        try:
                            parent = args[0].window()
                        except:
                            parent = args[0] if isinstance(args[0], QWidget) else None
                    
                    if parent:
                        try:
                            _queue_toast(f"Error: {str(e)[:50]}...", "error", parent, 4000)
                        except:
                            pass  # Silently fail if toast can't be shown
                
                return fallback_value
        return wrapper
    return decorator


def safe_execute(func, *args, fallback=None, parent=None, **kwargs):
    """
    Execute a function safely with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to function
        fallback: Value to return on error
        parent: Parent widget for toast notifications
        **kwargs: Keyword arguments to pass to function
    
    Returns:
        Function result or fallback value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error in {func.__name__ if hasattr(func, '__name__') else 'anonymous'}: {e}")
        if parent:
            try:
                _queue_toast(f"Error: {str(e)[:50]}", "error", parent, 4000)
            except:
                pass
        return fallback
