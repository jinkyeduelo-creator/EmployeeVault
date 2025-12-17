"""
Particle Effects System for EmployeeVault
Confetti, sparkles, and celebration animations
"""

import random
import math
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath


class Particle:
    """Individual particle with physics - Optimized with reset() for object pooling"""

    def __init__(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0,
                 color: QColor = None, size: float = 5, shape: str = "circle"):
        self.reset(x, y, vx, vy, color or QColor(255, 255, 255), size, shape)

    def reset(self, x: float, y: float, vx: float, vy: float,
              color: QColor, size: float, shape: str = "circle"):
        """Reset particle for reuse (object pooling optimization)"""
        self.x = x
        self.y = y
        self.vx = vx  # Velocity X
        self.vy = vy  # Velocity Y
        self.color = color
        self.size = size
        self.shape = shape
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        self.lifetime = 1.0  # 0 to 1
        self.fade_speed = random.uniform(0.005, 0.015)
        self.gravity = 0.2
    
    def update(self):
        """Update particle physics"""
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity  # Apply gravity
        self.rotation += self.rotation_speed
        self.lifetime -= self.fade_speed
        
        return self.lifetime > 0
    
    def draw(self, painter: QPainter):
        """Draw particle"""
        if self.lifetime <= 0:
            return
        
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(self.rotation)
        
        # Set color with lifetime-based opacity
        color = QColor(self.color)
        color.setAlphaF(self.lifetime)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        
        if self.shape == "circle":
            painter.drawEllipse(QPointF(0, 0), self.size, self.size)
        elif self.shape == "square":
            half = self.size / 2
            painter.drawRect(QRectF(-half, -half, self.size, self.size))
        elif self.shape == "triangle":
            path = QPainterPath()
            path.moveTo(0, -self.size)
            path.lineTo(-self.size, self.size)
            path.lineTo(self.size, self.size)
            path.closeSubpath()
            painter.drawPath(path)
        elif self.shape == "star":
            self._draw_star(painter, self.size)
        
        painter.restore()
    
    def _draw_star(self, painter: QPainter, size: float):
        """Draw 5-pointed star"""
        path = QPainterPath()
        points = 5
        outer_radius = size
        inner_radius = size * 0.4
        
        for i in range(points * 2):
            angle = i * math.pi / points - math.pi / 2
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        path.closeSubpath()
        painter.drawPath(path)


