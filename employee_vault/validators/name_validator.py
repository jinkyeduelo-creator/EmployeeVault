"""Name Validator"""

import re
from typing import Tuple


class NameValidator:
    """Name validation"""

    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> Tuple[bool, str]:
        """Validate name field"""
        if not name or not name.strip():
            return False, f"{field_name} is required"

        name = name.strip()

        if len(name) < 2:
            return False, f"{field_name} is too short (minimum 2 characters)"

        if len(name) > 100:
            return False, f"{field_name} is too long (maximum 100 characters)"

        # Check for invalid characters (allow letters, spaces, hyphens, apostrophes, periods)
        if not re.match(r"^[A-Za-z\s\-'\.]+$", name):
            return False, f"{field_name} should contain only letters, spaces, hyphens, and apostrophes"

        # Check for excessive spaces
        if '  ' in name:
            return False, f"{field_name} contains excessive spaces"

        return True, ""
