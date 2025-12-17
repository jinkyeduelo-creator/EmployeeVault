"""
Photo Thumbnail Cache
v5.3.0: LRU cache for employee photo thumbnails to improve performance
"""

import os
import logging
import threading
from typing import Optional, Dict
from collections import OrderedDict
from pathlib import Path

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QSize


class ThumbnailCache:
    """
    Thread-safe LRU cache for employee photo thumbnails.
    Reduces disk I/O and improves table rendering performance.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, max_size: int = 200):
        """Singleton pattern for global cache"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_size: int = 200):
        """Initialize cache with max size"""
        if self._initialized:
            return
            
        self._cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._max_size = max_size
        self._cache_lock = threading.Lock()
        self._initialized = True
        logging.info(f"ThumbnailCache initialized with max_size={max_size}")
        
    def get(self, emp_id: str, size: int = 50) -> Optional[QPixmap]:
        """
        Get cached thumbnail for employee.
        
        Args:
            emp_id: Employee ID
            size: Thumbnail size in pixels
            
        Returns:
            Cached QPixmap or None if not in cache
        """
        cache_key = f"{emp_id}_{size}"
        
        with self._cache_lock:
            if cache_key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key]
        return None
        
    def put(self, emp_id: str, pixmap: QPixmap, size: int = 50):
        """
        Store thumbnail in cache.
        
        Args:
            emp_id: Employee ID
            pixmap: Thumbnail QPixmap
            size: Thumbnail size in pixels
        """
        cache_key = f"{emp_id}_{size}"
        
        with self._cache_lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
                
            self._cache[cache_key] = pixmap
            self._cache.move_to_end(cache_key)
            
    def invalidate(self, emp_id: str):
        """
        Invalidate all cached thumbnails for an employee.
        Call this when employee photo is updated.
        
        Args:
            emp_id: Employee ID to invalidate
        """
        with self._cache_lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{emp_id}_")]
            for key in keys_to_remove:
                del self._cache[key]
                
        logging.debug(f"Invalidated cache for employee {emp_id}")
        
    def clear(self):
        """Clear entire cache"""
        with self._cache_lock:
            self._cache.clear()
        logging.info("ThumbnailCache cleared")
        
    def stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._cache_lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'available': self._max_size - len(self._cache)
            }


def get_thumbnail_cache() -> ThumbnailCache:
    """Get the global thumbnail cache instance"""
    return ThumbnailCache()


def load_employee_thumbnail(
    emp_id: str,
    photo_path: str,
    size: int = 50,
    use_cache: bool = True
) -> Optional[QPixmap]:
    """
    Load employee photo thumbnail with caching.
    
    Args:
        emp_id: Employee ID
        photo_path: Path to photo file
        size: Thumbnail size in pixels
        use_cache: Whether to use cache (default True)
        
    Returns:
        QPixmap thumbnail or None if photo doesn't exist
    """
    cache = get_thumbnail_cache()
    
    # Check cache first
    if use_cache:
        cached = cache.get(emp_id, size)
        if cached is not None:
            return cached
    
    # Load from disk
    if not photo_path or not os.path.exists(photo_path):
        return None
        
    try:
        pixmap = QPixmap(photo_path)
        
        if pixmap.isNull():
            return None
            
        # Scale to thumbnail size
        scaled = pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Store in cache
        if use_cache:
            cache.put(emp_id, scaled, size)
            
        return scaled
        
    except Exception as e:
        logging.warning(f"Error loading thumbnail for {emp_id}: {e}")
        return None


def create_circular_thumbnail(
    pixmap: QPixmap,
    size: int = 50
) -> QPixmap:
    """
    Create a circular thumbnail from a pixmap.
    
    Args:
        pixmap: Source pixmap
        size: Output size in pixels
        
    Returns:
        Circular QPixmap
    """
    from PySide6.QtGui import QPainter, QBrush, QPainterPath
    
    # Scale pixmap to size
    scaled = pixmap.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )
    
    # Create circular mask
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Clip to circle
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    
    # Center the image
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    
    painter.end()
    
    return result


class ThumbnailLoader:
    """
    Helper class for loading thumbnails in batch.
    Useful for populating tables efficiently.
    """
    
    def __init__(self, photo_dir: str, size: int = 50):
        """
        Initialize loader.
        
        Args:
            photo_dir: Directory containing employee photos
            size: Thumbnail size in pixels
        """
        self.photo_dir = photo_dir
        self.size = size
        self.cache = get_thumbnail_cache()
        
    def load_for_employee(self, emp_id: str) -> Optional[QPixmap]:
        """
        Load thumbnail for a specific employee.
        
        Args:
            emp_id: Employee ID
            
        Returns:
            QPixmap or None
        """
        # Common photo naming patterns
        patterns = [
            f"{emp_id}.jpg",
            f"{emp_id}.jpeg",
            f"{emp_id}.png",
            f"{emp_id}_photo.jpg",
            f"{emp_id}_photo.png"
        ]
        
        for pattern in patterns:
            photo_path = os.path.join(self.photo_dir, pattern)
            if os.path.exists(photo_path):
                return load_employee_thumbnail(emp_id, photo_path, self.size)
                
        return None
        
    def preload_batch(self, emp_ids: list):
        """
        Preload thumbnails for a batch of employees.
        
        Args:
            emp_ids: List of employee IDs to preload
        """
        for emp_id in emp_ids:
            # Only load if not already cached
            if self.cache.get(emp_id, self.size) is None:
                self.load_for_employee(emp_id)
