"""
ID Card Generator
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from employee_vault.config import *
from employee_vault.database import DB
from employee_vault.validators import *
from employee_vault.utils import *
from employee_vault.models import *
from employee_vault.ui.widgets import *
from employee_vault.ui.widgets import ModernAnimatedButton
from employee_vault.ui.ios_button_styles import apply_ios_style

class IDCardGeneratorBackend:
    """
    Professional ID Card Generator for Employee Vault
    Supports QR codes, barcodes, templates, and direct printing
    Works 100% offline for LAN deployment
    """

    def __init__(self, db_path: str, template_dir: str = "templates"):
        """
        Initialize ID Card Generator

        Args:
            db_path: Path to SQLite database
            template_dir: Directory containing card templates
        """
        self.db_path = db_path
        self.template_dir = template_dir
        self.card_size = (638, 1011)  # CR80 card size at 300 DPI - PORTRAIT (53.98mm x 85.6mm)
        self.secret_key = "EmployeeVault2024"  # For QR code security checksums

        # Ensure template directory exists
        os.makedirs(template_dir, exist_ok=True)

        logging.info(f"IDCardGenerator initialized with database: {db_path}")

    def generate_card(self, employee_id: int, template: str = "standard", side: str = "front"):
        """
        Generate ID card for a single employee

        Args:
            employee_id: Database ID of employee
            template: Template name to use (standard, visitor, contractor, management)
            side: "front" or "back" to generate specific side

        Returns:
            PIL Image object of the generated card (or dict with both sides if side="both")

        Raises:
            ValueError: If employee not found or invalid data
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            raise ImportError("Pillow library required. Install with: pip install Pillow")

        # Fetch employee data from database
        employee = self._get_employee_data(employee_id)

        if side == "both":
            # Generate both sides
            front = self._generate_front(employee, template)
            back = self._generate_back(employee, template)
            logging.info(f"Both card sides generated for employee {employee_id}: {employee.get('name', 'Unknown')}")
            return {'front': front, 'back': back}
        elif side == "back":
            # Generate only back
            card = self._generate_back(employee, template)
            logging.info(f"Back card generated for employee {employee_id}: {employee.get('name', 'Unknown')}")
            return card
        else:
            # Generate only front (default)
            card = self._generate_front(employee, template)
            logging.info(f"Front card generated for employee {employee_id}: {employee.get('name', 'Unknown')}")
            return card

    def _generate_front(self, employee: dict, template: str):
        """Generate front side of ID card"""
        # Load base template with colorful background
        card = self._load_template(template, employee.get('department', 'Default'))

        # Add employee photo
        card = self._add_photo(card, employee.get('photo'))

        # Add text fields
        card = self._add_text_fields(card, employee)

        # Add QR code
        card = self._add_qr_code(card, employee)

        # Barcode removed as per requirement

        # Add company logo
        card = self._add_logo(card)

        return card

    def _generate_back(self, employee: dict, template: str):
        """Generate back side of ID card - MODERN PROFESSIONAL STYLE
        v4.3.8: Clean layout with better organization and spacing
        """
        from PIL import Image, ImageDraw, ImageFont

        # Try to load the colorful background image
        background_path = "id_card_background.png"
        if os.path.exists(background_path):
            try:
                back_card = Image.open(background_path).copy()
                back_card = back_card.resize(self.card_size, Image.Resampling.LANCZOS)
                logging.debug(f"Loaded colorful background for back card from {background_path}")
            except Exception as e:
                logging.warning(f"Could not load background image: {e}, using white background")
                back_card = Image.new('RGB', self.card_size, color='white')
        else:
            back_card = Image.new('RGB', self.card_size, color='white')

        draw = ImageDraw.Draw(back_card)

        # Get department color for header
        header_color = self._get_department_color(employee.get('department', 'Default'))

        # Draw colored header bar (top 80 pixels)
        draw.rectangle([(0, 0), (self.card_size[0], 80)], fill=header_color)

        # Draw border
        draw.rectangle([(0, 0), (self.card_size[0]-1, self.card_size[1]-1)],
                      outline='black', width=3)

        # v4.3.8: Modern fonts with proper hierarchy
        try:
            font_header = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 26)  # Bold header
            font_section = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 22) # Bold sections
            font_label = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 18)     # Labels
            font_value = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 20)     # Values (slightly larger)
            font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 16)     # Small text
        except:
            font_header = ImageFont.load_default()
            font_section = ImageFont.load_default()
            font_label = ImageFont.load_default()
            font_value = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Header text (centered)
        header_text = "EMPLOYEE INFORMATION"
        bbox = draw.textbbox((0, 0), header_text, font=font_header)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, 28), header_text, fill='white', font=font_header)

        # v4.3.8: Contact Information Section (NO ICON - removed tofu)
        y_pos = 130
        section_text = "CONTACT"
        bbox = draw.textbbox((0, 0), section_text, font=font_section)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), section_text, fill='#2196F3', font=font_section)
        y_pos += 40

        # Email
        if employee.get('email'):
            email_text = f"Email: {employee['email']}"
            bbox = draw.textbbox((0, 0), email_text, font=font_value)
            text_width = bbox[2] - bbox[0]
            x_centered = (638 - text_width) // 2
            draw.text((x_centered, y_pos), email_text, fill='#212121', font=font_value)
            y_pos += 50

        # v4.3.8: Emergency Contact Section (NO ICON)
        section_text = "EMERGENCY CONTACT"
        bbox = draw.textbbox((0, 0), section_text, font=font_section)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), section_text, fill='#F44336', font=font_section)
        y_pos += 40

        contact_name = employee.get('emergency_contact_name', 'N/A')
        bbox = draw.textbbox((0, 0), contact_name, font=font_value)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), contact_name, fill='#212121', font=font_value)
        y_pos += 30

        contact_phone = employee.get('emergency_contact_phone', 'N/A')
        bbox = draw.textbbox((0, 0), contact_phone, font=font_value)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), contact_phone, fill='#424242', font=font_value)
        y_pos += 50

        # v4.3.8: Card Validity Section (NO ICON)
        section_text = "CARD VALIDITY"
        bbox = draw.textbbox((0, 0), section_text, font=font_section)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), section_text, fill='#4CAF50', font=font_section)
        y_pos += 40

        issue_text = f"Issued: {employee['issue_date']}"
        bbox = draw.textbbox((0, 0), issue_text, font=font_value)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), issue_text, fill='#616161', font=font_value)
        y_pos += 30

        expiry_text = f"Expires: {employee['expiry_date']}"
        bbox = draw.textbbox((0, 0), expiry_text, font=font_value)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), expiry_text, fill='#D32F2F', font=font_value)
        y_pos += 60

        # v4.3.8: Card Usage Guidelines (NO ICON)
        section_text = "CARD USAGE"
        bbox = draw.textbbox((0, 0), section_text, font=font_section)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), section_text, fill='#FF9800', font=font_section)
        y_pos += 35

        guidelines = [
            "• Wear visibly at all times on premises",
            "• Report lost/stolen cards immediately",
            "• Non-transferable - personal use only",
            "• Return upon employment termination",
            "• Scan QR code on front to verify"
        ]

        for guideline in guidelines:
            bbox = draw.textbbox((0, 0), guideline, font=font_small)
            text_width = bbox[2] - bbox[0]
            x_centered = (638 - text_width) // 2
            draw.text((x_centered, y_pos), guideline, fill='#616161', font=font_small)
            y_pos += 28

        # Signature line (centered)
        y_pos = 780
        sig_start = 150
        sig_end = 488
        draw.line([(sig_start, y_pos), (sig_end, y_pos)], fill='#9E9E9E', width=2)

        sig_text = "Authorized Signature"
        bbox = draw.textbbox((0, 0), sig_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos + 12), sig_text, fill='#9E9E9E', font=font_small)

        # Company footer
        y_pos = 920
        company_text = "Cuddly International Corporation"
        bbox = draw.textbbox((0, 0), company_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), company_text, fill='#BDBDBD', font=font_small)

        y_pos += 24
        id_text = f"Card ID: {employee['employee_id']}"
        bbox = draw.textbbox((0, 0), id_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, y_pos), id_text, fill='#BDBDBD', font=font_small)

        logging.debug("Back card generated (modern style: clean sections, color-coded)")

        return back_card

    def _get_employee_data(self, employee_id: int) -> dict:
        """
        Fetch employee data from database

        Args:
            employee_id: Database ID

        Returns:
            Dictionary with employee information
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query employee data
        # Note: Database uses 'emp_id' and 'name' fields, not 'first_name' and 'last_name'
        # Note: Database does NOT have a 'photo' column - photos are stored separately
        cursor.execute("""
            SELECT emp_id, name, department, position,
                   hire_date, email, emergency_contact_name, emergency_contact_phone
            FROM employees
            WHERE emp_id = ?
        """, (employee_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Employee with ID {employee_id} not found in database")

        # Calculate expiry date (1 year from now)
        issue_date = datetime.now()
        expiry_date = issue_date + timedelta(days=365)

        # Use the emp_id from database
        emp_id_str = str(row['emp_id'])

        # Parse name (database stores full name in single field)
        full_name = row['name'] or 'Unknown'
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else 'Unknown'
        last_name = name_parts[-1] if len(name_parts) > 1 else ''

        # v4.5.0: Load photo from employee_photos folder
        photo_path = f"employee_photos/{emp_id_str}.png"
        photo_data = None
        if os.path.exists(photo_path):
            try:
                with open(photo_path, 'rb') as f:
                    photo_data = f.read()
                logging.debug(f"Loaded photo from {photo_path}")
            except Exception as e:
                logging.warning(f"Could not load photo from {photo_path}: {e}")

        employee_data = {
            'id': employee_id,
            'employee_id': emp_id_str,
            'name': full_name,
            'first_name': first_name,
            'last_name': last_name,
            'department': row['department'] or 'General',
            'position': row['position'] or 'Employee',
            'hire_date': row['hire_date'] or issue_date.strftime("%Y-%m-%d"),
            'photo': photo_data,  # v4.5.0: Load from employee_photos folder
            'email': row['email'],
            'emergency_contact_name': row['emergency_contact_name'] or 'N/A',
            'emergency_contact_phone': row['emergency_contact_phone'] or 'N/A',
            'issue_date': issue_date.strftime("%Y-%m-%d"),
            'expiry_date': expiry_date.strftime("%Y-%m-%d")
        }

        return employee_data

    def _load_template(self, template: str, department: str):
        """
        Load card template based on template name and department

        Args:
            template: Template type (standard, visitor, contractor)
            department: Employee department for color coding

        Returns:
            PIL Image object with base template
        """
        from PIL import Image, ImageDraw

        # Try to load the colorful background image
        background_path = "id_card_background.png"
        if os.path.exists(background_path):
            try:
                # Load and resize background to fit card size
                background = Image.open(background_path).copy()
                background = background.resize(self.card_size, Image.Resampling.LANCZOS)
                card = background
                logging.debug(f"Loaded colorful background from {background_path}")
            except Exception as e:
                logging.warning(f"Could not load background image: {e}, creating plain template")
                card = self._create_plain_template(department)
        else:
            # Check for specific template file
            template_path = os.path.join(self.template_dir, f"{template}.png")
            
            if os.path.exists(template_path):
                # Load existing template
                card = Image.open(template_path).copy()
                logging.debug(f"Loaded template from {template_path}")
            else:
                # Create plain template
                card = self._create_plain_template(department)

        # Add colored header bar for department identification
        draw = ImageDraw.Draw(card)
        header_color = self._get_department_color(department)
        draw.rectangle([(0, 0), (self.card_size[0], 80)], fill=header_color)
        
        # Draw border
        draw.rectangle([(0, 0), (self.card_size[0]-1, self.card_size[1]-1)],
                      outline='black', width=3)

        return card
    
    def _create_plain_template(self, department: str):
        """Create a plain white template with department color header"""
        from PIL import Image, ImageDraw
        
        card = Image.new('RGB', self.card_size, color='white')
        logging.debug(f"Created plain template")
        return card

    def _get_department_color(self, department: str) -> tuple:
        """
        Get RGB color tuple for department

        Args:
            department: Department name

        Returns:
            RGB tuple (r, g, b)
        """
        colors = {
            'IT': (0, 102, 204),        # Blue
            'HR': (0, 170, 0),          # Green
            'Finance': (255, 215, 0),   # Gold
            'Operations': (255, 102, 0), # Orange
            'Management': (102, 0, 153), # Purple
            'Sales': (220, 20, 60),     # Crimson
            'Marketing': (255, 20, 147), # Deep Pink
            'Default': (128, 128, 128)  # Gray
        }

        return colors.get(department, colors['Default'])

    def _add_photo(self, card, photo_blob: bytes):
        """
        Add employee photo to card - CIRCULAR STYLE (like Add Employee form)
        v4.5.0: Changed to circular photo with proper positioning

        Args:
            card: Card image
            photo_blob: Photo data from database (BLOB)

        Returns:
            Card with photo added
        """
        if not photo_blob:
            logging.debug("No photo available, skipping")
            return card

        try:
            from PIL import Image, ImageDraw
            from io import BytesIO

            # Convert BLOB to image
            photo = Image.open(BytesIO(photo_blob))

            # v4.5.0: CIRCULAR photo (250px diameter)
            photo_size = 250

            # Resize and crop to square first
            min_dim = min(photo.size)
            left = (photo.size[0] - min_dim) // 2
            top = (photo.size[1] - min_dim) // 2
            photo = photo.crop((left, top, left + min_dim, top + min_dim))
            photo = photo.resize((photo_size, photo_size), Image.Resampling.LANCZOS)

            # v4.5.0: Create circular mask
            mask = Image.new('L', (photo_size, photo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (photo_size, photo_size)], fill=255)

            # Apply circular mask to photo
            circular_photo = Image.new('RGBA', (photo_size, photo_size), (255, 255, 255, 0))
            circular_photo.paste(photo, (0, 0))
            circular_photo.putalpha(mask)

            # v4.5.0: Position photo centered horizontally, below logo/company info
            # Card width is 638, photo is 250, so center at (638-250)/2 = 194
            # Position below logo area (logo ends around y=110, add padding)
            # Paste with alpha channel to maintain transparency
            card.paste(circular_photo, (194, 130), circular_photo)

            logging.debug("Photo added successfully (circular style)")

        except Exception as e:
            logging.warning(f"Could not add photo: {e}")

        return card

    def _add_text_fields(self, card, employee: dict):
        """
        Add text fields to card (PORTRAIT orientation) - MODERN GOOGLE/MICROSOFT STYLE
        v4.3.8: Professional typography hierarchy with proper sizing and spacing

        Args:
            card: Card image
            employee: Employee data dictionary

        Returns:
            Card with text fields added
        """
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(card)

        # v4.3.8: Modern typography hierarchy - FURTHER REDUCED for proper fit
        # Name: 14pt bold → 38px (was 48px)
        # Role: 11pt medium → 30px (was 36px)
        # Department: 9pt → 24px (was 28px)
        # Details: 8pt → 20px (was 24px)
        # Small: 7pt → 16px (was 18px)
        try:
            font_name = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 38)  # Bold for name (reduced)
            font_role = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 30)    # Role (reduced)
            font_dept = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 24)    # Department (reduced)
            font_details = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 20) # ID/Dates (reduced)
            font_tiny = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 16)    # Very small text (reduced)
        except:
            try:
                font_name = ImageFont.truetype("arial.ttf", 38)
                font_role = ImageFont.truetype("arial.ttf", 30)
                font_dept = ImageFont.truetype("arial.ttf", 24)
                font_details = ImageFont.truetype("arial.ttf", 20)
                font_tiny = ImageFont.truetype("arial.ttf", 16)
            except:
                font_name = ImageFont.load_default()
                font_role = ImageFont.load_default()
                font_dept = ImageFont.load_default()
                font_details = ImageFont.load_default()
                font_tiny = ImageFont.load_default()

        # v4.3.8: Company name in header (white text, centered)
        company_text = "CUDDLY INTERNATIONAL"
        bbox = draw.textbbox((0, 0), company_text, font=font_details)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, 35), company_text, fill='white', font=font_details)

        # v4.3.8: Employee name (LARGEST, bold, centered below photo)
        # Photo ends at y=110+380=490, add spacing of 30px
        y_pos = 520
        name_bbox = draw.textbbox((0, 0), employee['name'], font=font_name)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = max(30, (638 - name_width) // 2)
        draw.text((name_x, y_pos), employee['name'], fill='#212121', font=font_name)

        # v4.3.8: Position/Role (SECOND largest, medium weight)
        y_pos += 70
        pos_bbox = draw.textbbox((0, 0), employee['position'], font=font_role)
        pos_width = pos_bbox[2] - pos_bbox[0]
        pos_x = (638 - pos_width) // 2
        draw.text((pos_x, y_pos), employee['position'], fill='#424242', font=font_role)

        # v4.3.8: Department (NO ICON - removed tofu boxes)
        y_pos += 60
        dept_text = f"Dept: {employee['department']}"
        dept_bbox = draw.textbbox((0, 0), dept_text, font=font_dept)
        dept_width = dept_bbox[2] - dept_bbox[0]
        dept_x = (638 - dept_width) // 2
        draw.text((dept_x, y_pos), dept_text, fill='#616161', font=font_dept)

        # v4.3.8: Employee ID (NO ICON, blue accent color)
        y_pos += 55
        id_text = f"ID: {employee['employee_id']}"
        id_bbox = draw.textbbox((0, 0), id_text, font=font_details)
        id_width = id_bbox[2] - id_bbox[0]
        id_x = (638 - id_width) // 2
        draw.text((id_x, y_pos), id_text, fill='#2196F3', font=font_details)

        # v4.3.8: Hire date (NO ICON, small text)
        y_pos += 45
        hired_text = f"Since: {employee['hire_date']}"
        hired_bbox = draw.textbbox((0, 0), hired_text, font=font_tiny)
        hired_width = hired_bbox[2] - hired_bbox[0]
        hired_x = (638 - hired_width) // 2
        draw.text((hired_x, y_pos), hired_text, fill='#757575', font=font_tiny)

        logging.debug("Text fields added (modern style: proper hierarchy, icons, spacing)")

        return card

    def _add_qr_code(self, card, employee: dict):
        """
        Add QR code with employee data - MODERN STYLE
        v4.3.8: Positioned at bottom center with proper spacing

        Args:
            card: Card image
            employee: Employee data dictionary

        Returns:
            Card with QR code added
        """
        try:
            import qrcode
        except ImportError:
            logging.warning("qrcode library not installed, skipping QR code")
            return card

        # Create readable text format for QR code
        qr_text = f"""EMPLOYEE ID CARD
