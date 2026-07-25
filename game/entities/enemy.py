"""
Simple enemies: bullies, rivals, drones – silhouette readable.
"""

import random
import pygame
from game.core.settings import Colors, GRAVITY


class Enemy:
    def __init__(self, x, y, kind="bully"):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.w = 24
        self.h = 32
        self.vx = 0.0
        self.vy = 0.0
        self.hp = 2 if kind == "bully" else 3
        self.max_hp = self.hp
        self.alive = True
        self.facing = -1
        self.timer = random.randint(0, 60)
        self.state = "idle"
        self.hurt_timer = 0
        self.speed = 1.6 if kind == "bully" else 2.2
        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)
        self.score_value = 10

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        return self.rect

    def update(self, dt, player, solids):
        if not self.alive:
            return
        self.timer += 1
        if self.hurt_timer > 0:
            self.hurt_timer -= 1

        dx = player.x - self.x
        dist = abs(dx)
        if dist < 220 and player.alive:
            self.facing = 1 if dx > 0 else -1
            self.vx = self.facing * self.speed
            self.state = "chase"
        else:
            if self.timer % 90 < 45:
                self.vx = self.facing * self.speed * 0.6
            else:
                self.vx = 0
                if self.timer % 90 == 45:
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
        self.hurt_timer = 10
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
        col = Colors.DANGER if self.hurt_timer > 0 else (90, 50, 40)
        if self.kind == "rival":
            col = (60, 70, 110) if self.hurt_timer == 0 else Colors.DANGER
        pygame.draw.rect(surface, col, (sx + 3, sy + 6, 18, 20))
        pygame.draw.rect(surface, (180, 150, 120), (sx + 5, sy, 14, 10))
        pygame.draw.line(surface, (20, 10, 10), (sx + 7, sy + 4), (sx + 11, sy + 5), 2)
        pygame.draw.line(surface, (20, 10, 10), (sx + 13, sy + 5), (sx + 17, sy + 4), 2)
        pygame.draw.rect(surface, (50, 30, 25), (sx + 5, sy + 26, 6, 6))
        pygame.draw.rect(surface, (50, 30, 25), (sx + 13, sy + 26, 6, 6))
