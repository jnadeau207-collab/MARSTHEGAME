"""
Player: Elon — high-detail procedural sprite with shading, animation, glow.
"""

import math
import pygame
from game.core.settings import (
    GRAVITY, PLAYER_SPEED, PLAYER_JUMP, PLAYER_DASH_SPEED,
    PLAYER_DASH_DURATION, COYOTE_TIME, JUMP_BUFFER, Colors
)
from game.core import gfx


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w = 26
        self.h = 40
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
        self.can_double_jump = False
        self.jumps_left = 1
        self.anim = 0.0
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def get_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        return self.rect

    def update(self, dt, inp, solids, enemies, particles, camera, engine):
        if not self.alive:
            return

        self.anim += dt * 0.18

        if self.invuln > 0:
            self.invuln -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1

        if self.on_ground:
            self.coyote = COYOTE_TIME
            self.jumps_left = 2 if self.can_double_jump else 1
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
            if self.dash_timer % 2 == 0:
                particles.emit(self.x + self.w / 2, self.y + self.h / 2,
                               count=2, speed=1.2, color=(0, 200, 255), life=12, size=2, gravity=0)
            if self.dash_timer == 0:
                self.vx *= 0.4
        else:
            ax, _ = inp.get_axis()
            if ax != 0:
                self.facing = 1 if ax > 0 else -1
                self.vx = ax * PLAYER_SPEED
                self.state = "run" if self.on_ground else self.state
            else:
                self.vx *= 0.78
                if abs(self.vx) < 0.3:
                    self.vx = 0
                    if self.on_ground:
                        self.state = "idle"

            if self.jump_buffer > 0:
                if self.coyote > 0 or (self.jumps_left > 0 and not self.on_ground):
                    self.vy = PLAYER_JUMP
                    self.on_ground = False
                    self.coyote = 0
                    self.jump_buffer = 0
                    self.jumps_left -= 1
                    inp.consume_buffer("jump")
                    particles.emit_dust(self.x + self.w / 2, self.y + self.h)
                    if self.jumps_left == 0 and self.can_double_jump:
                        particles.emit(self.x + self.w / 2, self.y + self.h,
                                       count=12, speed=3.2, color=Colors.ACCENT, life=22, size=3)
                    self.state = "jump"

            if not inp.is_held("jump") and self.vy < -4:
                self.vy *= 0.55

            if self.can_dash and (inp.just_pressed("dash") or inp.consume_buffer("dash")) and self.dash_timer == 0:
                self.dash_timer = PLAYER_DASH_DURATION
                self.dash_dir = self.facing
                self.invuln = max(self.invuln, 8)
                particles.emit(self.x + self.w / 2, self.y + self.h / 2, count=10, speed=3, color=Colors.ACCENT)

            if (inp.just_pressed("attack") or inp.consume_buffer("attack")) and self.attack_cooldown == 0:
                self.attack_timer = 12
                self.attack_cooldown = 20
                self.state = "attack"
                hx = self.x + (self.w if self.facing > 0 else -30)
                hit = pygame.Rect(hx, self.y + 2, 30, 30)
                for e in enemies:
                    if e.alive and hit.colliderect(e.get_rect()):
                        e.take_damage(1, self.facing * 5, -4)
                        particles.emit_burst(e.x + e.w / 2, e.y + e.h / 2)
                        engine.trigger_hit_stop(3)
                        camera.add_shake(4)

        if self.dash_timer == 0:
            self.vy += GRAVITY
            if self.vy > 15:
                self.vy = 15

        if self.vy > 0 and not self.on_ground:
            self.state = "fall"
        elif self.vy < 0:
            self.state = "jump"

        self.x += self.vx * dt
        self._resolve_x(solids)
        self.y += self.vy * dt
        self.on_ground = False
        self._resolve_y(solids)

        if self.y > 2400:
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

        # ground contact shadow
        sh = pygame.Surface((28, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 28, 10))
        surface.blit(sh, (sx - 1, sy + self.h - 5))

        # dash / thruster aura
        if self.state == "dash":
            gfx.soft_circle_additive(surface, (0, 220, 255), (sx + 13, sy + 20), 22)
        if not self.on_ground and self.can_double_jump and self.jumps_left == 0 and self.vy < 0:
            pulse = 10 + int(6 * math.sin(self.anim * 12))
            gfx.soft_circle_additive(surface, (40, 160, 255), (sx + 13, sy + self.h + 4), pulse)

        f = self.facing
        jacket = (32, 42, 68)
        jacket_hi = (48, 62, 95)
        jacket_lo = (22, 28, 48)
        if self.state == "dash":
            jacket, jacket_hi, jacket_lo = (0, 160, 210), (40, 200, 255), (0, 100, 150)
        elif self.state == "hurt":
            jacket, jacket_hi, jacket_lo = (180, 40, 40), (220, 70, 70), (120, 20, 20)

        leg_y = sy + 27
        pant = (24, 28, 38)
        boot = (18, 18, 24)

        # legs
        if self.state == "run":
            phase = int(self.anim * 10) % 6
            cycle = [(-2, 3), (-1, 1), (0, 0), (1, -1), (2, -2), (1, 0)]
            lo, ro = cycle[phase]
            # left leg
            pygame.draw.rect(surface, pant, (sx + 5, leg_y + lo, 7, 11), border_radius=1)
            pygame.draw.rect(surface, boot, (sx + 4, leg_y + lo + 9, 9, 5), border_radius=1)
            # right leg
            pygame.draw.rect(surface, pant, (sx + 14, leg_y + ro, 7, 11), border_radius=1)
            pygame.draw.rect(surface, boot, (sx + 13, leg_y + ro + 9, 9, 5), border_radius=1)
        elif self.state in ("jump", "fall"):
            pygame.draw.rect(surface, pant, (sx + 6, leg_y - 3, 6, 12), border_radius=1)
            pygame.draw.rect(surface, pant, (sx + 14, leg_y + 1, 6, 10), border_radius=1)
            pygame.draw.rect(surface, boot, (sx + 5, leg_y + 7, 8, 4))
            pygame.draw.rect(surface, boot, (sx + 13, leg_y + 9, 8, 4))
        else:
            # idle slight breathe
            b = int(math.sin(self.anim * 2) * 1)
            pygame.draw.rect(surface, pant, (sx + 5, leg_y + b, 7, 11), border_radius=1)
            pygame.draw.rect(surface, pant, (sx + 14, leg_y + b, 7, 11), border_radius=1)
            pygame.draw.rect(surface, boot, (sx + 4, leg_y + 9 + b, 9, 5), border_radius=1)
            pygame.draw.rect(surface, boot, (sx + 13, leg_y + 9 + b, 9, 5), border_radius=1)

        # torso with shading
        pygame.draw.rect(surface, jacket_lo, (sx + 4, sy + 11, 18, 18), border_radius=3)
        pygame.draw.rect(surface, jacket, (sx + 5, sy + 11, 16, 15), border_radius=2)
        pygame.draw.rect(surface, jacket_hi, (sx + 6, sy + 11, 14, 5), border_radius=2)
        # collar / zipper
        pygame.draw.line(surface, (70, 90, 130) if self.state != "hurt" else (200, 80, 80),
                         (sx + 13, sy + 12), (sx + 13, sy + 24), 1)
        # shoulder pads
        pygame.draw.rect(surface, jacket_hi, (sx + 3, sy + 12, 5, 5), border_radius=1)
        pygame.draw.rect(surface, jacket_hi, (sx + 18, sy + 12, 5, 5), border_radius=1)

        # arms
        arm = jacket
        if self.state == "attack":
            ax = sx + (22 if f > 0 else -8)
            ay = sy + 8
            pygame.draw.line(surface, arm, (sx + 13, sy + 15), (ax, ay), 4)
            pygame.draw.circle(surface, (200, 170, 140), (ax, ay), 3)
            # energy slash
            gfx.soft_circle(surface, Colors.GOLD, (ax + (8 if f > 0 else -8), ay), 14, layers=3)
            pygame.draw.arc(surface, Colors.GOLD,
                            (ax - 10, ay - 12, 36, 36),
                            0.3 if f > 0 else 2.5, 2.5 if f > 0 else 5.5, 2)
        else:
            swing = int(math.sin(self.anim * 8) * 3) if self.state == "run" else 0
            pygame.draw.line(surface, arm, (sx + 6, sy + 15), (sx + 2, sy + 24 + swing), 3)
            pygame.draw.line(surface, arm, (sx + 20, sy + 15), (sx + 24, sy + 24 - swing), 3)
            pygame.draw.circle(surface, (200, 170, 140), (sx + 2, sy + 24 + swing), 2)
            pygame.draw.circle(surface, (200, 170, 140), (sx + 24, sy + 24 - swing), 2)

        # head
        skin = (225, 190, 160)
        skin_sh = (200, 160, 130)
        pygame.draw.ellipse(surface, skin_sh, (sx + 5, sy + 1, 16, 14))
        pygame.draw.ellipse(surface, skin, (sx + 6, sy, 14, 13))

        # hair — layered
        hair = (28, 22, 18)
        hair_hi = (50, 40, 32)
        pygame.draw.ellipse(surface, hair, (sx + 4, sy - 4, 18, 11))
        pygame.draw.ellipse(surface, hair_hi, (sx + 7, sy - 3, 10, 6))
        # sideburn / temple
        pygame.draw.rect(surface, hair, (sx + 4, sy + 2, 3, 7))
        pygame.draw.rect(surface, hair, (sx + 19, sy + 2, 3, 7))
        # fringe
        for i, dx in enumerate((-3, 0, 3, 6)):
            pygame.draw.line(surface, hair, (sx + 9 + dx, sy - 1), (sx + 8 + dx, sy + 3), 2)

        # eyes
        if f > 0:
            pygame.draw.rect(surface, (20, 24, 32), (sx + 13, sy + 4, 4, 3))
            pygame.draw.rect(surface, (0, 220, 255), (sx + 14, sy + 5, 2, 1))
            # brow
            pygame.draw.line(surface, hair, (sx + 12, sy + 3), (sx + 17, sy + 2), 1)
        else:
            pygame.draw.rect(surface, (20, 24, 32), (sx + 9, sy + 4, 4, 3))
            pygame.draw.rect(surface, (0, 220, 255), (sx + 10, sy + 5, 2, 1))
            pygame.draw.line(surface, hair, (sx + 9, sy + 2), (sx + 14, sy + 3), 1)

        # subtle cheek
        pygame.draw.circle(surface, (230, 170, 150), (sx + (16 if f > 0 else 10), sy + 8), 2)
