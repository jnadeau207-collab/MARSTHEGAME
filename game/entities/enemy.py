"""
Enemies with shaded, detailed silhouettes.
"""

import random

import pygame

from game.core import gfx
from game.core.settings import GRAVITY


class Enemy:
    def __init__(self, x, y, kind="bully"):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.w = 28
        self.h = 36
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
        self.anim += dt * 0.14
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
        f = self.facing

        # shadow
        sh = pygame.Surface((30, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), (0, 0, 30, 8))
        surface.blit(sh, (sx - 1, sy + self.h - 4))

        if self.kind == "bully":
            body = (160, 45, 35) if hurt else (88, 42, 32)
            body_hi = (200, 70, 55) if hurt else (110, 55, 42)
            body_lo = (60, 28, 22)
            head = (210, 100, 90) if hurt else (195, 160, 130)
            pants = (40, 25, 20)
        else:
            body = (180, 50, 50) if hurt else (45, 52, 88)
            body_hi = (220, 80, 80) if hurt else (65, 75, 120)
            body_lo = (30, 35, 55)
            head = (210, 100, 90) if hurt else (205, 175, 145)
            pants = (28, 30, 48)

        # legs walk cycle
        phase = int(self.anim * 8) % 4 if abs(self.vx) > 0.3 else 0
        offs = [0, 2, 0, -2]
        lo = offs[phase]
        pygame.draw.rect(surface, pants, (sx + 6, sy + 26 + lo, 7, 10), border_radius=1)
        pygame.draw.rect(surface, pants, (sx + 15, sy + 26 - lo, 7, 10), border_radius=1)
        pygame.draw.rect(surface, (20, 15, 12), (sx + 5, sy + 34 + lo, 9, 3))
        pygame.draw.rect(surface, (20, 15, 12), (sx + 14, sy + 34 - lo, 9, 3))

        # torso shaded
        pygame.draw.rect(surface, body_lo, (sx + 4, sy + 11, 20, 17), border_radius=3)
        pygame.draw.rect(surface, body, (sx + 5, sy + 11, 18, 14), border_radius=2)
        pygame.draw.rect(surface, body_hi, (sx + 6, sy + 11, 16, 5), border_radius=2)

        if self.kind == "rival" and not hurt:
            pygame.draw.line(surface, (90, 110, 170), (sx + 7, sy + 16), (sx + 21, sy + 16), 1)
            pygame.draw.circle(surface, (120, 140, 200), (sx + 14, sy + 20), 2)

        # head
        pygame.draw.ellipse(surface, gfx.shade(head, -25), (sx + 5, sy + 1, 18, 14))
        pygame.draw.ellipse(surface, head, (sx + 6, sy, 16, 13))

        # angry brows + eyes
        brow = (30, 18, 12)
        if f > 0:
            pygame.draw.line(surface, brow, (sx + 10, sy + 4), (sx + 15, sy + 2), 2)
            pygame.draw.line(surface, brow, (sx + 16, sy + 2), (sx + 21, sy + 4), 2)
            pygame.draw.rect(surface, (15, 10, 8), (sx + 12, sy + 5, 3, 3))
            pygame.draw.rect(surface, (15, 10, 8), (sx + 18, sy + 5, 3, 3))
            if self.state == "chase":
                pygame.draw.rect(surface, (220, 40, 30), (sx + 13, sy + 6, 1, 1))
                pygame.draw.rect(surface, (220, 40, 30), (sx + 19, sy + 6, 1, 1))
        else:
            pygame.draw.line(surface, brow, (sx + 7, sy + 4), (sx + 12, sy + 2), 2)
            pygame.draw.line(surface, brow, (sx + 13, sy + 2), (sx + 18, sy + 4), 2)
            pygame.draw.rect(surface, (15, 10, 8), (sx + 8, sy + 5, 3, 3))
            pygame.draw.rect(surface, (15, 10, 8), (sx + 14, sy + 5, 3, 3))

        # fists when chasing
        if self.state == "chase":
            fx = sx + (24 if f > 0 else 0)
            pygame.draw.circle(surface, head, (fx, sy + 18), 4)
            pygame.draw.circle(surface, gfx.shade(head, -20), (fx, sy + 18), 4, 1)
