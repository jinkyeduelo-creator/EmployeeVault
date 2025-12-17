"""Email Validator"""

import re
from typing import Tuple

# Email regex pattern
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class EmailValidator:
    """Enhanced email validation"""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email:
            return True, ""  # Empty is okay

        if not EMAIL_RE.match(email):
            return False, "Invalid email format (e.g., name@example.com)"

        # Check for common typos
        domain = email.split('@')[1].lower()

        # Check for common typos
        typo_suggestions = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'yahooo.com': 'yahoo.com',
            'yaho.com': 'yahoo.com',
            'outlok.com': 'outlook.com',
            'hotmial.com': 'hotmail.com'
        }

        if domain in typo_suggestions:
            return False, f"Did you mean '@{typo_suggestions[domain]}'?"

        return True, ""
