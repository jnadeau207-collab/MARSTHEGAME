"""
Chapter select – walk the full arc.
"""

import pygame
from game.scenes.base import Scene
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, CHAPTERS


class ChapterSelectScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.selected = 0

    def on_enter(self):
        self.selected = min(self.selected, len(CHAPTERS) - 1)

    def update(self, dt):
        inp = self.engine.input
        if inp.just_pressed("left") or inp.just_pressed("up"):
            self.selected = (self.selected - 1) % len(CHAPTERS)
        if inp.just_pressed("right") or inp.just_pressed("down"):
            self.selected = (self.selected + 1) % len(CHAPTERS)
        if inp.just_pressed("confirm") or inp.just_pressed("jump"):
            ch = CHAPTERS[self.selected]
            if ch["id"] <= self.engine.save.chapter_unlocked or True:
                self.engine.start_chapter(ch["id"])
        if inp.just_pressed("cancel") or inp.just_pressed("pause"):
            self.engine.go_title()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.engine.go_title()

    def draw(self, surface):
        surface.fill(Colors.DARK)
        header = self.engine.font_lg.render("THE ODYSSEY", True, Colors.WHITE)
        surface.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 40))

        ch = CHAPTERS[self.selected]
        card = pygame.Rect(140, 120, SCREEN_WIDTH - 280, 420)
        pygame.draw.rect(surface, (25, 28, 40), card, border_radius=8)
        pygame.draw.rect(surface, Colors.ACCENT, card, 2, border_radius=8)

        num = self.engine.font_md.render(f"Chapter {ch['id']}", True, Colors.ACCENT)
        surface.blit(num, (card.x + 30, card.y + 30))
        title = self.engine.font_lg.render(ch["title"], True, Colors.WHITE)
        surface.blit(title, (card.x + 30, card.y + 70))
        sub = self.engine.font_md.render(ch["subtitle"], True, Colors.GOLD)
        surface.blit(sub, (card.x + 30, card.y + 120))
        year = self.engine.font_sm.render(ch["year"], True, Colors.GRAY)
        surface.blit(year, (card.x + 30, card.y + 155))

        words = ch["description"].split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if self.engine.font_sm.size(test)[0] < card.width - 60:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for i, line in enumerate(lines):
            t = self.engine.font_sm.render(line, True, Colors.WHITE)
            surface.blit(t, (card.x + 30, card.y + 200 + i * 22))

        nav = self.engine.font_sm.render("<  Left / Right  >    Enter to launch    Esc back", True, Colors.GRAY)
        surface.blit(nav, (SCREEN_WIDTH // 2 - nav.get_width() // 2, SCREEN_HEIGHT - 50))

        for i in range(len(CHAPTERS)):
            cx = SCREEN_WIDTH // 2 - (len(CHAPTERS) * 18) // 2 + i * 18
            col = Colors.ACCENT if i == self.selected else Colors.GRAY
            pygame.draw.circle(surface, col, (cx, SCREEN_HEIGHT - 80), 5)
