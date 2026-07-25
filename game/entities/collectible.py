"""
Books, parts, code fragments – scavenging. Improved icons.
"""

import math
import pygame
from game.core.settings import Colors


class Collectible:
    def __init__(self, x, y, kind="book"):
        self.x = x
        self.y = y
        self.kind = kind
        self.w = 16
        self.h = 16
        self.alive = True
        self.bob = random_bob()
        self.rect = pygame.Rect(x, y, self.w, self.h)

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y + math.sin(self.bob) * 3.5)
        return self.rect

    def update(self, dt, player):
        if not self.alive:
            return
        self.bob += 0.09 * dt
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
        sy = int(self.y + math.sin(self.bob) * 3.5 - oy)

        # soft glow
        glow_col = {
            "book": (60, 100, 180),
            "part": (200, 160, 40),
            "code": (0, 180, 230),
            "health": (60, 200, 100),
        }.get(self.kind, (150, 150, 150))
        pygame.draw.circle(surface, (*glow_col, 40) if False else glow_col, (sx + 8, sy + 8), 10)
        pygame.draw.circle(surface, (20, 20, 30), (sx + 8, sy + 8), 9)

        if self.kind == "book":
            pygame.draw.rect(surface, (55, 95, 155), (sx + 2, sy + 1, 12, 14), border_radius=1)
            pygame.draw.rect(surface, (200, 205, 220), (sx + 4, sy + 3, 8, 2))
            pygame.draw.rect(surface, (180, 185, 200), (sx + 4, sy + 7, 8, 1))
            pygame.draw.rect(surface, (180, 185, 200), (sx + 4, sy + 10, 6, 1))
        elif self.kind == "part":
            pygame.draw.rect(surface, Colors.GOLD, (sx + 2, sy + 3, 12, 10), border_radius=2)
            pygame.draw.rect(surface, (40, 40, 50), (sx + 5, sy + 5, 6, 6))
            pygame.draw.circle(surface, (80, 80, 90), (sx + 8, sy + 8), 2)
        elif self.kind == "code":
            pygame.draw.rect(surface, Colors.ACCENT, (sx + 1, sy + 2, 14, 12), border_radius=2)
            pygame.draw.line(surface, (10, 20, 30), (sx + 3, sy + 5), (sx + 12, sy + 5), 1)
            pygame.draw.line(surface, (10, 20, 30), (sx + 3, sy + 8), (sx + 9, sy + 8), 1)
            pygame.draw.line(surface, (10, 20, 30), (sx + 3, sy + 11), (sx + 11, sy + 11), 1)
        elif self.kind == "health":
            pygame.draw.rect(surface, Colors.SUCCESS, (sx + 6, sy + 1, 4, 14))
            pygame.draw.rect(surface, Colors.SUCCESS, (sx + 1, sy + 6, 14, 4))


def random_bob():
    import random
    return random.uniform(0, 6.28)
