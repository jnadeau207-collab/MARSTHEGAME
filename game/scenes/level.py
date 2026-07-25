"""
Core level / chapter runner – data-driven.
Chapters 1–3 polished; 4–8 scaffolded with solid encounters.
"""

import pygame
from game.scenes.base import Scene
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, CHAPTERS
from game.core.camera import Camera
from game.entities.player import Player
from game.entities.enemy import Enemy
from game.entities.collectible import Collectible
from game.data.levels import LEVELS


class LevelScene(Scene):
    def __init__(self, engine, chapter_id):
        super().__init__(engine)
        self.chapter_id = chapter_id
        self.data = LEVELS.get(chapter_id, LEVELS[1])
        self.camera = Camera()
        self.player = None
        self.enemies = []
        self.collectibles = []
        self.solids = []
        self.goal_rect = None
        self.narration_queue = []
        self.current_narration = ""
        self.narration_timer = 0
        self.paused = False
        self.won = False
        self.dead_timer = 0
        self.terminals_activated = set()
        self.fade = 255
        self.objective = self.data.get("objective", "")
        self.msg = ""
        self.msg_timer = 0

    def on_enter(self):
        d = self.data
        self.player = Player(*d["player_start"])
        self.player.can_dash = self.chapter_id >= 2 or self.engine.save.unlocks.get("dash", False)

        self.solids = [pygame.Rect(*s) for s in d["solids"]]
        self.enemies = [Enemy(x, y, kind) for kind, x, y in d.get("enemies", [])]
        self.collectibles = [Collectible(x, y, kind) for kind, x, y in d.get("collectibles", [])]
        gx, gy = d["goal"]
        self.goal_rect = pygame.Rect(gx, gy, 40, 60)

        self.camera.set_target(self.player.x, self.player.y)
        self.camera.set_bounds(0, 0, d["width"], d["height"])
        self.narration_queue = list(d.get("narration", []))
        self.current_narration = ""
        self.narration_timer = 0
        self.won = False
        self.dead_timer = 0
        self.fade = 255
        self.msg = ""
        self.msg_timer = 0
        self.terminals_activated = set()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            if self.paused and event.key == pygame.K_q:
                self.engine.go_title()

    def update(self, dt):
        if self.paused:
            return

        if self.fade > 0:
            self.fade = max(0, self.fade - 8)

        if self.won:
            self.dead_timer += dt
            if self.dead_timer > 90:
                self.engine.save.complete_chapter(self.chapter_id)
                self.engine.save.current_chapter = min(8, self.chapter_id + 1)
                self.engine.save.save()
                if self.chapter_id >= 8:
                    self.engine.go_credits()
                else:
                    self.engine.start_chapter(self.chapter_id + 1)
            return

        if not self.player.alive:
            self.dead_timer += dt
            if self.dead_timer > 60:
                self.engine.save.stats["deaths"] = self.engine.save.stats.get("deaths", 0) + 1
                self.on_enter()
            return

        inp = self.engine.input
        particles = self.engine.particles

        if inp.just_pressed("interact"):
            for i, term in enumerate(self.data.get("terminals", [])):
                tx, ty = term
                if abs(self.player.x - tx) < 40 and abs(self.player.y - ty) < 50:
                    if i not in self.terminals_activated:
                        self.terminals_activated.add(i)
                        self.player.books += 1
                        self.engine.save.stats["code_terminals"] = self.engine.save.stats.get("code_terminals", 0) + 1
                        self.msg = "Terminal activated. Path clarity +1"
                        self.msg_timer = 90
                        particles.emit(tx, ty, count=12, color=Colors.ACCENT, speed=3)

        self.player.update(dt, inp, self.solids, self.enemies, particles, self.camera, self.engine)

        for e in self.enemies:
            e.update(dt, self.player, self.solids)

        for c in self.collectibles:
            if c.update(dt, self.player):
                particles.emit(c.x, c.y, count=6, color=Colors.GOLD, speed=2)
                if c.kind == "book":
                    self.engine.save.stats["books_collected"] = self.engine.save.stats.get("books_collected", 0) + 1

        if self.narration_queue:
            trigger_x, text = self.narration_queue[0]
            if self.player.x >= trigger_x:
                self.current_narration = text
                self.narration_timer = 180
                self.narration_queue.pop(0)

        if self.narration_timer > 0:
            self.narration_timer -= dt
        if self.msg_timer > 0:
            self.msg_timer -= dt

        if self.goal_rect.colliderect(self.player.get_rect()):
            self.won = True
            self.dead_timer = 0
            self.engine.trigger_hit_stop(8)
            self.camera.add_shake(6)
            particles.emit_burst(self.player.x, self.player.y, Colors.SUCCESS)

        self.camera.set_target(self.player.x + self.player.w / 2, self.player.y + self.player.h / 2)
        self.camera.update()

    def draw(self, surface):
        d = self.data
        surface.fill(d.get("sky", Colors.DARK))

        ox, oy = self.camera.offset
        import random
        rng = random.Random(self.chapter_id * 99)
        for _ in range(40):
            sx = (rng.randint(0, d["width"]) - ox * 0.3) % SCREEN_WIDTH
            sy = rng.randint(0, SCREEN_HEIGHT // 2)
            pygame.draw.circle(surface, (200, 200, 210), (int(sx), int(sy)), 1)

        ground_col = d.get("ground_col", Colors.GRAY)
        for s in self.solids:
            r = self.camera.apply(s)
            pygame.draw.rect(surface, ground_col, r)
            pygame.draw.rect(surface, tuple(min(255, c + 30) for c in ground_col[:3]), r, 1)

        gx, gy = self.camera.world_to_screen(self.goal_rect.x, self.goal_rect.y)
        pygame.draw.rect(surface, Colors.SUCCESS, (gx, gy, 8, 50))
        pygame.draw.polygon(surface, Colors.GOLD, [(gx + 8, gy), (gx + 28, gy + 10), (gx + 8, gy + 20)])

        for i, (tx, ty) in enumerate(self.data.get("terminals", [])):
            sx, sy = self.camera.world_to_screen(tx, ty)
            col = Colors.ACCENT if i in self.terminals_activated else (80, 80, 100)
            pygame.draw.rect(surface, col, (sx - 10, sy - 20, 24, 28))
            pygame.draw.rect(surface, Colors.BLACK, (sx - 6, sy - 14, 16, 12))

        for c in self.collectibles:
            c.draw(surface, self.camera)
        for e in self.enemies:
            e.draw(surface, self.camera)
        self.player.draw(surface, self.camera)

        self.engine.particles.draw(surface, *self.camera.offset)
        self._draw_hud(surface)

        if self.narration_timer > 0 and self.current_narration:
            n = self.engine.font_md.render(self.current_narration, True, Colors.WHITE)
            bg = pygame.Surface((n.get_width() + 24, n.get_height() + 12), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            surface.blit(bg, (SCREEN_WIDTH // 2 - bg.get_width() // 2, 80))
            surface.blit(n, (SCREEN_WIDTH // 2 - n.get_width() // 2, 86))

        if self.msg_timer > 0:
            m = self.engine.font_sm.render(self.msg, True, Colors.ACCENT)
            surface.blit(m, (SCREEN_WIDTH // 2 - m.get_width() // 2, 130))

        if self.fade > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, min(255, int(self.fade))))
            surface.blit(overlay, (0, 0))

        if self.won:
            t = self.engine.font_lg.render("CHAPTER COMPLETE", True, Colors.SUCCESS)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            sub = self.engine.font_sm.render("Continuing the odyssey...", True, Colors.WHITE)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        if not self.player.alive and not self.won:
            t = self.engine.font_lg.render("FALLEN", True, Colors.DANGER)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            sub = self.engine.font_sm.render("Resolve remains. Restarting...", True, Colors.WHITE)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            t = self.engine.font_lg.render("PAUSED", True, Colors.WHITE)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
            s = self.engine.font_sm.render("Esc resume  ·  Q quit to title", True, Colors.GRAY)
            surface.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def _draw_hud(self, surface):
        for i in range(self.player.max_hp):
            col = Colors.SUCCESS if i < self.player.hp else (40, 40, 50)
            pygame.draw.rect(surface, col, (16 + i * 22, 14, 18, 14), border_radius=2)

        books = self.engine.font_sm.render(f"Books {self.player.books}", True, (150, 180, 220))
        parts = self.engine.font_sm.render(f"Parts {self.player.parts}", True, Colors.GOLD)
        surface.blit(books, (16, 36))
        surface.blit(parts, (110, 36))

        ch = next((c for c in CHAPTERS if c["id"] == self.chapter_id), None)
        if ch:
            tag = self.engine.font_sm.render(f"Ch.{ch['id']}  {ch['title']}", True, Colors.GRAY)
            surface.blit(tag, (SCREEN_WIDTH - tag.get_width() - 16, 14))

        if self.objective:
            obj = self.engine.font_sm.render(self.objective, True, (180, 180, 190))
            surface.blit(obj, (16, SCREEN_HEIGHT - 28))
