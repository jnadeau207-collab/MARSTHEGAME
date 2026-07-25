"""
Particle system with soft glow and varied styles.
"""

import math
import random
import pygame
from game.core import gfx


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity", "style")

    def __init__(self, x, y, vx, vy, life, color, size=3, gravity=0.15, style="circle"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = max(1, life)
        self.color = color
        self.size = size
        self.gravity = gravity
        self.style = style


class ParticleSystem:
    def __init__(self, max_particles=600):
        self.particles = []
        self.max_particles = max_particles

    def emit(self, x, y, count=8, speed=3.0, color=(255, 200, 80), life=30, size=3,
             gravity=0.15, spread=1.0, style="circle"):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                self.particles.pop(0)
            angle = random.uniform(0, 6.2832)
            spd = random.uniform(speed * 0.25, speed) * spread
            vx = spd * math.cos(angle)
            vy = spd * math.sin(angle) - random.uniform(0, speed * 0.45)
            self.particles.append(Particle(
                x, y, vx, vy, life + random.randint(-6, 6), color,
                size + random.randint(0, 1), gravity, style))

    def emit_burst(self, x, y, color=(255, 100, 50)):
        self.emit(x, y, count=22, speed=6.0, color=color, life=28, size=4, style="glow")
        self.emit(x, y, count=8, speed=3.0, color=(255, 220, 150), life=18, size=2)

    def emit_dust(self, x, y):
        self.emit(x, y, count=6, speed=1.8, color=(140, 115, 85), life=24, size=2, gravity=0.04)

    def update(self):
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravity
            p.vx *= 0.99
            p.life -= 1
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface, camera_x=0, camera_y=0):
        w, h = surface.get_width(), surface.get_height()
        for p in self.particles:
            t = p.life / p.max_life
            s = max(1, int(p.size * (0.4 + 0.6 * t)))
            sx = int(p.x - camera_x)
            sy = int(p.y - camera_y)
            if not (-20 < sx < w + 20 and -20 < sy < h + 20):
                continue
            r, g, b = p.color
            if p.style == "glow" and s >= 2:
                gfx.soft_circle(surface, (r, g, b), (sx, sy), s + 3, layers=3)
            else:
                # fade by darkening toward bg (cheap alpha)
                fade = 0.35 + 0.65 * t
                col = (int(r * fade), int(g * fade), int(b * fade))
                pygame.draw.circle(surface, col, (sx, sy), s)
