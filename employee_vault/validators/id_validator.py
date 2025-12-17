"""Philippine Government ID Validator"""

import re
from typing import Tuple


class PhilippineIDValidator:
    """Validates Philippine government ID formats"""

    @staticmethod
    def validate_sss(sss_number: str) -> Tuple[bool, str]:
        """Validate SSS number format: XX-XXXXXXX-X"""
        if not sss_number:
            return True, ""  # Empty is okay

        # Remove spaces and dashes for checking
        clean = re.sub(r'[\s-]', '', sss_number)

        if not clean.isdigit():
            return False, "SSS number should contain only digits"

        if len(clean) != 10:
            return False, "SSS number should be 10 digits (XX-XXXXXXX-X)"

        # Format check with dashes
        if not re.match(r'^\d{2}-\d{7}-\d{1}$', sss_number):
            return False, "Format should be XX-XXXXXXX-X (e.g., 34-1234567-8)"

        return True, ""

    @staticmethod
    def validate_tin(tin_number: str) -> Tuple[bool, str]:
        """Validate TIN number format: XXX-XXX-XXX or XXX-XXX-XXX-XXX"""
        if not tin_number:
            return True, ""  # Empty is okay

        # Remove spaces and dashes
        clean = re.sub(r'[\s-]', '', tin_number)

        if not clean.isdigit():
            return False, "TIN should contain only digits"

        if len(clean) not in [9, 12]:
            return False, "TIN should be 9 or 12 digits"

        # Format check
        if len(clean) == 12:
            if not re.match(r'^\d{3}-\d{3}-\d{3}-\d{3}$', tin_number):
                return False, "Format should be XXX-XXX-XXX-XXX (e.g., 123-456-789-000)"
        elif len(clean) == 9:
            if not re.match(r'^\d{3}-\d{3}-\d{3}$', tin_number):
                return False, "Format should be XXX-XXX-XXX (e.g., 123-456-789)"

        return True, ""

    @staticmethod
    def validate_philhealth(philhealth_number: str) -> Tuple[bool, str]:
        """Validate PhilHealth number format: XX-XXXXXXXXX-X"""
        if not philhealth_number:
            return True, ""  # Empty is okay

        # Remove spaces and dashes
        clean = re.sub(r'[\s-]', '', philhealth_number)

        if not clean.isdigit():
            return False, "PhilHealth number should contain only digits"

        if len(clean) != 12:
            return False, "PhilHealth number should be 12 digits"

        # Format check
        if not re.match(r'^\d{2}-\d{9}-\d{1}$', philhealth_number):
            return False, "Format should be XX-XXXXXXXXX-X (e.g., 12-345678901-2)"

        return True, ""

    @staticmethod
    def validate_pagibig(pagibig_number: str) -> Tuple[bool, str]:
        """Validate Pag-IBIG number format: XXXX-XXXX-XXXX"""
        if not pagibig_number:
            return True, ""  # Empty is okay

        # Remove spaces and dashes
        clean = re.sub(r'[\s-]', '', pagibig_number)

        if not clean.isdigit():
            return False, "Pag-IBIG number should contain only digits"

        if len(clean) != 12:
            return False, "Pag-IBIG number should be 12 digits"

        # Format check
        if not re.match(r'^\d{4}-\d{4}-\d{4}$', pagibig_number):
            return False, "Format should be XXXX-XXXX-XXXX (e.g., 1234-5678-9012)"

        return True, ""

    @staticmethod
    def auto_format_sss(text: str) -> str:
        """Auto-format SSS number as user types"""
        clean = re.sub(r'[^\d]', '', text)
        if len(clean) <= 2:
            return clean
        elif len(clean) <= 9:
            return f"{clean[:2]}-{clean[2:]}"
        else:
            return f"{clean[:2]}-{clean[2:9]}-{clean[9:10]}"

    @staticmethod
    def auto_format_tin(text: str) -> str:
        """Auto-format TIN number as user types"""
        clean = re.sub(r'[^\d]', '', text)
        if len(clean) <= 3:
            return clean
        elif len(clean) <= 6:
            return f"{clean[:3]}-{clean[3:]}"
        elif len(clean) <= 9:
            return f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
        else:
            return f"{clean[:3]}-{clean[3:6]}-{clean[6:9]}-{clean[9:12]}"

    @staticmethod
    def auto_format_philhealth(text: str) -> str:
        """Auto-format PhilHealth number as user types"""
        clean = re.sub(r'[^\d]', '', text)
        if len(clean) <= 2:
            return clean
        elif len(clean) <= 11:
            return f"{clean[:2]}-{clean[2:]}"
        else:
            return f"{clean[:2]}-{clean[2:11]}-{clean[11:12]}"

    @staticmethod
    def auto_format_pagibig(text: str) -> str:
        """Auto-format Pag-IBIG number as user types"""
        clean = re.sub(r'[^\d]', '', text)
        if len(clean) <= 4:
            return clean
        elif len(clean) <= 8:
            return f"{clean[:4]}-{clean[4:]}"
        else:
            return f"{clean[:4]}-{clean[4:8]}-{clean[8:12]}"
