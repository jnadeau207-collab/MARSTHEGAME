"""
Books, parts, code fragments – scavenging.
"""

import pygame
from game.core.settings import Colors


class Collectible:
    def __init__(self, x, y, kind="book"):
        self.x = x
        self.y = y
        self.kind = kind
        self.w = 14
        self.h = 14
        self.alive = True
        self.bob = 0
        self.rect = pygame.Rect(x, y, self.w, self.h)

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y + __import__("math").sin(self.bob) * 3)
        return self.rect

    def update(self, dt, player):
        if not self.alive:
            return
        self.bob += 0.08 * dt
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
        sy = int(self.y + __import__("math").sin(self.bob) * 3 - oy)
        if self.kind == "book":
            pygame.draw.rect(surface, (60, 100, 160), (sx, sy, 12, 14))
            pygame.draw.rect(surface, (200, 200, 220), (sx + 2, sy + 2, 8, 2))
        elif self.kind == "part":
            pygame.draw.rect(surface, Colors.GOLD, (sx, sy, 12, 10))
            pygame.draw.rect(surface, (40, 40, 40), (sx + 3, sy + 3, 6, 4))
        elif self.kind == "code":
            pygame.draw.rect(surface, Colors.ACCENT, (sx, sy, 14, 12))
            pygame.draw.line(surface, Colors.BLACK, (sx + 2, sy + 3), (sx + 11, sy + 3), 1)
            pygame.draw.line(surface, Colors.BLACK, (sx + 2, sy + 6), (sx + 8, sy + 6), 1)
        elif self.kind == "health":
            pygame.draw.rect(surface, Colors.SUCCESS, (sx + 4, sy, 6, 14))
            pygame.draw.rect(surface, Colors.SUCCESS, (sx, sy + 4, 14, 6))
