"""
Title screen — cinematic procedural presentation.
"""

import math
import random
import pygame
from game.scenes.base import Scene
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, TITLE
from game.core import gfx


class TitleScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.timer = 0.0
        self.selected = 0
        self.options = ["New Odyssey", "Continue", "Chapters", "Settings", "Credits", "Quit"]
        rng = random.Random(42)
        self.stars = [{
            "x": rng.uniform(0, SCREEN_WIDTH),
            "y": rng.uniform(0, SCREEN_HEIGHT),
            "z": rng.uniform(0.2, 1.0),
            "s": rng.choice([1, 1, 1, 2, 2, 3]),
            "tw": rng.uniform(0, 6.28),
        } for _ in range(160)]
        self.meteors = []

    def on_enter(self):
        self.timer = 0.0
        self.engine.save.load()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate()

    def update(self, dt):
        self.timer += dt
        inp = self.engine.input
        if inp.just_pressed("up"):
            self.selected = (self.selected - 1) % len(self.options)
        if inp.just_pressed("down"):
            self.selected = (self.selected + 1) % len(self.options)
        if inp.just_pressed("confirm") or inp.just_pressed("jump"):
            self._activate()

        # occasional meteor
        if random.random() < 0.008:
            self.meteors.append({
                "x": random.uniform(0, SCREEN_WIDTH),
                "y": -10,
                "vx": random.uniform(-2, -0.5),
                "vy": random.uniform(3, 6),
                "life": 60,
            })
        alive = []
        for m in self.meteors:
            m["x"] += m["vx"] * dt
            m["y"] += m["vy"] * dt
            m["life"] -= dt
            if m["life"] > 0 and m["y"] < SCREEN_HEIGHT + 20:
                alive.append(m)
        self.meteors = alive

    def _activate(self):
        opt = self.options[self.selected]
        if opt == "New Odyssey":
            self.engine.save.reset()
            self.engine.save.save()
            self.engine.start_chapter(1)
        elif opt == "Continue":
            ch = max(1, self.engine.save.current_chapter)
            self.engine.start_chapter(ch)
        elif opt == "Chapters":
            self.engine.go_chapter_select()
        elif opt == "Settings":
            self.engine.settings["show_fps"] = not self.engine.settings.get("show_fps", False)
        elif opt == "Credits":
            self.engine.go_credits()
        elif opt == "Quit":
            self.engine.running = False

    def draw(self, surface):
        # deep space gradient
        gfx.gradient_sky(surface, (4, 6, 18), (12, 8, 28), bands=32)

        # nebula washes
        for i, (cx, cy, col, r) in enumerate([
            (200, 180, (40, 20, 80), 180),
            (1000, 400, (20, 40, 90), 220),
            (640, 100, (60, 30, 50), 140),
        ]):
            pulse = 1 + 0.08 * math.sin(self.timer * 0.03 + i)
            gfx.soft_circle(surface, col, (cx, int(cy + math.sin(self.timer * 0.02 + i) * 10)),
                            int(r * pulse), layers=6)

        # stars
        for st in self.stars:
            tw = 0.5 + 0.5 * math.sin(self.timer * 0.07 + st["tw"])
            b = int(180 * tw * st["z"])
            px = int((st["x"] + self.timer * st["z"] * 0.3) % SCREEN_WIDTH)
            py = int(st["y"])
            col = (b, b, min(255, b + 40))
            if st["s"] >= 2:
                gfx.soft_circle(surface, col, (px, py), st["s"] + 1, layers=2)
            pygame.draw.circle(surface, col, (px, py), st["s"])

        # meteors
        for m in self.meteors:
            for i in range(6):
                pygame.draw.circle(surface, (200, 220, 255),
                                   (int(m["x"] - m["vx"] * i * 2), int(m["y"] - m["vy"] * i * 2)),
                                   max(1, 3 - i // 2))

        # Mars planet bottom-right
        mx, my = SCREEN_WIDTH - 180, SCREEN_HEIGHT - 80
        gfx.soft_circle(surface, (120, 50, 30), (mx, my), 110, layers=5)
        pygame.draw.circle(surface, (140, 55, 30), (mx, my), 70)
        pygame.draw.circle(surface, (160, 70, 40), (mx - 20, my - 15), 25)
        pygame.draw.circle(surface, (100, 40, 25), (mx + 25, my + 10), 18)
        pygame.draw.circle(surface, (180, 90, 50), (mx - 5, my + 20), 12)
        # atmosphere rim
        pygame.draw.circle(surface, (200, 120, 80), (mx, my), 72, 1)

        # title glow
        title_y = 110
        gfx.soft_circle_additive(surface, (0, 180, 255), (SCREEN_WIDTH // 2, title_y + 30), 120)

        title = self.engine.font_xl.render("STARMAN", True, Colors.WHITE)
        # shadow
        shadow = self.engine.font_xl.render("STARMAN", True, (0, 40, 80))
        surface.blit(shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, title_y + 3))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, title_y))

        sub = self.engine.font_md.render("An Elon Odyssey", True, Colors.ACCENT)
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, title_y + 70))

        tag = self.engine.font_sm.render("You are Elon. Build the future.", True, (140, 150, 170))
        surface.blit(tag, (SCREEN_WIDTH // 2 - tag.get_width() // 2, title_y + 110))

        # menu panel
        start_y = 300
        panel_h = len(self.options) * 40 + 20
        panel = pygame.Surface((280, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 130))
        pygame.draw.rect(panel, (0, 200, 255, 50), (0, 0, 280, panel_h), 1, border_radius=6)
        surface.blit(panel, (SCREEN_WIDTH // 2 - 140, start_y - 10))

        for i, opt in enumerate(self.options):
            y = start_y + i * 40
            if i == self.selected:
                # selection glow bar
                bar = pygame.Surface((260, 32), pygame.SRCALPHA)
                bar.fill((0, 180, 255, 40))
                surface.blit(bar, (SCREEN_WIDTH // 2 - 130, y - 4))
                pygame.draw.rect(surface, Colors.ACCENT, (SCREEN_WIDTH // 2 - 130, y - 4, 3, 32))
                col = Colors.GOLD
                prefix = "▸ "
            else:
                col = (200, 205, 215)
                prefix = "  "
            txt = self.engine.font_md.render(f"{prefix}{opt}", True, col)
            surface.blit(txt, (SCREEN_WIDTH // 2 - 100, y))

        foot = self.engine.font_sm.render("WASD / Arrows  ·  Enter / Space  ·  Gamepad supported", True, (100, 110, 130))
        surface.blit(foot, (SCREEN_WIDTH // 2 - foot.get_width() // 2, SCREEN_HEIGHT - 36))

        gfx.draw_vignette(surface, strength=80)
