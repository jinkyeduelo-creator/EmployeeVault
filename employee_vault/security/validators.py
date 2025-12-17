"""
Security Validation Framework for Employee Vault
2025 Security Best Practices - Input Validation
"""

import os
import re
from typing import Tuple, Optional
import logging


class SecurityValidator:
    """
    Centralized input validation for security-sensitive operations.
    Prevents injection attacks, path traversal, and DoS.
    """
    
    # Size limits
    MAX_USERNAME_LENGTH = 64
    MAX_PASSWORD_LENGTH = 128
    MAX_EMPLOYEE_ID_LENGTH = 32
    MAX_NAME_LENGTH = 128
    MAX_EMAIL_LENGTH = 254
    MAX_PHONE_LENGTH = 20
    MAX_PATH_LENGTH = 260  # Windows MAX_PATH
    MAX_NOTES_LENGTH = 5000
    MAX_FILE_SIZE_MB = 10
    
    # Allowed patterns
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')
    EMPLOYEE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]+$')
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"('|\")\s*(OR|AND)\s*('|\")?",
        r";\s*(DROP|DELETE|UPDATE|INSERT|EXEC|EXECUTE)",
        r"--\s*$",
        r"/\*.*\*/",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",
        r"\.\.\\",
        r"\.\./",
        r"%2e%2e",
        r"%252e%252e",
    ]
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username for security.
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        if len(username) > SecurityValidator.MAX_USERNAME_LENGTH:
            return False, f"Username must be at most {SecurityValidator.MAX_USERNAME_LENGTH} characters"
        
        if not SecurityValidator.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, ""
    
    @staticmethod
    def validate_employee_id(emp_id: str) -> Tuple[bool, str]:
        """
        Validate employee ID for security.
        
        Args:
            emp_id: Employee ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not emp_id:
            return False, "Employee ID is required"
        
        if len(emp_id) > SecurityValidator.MAX_EMPLOYEE_ID_LENGTH:
            return False, f"Employee ID must be at most {SecurityValidator.MAX_EMPLOYEE_ID_LENGTH} characters"
        
        if not SecurityValidator.EMPLOYEE_ID_PATTERN.match(emp_id):
            return False, "Employee ID contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email address.
        
        Args:
            email: Email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return True, ""  # Email is optional
        
        if len(email) > SecurityValidator.MAX_EMAIL_LENGTH:
            return False, f"Email must be at most {SecurityValidator.MAX_EMAIL_LENGTH} characters"
        
        if not SecurityValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """
        Validate phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return True, ""  # Phone is optional
        
        if len(phone) > SecurityValidator.MAX_PHONE_LENGTH:
            return False, f"Phone must be at most {SecurityValidator.MAX_PHONE_LENGTH} characters"
        
        if not SecurityValidator.PHONE_PATTERN.match(phone):
            return False, "Phone contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_file_path(path: str, allowed_base: str) -> Tuple[bool, str]:
        """
        Validate file path against directory traversal.
        
        Args:
            path: File path to validate
            allowed_base: Base directory that files must be within
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path:
            return False, "Path is required"
        
        # Check for path traversal patterns
        for pattern in SecurityValidator.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                logging.warning(f"Path traversal attempt detected: {path}")
                return False, "Invalid path - potential security risk"
        
        # Resolve to absolute paths
        try:
            abs_path = os.path.abspath(path)
            abs_base = os.path.abspath(allowed_base)
            
            # Check if path is within allowed directory
            if not abs_path.startswith(abs_base):
                logging.warning(f"Path outside allowed directory: {abs_path} not in {abs_base}")
                return False, "Path is outside allowed directory"
            
            # Check length
            if len(abs_path) > SecurityValidator.MAX_PATH_LENGTH:
                return False, "Path is too long"
                
        except Exception as e:
            logging.error(f"Path validation error: {e}")
            return False, "Invalid path format"
        
        return True, ""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to remove dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        if not filename:
            return "unnamed"
        
        # Remove path separators and dangerous characters
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        safe = safe.strip('. ')
        
        # Limit length
        if len(safe) > 255:
            # Keep extension if present
            name, ext = os.path.splitext(safe)
            max_name_len = 255 - len(ext)
            safe = name[:max_name_len] + ext
        
        return safe or "unnamed"
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """
        Validate person name.
        
        Args:
            name: Name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Name is required"
        
        if len(name) > SecurityValidator.MAX_NAME_LENGTH:
            return False, f"Name must be at most {SecurityValidator.MAX_NAME_LENGTH} characters"
        
        # Check for SQL injection patterns
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                logging.warning(f"Potential SQL injection in name: {name}")
                return False, "Name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_notes(notes: str) -> Tuple[bool, str]:
        """
        Validate notes/text field.
        
        Args:
            notes: Notes text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not notes:
            return True, ""  # Notes are optional
        
        if len(notes) > SecurityValidator.MAX_NOTES_LENGTH:
            return False, f"Notes must be at most {SecurityValidator.MAX_NOTES_LENGTH} characters"
        
        return True, ""
    
    @staticmethod
    def validate_file_upload(file_path: str, max_size_mb: float = None) -> Tuple[bool, str]:
        """
        Validate file for upload.
        
        Args:
            file_path: Path to file being uploaded
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path or not os.path.exists(file_path):
            return False, "File not found"
        
        max_size = (max_size_mb or SecurityValidator.MAX_FILE_SIZE_MB) * 1024 * 1024
        
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return False, f"File too large (max {max_size_mb or SecurityValidator.MAX_FILE_SIZE_MB}MB)"
        except Exception as e:
            return False, f"Could not check file size: {e}"
        
        return True, ""
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Sanitize input for use in SQL (though parameterized queries should be used).
        This is a backup defense layer.
        
        Args:
            value: Input value to sanitize
            
        Returns:
            Sanitized value
        """
        if not value:
            return ""
        
        # Remove common SQL injection characters
        sanitized = value.replace("'", "''")  # Escape single quotes
        sanitized = re.sub(r'[;\-\-]', '', sanitized)  # Remove semicolons and comment markers
        
        return sanitized


# Convenience functions for common validations
def validate_input(input_type: str, value: str, **kwargs) -> Tuple[bool, str]:
    """
    Convenience function for input validation.
    
    Args:
        input_type: Type of input ('username', 'email', 'phone', 'name', 'employee_id', 'notes')
        value: Value to validate
        **kwargs: Additional arguments for specific validators
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validators = {
        'username': SecurityValidator.validate_username,
        'email': SecurityValidator.validate_email,
        'phone': SecurityValidator.validate_phone,
        'name': SecurityValidator.validate_name,
        'employee_id': SecurityValidator.validate_employee_id,
        'notes': SecurityValidator.validate_notes,
    }
    
    validator = validators.get(input_type)
    if not validator:
        return False, f"Unknown input type: {input_type}"
    
    return validator(value)
