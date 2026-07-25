"""
Player: Elon. Responsive movement, coyote, buffer, dash, light combat.
"""

import pygame
from game.core.settings import (
    GRAVITY, PLAYER_SPEED, PLAYER_JUMP, PLAYER_DASH_SPEED,
    PLAYER_DASH_DURATION, COYOTE_TIME, JUMP_BUFFER, Colors
)


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w = 22
        self.h = 36
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.hp = 5
        self.max_hp = 5
        self.invuln = 0
        self.dash_timer = 0
        self.dash_dir = 0
        self.coyote = 0
        self.jump_buffer = 0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.books = 0
        self.parts = 0
        self.state = "idle"
        self.alive = True
        self.can_dash = True
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        return self.rect

    def update(self, dt, inp, solids, enemies, particles, camera, engine):
        if not self.alive:
            return

        if self.invuln > 0:
            self.invuln -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1

        if self.on_ground:
            self.coyote = COYOTE_TIME
        elif self.coyote > 0:
            self.coyote -= 1

        if inp.has_buffer("jump") or inp.just_pressed("jump"):
            self.jump_buffer = JUMP_BUFFER
        elif self.jump_buffer > 0:
            self.jump_buffer -= 1

        if self.dash_timer > 0:
            self.dash_timer -= 1
            self.vx = self.dash_dir * PLAYER_DASH_SPEED
            self.vy = 0
            self.state = "dash"
            if self.dash_timer == 0:
                self.vx *= 0.4
        else:
            ax, _ = inp.get_axis()
            if ax != 0:
                self.facing = 1 if ax > 0 else -1
                self.vx = ax * PLAYER_SPEED
                self.state = "run" if self.on_ground else self.state
            else:
                self.vx *= 0.75
                if abs(self.vx) < 0.3:
                    self.vx = 0
                    if self.on_ground:
                        self.state = "idle"

            if self.jump_buffer > 0 and self.coyote > 0:
                self.vy = PLAYER_JUMP
                self.on_ground = False
                self.coyote = 0
                self.jump_buffer = 0
                inp.consume_buffer("jump")
                particles.emit_dust(self.x + self.w / 2, self.y + self.h)
                self.state = "jump"

            if not inp.is_held("jump") and self.vy < -4:
                self.vy *= 0.6

            if self.can_dash and (inp.just_pressed("dash") or inp.consume_buffer("dash")) and self.dash_timer == 0:
                self.dash_timer = PLAYER_DASH_DURATION
                self.dash_dir = self.facing
                self.invuln = max(self.invuln, 8)
                particles.emit(self.x + self.w / 2, self.y + self.h / 2, count=6, speed=2, color=Colors.ACCENT)

            if (inp.just_pressed("attack") or inp.consume_buffer("attack")) and self.attack_cooldown == 0:
                self.attack_timer = 12
                self.attack_cooldown = 22
                self.state = "attack"
                hx = self.x + (self.w if self.facing > 0 else -28)
                hit = pygame.Rect(hx, self.y + 4, 28, 28)
                for e in enemies:
                    if e.alive and hit.colliderect(e.get_rect()):
                        e.take_damage(1, self.facing * 4, -3)
                        particles.emit_burst(e.x + e.w / 2, e.y + e.h / 2)
                        engine.trigger_hit_stop(3)
                        camera.add_shake(4)

        if self.dash_timer == 0:
            self.vy += GRAVITY
            if self.vy > 16:
                self.vy = 16

        if self.vy > 0 and not self.on_ground:
            self.state = "fall"
        elif self.vy < 0:
            self.state = "jump"

        self.x += self.vx * dt
        self._resolve_x(solids)
        self.y += self.vy * dt
        self.on_ground = False
        self._resolve_y(solids)

        if self.y > 2000:
            self.take_damage(99, 0, 0)

    def _resolve_x(self, solids):
        r = self.get_rect()
        for s in solids:
            if r.colliderect(s):
                if self.vx > 0:
                    self.x = s.left - self.w
                elif self.vx < 0:
                    self.x = s.right
                self.vx = 0
                r = self.get_rect()

    def _resolve_y(self, solids):
        r = self.get_rect()
        for s in solids:
            if r.colliderect(s):
                if self.vy > 0:
                    self.y = s.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = s.bottom
                    self.vy = 0
                r = self.get_rect()

    def take_damage(self, amount, kx=0, ky=0):
        if self.invuln > 0 or not self.alive:
            return
        self.hp -= amount
        self.invuln = 45
        self.vx = kx
        self.vy = ky
        self.state = "hurt"
        if self.hp <= 0:
            self.alive = False
            self.hp = 0

    def heal(self, n=1):
        self.hp = min(self.max_hp, self.hp + n)

    def draw(self, surface, camera):
        if not self.alive:
            return
        ox, oy = camera.offset
        sx = int(self.x - ox)
        sy = int(self.y - oy)

        if self.invuln > 0 and (self.invuln // 3) % 2 == 0:
            return

        body_col = Colors.ACCENT if self.state == "dash" else (50, 60, 80)
        if self.state == "hurt":
            body_col = Colors.DANGER
        pygame.draw.rect(surface, body_col, (sx + 4, sy + 8, 14, 22))
        pygame.draw.rect(surface, (220, 190, 160), (sx + 5, sy, 12, 12))
        eye = (0, 200, 255) if self.facing > 0 else (0, 180, 220)
        pygame.draw.rect(surface, eye, (sx + (10 if self.facing > 0 else 5), sy + 4, 3, 3))
        leg_y = sy + 28
        if self.state == "run" and (pygame.time.get_ticks() // 80) % 2:
            pygame.draw.rect(surface, (40, 45, 55), (sx + 5, leg_y, 5, 8))
            pygame.draw.rect(surface, (40, 45, 55), (sx + 12, leg_y + 2, 5, 6))
        else:
            pygame.draw.rect(surface, (40, 45, 55), (sx + 5, leg_y, 5, 8))
            pygame.draw.rect(surface, (40, 45, 55), (sx + 12, leg_y, 5, 8))

        if self.attack_timer > 0:
            ax = sx + (self.w if self.facing > 0 else -18)
            pygame.draw.arc(surface, Colors.GOLD,
                            (ax, sy + 2, 30, 30),
                            0.5 if self.facing > 0 else 2.5,
                            2.5 if self.facing > 0 else 5.5, 3)
