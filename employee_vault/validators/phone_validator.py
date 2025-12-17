"""Phone Number Validator"""

import re
from typing import Tuple


class PhoneValidator:
    """Validates phone numbers with international support"""

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate phone number (Philippine and international formats)"""
        if not phone:
            return True, ""  # Empty is okay

        # Remove common separators
        clean = re.sub(r'[\s\-\(\)\.]+', '', phone)

        # Check if it contains only digits and optional + at start
        if not re.match(r'^\+?\d+$', clean):
            return False, "Phone number should contain only digits, spaces, dashes, or parentheses"

        # Remove + for length check
        digits_only = clean.lstrip('+')

        # Phone numbers should be 7-15 digits (international standard)
        if len(digits_only) < 7:
            return False, "Phone number is too short (minimum 7 digits)"

        if len(digits_only) > 15:
            return False, "Phone number is too long (maximum 15 digits)"

        # Philippine format validation (if it looks like a PH number)
        if clean.startswith('+63') or clean.startswith('63') or clean.startswith('0'):
            if clean.startswith('+63'):
                ph_number = clean[3:]
            elif clean.startswith('63'):
                ph_number = clean[2:]
            else:  # starts with 0
                ph_number = clean[1:]

            if len(ph_number) != 10:
                return False, "Philippine mobile numbers should be 10 digits after country code (e.g., +63 917 123 4567)"

        return True, ""

    @staticmethod
    def auto_format_phone(text: str) -> str:
        """Auto-format Philippine phone number as user types"""
        clean = re.sub(r'[^\d+]', '', text)

        # Check if it's a Philippine number
        if clean.startswith('+63') or clean.startswith('63') or clean.startswith('0'):
            if clean.startswith('+63'):
                return f"+63 {clean[3:6]} {clean[6:9]} {clean[9:13]}"
            elif clean.startswith('63'):
                return f"+63 {clean[2:5]} {clean[5:8]} {clean[8:12]}"
            elif clean.startswith('0'):
                if len(clean) <= 4:
                    return clean
                elif len(clean) <= 7:
                    return f"{clean[:4]} {clean[4:]}"
                else:
                    return f"{clean[:4]} {clean[4:7]} {clean[7:11]}"

        return text
