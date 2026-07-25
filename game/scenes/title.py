"""
Title screen – STARMAN: An Elon Odyssey.
"""

import pygame
from game.scenes.base import Scene
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, TITLE


class TitleScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.timer = 0
        self.selected = 0
        self.options = ["New Odyssey", "Continue", "Chapters", "Settings", "Credits", "Quit"]

    def on_enter(self):
        self.timer = 0
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
        surface.fill(Colors.BLACK)
        for i in range(20):
            y = int(SCREEN_HEIGHT * 0.3 + i * 8)
            c = 12 + i
            pygame.draw.line(surface, (c, c, c + 8), (0, y), (SCREEN_WIDTH, y))

        import random
        rng = random.Random(42)
        for _ in range(60):
            x = rng.randint(0, SCREEN_WIDTH)
            y = rng.randint(0, SCREEN_HEIGHT // 2)
            pygame.draw.circle(surface, (180, 180, 200), (x, y), 1)

        title = self.engine.font_xl.render("STARMAN", True, Colors.WHITE)
        sub = self.engine.font_md.render("An Elon Odyssey", True, Colors.ACCENT)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 185))

        tag = self.engine.font_sm.render("You are Elon. Build the future.", True, Colors.GRAY)
        surface.blit(tag, (SCREEN_WIDTH // 2 - tag.get_width() // 2, 230))

        start_y = 320
        for i, opt in enumerate(self.options):
            col = Colors.GOLD if i == self.selected else Colors.WHITE
            prefix = ">" if i == self.selected else " "
            txt = self.engine.font_md.render(f"{prefix} {opt}", True, col)
            surface.blit(txt, (SCREEN_WIDTH // 2 - 100, start_y + i * 36))

        foot = self.engine.font_sm.render("WASD / Arrows  ·  Enter / Space  ·  Gamepad supported", True, Colors.GRAY)
        surface.blit(foot, (SCREEN_WIDTH // 2 - foot.get_width() // 2, SCREEN_HEIGHT - 40))