class ParticleEmitter(QWidget):
    """Particle emitter overlay widget - Optimized with object pooling"""

    def __init__(self, parent=None, max_particles=200):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Object pooling optimization - pre-allocate particles
        self.max_particles = max_particles
        self.particle_pool = [Particle() for _ in range(max_particles)]
        self.active_particles = []
        self.is_emitting = False

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_particles)
    
    def emit_confetti(self, count: int = 50, origin: QPointF = None):
        """Emit colorful confetti particles - Using object pool"""
        if origin is None:
            origin = QPointF(self.width() / 2, self.height() / 2)

        colors = [
            QColor(255, 107, 107),  # Red
            QColor(78, 205, 196),   # Teal
            QColor(255, 195, 0),    # Yellow
            QColor(138, 43, 226),   # Purple
            QColor(255, 165, 0),    # Orange
            QColor(46, 204, 113),   # Green
        ]

        shapes = ["circle", "square", "triangle"]

        particles_to_create = min(count, self.max_particles - len(self.active_particles))
        for i in range(particles_to_create):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 10)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(5, 10)  # Bias upward

            color = random.choice(colors)
            size = random.uniform(4, 8)
            shape = random.choice(shapes)

            # Reuse particle from pool instead of creating new
            particle = self.particle_pool[len(self.active_particles)]
            particle.reset(origin.x(), origin.y(), vx, vy, color, size, shape)
            self.active_particles.append(particle)

        self.start_animation()
    
    def emit_sparkles(self, count: int = 30, origin: QPointF = None):
        """Emit sparkling star particles - Using object pool"""
        if origin is None:
            origin = QPointF(self.width() / 2, self.height() / 2)

        particles_to_create = min(count, self.max_particles - len(self.active_particles))
        for _ in range(particles_to_create):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = QColor(255, 215, 0)  # Gold
            size = random.uniform(3, 6)

            # Reuse particle from pool
            particle = self.particle_pool[len(self.active_particles)]
            particle.reset(origin.x(), origin.y(), vx, vy, color, size, "star")
            particle.gravity = 0.05  # Less gravity for sparkles
            self.active_particles.append(particle)

        self.start_animation()
    
    def emit_success_burst(self, origin: QPointF = None):
        """Emit success celebration burst - Using object pool"""
        if origin is None:
            origin = QPointF(self.width() / 2, self.height() / 2)

        # Green sparkles in circle pattern
        particles_to_create = min(24, self.max_particles - len(self.active_particles))
        for i in range(particles_to_create):
            angle = (i / 24) * 2 * math.pi
            speed = 8
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = QColor(46, 204, 113)  # Green
            size = 5

            # Reuse particle from pool
            particle = self.particle_pool[len(self.active_particles)]
            particle.reset(origin.x(), origin.y(), vx, vy, color, size, "star")
            particle.gravity = 0.1
            self.active_particles.append(particle)

        self.start_animation()

    def emit_firework(self, origin: QPointF = None):
        """Emit firework explosion - Using object pool"""
        if origin is None:
            origin = QPointF(self.width() / 2, self.height() / 4)

        colors = [
            QColor(255, 107, 107),
            QColor(78, 205, 196),
            QColor(255, 195, 0),
        ]
        main_color = random.choice(colors)

        # Radial burst
        particles_to_create = min(40, self.max_particles - len(self.active_particles))
        for i in range(particles_to_create):
            angle = (i / 40) * 2 * math.pi
            speed = random.uniform(5, 12)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            size = random.uniform(2, 5)

            # Reuse particle from pool
            particle = self.particle_pool[len(self.active_particles)]
            particle.reset(origin.x(), origin.y(), vx, vy, main_color, size, "circle")
            particle.gravity = 0.15
            self.active_particles.append(particle)

        self.start_animation()

    def emit_trail(self, start: QPointF, end: QPointF, count: int = 20):
        """Emit particle trail from start to end - Using object pool"""
        colors = [
            QColor(138, 43, 226),
            QColor(255, 107, 107),
        ]

        particles_to_create = min(count, self.max_particles - len(self.active_particles))
        for i in range(particles_to_create):
            t = i / count
            x = start.x() + (end.x() - start.x()) * t
            y = start.y() + (end.y() - start.y()) * t

            vx = random.uniform(-2, 2)
            vy = random.uniform(-2, 2)

            color = random.choice(colors)
            size = random.uniform(2, 4)

            # Reuse particle from pool
            particle = self.particle_pool[len(self.active_particles)]
            particle.reset(x, y, vx, vy, color, size, "circle")
            particle.gravity = 0.05
            particle.fade_speed = 0.02
            self.active_particles.append(particle)

        self.start_animation()
    
    def start_animation(self):
        """Start particle animation timer"""
        if not self.update_timer.isActive():
            self.update_timer.start(16)  # ~60 FPS
    
    def update_particles(self):
        """Update all particles - Optimized with object pooling"""
        # Update particles in-place, remove dead ones
        self.active_particles = [p for p in self.active_particles if p.update()]

        if not self.active_particles:
            self.update_timer.stop()

        self.update()

    def paintEvent(self, event):
        """Draw all particles"""
        if not self.active_particles:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for particle in self.active_particles:
            particle.draw(painter)

    def clear(self):
        """Clear all particles"""
        self.active_particles.clear()
        self.update_timer.stop()
        self.update()


def create_celebration_effect(widget: QWidget, effect_type: str = "confetti"):
    """
    Create celebration effect overlay on widget
    
    Args:
        widget: Parent widget to overlay effect on
        effect_type: "confetti", "sparkles", "success", "firework"
    """
    emitter = ParticleEmitter(widget)
    emitter.setGeometry(widget.rect())
    emitter.raise_()
    
    center = QPointF(widget.width() / 2, widget.height() / 2)
    
    if effect_type == "confetti":
        emitter.emit_confetti(count=100, origin=center)
    elif effect_type == "sparkles":
        emitter.emit_sparkles(count=50, origin=center)
    elif effect_type == "success":
        emitter.emit_success_burst(origin=center)
    elif effect_type == "firework":
        emitter.emit_firework(origin=QPointF(widget.width() / 2, widget.height() / 4))
    
    # Auto-cleanup after animation
    def cleanup():
        if not emitter.particles:
            emitter.deleteLater()
    
    emitter.update_timer.timeout.connect(cleanup)
    
    return emitter
