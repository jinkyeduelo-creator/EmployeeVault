"""
Helper utility functions
"""

import re
import os
from difflib import SequenceMatcher
from PIL import Image
from io import BytesIO


def compress_image(image_path: str, max_size_kb: int = 500, quality: int = 85,
                  max_dimension: int = 1200) -> bool:
    """
    Compress an image file to reduce its size while maintaining quality

    Args:
        image_path: Path to the image file
        max_size_kb: Target maximum size in kilobytes (default: 500KB)
        quality: JPEG quality (1-100, default: 85)
        max_dimension: Maximum width/height in pixels (default: 1200)

    Returns:
        True if compression was successful, False otherwise
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode not in ('RGB', 'L'):
                if img.mode == 'RGBA':
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                    img = background
                else:
                    img = img.convert('RGB')

            # Resize if image is too large
            if max(img.width, img.height) > max_dimension:
                ratio = max_dimension / max(img.width, img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save with compression
            output_buffer = BytesIO()
            img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            output_size = output_buffer.tell()

            # If still too large, reduce quality iteratively
            current_quality = quality
            while output_size > max_size_kb * 1024 and current_quality > 30:
                current_quality -= 5
                output_buffer = BytesIO()
                img.save(output_buffer, format='JPEG', quality=current_quality, optimize=True)
                output_size = output_buffer.tell()

            # Write compressed image back to file
            with open(image_path, 'wb') as f:
                f.write(output_buffer.getvalue())

            return True

    except Exception as e:
        import logging
        logging.error(f"Error compressing image {image_path}: {e}")
        # Raise exception for better error handling
        raise RuntimeError(f"Failed to compress image: {str(e)}") from e


def normalize_ph_phone(raw: str) -> str:
    """
    Normalize Philippine phone number to +63 9XX XXX XXXX format

    Args:
        raw: Raw phone number string

    Returns:
        Formatted phone number or original if invalid
    """
    s = re.sub(r'\D', '', raw or '')
    if not s:
        return ""

    # Handle different formats
    if len(s) == 11 and s.startswith('09'):
        s = '63' + s[1:]
    elif len(s) == 10 and s.startswith('9'):
        s = '63' + s
    elif len(s) == 12 and s.startswith('63') and s[2] == '9':
        pass  # Already in correct format

    # Format as +63 9XX XXX XXXX
    if len(s) == 12 and s.startswith('63') and s[2] == '9':
        return f"+63 {s[2]}{s[3]}{s[4]} {s[5]}{s[6]}{s[7]} {s[8]}{s[9]}{s[10]}{s[11]}"

    return raw  # Return original if doesn't match expected format


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings (0.0 to 1.0)

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity ratio from 0.0 (completely different) to 1.0 (identical)
    """
    if not str1 or not str2:
        return 0.0

    # Normalize strings for comparison
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    return SequenceMatcher(None, s1, s2).ratio()


def find_similar_employees(first_name: str, middle_name: str, last_name: str,
                          existing_employees: list, threshold: float = 0.85,
                          exclude_emp_id: str = None) -> list:
    """
    Find employees with similar names to detect potential duplicates

    Args:
        first_name: First name to check
        middle_name: Middle name to check
        last_name: Last name to check
        existing_employees: List of existing employee dictionaries
        threshold: Similarity threshold (0.0 to 1.0), default 0.85
        exclude_emp_id: Employee ID to exclude from comparison (for edits)

    Returns:
        List of similar employee dictionaries with similarity scores
    """
    if not first_name or not last_name:
        return []

    # Normalize input name
    input_first = first_name.lower().strip()
    input_middle = (middle_name or '').lower().strip()
    input_last = last_name.lower().strip()
    input_full = f"{input_first} {input_middle} {input_last}".strip()

    similar_employees = []

    for emp in existing_employees:
        # Skip if this is the same employee (during edit)
        if exclude_emp_id and emp.get('emp_id') == exclude_emp_id:
            continue

        # Get employee name parts
        emp_first = (emp.get('first_name') or '').lower().strip()
        emp_middle = (emp.get('middle_name') or '').lower().strip()
        emp_last = (emp.get('last_name') or '').lower().strip()
        emp_full = f"{emp_first} {emp_middle} {emp_last}".strip()

        if not emp_first or not emp_last:
            continue

        # Calculate similarity for full name
        full_name_similarity = calculate_similarity(input_full, emp_full)

        # Also check first + last name (ignoring middle name)
        first_last_input = f"{input_first} {input_last}"
        first_last_emp = f"{emp_first} {emp_last}"
        first_last_similarity = calculate_similarity(first_last_input, first_last_emp)

        # Use the higher similarity score
        max_similarity = max(full_name_similarity, first_last_similarity)

        if max_similarity >= threshold:
            similar_employees.append({
                'employee': emp,
                'similarity': max_similarity,
                'match_type': 'full_name' if full_name_similarity >= threshold else 'first_last'
            })

    # Sort by similarity (highest first)
    similar_employees.sort(key=lambda x: x['similarity'], reverse=True)

    return similar_employees


def remove_background(image_path: str, output_path: str = None) -> str:
    """
    Remove background from an image using AI-based rembg library.
    Ideal for profile/avatar photos to get a clean, professional look.

    Args:
        image_path: Path to the input image file
        output_path: Optional path for output. If None, overwrites input file.

    Returns:
        Path to the processed image with transparent background

    Raises:
        RuntimeError: If background removal fails
    """
    import logging
    
    if output_path is None:
        output_path = image_path
    
    try:
        # Import rembg - this will download the model on first use (~170MB)
        from rembg import remove
        
        logging.info(f"Removing background from: {image_path}")
        
        # Read input image
        with open(image_path, 'rb') as f:
            input_data = f.read()
        
        # Remove background - returns PNG with alpha channel
        output_data = remove(input_data)
        
        # Ensure output path has .png extension for transparency
        if not output_path.lower().endswith('.png'):
            output_path = os.path.splitext(output_path)[0] + '.png'
        
        # Write output
        with open(output_path, 'wb') as f:
            f.write(output_data)
        
        logging.info(f"Background removed successfully: {output_path}")
        return output_path
        
    except ImportError as ie:
        logging.warning(f"rembg not available: {ie}. Using original image.")
        # If rembg not installed, just copy if needed
        if output_path != image_path:
            import shutil
            shutil.copy2(image_path, output_path)
        return output_path
        
    except Exception as e:
        logging.error(f"Background removal failed: {e}")
        # On failure, use original image as fallback
        if output_path != image_path:
            import shutil
            shutil.copy2(image_path, output_path)
        return output_path
