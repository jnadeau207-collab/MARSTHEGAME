"""
Simple enemies: bullies, rivals – improved silhouettes.
"""

import random
import pygame
from game.core.settings import Colors, GRAVITY


class Enemy:
    def __init__(self, x, y, kind="bully"):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.w = 26
        self.h = 34
        self.vx = 0.0
        self.vy = 0.0
        self.hp = 2 if kind == "bully" else 3
        self.max_hp = self.hp
        self.alive = True
        self.facing = -1
        self.timer = random.randint(0, 60)
        self.state = "idle"
        self.hurt_timer = 0
        self.speed = 1.7 if kind == "bully" else 2.3
        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)
        self.score_value = 10
        self.anim = random.random() * 10

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        return self.rect

    def update(self, dt, player, solids):
        if not self.alive:
            return
        self.timer += 1
        self.anim += dt * 0.12
        if self.hurt_timer > 0:
            self.hurt_timer -= 1

        dx = player.x - self.x
        dist = abs(dx)
        if dist < 240 and player.alive:
            self.facing = 1 if dx > 0 else -1
            self.vx = self.facing * self.speed
            self.state = "chase"
        else:
            if self.timer % 90 < 50:
                self.vx = self.facing * self.speed * 0.55
            else:
                self.vx = 0
                if self.timer % 90 == 50:
                    self.facing *= -1
            self.state = "patrol"

        self.vy += GRAVITY
        if self.vy > 14:
            self.vy = 14

        self.x += self.vx * dt
        self._resolve_x(solids)
        self.y += self.vy * dt
        self._resolve_y(solids)

        if player.alive and player.invuln == 0 and self.get_rect().colliderect(player.get_rect()):
            player.take_damage(1, -self.facing * 5, -4)

    def _resolve_x(self, solids):
        r = self.get_rect()
        for s in solids:
            if r.colliderect(s):
                if self.vx > 0:
                    self.x = s.left - self.w
                elif self.vx < 0:
                    self.x = s.right
                self.vx = 0
                self.facing *= -1
                r = self.get_rect()

    def _resolve_y(self, solids):
        r = self.get_rect()
        for s in solids:
            if r.colliderect(s):
                if self.vy > 0:
                    self.y = s.top - self.h
                    self.vy = 0
                elif self.vy < 0:
                    self.y = s.bottom
                    self.vy = 0
                r = self.get_rect()

    def take_damage(self, amount, kx=0, ky=0):
        if not self.alive:
            return
        self.hp -= amount
        self.hurt_timer = 12
        self.vx = kx
        self.vy = ky
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface, camera):
        if not self.alive:
            return
        ox, oy = camera.offset
        sx = int(self.x - ox)
        sy = int(self.y - oy)

        hurt = self.hurt_timer > 0
        if self.kind == "bully":
            body = Colors.DANGER if hurt else (95, 48, 38)
            head = (190, 155, 125) if not hurt else (220, 100, 90)
            pants = (45, 28, 22)
        else:  # rival
            body = Colors.DANGER if hurt else (50, 58, 95)
            head = (200, 170, 140) if not hurt else (220, 100, 90)
            pants = (30, 35, 55)

        # legs
        pygame.draw.rect(surface, pants, (sx + 5, sy + 24, 7, 10))
        pygame.draw.rect(surface, pants, (sx + 14, sy + 24, 7, 10))

        # torso
        pygame.draw.rect(surface, body, (sx + 4, sy + 10, 18, 16), border_radius=2)

        # head
        pygame.draw.ellipse(surface, head, (sx + 5, sy, 16, 13))

        # angry brows / eyes
        brow = (25, 15, 12)
        if self.facing > 0:
            pygame.draw.line(surface, brow, (sx + 10, sy + 4), (sx + 15, sy + 3), 2)
            pygame.draw.line(surface, brow, (sx + 16, sy + 4), (sx + 20, sy + 5), 2)
            pygame.draw.rect(surface, (20, 15, 10), (sx + 12, sy + 6, 3, 3))
            pygame.draw.rect(surface, (20, 15, 10), (sx + 17, sy + 6, 3, 3))
        else:
            pygame.draw.line(surface, brow, (sx + 6, sy + 5), (sx + 10, sy + 3), 2)
            pygame.draw.line(surface, brow, (sx + 11, sy + 3), (sx + 16, sy + 4), 2)
            pygame.draw.rect(surface, (20, 15, 10), (sx + 7, sy + 6, 3, 3))
            pygame.draw.rect(surface, (20, 15, 10), (sx + 12, sy + 6, 3, 3))

        # rival suit accent
        if self.kind == "rival" and not hurt:
            pygame.draw.line(surface, (80, 100, 160), (sx + 6, sy + 14), (sx + 20, sy + 14), 1)
