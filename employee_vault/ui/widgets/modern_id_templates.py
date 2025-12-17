"""
Modern ID Card Templates
Professional ID card designs inspired by Google, Microsoft, Apple, and Fortune 500 companies
"""

from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import os

class ModernIDCardTemplate:
    """Base class for modern ID card templates"""

    # Standard ID card sizes (in pixels at 300 DPI)
    SIZES = {
        "standard": (1012, 638),  # 3.375" x 2.125" (standard credit card size)
        "large": (1200, 750),     # Larger format
        "badge": (900, 1200),     # Vertical badge format
    }

    # Color schemes inspired by major companies
    COLOR_SCHEMES = {
        "tech_blue": {
            "primary": "#2196F3",
            "accent": "#00BCD4",
            "background": "#FFFFFF",
            "text": "#212121",
            "secondary": "#757575",
        },
        "corporate_navy": {
            "primary": "#1A237E",
            "accent": "#FFC107",
            "background": "#F5F5F5",
            "text": "#000000",
            "secondary": "#616161",
        },
        "creative_purple": {
            "primary": "#7C3AED",
            "accent": "#EC4899",
            "background": "#FFFFFF",
            "text": "#1E1B4B",
            "secondary": "#64748B",
        },
        "modern_green": {
            "primary": "#10B981",
            "accent": "#84CC16",
            "background": "#F0FDF4",
            "text": "#064E3B",
            "secondary": "#6B7280",
        },
        "elegant_black": {
            "primary": "#18181B",
            "accent": "#71717A",
            "background": "#FAFAFA",
            "text": "#09090B",
            "secondary": "#52525B",
        },
    }

    def __init__(self, size="standard", color_scheme="tech_blue"):
        """
        Initialize ID card template

        Args:
            size: Card size ("standard", "large", "badge")
            color_scheme: Color scheme name
        """
        self.size = self.SIZES.get(size, self.SIZES["standard"])
        self.colors = self.COLOR_SCHEMES.get(color_scheme, self.COLOR_SCHEMES["tech_blue"])

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class GoogleStyleTemplate(ModernIDCardTemplate):
    """
    Google/Microsoft Style - Modern Tech Company ID Card

    Features:
    - Minimalist design with lots of white space
    - Large, clear employee photo
    - QR code for digital verification
    - Sans-serif fonts
    - Color accent strip
    - Clean barcode at bottom
    - Rounded corners
    """

    def create_card(self, employee_data: Dict, photo_path: str = None,
                   qr_code_path: str = None, barcode_path: str = None,
                   company_logo_path: str = None) -> Image.Image:
        """
        Create Google-style ID card

        Args:
            employee_data: Dictionary with employee information
            photo_path: Path to employee photo
            qr_code_path: Path to QR code image
            barcode_path: Path to barcode image
            company_logo_path: Path to company logo

        Returns:
            PIL Image object
        """
        # Create blank card with rounded corners
        card = Image.new('RGB', self.size, self.hex_to_rgb(self.colors["background"]))
        draw = ImageDraw.Draw(card)

        # === TOP COLOR STRIP ===
        strip_height = 80
        draw.rectangle(
            [(0, 0), (self.size[0], strip_height)],
            fill=self.hex_to_rgb(self.colors["primary"])
        )

        # === COMPANY LOGO (if provided) ===
        if company_logo_path and os.path.exists(company_logo_path):
            try:
                logo = Image.open(company_logo_path)
                logo = logo.resize((120, 60), Image.Resampling.LANCZOS)
                card.paste(logo, (30, 10), logo if logo.mode == 'RGBA' else None)
            except:
                pass

        # === EMPLOYEE PHOTO ===
        photo_size = 250
        photo_x = 50
        photo_y = strip_height + 40

        if photo_path and os.path.exists(photo_path):
            try:
                photo = Image.open(photo_path)
                photo = photo.resize((photo_size, photo_size), Image.Resampling.LANCZOS)

                # Create circular mask
                mask = Image.new('L', (photo_size, photo_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, photo_size, photo_size], fill=255)

                # Paste with mask
                card.paste(photo, (photo_x, photo_y), mask)

                # Draw border around photo
                draw.ellipse(
                    [photo_x-3, photo_y-3, photo_x+photo_size+3, photo_y+photo_size+3],
                    outline=self.hex_to_rgb(self.colors["accent"]),
                    width=4
                )
            except Exception as e:
                # Draw placeholder
                draw.ellipse(
                    [photo_x, photo_y, photo_x+photo_size, photo_y+photo_size],
                    fill="#E0E0E0",
                    outline=self.hex_to_rgb(self.colors["accent"]),
                    width=3
                )
        else:
            # Placeholder
            draw.ellipse(
                [photo_x, photo_y, photo_x+photo_size, photo_y+photo_size],
                fill="#E0E0E0",
                outline=self.hex_to_rgb(self.colors["accent"]),
                width=3
            )

        # === TEXT INFORMATION ===
        text_x = photo_x + photo_size + 40
        text_y = photo_y

        try:
            # Try to use professional fonts
            font_name_large = ImageFont.truetype("arial.ttf", 42)
            font_role = ImageFont.truetype("arial.ttf", 28)
            font_details = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            # Fallback to default
            font_name_large = ImageFont.load_default()
            font_role = ImageFont.load_default()
            font_details = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Employee Name (largest)
        name = employee_data.get('name', 'EMPLOYEE NAME').upper()
        draw.text(
            (text_x, text_y),
            name,
            fill=self.hex_to_rgb(self.colors["text"]),
            font=font_name_large
        )

        # Role/Position (second)
        role = employee_data.get('position', 'Position')
        draw.text(
            (text_x, text_y + 55),
            role,
            fill=self.hex_to_rgb(self.colors["primary"]),
            font=font_role
        )

        # Department
        dept = employee_data.get('department', 'Department')
        draw.text(
            (text_x, text_y + 100),
            f"Department: {dept}",
            fill=self.hex_to_rgb(self.colors["secondary"]),
            font=font_details
        )

        # Employee ID
        emp_id = employee_data.get('emp_id', 'ID-0000')
        draw.text(
            (text_x, text_y + 135),
            f"ID: {emp_id}",
            fill=self.hex_to_rgb(self.colors["secondary"]),
            font=font_details
        )

        # Start Date
        hire_date = employee_data.get('hire_date', '')
        if hire_date:
            draw.text(
                (text_x, text_y + 170),
                f"Since: {hire_date}",
                fill=self.hex_to_rgb(self.colors["secondary"]),
                font=font_details
            )

        # === QR CODE & BARCODE ===
        qr_y = self.size[1] - 180

        # QR Code
        if qr_code_path and os.path.exists(qr_code_path):
            try:
                qr = Image.open(qr_code_path)
                qr = qr.resize((140, 140), Image.Resampling.LANCZOS)
                card.paste(qr, (50, qr_y))
            except:
                pass

        # Barcode
        if barcode_path and os.path.exists(barcode_path):
            try:
                barcode = Image.open(barcode_path)
                barcode = barcode.resize((300, 80), Image.Resampling.LANCZOS)
                card.paste(barcode, (220, qr_y + 30))
            except:
                pass

        # === EXPIRY DATE ===
        expiry = employee_data.get('contract_expiry', '')
        if expiry:
            draw.text(
                (text_x, self.size[1] - 60),
                f"Expires: {expiry}",
                fill=self.hex_to_rgb(self.colors["secondary"]),
                font=font_small
            )

        # === ROUNDED CORNERS ===
        card = self._add_rounded_corners(card, radius=20)

        return card

    def _add_rounded_corners(self, image: Image.Image, radius: int = 20) -> Image.Image:
        """Add rounded corners to image"""
        # Create mask with rounded corners
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [(0, 0), image.size],
            radius=radius,
            fill=255
        )

        # Apply mask
        output = Image.new('RGBA', image.size, (255, 255, 255, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)

        return output


class AppleStyleTemplate(ModernIDCardTemplate):
    """
    Apple/Amazon Style - Premium Professional ID Card

    Features:
    - High-contrast design
    - Premium materials feel
    - Employee signature area
    - Status badges (access level)
    - Clear hierarchy
    - Professional typography
    """

    def create_card(self, employee_data: Dict, photo_path: str = None,
                   qr_code_path: str = None, signature_path: str = None,
                   company_logo_path: str = None) -> Image.Image:
        """Create Apple-style ID card"""

        # Create card with premium background
        card = Image.new('RGB', self.size, self.hex_to_rgb(self.colors["background"]))
        draw = ImageDraw.Draw(card)

        # === PREMIUM BORDER ===
        border_width = 8
        draw.rectangle(
            [(0, 0), (self.size[0]-1, self.size[1]-1)],
            outline=self.hex_to_rgb(self.colors["primary"]),
            width=border_width
        )

        # === EMPLOYEE PHOTO (Large and centered) ===
        photo_size = 320
        photo_x = (self.size[0] - photo_size) // 2
        photo_y = 60

        if photo_path and os.path.exists(photo_path):
            try:
                photo = Image.open(photo_path)
                photo = photo.resize((photo_size, photo_size), Image.Resampling.LANCZOS)
                card.paste(photo, (photo_x, photo_y))

                # Premium border
                draw.rectangle(
                    [photo_x-4, photo_y-4, photo_x+photo_size+4, photo_y+photo_size+4],
                    outline=self.hex_to_rgb(self.colors["accent"]),
                    width=4
                )
            except:
                draw.rectangle(
                    [photo_x, photo_y, photo_x+photo_size, photo_y+photo_size],
                    fill="#E0E0E0",
                    outline=self.hex_to_rgb(self.colors["primary"]),
                    width=3
                )

        # === TEXT (Centered below photo) ===
        try:
            font_name = ImageFont.truetype("arialbd.ttf", 38)  # Bold
            font_role = ImageFont.truetype("arial.ttf", 26)
            font_details = ImageFont.truetype("arial.ttf", 20)
        except:
            font_name = ImageFont.load_default()
            font_role = ImageFont.load_default()
            font_details = ImageFont.load_default()

        text_y = photo_y + photo_size + 30

        # Name (centered, largest)
        name = employee_data.get('name', 'EMPLOYEE NAME').upper()
        try:
            bbox = draw.textbbox((0, 0), name, font=font_name)
            name_width = bbox[2] - bbox[0]
        except:
            name_width = len(name) * 20  # Estimate
        name_x = (self.size[0] - name_width) // 2
        draw.text(
            (name_x, text_y),
            name,
            fill=self.hex_to_rgb(self.colors["text"]),
            font=font_name
        )

        # Role (centered)
        role = employee_data.get('position', 'Position')
        try:
            bbox = draw.textbbox((0, 0), role, font=font_role)
            role_width = bbox[2] - bbox[0]
        except:
            role_width = len(role) * 15
        role_x = (self.size[0] - role_width) // 2
        draw.text(
            (role_x, text_y + 50),
            role,
            fill=self.hex_to_rgb(self.colors["primary"]),
            font=font_role
        )

        # Details (left-aligned)
        details_y = text_y + 100
        details_x = 80
        line_height = 30

        details = [
            f"Department: {employee_data.get('department', 'N/A')}",
            f"Employee ID: {employee_data.get('emp_id', 'N/A')}",
            f"Access Level: {'⬤⬤⬤⚪⚪' if employee_data.get('role') == 'Admin' else '⬤⬤⚪⚪⚪'}",
        ]

        for i, detail in enumerate(details):
            draw.text(
                (details_x, details_y + (i * line_height)),
                detail,
                fill=self.hex_to_rgb(self.colors["secondary"]),
                font=font_details
            )

        # === QR CODE (Bottom Right) ===
        if qr_code_path and os.path.exists(qr_code_path):
            try:
                qr = Image.open(qr_code_path)
                qr = qr.resize((100, 100), Image.Resampling.LANCZOS)
                card.paste(qr, (self.size[0] - 130, self.size[1] - 130))
            except:
                pass

        return card


# Template Registry
TEMPLATES = {
    "google": GoogleStyleTemplate,
    "apple": AppleStyleTemplate,
    "microsoft": GoogleStyleTemplate,  # Same as Google style
    "corporate": AppleStyleTemplate,   # Same as Apple style
}


def get_template(template_name: str = "google", **kwargs) -> ModernIDCardTemplate:
    """
    Get ID card template by name

    Args:
        template_name: Template name ("google", "apple", "microsoft", "corporate")
        **kwargs: Additional arguments for template initialization

    Returns:
        Template instance
    """
    template_class = TEMPLATES.get(template_name.lower(), GoogleStyleTemplate)
    return template_class(**kwargs)
