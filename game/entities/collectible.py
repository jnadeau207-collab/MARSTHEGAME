"""
Collectibles with glow, spin, and sparkle.
"""

import math
import random

import pygame

from game.core import gfx
from game.core.settings import Colors


class Collectible:
    def __init__(self, x, y, kind="book"):
        self.x = x
        self.y = y
        self.kind = kind
        self.w = 18
        self.h = 18
        self.alive = True
        self.bob = random.uniform(0, 6.28)
        self.spin = random.uniform(0, 6.28)
        self.rect = pygame.Rect(x, y, self.w, self.h)

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y + math.sin(self.bob) * 4)
        return self.rect

    def update(self, dt, player):
        if not self.alive:
            return
        self.bob += 0.1 * dt
        self.spin += 0.08 * dt
        if self.get_rect().colliderect(player.get_rect()):
            self.alive = False
            if self.kind == "book":
                player.books += 1
            elif self.kind == "part":
                player.parts += 1
            elif self.kind == "health":
                player.heal(1)
            return True
        return False

    def draw(self, surface, camera):
        if not self.alive:
            return
        ox, oy = camera.offset
        sx = int(self.x - ox)
        sy = int(self.y + math.sin(self.bob) * 4 - oy)
        cx, cy = sx + 9, sy + 9

        glow = {
            "book": (50, 100, 200),
            "part": (255, 190, 40),
            "code": (0, 210, 255),
            "health": (50, 230, 100),
        }.get(self.kind, (180, 180, 180))

        pulse = 11 + int(3 * math.sin(self.bob * 2))
        gfx.soft_circle(surface, glow, (cx, cy), pulse, layers=4)

        if self.kind == "book":
            pygame.draw.rect(surface, (40, 70, 130), (sx + 2, sy + 1, 14, 16), border_radius=2)
            pygame.draw.rect(surface, (70, 110, 180), (sx + 3, sy + 2, 12, 14), border_radius=1)
            pygame.draw.rect(surface, (220, 225, 240), (sx + 5, sy + 4, 8, 2))
            pygame.draw.rect(surface, (200, 205, 220), (sx + 5, sy + 8, 8, 1))
            pygame.draw.rect(surface, (200, 205, 220), (sx + 5, sy + 11, 6, 1))
            pygame.draw.line(surface, (30, 50, 90), (sx + 9, sy + 2), (sx + 9, sy + 15), 1)
        elif self.kind == "part":
            # gear-like
            pygame.draw.circle(surface, Colors.GOLD, (cx, cy), 8)
            pygame.draw.circle(surface, (40, 35, 20), (cx, cy), 4)
            pygame.draw.circle(surface, (255, 220, 100), (cx, cy), 8, 1)
            for a in range(0, 360, 45):
                rad = math.radians(a + self.spin * 40)
                px = cx + int(math.cos(rad) * 9)
                py = cy + int(math.sin(rad) * 9)
                pygame.draw.rect(surface, Colors.GOLD, (px - 2, py - 2, 4, 4))
        elif self.kind == "code":
            pygame.draw.rect(surface, (0, 40, 60), (sx + 1, sy + 2, 16, 14), border_radius=3)
            pygame.draw.rect(surface, Colors.ACCENT, (sx + 2, sy + 3, 14, 12), border_radius=2)
            for i, w in enumerate((10, 7, 11)):
                pygame.draw.line(
                    surface, (0, 30, 40), (sx + 4, sy + 6 + i * 3), (sx + 4 + w, sy + 6 + i * 3), 1
                )
            # blink cursor
            if int(self.bob * 3) % 2:
                pygame.draw.rect(surface, (255, 255, 255), (sx + 5, sy + 13, 5, 1))
        elif self.kind == "health":
            # cross with depth
            pygame.draw.rect(surface, (20, 80, 40), (sx + 7, sy + 1, 5, 16), border_radius=1)
            pygame.draw.rect(surface, (20, 80, 40), (sx + 1, sy + 7, 16, 5), border_radius=1)
            pygame.draw.rect(surface, Colors.SUCCESS, (sx + 8, sy + 2, 3, 14))
            pygame.draw.rect(surface, Colors.SUCCESS, (sx + 2, sy + 8, 14, 3))
            gfx.soft_circle(surface, (100, 255, 140), (cx, cy), 6, layers=2)
