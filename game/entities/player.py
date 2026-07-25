"""
Player: Elon. Responsive movement, coyote, buffer, dash, double-jump, light combat.
Improved procedural silhouette graphics.
"""

import math
import pygame
from game.core.settings import (
    GRAVITY, PLAYER_SPEED, PLAYER_JUMP, PLAYER_DASH_SPEED,
    PLAYER_DASH_DURATION, COYOTE_TIME, JUMP_BUFFER, Colors
)


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w = 24
        self.h = 38
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

        self.anim += dt * 0.15

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

            # Jump / double-jump
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
                        # small thruster burst for second jump
                        particles.emit(self.x + self.w / 2, self.y + self.h,
                                       count=8, speed=2.5, color=Colors.ACCENT, life=18)
                    self.state = "jump"

            if not inp.is_held("jump") and self.vy < -4:
                self.vy *= 0.55

            if self.can_dash and (inp.just_pressed("dash") or inp.consume_buffer("dash")) and self.dash_timer == 0:
                self.dash_timer = PLAYER_DASH_DURATION
                self.dash_dir = self.facing
                self.invuln = max(self.invuln, 8)
                particles.emit(self.x + self.w / 2, self.y + self.h / 2, count=8, speed=2.5, color=Colors.ACCENT)

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

        # Shadow
        pygame.draw.ellipse(surface, (0, 0, 0, 60), (sx + 2, sy + self.h - 4, 20, 6))

        # Body palette
        jacket = (35, 45, 70)
        if self.state == "dash":
            jacket = Colors.ACCENT
        elif self.state == "hurt":
            jacket = Colors.DANGER

        # Legs (animated)
        leg_y = sy + 26
        run_frame = int(self.anim * 8) % 4 if self.state == "run" else 0
        if self.state == "run":
            offsets = [(0, 2), (1, 0), (0, 2), (-1, 0)]
            lo, ro = offsets[run_frame]
            pygame.draw.rect(surface, (28, 32, 42), (sx + 5, leg_y + lo, 6, 12))
            pygame.draw.rect(surface, (28, 32, 42), (sx + 13, leg_y + ro, 6, 12))
            # boots
            pygame.draw.rect(surface, (20, 22, 30), (sx + 4, leg_y + lo + 10, 8, 4))
            pygame.draw.rect(surface, (20, 22, 30), (sx + 12, leg_y + ro + 10, 8, 4))
        elif self.state == "jump" or self.state == "fall":
            pygame.draw.rect(surface, (28, 32, 42), (sx + 6, leg_y - 2, 5, 12))
            pygame.draw.rect(surface, (28, 32, 42), (sx + 13, leg_y + 2, 5, 10))
        else:
            pygame.draw.rect(surface, (28, 32, 42), (sx + 5, leg_y, 6, 12))
            pygame.draw.rect(surface, (28, 32, 42), (sx + 13, leg_y, 6, 12))
            pygame.draw.rect(surface, (20, 22, 30), (sx + 4, leg_y + 10, 8, 4))
            pygame.draw.rect(surface, (20, 22, 30), (sx + 12, leg_y + 10, 8, 4))

        # Torso / jacket
        pygame.draw.rect(surface, jacket, (sx + 4, sy + 10, 16, 18), border_radius=2)
        # collar
        pygame.draw.rect(surface, (50, 60, 90), (sx + 5, sy + 10, 14, 4))
        # accent stripe
        pygame.draw.line(surface, Colors.ACCENT if self.state != "hurt" else Colors.DANGER,
                         (sx + 6, sy + 16), (sx + 18, sy + 16), 1)

        # Head
        skin = (220, 185, 155)
        pygame.draw.ellipse(surface, skin, (sx + 5, sy - 1, 14, 14))
        # hair (dark, slightly messy)
        hair = (35, 28, 22)
        pygame.draw.ellipse(surface, hair, (sx + 4, sy - 3, 16, 10))
        pygame.draw.rect(surface, hair, (sx + 4, sy + 2, 3, 6))  # side
        # eyes
        eye_x = sx + (11 if self.facing > 0 else 7)
        pygame.draw.rect(surface, (25, 30, 40), (eye_x, sy + 4, 3, 3))
        pygame.draw.rect(surface, (0, 210, 255), (eye_x + 1, sy + 5, 1, 1))  # glint

        # Arm (simple)
        arm_col = jacket
        if self.state == "attack":
            ax = sx + (self.w - 2 if self.facing > 0 else -6)
            pygame.draw.line(surface, arm_col, (sx + 12, sy + 14), (ax + 10, sy + 10), 3)
        else:
            pygame.draw.line(surface, arm_col, (sx + 6, sy + 14), (sx + 2, sy + 22), 3)
            pygame.draw.line(surface, arm_col, (sx + 18, sy + 14), (sx + 22, sy + 22), 3)

        # Attack arc
        if self.attack_timer > 0:
            ax = sx + (self.w if self.facing > 0 else -20)
            pygame.draw.arc(surface, Colors.GOLD,
                            (ax, sy, 34, 34),
                            0.4 if self.facing > 0 else 2.4,
                            2.6 if self.facing > 0 else 5.6, 3)

        # Double-jump thruster glow
        if not self.on_ground and self.can_double_jump and self.jumps_left == 0 and self.vy < 0:
            glow = int(80 + 40 * math.sin(self.anim * 10))
            pygame.draw.circle(surface, (0, glow, 255), (sx + 12, sy + self.h + 2), 5)
