"""Telegraphed adaptive sentinel used by the Phase 1 Mars slice."""

from __future__ import annotations

import math

import pygame

from game.core import gfx
from game.core.settings import Colors, GRAVITY


class MarsSentinel:
    """A readable commit-and-recover enemy with failure-informed telegraphing."""

    def __init__(self, sentinel_id: str, x: float, y: float, tier: int = 1) -> None:
        if tier not in {1, 2, 3}:
            raise ValueError("sentinel tier must be 1, 2, or 3")
        self.sentinel_id = sentinel_id
        self.x = float(x)
        self.y = float(y)
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.tier = tier
        self.kind = "sentinel"
        self.w = 34
        self.h = 40
        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)
        self.max_hp = tier + 1
        self.hp = self.max_hp
        self.alive = True
        self.facing = -1
        self.state = "scan"
        self.timer = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.hurt_timer = 0.0
        self.insight_level = 0
        self.resource_disrupted = False
        self._charge_direction = -1
        self._anim = 0.0

    @property
    def vulnerable(self) -> bool:
        return self.state == "recover"

    def configure_encounter(self, insight_level: int, resource_disrupted: bool) -> None:
        self.insight_level = max(0, min(3, int(insight_level)))
        self.resource_disrupted = bool(resource_disrupted)
        if self.resource_disrupted and self.tier >= 2:
            self.max_hp = max(1, self.tier)
            self.hp = min(self.hp, self.max_hp)

    def get_rect(self) -> pygame.Rect:
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        return self.rect

    def reset(self, *, preserve_damage: bool = False) -> None:
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.state = "scan"
        self.timer = 0.0
        self.alive = True
        self.hurt_timer = 0.0
        if not preserve_damage:
            self.hp = self.max_hp

    def _resolve_x(self, solids) -> None:
        rect = self.get_rect()
        for solid in solids:
            if not rect.colliderect(solid):
                continue
            if self.vx > 0:
                self.x = solid.left - self.w
            elif self.vx < 0:
                self.x = solid.right
            self.vx = 0.0
            self.state = "recover"
            self.timer = 0.0
            rect = self.get_rect()

    def _resolve_y(self, solids) -> None:
        rect = self.get_rect()
        for solid in solids:
            if not rect.colliderect(solid):
                continue
            if self.vy > 0:
                self.y = solid.top - self.h
                self.vy = 0.0
            elif self.vy < 0:
                self.y = solid.bottom
                self.vy = 0.0
            rect = self.get_rect()

    def update(self, dt, player, solids) -> None:
        if not self.alive:
            return
        self.timer += dt
        self._anim += dt
        if self.hurt_timer > 0:
            self.hurt_timer = max(0.0, self.hurt_timer - dt)

        dx = player.x - self.x
        distance = abs(dx)
        self.facing = 1 if dx >= 0 else -1

        if self.state == "scan":
            self.vx *= 0.7
            if distance < 330:
                self.state = "windup"
                self.timer = 0.0
        elif self.state == "windup":
            self.vx = 0.0
            windup = 42.0 + self.insight_level * 9.0 + (8.0 if self.resource_disrupted else 0.0)
            if self.timer >= windup:
                self.state = "charge"
                self.timer = 0.0
                self._charge_direction = self.facing
                base_speed = 7.0 + self.tier * 1.4
                if self.resource_disrupted:
                    base_speed *= 0.82
                self.vx = self._charge_direction * base_speed
        elif self.state == "charge":
            if self.timer >= 28.0 + self.tier * 4.0:
                self.state = "recover"
                self.timer = 0.0
                self.vx *= 0.25
        elif self.state == "recover":
            self.vx *= 0.82
            recovery = max(28.0, 52.0 - self.insight_level * 5.0)
            if self.timer >= recovery:
                self.state = "scan"
                self.timer = 0.0

        self.vy = min(14.0, self.vy + GRAVITY)
        self.x += self.vx * dt
        self._resolve_x(solids)
        self.y += self.vy * dt
        self._resolve_y(solids)

        if (
            player.alive
            and player.invuln == 0
            and self.get_rect().colliderect(player.get_rect())
        ):
            damage = 2 if self.state == "charge" and self.tier >= 2 else 1
            player.take_damage(damage, -self.facing * 6, -5)
            if self.state == "charge":
                self.state = "recover"
                self.timer = 0.0
                self.vx *= -0.15

    def take_damage(self, amount, kx=0, ky=0) -> None:
        if not self.alive or not self.vulnerable:
            return
        self.hp -= int(amount)
        self.hurt_timer = 12.0
        self.vx = float(kx)
        self.vy = float(ky)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw(self, surface, camera) -> None:
        if not self.alive:
            return
        ox, oy = camera.offset
        sx = int(self.x - ox)
        sy = int(self.y - oy)
        pulse = 0.5 + 0.5 * math.sin(self._anim * 0.16)

        shadow = pygame.Surface((40, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, 40, 10))
        surface.blit(shadow, (sx - 3, sy + self.h - 5))

        if self.state == "windup":
            core = (255, 170, 60)
            radius = 16 + int(pulse * 8)
            gfx.soft_circle_additive(surface, core, (sx + 17, sy + 18), radius)
        elif self.state == "charge":
            core = (255, 60, 50)
            gfx.soft_circle_additive(surface, core, (sx + 17, sy + 18), 22)
        elif self.state == "recover":
            core = Colors.ACCENT if self.resource_disrupted else (100, 220, 255)
            gfx.soft_circle_additive(surface, core, (sx + 17, sy + 18), 18)
        else:
            core = (120, 150, 190)

        body = (85, 96, 112) if self.hurt_timer <= 0 else (190, 78, 66)
        body_hi = gfx.shade(body, 38)
        body_lo = gfx.shade(body, -38)
        pygame.draw.polygon(
            surface,
            body_lo,
            [(sx + 5, sy + 11), (sx + 29, sy + 11), (sx + 25, sy + 34), (sx + 9, sy + 34)],
        )
        pygame.draw.polygon(
            surface,
            body,
            [(sx + 7, sy + 10), (sx + 27, sy + 10), (sx + 23, sy + 30), (sx + 11, sy + 30)],
        )
        pygame.draw.line(surface, body_hi, (sx + 9, sy + 12), (sx + 25, sy + 12), 3)
        pygame.draw.circle(surface, body_lo, (sx + 17, sy + 7), 8)
        pygame.draw.circle(surface, body, (sx + 17, sy + 6), 7)
        pygame.draw.circle(surface, core, (sx + 17, sy + 6), 3)
        pygame.draw.circle(surface, core, (sx + 17, sy + 20), 4)

        leg_offset = int(math.sin(self._anim * 0.22) * 2) if self.state == "charge" else 0
        pygame.draw.rect(surface, body_lo, (sx + 9, sy + 29 + leg_offset, 6, 11))
        pygame.draw.rect(surface, body_lo, (sx + 20, sy + 29 - leg_offset, 6, 11))
        pygame.draw.rect(surface, (35, 38, 46), (sx + 6, sy + 37 + leg_offset, 10, 4))
        pygame.draw.rect(surface, (35, 38, 46), (sx + 19, sy + 37 - leg_offset, 10, 4))

        if self.state == "recover":
            pygame.draw.arc(surface, core, (sx - 5, sy - 8, 44, 50), 0.2, 2.9, 2)
            pygame.draw.arc(surface, core, (sx, sy - 3, 34, 40), 3.3, 6.0, 2)

        health_width = 32
        pygame.draw.rect(surface, (20, 20, 26), (sx + 1, sy - 10, health_width, 4))
        fill = int(health_width * self.hp / max(1, self.max_hp))
        pygame.draw.rect(surface, core, (sx + 1, sy - 10, fill, 4))