━━━━━━━━━━━━━━━━
Name: {employee['name']}
ID: {employee['employee_id']}
Department: {employee['department']}
Position: {employee['position']}
━━━━━━━━━━━━━━━━
Hired: {employee['hire_date']}
Issued: {employee['issue_date']}
Valid Until: {employee['expiry_date']}
━━━━━━━━━━━━━━━━
Cuddly International Corporation
Verified ✓"""

        # v4.3.8: Generate QR code with modern sizing
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=1
        )
        qr.add_data(qr_text)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((160, 160))  # Slightly larger QR code

        # v4.3.8: Paste QR code at bottom center with better positioning
        # Card width is 638, QR is 160, so center at (638-160)/2 = 239
        # Position at bottom with 40px margin from bottom
        card.paste(qr_img, (239, 820))

        # Add "Scan for verification" text below QR code
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(card)

        try:
            font_tiny = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 16)
        except:
            font_tiny = ImageFont.load_default()

        scan_text = "Scan for verification"
        bbox = draw.textbbox((0, 0), scan_text, font=font_tiny)
        text_width = bbox[2] - bbox[0]
        x_centered = (638 - text_width) // 2
        draw.text((x_centered, 990), scan_text, fill='#757575', font=font_tiny)

        logging.debug("QR code added (modern style: larger, better positioned)")

        return card

    def _add_barcode(self, card, employee_id: str):
        """
        Add barcode of employee ID

        Args:
            card: Card image
            employee_id: Employee ID string

        Returns:
            Card with barcode added
        """
        try:
            import barcode
            from barcode.writer import ImageWriter
            from io import BytesIO
            from PIL import Image
        except ImportError:
            logging.warning("python-barcode library not installed, skipping barcode")
            return card

        try:
            # Generate Code128 barcode (supports alphanumeric)
            CODE128 = barcode.get_barcode_class('code128')

            # Remove "EMP" prefix for cleaner barcode
            barcode_data = employee_id.replace("EMP", "")

            # Generate barcode
            barcode_img = CODE128(barcode_data, writer=ImageWriter())

            # Render to BytesIO
            buffer = BytesIO()
            barcode_img.write(buffer, options={'write_text': False})
            buffer.seek(0)

            # Convert to PIL Image
            barcode_pil = Image.open(buffer)

            # Resize to fit card
            barcode_pil = barcode_pil.resize((450, 80))

            # Paste barcode onto card (bottom left)
            card.paste(barcode_pil, (50, 540))

            logging.debug("Barcode added")

        except Exception as e:
            logging.warning(f"Could not add barcode: {e}")

        return card

    def _add_logo(self, card):
        """
        Add company logos to card
        v4.5.0: Cuddly logo at top center above photo, Apruva logos at bottom corners

        Args:
            card: Card image

        Returns:
            Card with logo added
        """
        from PIL import Image, ImageDraw, ImageFont

        # v4.5.0: Add Cuddly logo at top center, above circular photo
        cuddly_logo_paths = [
            "cuddly_logo.png",
            "company_logo.png",
            os.path.join(self.template_dir, "logo.png"),
            os.path.join(self.template_dir, "company_logo.png")
        ]

        cuddly_logo_path = None
        for path in cuddly_logo_paths:
            if os.path.exists(path):
                cuddly_logo_path = path
                break

        # Add Cuddly logo at top center
        if cuddly_logo_path:
            try:
                logo = Image.open(cuddly_logo_path)

                # Resize logo to fit at top (maintain aspect ratio)
                logo_height = 45
                logo_width = int(logo_height * logo.size[0] / logo.size[1])
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

                # Position: Center horizontally at top
                # Card width is 638, center the logo
                logo_x = (638 - logo_width) // 2
                logo_y = 15

                if logo.mode == 'RGBA':
                    card.paste(logo, (logo_x, logo_y), logo)
                else:
                    card.paste(logo, (logo_x, logo_y))

                logging.debug(f"Cuddly logo added at top center from {cuddly_logo_path}")
            except Exception as e:
                logging.warning(f"Could not add Cuddly logo: {e}")

        # v4.5.0: Add company name and info centered below logo, above photo
        try:
            draw = ImageDraw.Draw(card)

            # Company name font - bold
            try:
                font_company = ImageFont.truetype("C:\\Windows\\Fonts\\calibrib.ttf", 12)
            except:
                font_company = ImageFont.load_default()

            company_text = "CUDDLY INTERNATIONAL CORPORATION"

            # Calculate text width for centering
            bbox = draw.textbbox((0, 0), company_text, font=font_company)
            text_width = bbox[2] - bbox[0]
            text_x = (638 - text_width) // 2

            # Draw company name centered below logo
            draw.text((text_x, 70), company_text, font=font_company, fill=(0, 0, 0))

            # Address and contact - smaller, centered
            try:
                font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 8)
            except:
                font_small = ImageFont.load_default()

            address_text = "#650 Jesus Ext. cor. Beata, Pandacan, Manila"
            bbox = draw.textbbox((0, 0), address_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            text_x = (638 - text_width) // 2
            draw.text((text_x, 88), address_text, font=font_small, fill=(64, 64, 64))

            contact_text = "Tel. Nos. 8588-0324 / Fax No. 8588-0327"
            bbox = draw.textbbox((0, 0), contact_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            text_x = (638 - text_width) // 2
            draw.text((text_x, 100), contact_text, font=font_small, fill=(64, 64, 64))

            logging.debug("Company name and contact info added (centered)")

        except Exception as e:
            logging.warning(f"Could not add company info: {e}")

        # v4.5.0: Add Apruva logos at bottom corners
        apruva_logo_path = "apruva_logo.png"

        if os.path.exists(apruva_logo_path):
            try:
                apruva_logo = Image.open(apruva_logo_path)

                # Resize Apruva logo (small, for bottom corners)
                apruva_height = 35
                apruva_width = int(apruva_height * apruva_logo.size[0] / apruva_logo.size[1])
                apruva_logo = apruva_logo.resize((apruva_width, apruva_height), Image.Resampling.LANCZOS)

                # Bottom left corner
                # Card height is 1011, position logo near bottom
                bottom_y = 1011 - apruva_height - 15  # 15px from bottom

                if apruva_logo.mode == 'RGBA':
                    # Bottom left
                    card.paste(apruva_logo, (15, bottom_y), apruva_logo)
                    # Bottom right
                    card.paste(apruva_logo, (638 - apruva_width - 15, bottom_y), apruva_logo)
                else:
                    card.paste(apruva_logo, (15, bottom_y))
                    card.paste(apruva_logo, (638 - apruva_width - 15, bottom_y))

                logging.debug("Apruva logos added at bottom corners")
            except Exception as e:
                logging.warning(f"Could not add Apruva logos: {e}")
        else:
            logging.debug("Apruva logo not found, skipping bottom logos")

        return card

    def save_card(self, card, output_path: str):
        """
        Save card image to file

        Args:
            card: PIL Image object
            output_path: File path to save (PNG format)
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # Save as high-quality PNG
            card.save(output_path, 'PNG', dpi=(300, 300), optimize=True)

            file_size = os.path.getsize(output_path) / 1024  # KB
            logging.info(f"Card saved to {output_path} ({file_size:.1f} KB)")

            return output_path

        except Exception as e:
            logging.error(f"Error saving card: {e}")
            raise

    def print_card(self, card, printer_name: str = None, scale_factor: float = 1.0):
        """
        Print card to Windows printer with size control

        Args:
            card: PIL Image object
            printer_name: Name of printer (None = default printer)
            scale_factor: Print size multiplier (1.0 = actual size, 0 = full page, 1.5 = quarter page, 2.5 = half page)

        Note:
            Requires pywin32 library on Windows
        """
        try:
            import win32print
            import win32ui
            from PIL import ImageWin
        except ImportError:
            logging.error("pywin32 library required for printing. Install with: pip install pywin32")
            raise ImportError("pywin32 required for Windows printing")

        try:
            # Get default printer if not specified
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()

            logging.info(f"Printing to: {printer_name} (scale: {scale_factor})")

            # Create device context
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)

            # Start print job
            hdc.StartDoc("Employee ID Card")
            hdc.StartPage()

            # Get printer capabilities
            printable_width = hdc.GetDeviceCaps(110)  # HORZRES
            printable_height = hdc.GetDeviceCaps(111)  # VERTRES
            dpi_x = hdc.GetDeviceCaps(88)  # LOGPIXELSX
            dpi_y = hdc.GetDeviceCaps(90)  # LOGPIXELSY

            # Calculate scaling
            card_width, card_height = card.size
            
            if scale_factor == 0:
                # Full page auto-scale
                scale = min(printable_width / card_width, printable_height / card_height) * 0.9
            else:
                # Fixed scale based on actual card size
                # Card is at 300 DPI, printer uses its DPI
                scale = (dpi_x / 300.0) * scale_factor

            scaled_width = int(card_width * scale)
            scaled_height = int(card_height * scale)

            # Center position
            x = (printable_width - scaled_width) // 2
            y = (printable_height - scaled_height) // 2

            # Print the image
            dib = ImageWin.Dib(card)
            dib.draw(hdc.GetHandleOutput(), (x, y, x + scaled_width, y + scaled_height))

            # End print job
            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()

            logging.info(f"Card printed successfully to {printer_name} at scale {scale_factor}")

        except Exception as e:
            logging.error(f"Printing error: {e}")
            raise

    def batch_generate(self, employee_ids: list = None, department: str = None,
                      template: str = "standard", output_dir: str = "cards", side: str = "front") -> dict:
        """
        Generate multiple ID cards at once

        Args:
            employee_ids: List of employee database IDs (None = all employees)
            department: Filter by department name (None = no filter)
            template: Template to use for all cards
            output_dir: Directory to save generated cards
            side: "front", "back", or "both" - which side(s) to generate

        Returns:
            Dictionary with 'success', 'errors', and 'total' keys
        """
        os.makedirs(output_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query based on filters
        if employee_ids:
            placeholders = ','.join('?' * len(employee_ids))
            query = f"SELECT emp_id FROM employees WHERE emp_id IN ({placeholders})"
            cursor.execute(query, employee_ids)
        elif department:
            cursor.execute("SELECT emp_id FROM employees WHERE department = ?", (department,))
        else:
            cursor.execute("SELECT emp_id FROM employees")

        employee_list = [row[0] for row in cursor.fetchall()]
        conn.close()

        logging.info(f"Batch generating {len(employee_list)} cards ({side} side(s))...")

        generated_files = []
        errors = []

        for emp_id in employee_list:
            try:
                # Generate card with specified side(s)
                result = self.generate_card(emp_id, template=template, side=side)

                if side == "both":
                    # Save both sides
                    front_path = os.path.join(output_dir, f"card_emp_{emp_id}_front.png")
                    back_path = os.path.join(output_dir, f"card_emp_{emp_id}_back.png")

                    self.save_card(result['front'], front_path)
                    self.save_card(result['back'], back_path)

                    generated_files.append(front_path)
                    generated_files.append(back_path)
                else:
                    # Save single side
                    side_suffix = f"_{side}" if side != "front" else ""
                    output_path = os.path.join(output_dir, f"card_emp_{emp_id}{side_suffix}.png")
                    self.save_card(result, output_path)
                    generated_files.append(output_path)

            except Exception as e:
                error_msg = f"Employee {emp_id}: {str(e)}"
                errors.append(error_msg)
                logging.error(error_msg)

        # Summary
        logging.info(f"Batch generation complete: {len(generated_files)} success, {len(errors)} errors")

        if errors:
            logging.warning(f"Errors encountered: {errors}")

        return {
            'success': generated_files,
            'errors': errors,
            'total': len(employee_list)
        }

    def verify_qr_code(self, qr_data_str: str) -> dict:
        """
        Verify scanned QR code checksum and expiry

        Args:
            qr_data_str: JSON string from scanned QR code

        Returns:
            Employee data dictionary if valid

        Raises:
            ValueError: If QR code is invalid or expired
        """
        try:
            qr_data = json.loads(qr_data_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid QR code format")

        # Extract checksum
        provided_checksum = qr_data.pop('checksum', None)

        if not provided_checksum:
            raise ValueError("QR code missing security checksum")

        # Recalculate checksum
        data_str = json.dumps(qr_data, sort_keys=True)
        expected_checksum = hashlib.sha256((data_str + self.secret_key).encode()).hexdigest()[:8]

        # Verify checksum
        if provided_checksum != expected_checksum:
            raise ValueError("Invalid QR code - security checksum mismatch (tampered or fake card)")

        # Check expiry date
        try:
            expiry_date = datetime.strptime(qr_data['valid_until'], "%Y-%m-%d")
            if expiry_date < datetime.now():
                raise ValueError(f"ID card expired on {qr_data['valid_until']}")
        except KeyError:
            raise ValueError("QR code missing expiry date")

        logging.info(f"QR code verified successfully for {qr_data.get('name', 'Unknown')}")

        return qr_data

    def get_card_statistics(self) -> dict:
        """
        Get statistics about ID card generation

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT department) FROM employees WHERE department IS NOT NULL")
        total_departments = cursor.fetchone()[0]

        conn.close()

        templates_available = 0
        if os.path.exists(self.template_dir):
            templates_available = len([f for f in os.listdir(self.template_dir) if f.endswith('.png')])

        return {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'templates_available': templates_available
        }


# --- (This goes between EnhancedDashboardPage and MainWindow) ---
# --- PASTE THIS NEW CLASS, REPLACING THE OLD IDCardGeneratorBackenderator ---

class IDCardGeneratorBackenderator(AnimatedDialogBase):
    """
    Professional ID Card Generator with QR codes, barcodes, and batch generation
    Now with smooth entrance animation
    """
    def __init__(self, parent=None, db=None):
        super().__init__(parent, animation_style="scale")
        self.db = db
        self.setWindowTitle("🆔 Professional ID Card Generator")
        self.resize(900, 700)

        # Initialize the professional card generator
        if not ID_CARD_GEN_AVAILABLE:
            QMessageBox.critical(self, "Error", "Professional ID card generator module not found!")
            self.close()
            return

        try:
            db_path = getattr(self.db, 'db_path', DB_FILE)
            self.card_generator = IDCardGeneratorBackend(db_path=db_path, template_dir="templates")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize card generator: {e}")
            self.close()
            return

        # Main layout
        layout = QVBoxLayout(self)

        # Title (fixed at top)
        title = QLabel("<h2>🆔 Professional ID Card Generator</h2>")
        title.setStyleSheet("background-color: #4a9eff; color: white; padding: 10px;")
        layout.addWidget(title)

        # Create scroll area for main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Widget to hold all scrollable content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Info
        info = QLabel("Generate professional employee ID cards with photos, QR codes, and barcodes.")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        content_layout.addWidget(info)

        # === SINGLE CARD GENERATION ===
        single_group = QGroupBox("🎴 Generate Single Card")
        single_layout = QVBoxLayout()

        # Employee selection
        emp_row = QHBoxLayout()
        emp_row.addWidget(QLabel("<b>Select Employee:</b>"))

        self.employee_combo = NeumorphicGradientComboBox("— Select an Active Employee —")
        self.employee_combo.setMinimumHeight(70)
        self.employees = {e['emp_id']: e for e in self.db.all_employees() if not e.get('resign_date')}
        self.employee_combo.addItem("— Select an Active Employee —", None)
        for emp_id, emp in sorted(self.employees.items(), key=lambda item: item[1]['name']):
            self.employee_combo.addItem(f"{emp['name']} (ID: {emp_id})", emp_id)
        emp_row.addWidget(self.employee_combo, 1)
        single_layout.addLayout(emp_row)

        # Template removed - using default only
        
        # Side selection (Front/Back/Both)
        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("<b>Card Side:</b>"))

        self.side_group = QButtonGroup()
        self.front_radio = QRadioButton("Front Only")
        self.back_radio = QRadioButton("Back Only")
        self.both_radio = QRadioButton("Both Sides")

        self.front_radio.setChecked(True)
        self.side_group.addButton(self.front_radio)
        self.side_group.addButton(self.back_radio)
        self.side_group.addButton(self.both_radio)

        side_row.addWidget(self.front_radio)
        side_row.addWidget(self.back_radio)
        side_row.addWidget(self.both_radio)
        side_row.addStretch()
        single_layout.addLayout(side_row)

        # Buttons - Phase 3: iOS frosted glass
        single_btn_row = QHBoxLayout()
        self.generate_btn = ModernAnimatedButton("📄 Generate & Preview")
        apply_ios_style(self.generate_btn, 'blue')
        self.generate_btn.clicked.connect(self._generate_single_card)
        single_btn_row.addWidget(self.generate_btn)

        self.save_btn = ModernAnimatedButton("💾 Save to File")
        apply_ios_style(self.save_btn, 'green')
        self.save_btn.clicked.connect(self._save_single_card)
        self.save_btn.setEnabled(False)
        single_btn_row.addWidget(self.save_btn)

        self.print_btn = ModernAnimatedButton("🖨️ Print Card")
        apply_ios_style(self.print_btn, 'blue')
        self.print_btn.clicked.connect(self._print_single_card)
        self.print_btn.setEnabled(False)
        single_btn_row.addWidget(self.print_btn)
        single_layout.addLayout(single_btn_row)

        # Preview
        self.preview_label = QLabel("<i>Card preview will appear here</i>")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 5px;")
        single_layout.addWidget(self.preview_label)

        single_group.setLayout(single_layout)
        content_layout.addWidget(single_group)

        # === BATCH GENERATION ===
        batch_group = QGroupBox("📦 Batch Card Generation")
        batch_layout = QVBoxLayout()

        # Batch options
        self.batch_all_radio = QRadioButton("All Active Employees")
        self.batch_all_radio.setChecked(True)
        batch_layout.addWidget(self.batch_all_radio)

        dept_row = QHBoxLayout()
        self.batch_dept_radio = QRadioButton("Specific Department:")
        dept_row.addWidget(self.batch_dept_radio)

        self.dept_combo = NeumorphicGradientComboBox("Select Department")
        self.dept_combo.setMinimumHeight(70)
        departments = set(emp.get('department') for emp in self.employees.values() if emp.get('department'))
        self.dept_combo.addItems(sorted(departments))
        self.dept_combo.setEnabled(False)
        dept_row.addWidget(self.dept_combo)
        dept_row.addStretch()
        batch_layout.addLayout(dept_row)

        self.batch_dept_radio.toggled.connect(lambda checked: self.dept_combo.setEnabled(checked))

        # Batch side selection
        batch_side_row = QHBoxLayout()
        batch_side_row.addWidget(QLabel("<b>Card Side:</b>"))

        self.batch_side_group = QButtonGroup()
        self.batch_front_radio = QRadioButton("Front Only")
        self.batch_back_radio = QRadioButton("Back Only")
        self.batch_both_radio = QRadioButton("Both Sides")

        self.batch_front_radio.setChecked(True)
        self.batch_side_group.addButton(self.batch_front_radio)
        self.batch_side_group.addButton(self.batch_back_radio)
        self.batch_side_group.addButton(self.batch_both_radio)

        batch_side_row.addWidget(self.batch_front_radio)
        batch_side_row.addWidget(self.batch_back_radio)
        batch_side_row.addWidget(self.batch_both_radio)
        batch_side_row.addStretch()
        batch_layout.addLayout(batch_side_row)

        # Output directory
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("<b>Output Directory:</b>"))
        self.output_path_label = QLabel("cards_output")
        # Fix: Add color to make text visible on white background
        self.output_path_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background-color: white; color: #000000; border-radius: 6px;")
        output_row.addWidget(self.output_path_label, 1)

        browse_btn = ModernAnimatedButton("📁 Browse...")
        apply_ios_style(browse_btn, 'blue')
        browse_btn.clicked.connect(self._browse_output_dir)
        output_row.addWidget(browse_btn)
        batch_layout.addLayout(output_row)

        # Batch button
        batch_btn_row = QHBoxLayout()
        self.batch_generate_btn = ModernAnimatedButton("🚀 Generate All Cards")
        apply_ios_style(self.batch_generate_btn, 'blue')
        self.batch_generate_btn.clicked.connect(self._batch_generate)
        batch_btn_row.addWidget(self.batch_generate_btn)

        self.batch_print_btn = ModernAnimatedButton("🖨️ Print Multiple Cards")
        apply_ios_style(self.batch_print_btn, 'green')
        self.batch_print_btn.clicked.connect(self._batch_print_dialog)
        batch_btn_row.addWidget(self.batch_print_btn)
        
        batch_layout.addLayout(batch_btn_row)

        batch_group.setLayout(batch_layout)
        content_layout.addWidget(batch_group)

        # Add stretch at bottom of scrollable content
        content_layout.addStretch()

        # Set the content widget to scroll area
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Close button (fixed at bottom, not scrollable)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = ModernAnimatedButton("Close")
        apply_ios_style(close_btn, 'gray')
        close_btn.clicked.connect(self.close)
        close_btn.setFixedHeight(35)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        self.current_card = None

    def _generate_single_card(self):
        emp_id = self.employee_combo.combo_box.currentData()
        if not emp_id:
            QMessageBox.warning(self, "No Selection", "Please select an employee first.")
            return

        # v3.1: Use default template only
        template = "standard"

        # Determine which side to generate
        if self.front_radio.isChecked():
            side = "front"
        elif self.back_radio.isChecked():
            side = "back"
        else:  # both_radio is checked
            side = "both"

        try:
            result = self.card_generator.generate_card(emp_id, template=template, side=side)

            if side == "both":
                # Handle both sides - create a composite image showing both
                from PIL import Image

                # Get the front and back images
                front_img = result['front']
                back_img = result['back']

                # Create a composite image with both cards side by side
                # Add 20 pixels spacing between cards
                spacing = 20
                composite_width = front_img.width + back_img.width + spacing
                composite_height = max(front_img.height, back_img.height)

                composite = Image.new('RGB', (composite_width, composite_height), color='white')
                composite.paste(front_img, (0, 0))
                composite.paste(back_img, (front_img.width + spacing, 0))

                # Save composite for preview
                temp_path = "temp_card_preview_both.png"
                composite.save(temp_path)

                pixmap = QPixmap(temp_path)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width() - 20,
                    self.preview_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)

                self.current_card = result  # Store both sides
                self.current_emp_id = emp_id
                self.save_btn.setEnabled(True)
                self.print_btn.setEnabled(True)

                QMessageBox.information(self, "Card Generated",
                    "Both sides generated successfully!\nPreview shows front (left) and back (right).")
            else:
                # Handle single side
                temp_path = "temp_card_preview.png"
                self.card_generator.save_card(result, temp_path)

                pixmap = QPixmap(temp_path)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width() - 20,
                    self.preview_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)

                self.save_btn.setEnabled(True)
                self.print_btn.setEnabled(True)
                self.current_card = result
                self.current_emp_id = emp_id

                side_text = "Front" if side == "front" else "Back"
                QMessageBox.information(self, "Card Generated", f"ID card ({side_text} side) generated successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate card:\n{str(e)}")

    def _save_single_card(self):
        if not self.current_card:
            QMessageBox.warning(self, "No Card", "Please generate a card first.")
            return

        # Check if we have both sides
        if isinstance(self.current_card, dict) and 'front' in self.current_card and 'back' in self.current_card:
            # Save both sides
            default_name = f"id_card_emp_{self.current_emp_id}_front.png"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save ID Card (Front)", default_name, "PNG Images (*.png)")

            if file_path:
                try:
                    # Save front
                    self.card_generator.save_card(self.current_card['front'], file_path)

                    # Generate back filename
                    back_path = file_path.replace("_front.png", "_back.png")
                    if back_path == file_path:  # If didn't contain "_front"
                        back_path = file_path.replace(".png", "_back.png")

                    # Save back
                    self.card_generator.save_card(self.current_card['back'], back_path)

                    QMessageBox.information(self, "Saved",
                        f"Both sides saved successfully:\n\nFront: {file_path}\nBack: {back_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save card:\n{str(e)}")
        else:
            # Save single side
            default_name = f"id_card_emp_{self.current_emp_id}.png"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save ID Card", default_name, "PNG Images (*.png)")

            if file_path:
                try:
                    self.card_generator.save_card(self.current_card, file_path)
                    QMessageBox.information(self, "Saved", f"ID card saved successfully to:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save card:\n{str(e)}")

    def _print_single_card(self):
        if not self.current_card:
            QMessageBox.warning(self, "No Card", "Please generate a card first.")
            return

        # Show print size selection dialog
        # v4.4.1: Animated dialog for print size selection
        from employee_vault.ui.widgets import QuickAnimatedDialog
        size_dialog = QuickAnimatedDialog(self, animation_style="fade")
        size_dialog.setWindowTitle("Select Print Size")
        size_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(size_dialog)
        
        layout.addWidget(QLabel("<h3>📐 Select ID Card Print Size</h3>"))
        layout.addWidget(QLabel("Choose the size for printing your ID card:"))
        
        # Size options with radio buttons
        size_group = QButtonGroup(size_dialog)
        
        # Actual size (recommended)
        actual_radio = QRadioButton("✓ Actual Size (Recommended)")
        actual_radio.setChecked(True)
        actual_info = QLabel("   → Prints at CR80 standard size (53.98mm × 85.6mm / 2.125\" × 3.375\")")
        actual_info.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
        
        # Half page
        half_radio = QRadioButton("Half Page Size")
        half_info = QLabel("   → Prints at ~105mm × 148mm (fits 2 per A4 page)")
        half_info.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
        
        # Quarter page  
        quarter_radio = QRadioButton("Quarter Page Size")
        quarter_info = QLabel("   → Prints at ~75mm × 105mm (fits 4 per A4 page)")
        quarter_info.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
        
        # Full page
        full_radio = QRadioButton("Full Page Size")
        full_info = QLabel("   → Prints across entire page (not recommended)")
        full_info.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px;")
        
        size_group.addButton(actual_radio, 1)
        size_group.addButton(quarter_radio, 2)
        size_group.addButton(half_radio, 3)
        size_group.addButton(full_radio, 4)
        
        layout.addWidget(actual_radio)
        layout.addWidget(actual_info)
        layout.addWidget(quarter_radio)
        layout.addWidget(quarter_info)
        layout.addWidget(half_radio)
        layout.addWidget(half_info)
        layout.addWidget(full_radio)
        layout.addWidget(full_info)
        
        layout.addWidget(QLabel("\n💡 Tip: Choose 'Actual Size' for standard ID cards that fit in card holders."))
        
        # Buttons
        btn_layout = QHBoxLayout()
        preview_btn = ModernAnimatedButton("👁️ Preview")
        preview_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00BCD4, stop:1 #00ACC1);
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ACC1, stop:1 #00BCD4);
            }
        """)
        print_btn = ModernAnimatedButton("🖨️ Print")
        cancel_btn = ModernAnimatedButton("Cancel")

        preview_btn.clicked.connect(lambda: self._show_print_preview(size_group))
        print_btn.clicked.connect(size_dialog.accept)
        cancel_btn.clicked.connect(size_dialog.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(preview_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        if size_dialog.exec() != QDialog.Accepted:
            return
        
        # Get selected size
        selected_id = size_group.checkedId()
        if selected_id == 1:
            scale_factor = 1.0  # Actual size
        elif selected_id == 2:
            scale_factor = 1.5  # Quarter page
        elif selected_id == 3:
            scale_factor = 2.5  # Half page
        else:
            scale_factor = 0  # Full page (auto-scale)

        # Check if we have both sides
        if isinstance(self.current_card, dict) and 'front' in self.current_card and 'back' in self.current_card:
            # v3.1: Print both sides using cross-platform QPrintPreviewDialog
            try:
                from PIL import Image
                from employee_vault.ui.dialogs.print_dialogs import print_image_with_preview
                
                # Create side-by-side layout
                front_img = self.current_card['front']
                back_img = self.current_card['back']
                
                # Add spacing between cards
                spacing = 40
                combined_width = front_img.width + back_img.width + spacing
                combined_height = max(front_img.height, back_img.height)
                
                # Create white background
                combined = Image.new('RGB', (combined_width, combined_height), color='white')
                combined.paste(front_img, (0, 0))
                combined.paste(back_img, (front_img.width + spacing, 0))
                
                # Print with mandatory preview
                print_image_with_preview(self, combined, "ID Card (Front & Back)")
            except Exception as e:
                QMessageBox.critical(self, "Print Error", f"Failed to print card:\n{str(e)}")
        else:
            # Print single side using cross-platform QPrintPreviewDialog
            try:
                from employee_vault.ui.dialogs.print_dialogs import print_image_with_preview
                print_image_with_preview(self, self.current_card, "ID Card")
            except Exception as e:
                QMessageBox.critical(self, "Print Error", f"Failed to print card:\n{str(e)}")

    def _show_print_preview(self, size_group):
        """Show print preview before actual printing"""
        if not self.current_card:
            QMessageBox.warning(self, "No Card", "Please generate a card first.")
            return

        # Get selected scale factor
        selected_id = size_group.checkedId()
        if selected_id == 1:
            scale_factor = 1.0  # Actual size
            size_text = "Actual Size (53.98mm × 85.6mm)"
        elif selected_id == 2:
            scale_factor = 1.5  # Quarter page
            size_text = "Quarter Page (~75mm × 105mm)"
        elif selected_id == 3:
            scale_factor = 2.5  # Half page
            size_text = "Half Page (~105mm × 148mm)"
        else:
            scale_factor = 0  # Full page
            size_text = "Full Page"

        # Create preview dialog
        from employee_vault.ui.widgets import SmoothAnimatedDialog
        preview_dialog = SmoothAnimatedDialog(self, animation_style="fade")
        preview_dialog.setWindowTitle(f"🖨️ Print Preview - {size_text}")
        preview_dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(preview_dialog)

        # Info label
        info_label = QLabel(f"<h3>📄 Print Preview - {size_text}</h3>")
        info_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(info_label)

        desc_label = QLabel("This is how your ID card will appear when printed:")
        desc_label.setStyleSheet("color: #757575; margin-bottom: 15px;")
        layout.addWidget(desc_label)

        # Scroll area for preview
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: #F5F5F5;
            }
        """)

        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setAlignment(Qt.AlignCenter)

        # Create preview image
        try:
            from PIL import Image
            import io

            # Check if we have both sides
            if isinstance(self.current_card, dict) and 'front' in self.current_card and 'back' in self.current_card:
                # Create side-by-side layout
                front_img = self.current_card['front']
                back_img = self.current_card['back']

                spacing = 40
                combined_width = front_img.width + back_img.width + spacing
                combined_height = max(front_img.height, back_img.height)

                # Create white background
                combined = Image.new('RGB', (combined_width, combined_height), color='white')
                combined.paste(front_img, (0, 0))
                combined.paste(back_img, (front_img.width + spacing, 0))

                preview_image = combined
            else:
                # Single side
                preview_image = self.current_card

            # Convert PIL Image to QPixmap
            img_byte_arr = io.BytesIO()
            preview_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(img_byte_arr.read())

            # Scale preview to fit window (but not larger than actual)
            max_width = 750
            if pixmap.width() > max_width:
                pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)

            # Display preview
            preview_label = QLabel()
            preview_label.setPixmap(pixmap)
            preview_label.setAlignment(Qt.AlignCenter)
            preview_layout.addWidget(preview_label)

            # Size information
            size_info = QLabel(f"Preview Size: {pixmap.width()} × {pixmap.height()} pixels")
            size_info.setStyleSheet("color: #757575; font-size: 11px; margin-top: 10px;")
            size_info.setAlignment(Qt.AlignCenter)
            preview_layout.addWidget(size_info)

        except Exception as e:
            error_label = QLabel(f"❌ Error generating preview:\n{str(e)}")
            error_label.setStyleSheet("color: #F44336; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            preview_layout.addWidget(error_label)

        scroll.setWidget(preview_widget)
        layout.addWidget(scroll, 1)

        # Close button
        close_btn = ModernAnimatedButton("✓ Close Preview")
        close_btn.clicked.connect(preview_dialog.accept)
        close_btn.setMinimumHeight(50)
        layout.addWidget(close_btn)

        preview_dialog.exec()

    def _browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_path_label.text())
        if directory:
            self.output_path_label.setText(directory)

    def _batch_generate(self):
        output_dir = self.output_path_label.text()

        if self.batch_all_radio.isChecked():
            target = "all employees"
            department = None
        else:
            department = self.dept_combo.combo_box.currentText()
            target = f"department: {department}"

        # Determine which side to generate for batch
        if self.batch_front_radio.isChecked():
            side = "front"
            side_text = "Front Only"
        elif self.batch_back_radio.isChecked():
            side = "back"
            side_text = "Back Only"
        else:  # batch_both_radio is checked
            side = "both"
            side_text = "Both Sides"

        reply = QMessageBox.question(self, "Batch Generation",
                                     f"Generate ID cards ({side_text}) for {target}?\n\nOutput: {output_dir}",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.No:
            return

        try:
            from PySide6.QtWidgets import QProgressDialog
            progress = QProgressDialog("Generating ID cards...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(0)
            progress.show()

            if department:
                result = self.card_generator.batch_generate(department=department, output_dir=output_dir, side=side)
            else:
                result = self.card_generator.batch_generate(output_dir=output_dir, side=side)

            progress.setValue(100)
            progress.close()

            success_count = len(result['success'])
            error_count = len(result['errors'])

            result_msg = (f"Batch generation complete!\n\n"
                         f"Total: {result['total']}\n"
                         f"Successful: {success_count}\n"
                         f"Errors: {error_count}\n\n"
                         f"Cards saved to:\n{output_dir}")

            if error_count > 0:
                result_msg += f"\n\nErrors:\n" + "\n".join(result['errors'][:5])

            # v3.2: Add "Go to Folder" option
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Batch Complete")
            msg_box.setText(result_msg)
            msg_box.setIcon(QMessageBox.Information)
            
            ok_btn = msg_box.addButton("OK", QMessageBox.AcceptRole)
            folder_btn = msg_box.addButton("📁 Go to Folder", QMessageBox.ActionRole)
            
            msg_box.exec()
            
            # Check which button was clicked
            if msg_box.clickedButton() == folder_btn:
                # Open folder in file explorer
                import subprocess
                import platform
                
                abs_output_dir = os.path.abspath(output_dir)
                if platform.system() == "Windows":
                    subprocess.Popen(f'explorer "{abs_output_dir}"')
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", abs_output_dir])
                else:  # Linux
                    subprocess.Popen(["xdg-open", abs_output_dir])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Batch generation failed:\n{str(e)}")

    def _batch_print_dialog(self):
        """Show dialog for batch printing multiple ID cards on one paper"""
        dialog = BatchPrintDialog(self, self.db, self.card_generator)
        dialog.exec()

# --- (The class MainWindow(QMainWindow) should start after this) ---

# ============================================================================
# BATCH PRINT DIALOG - Multiple Cards Per Page
# ============================================================================

