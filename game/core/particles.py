"""
Lightweight particle system for juice (hit sparks, dust, explosions).
"""

import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size=3, gravity=0.15):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity


class ParticleSystem:
    def __init__(self, max_particles=400):
        self.particles = []
        self.max_particles = max_particles

    def emit(self, x, y, count=8, speed=3.0, color=(255, 200, 80), life=30, size=3, gravity=0.15, spread=1.0):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                self.particles.pop(0)
            angle = random.uniform(0, 6.2832)
            spd = random.uniform(speed * 0.3, speed) * spread
            vx = spd * __import__("math").cos(angle)
            vy = spd * __import__("math").sin(angle) - random.uniform(0, speed * 0.4)
            self.particles.append(Particle(x, y, vx, vy, life + random.randint(-5, 5), color, size, gravity))

    def emit_burst(self, x, y, color=(255, 100, 50)):
        self.emit(x, y, count=16, speed=5.5, color=color, life=25, size=4)

    def emit_dust(self, x, y):
        self.emit(x, y, count=4, speed=1.5, color=(120, 100, 80), life=20, size=2, gravity=0.05)

    def update(self):
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravity
            p.life -= 1
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface, camera_x=0, camera_y=0):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / p.max_life))))
            r, g, b = p.color
            s = max(1, int(p.size * (p.life / p.max_life)))
            sx = int(p.x - camera_x)
            sy = int(p.y - camera_y)
            if -10 < sx < surface.get_width() + 10 and -10 < sy < surface.get_height() + 10:
                pygame.draw.circle(surface, (r, g, b), (sx, sy), s)
