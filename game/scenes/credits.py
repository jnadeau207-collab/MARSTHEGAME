"""
Credits / epilogue.
"""

import pygame
from game.scenes.base import Scene
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Colors


class CreditsScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.y = SCREEN_HEIGHT
        self.lines = [
            "STARMAN: An Elon Odyssey",
            "",
            "A narrative action game",
            "about resolve, iteration, and multiplanetary life.",
            "",
            "You are Elon.",
            "",
            "Chapters",
            "1  Pretoria Streets",
            "2  Crossing — Canada & Arrival",
            "3  College & Zip2",
            "4  X.com / PayPal Wars",
            "5  Tesla Factory Floor",
            "6  SpaceX: Failures Before Flight",
            "7  Starship to Mars",
            "8  Mars Colony",
            "",
            "Built with pure Python + Pygame",
            "Original art direction · procedural shapes",
            "No copyrighted assets",
            "",
            "Failure is progress.",
            "The frontier is open.",
            "",
            "Press Esc or Enter to return",
        ]

    def update(self, dt):
        self.y -= 0.8 * dt
        if self.engine.input.just_pressed("cancel") or self.engine.input.just_pressed("confirm"):
            self.engine.go_title()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.engine.go_title()

    def draw(self, surface):
        surface.fill(Colors.BLACK)
        yy = self.y
        for line in self.lines:
            if line.startswith("STARMAN"):
                t = self.engine.font_lg.render(line, True, Colors.ACCENT)
            elif line in ("You are Elon.", "Failure is progress.", "The frontier is open."):
                t = self.engine.font_md.render(line, True, Colors.GOLD)
            else:
                t = self.engine.font_sm.render(line, True, Colors.WHITE)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, int(yy)))
            yy += 28
        if yy < 0:
            self.y = SCREEN_HEIGHT
