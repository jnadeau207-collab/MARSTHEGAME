"""Title screen — cinematic procedural presentation."""

import math
import random

import pygame

from game.core import gfx
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Colors
from game.data.content import get_text
from game.scenes.base import Scene


class TitleScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.timer = 0.0
        self.selected = 0
        self.short_title = get_text("game.short_title")
        self.subtitle = get_text("game.subtitle")
        self.tagline = get_text("title.tagline")
        self.options = [
            ("campaign", "Frontier Campaign"),
            ("new", "New Classic Odyssey"),
            ("continue", "Continue Classic Mode"),
            ("chapters", "Classic Chapters"),
            ("settings", "Accessibility & Settings"),
            ("credits", "Credits"),
            ("quit", "Quit"),
        ]
        rng = random.Random(42)
        self.stars = [
            {
                "x": rng.uniform(0, SCREEN_WIDTH),
                "y": rng.uniform(0, SCREEN_HEIGHT),
                "z": rng.uniform(0.2, 1.0),
                "s": rng.choice([1, 1, 1, 2, 2, 3]),
                "tw": rng.uniform(0, 6.28),
            }
            for _ in range(160)
        ]
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

        if random.random() < 0.008:
            self.meteors.append(
                {
                    "x": random.uniform(0, SCREEN_WIDTH),
                    "y": -10,
                    "vx": random.uniform(-2, -0.5),
                    "vy": random.uniform(3, 6),
                    "life": 60,
                }
            )
        alive = []
        for meteor in self.meteors:
            meteor["x"] += meteor["vx"] * dt
            meteor["y"] += meteor["vy"] * dt
            meteor["life"] -= dt
            if meteor["life"] > 0 and meteor["y"] < SCREEN_HEIGHT + 20:
                alive.append(meteor)
        self.meteors = alive

    def _activate(self):
        option_id, _label = self.options[self.selected]
        if option_id == "campaign":
            self.engine.go_campaign()
        elif option_id == "new":
            self.engine.save.reset()
            self.engine.save.save()
            self.engine.start_chapter(1)
        elif option_id == "continue":
            chapter_id = max(1, self.engine.save.current_chapter)
            self.engine.start_chapter(chapter_id)
        elif option_id == "chapters":
            self.engine.go_chapter_select()
        elif option_id == "settings":
            self.engine.go_settings()
        elif option_id == "credits":
            self.engine.go_credits()
        elif option_id == "quit":
            self.engine.running = False

    def draw(self, surface):
        gfx.gradient_sky(surface, (4, 6, 18), (12, 8, 28), bands=32)

        for index, (cx, cy, color, radius) in enumerate(
            [
                (200, 180, (40, 20, 80), 180),
                (1000, 400, (20, 40, 90), 220),
                (640, 100, (60, 30, 50), 140),
            ]
        ):
            pulse = 1 + 0.08 * math.sin(self.timer * 0.03 + index)
            gfx.soft_circle(
                surface,
                color,
                (cx, int(cy + math.sin(self.timer * 0.02 + index) * 10)),
                int(radius * pulse),
                layers=6,
            )

        for star in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(self.timer * 0.07 + star["tw"])
            brightness = int(180 * twinkle * star["z"])
            px = int((star["x"] + self.timer * star["z"] * 0.3) % SCREEN_WIDTH)
            py = int(star["y"])
            color = (brightness, brightness, min(255, brightness + 40))
            if star["s"] >= 2:
                gfx.soft_circle(
                    surface,
                    color,
                    (px, py),
                    star["s"] + 1,
                    layers=2,
                )
            pygame.draw.circle(surface, color, (px, py), star["s"])

        for meteor in self.meteors:
            for index in range(6):
                pygame.draw.circle(
                    surface,
                    (200, 220, 255),
                    (
                        int(meteor["x"] - meteor["vx"] * index * 2),
                        int(meteor["y"] - meteor["vy"] * index * 2),
                    ),
                    max(1, 3 - index // 2),
                )

        mars_x, mars_y = SCREEN_WIDTH - 180, SCREEN_HEIGHT - 80
        gfx.soft_circle(
            surface,
            (120, 50, 30),
            (mars_x, mars_y),
            110,
            layers=5,
        )
        pygame.draw.circle(surface, (140, 55, 30), (mars_x, mars_y), 70)
        pygame.draw.circle(surface, (160, 70, 40), (mars_x - 20, mars_y - 15), 25)
        pygame.draw.circle(surface, (100, 40, 25), (mars_x + 25, mars_y + 10), 18)
        pygame.draw.circle(surface, (180, 90, 50), (mars_x - 5, mars_y + 20), 12)
        pygame.draw.circle(surface, (200, 120, 80), (mars_x, mars_y), 72, 1)

        title_y = 88
        gfx.soft_circle_additive(
            surface,
            (0, 180, 255),
            (SCREEN_WIDTH // 2, title_y + 30),
            120,
        )

        title = self.engine.font_xl.render(self.short_title, True, Colors.WHITE)
        shadow = self.engine.font_xl.render(self.short_title, True, (0, 40, 80))
        surface.blit(
            shadow,
            (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, title_y + 3),
        )
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, title_y))

        subtitle = self.engine.font_md.render(self.subtitle, True, Colors.ACCENT)
        surface.blit(
            subtitle,
            (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, title_y + 70),
        )

        tagline = self.engine.font_sm.render(self.tagline, True, (140, 150, 170))
        surface.blit(
            tagline,
            (SCREEN_WIDTH // 2 - tagline.get_width() // 2, title_y + 110),
        )

        start_y = 260
        panel_h = len(self.options) * 40 + 20
        panel = pygame.Surface((360, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 130))
        pygame.draw.rect(
            panel,
            (0, 200, 255, 50),
            (0, 0, 360, panel_h),
            1,
            border_radius=6,
        )
        surface.blit(panel, (SCREEN_WIDTH // 2 - 180, start_y - 10))

        for index, (_option_id, label) in enumerate(self.options):
            y = start_y + index * 40
            if index == self.selected:
                bar = pygame.Surface((340, 32), pygame.SRCALPHA)
                bar.fill((0, 180, 255, 40))
                surface.blit(bar, (SCREEN_WIDTH // 2 - 170, y - 4))
                pygame.draw.rect(
                    surface,
                    Colors.ACCENT,
                    (SCREEN_WIDTH // 2 - 170, y - 4, 3, 32),
                )
                color = Colors.GOLD
                prefix = "▸ "
            else:
                color = (200, 205, 215)
                prefix = "  "
            text = self.engine.font_md.render(f"{prefix}{label}", True, color)
            surface.blit(text, (SCREEN_WIDTH // 2 - 145, y))

        footer = self.engine.font_sm.render(
            "WASD / Arrows  ·  Enter / Space  ·  Gamepad supported",
            True,
            (100, 110, 130),
        )
        surface.blit(
            footer,
            (SCREEN_WIDTH // 2 - footer.get_width() // 2, SCREEN_HEIGHT - 28),
        )

        gfx.draw_vignette(surface, strength=80)
