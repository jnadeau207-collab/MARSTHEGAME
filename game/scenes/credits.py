"""
Credits / epilogue.
"""

import pygame

from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Colors
from game.data.content import build_credits_lines
from game.scenes.base import Scene


class CreditsScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.y = SCREEN_HEIGHT
        self.lines = build_credits_lines()

    def update(self, dt):
        self.y -= 0.8 * dt
        if self.engine.input.just_pressed("cancel") or self.engine.input.just_pressed("confirm"):
            self.engine.go_title()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.engine.go_title()

    def draw(self, surface):
        surface.fill(Colors.BLACK)
        y = self.y
        for style, line in self.lines:
            if style == "title":
                text = self.engine.font_lg.render(line, True, Colors.ACCENT)
            elif style == "emphasis":
                text = self.engine.font_md.render(line, True, Colors.GOLD)
            else:
                text = self.engine.font_sm.render(line, True, Colors.WHITE)
            surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, int(y)))
            y += 28
        if y < 0:
            self.y = SCREEN_HEIGHT
