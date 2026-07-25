"""
Core level / chapter runner – data-driven.
Improved procedural backgrounds, platforms, and atmosphere.
"""

import math
import random
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
        self.tick = 0
        # precompute decorative elements
        self._stars = []
        self._bg_props = []

    def on_enter(self):
        d = self.data
        self.player = Player(*d["player_start"])
        self.player.can_dash = self.chapter_id >= 2 or self.engine.save.unlocks.get("dash", False)
        self.player.can_double_jump = self.chapter_id >= 6

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
        self.tick = 0

        # build parallax / star field
        rng = random.Random(self.chapter_id * 7919)
        self._stars = [(rng.randint(0, d["width"]), rng.randint(0, max(100, d["height"] // 2)),
                        rng.choice([1, 1, 1, 2]), rng.randint(140, 230))
                       for _ in range(90 if self.chapter_id in (6, 7) else 45)]
        self._bg_props = []
        if self.chapter_id == 1:
            for _ in range(12):
                self._bg_props.append(("building", rng.randint(0, d["width"]), rng.randint(80, 200),
                                       rng.randint(40, 90), rng.randint(120, 280)))
        elif self.chapter_id == 8:
            for _ in range(18):
                self._bg_props.append(("rock", rng.randint(0, d["width"]), rng.randint(30, 80),
                                       rng.randint(20, 60), rng.randint(40, 100)))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            if self.paused and event.key == pygame.K_q:
                self.engine.go_title()

    def update(self, dt):
        if self.paused:
            return

        self.tick += dt

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
                particles.emit(c.x, c.y, count=8, color=Colors.GOLD, speed=2.5)
                if c.kind == "book":
                    self.engine.save.stats["books_collected"] = self.engine.save.stats.get("books_collected", 0) + 1

        if self.narration_queue:
            trigger_x, text = self.narration_queue[0]
            # for vertical levels use player y progress inverted
            if self.chapter_id == 7:
                if self.player.y <= self.data["height"] - trigger_x * 2:
                    self.current_narration = text
                    self.narration_timer = 200
                    self.narration_queue.pop(0)
            elif self.player.x >= trigger_x:
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
        sky = d.get("sky", Colors.DARK)
        surface.fill(sky)

        # gradient sky wash
        for i in range(6):
            t = i / 6
            c = tuple(max(0, int(sky[j] * (1 - t * 0.35))) for j in range(3))
            y0 = int(SCREEN_HEIGHT * t * 0.55)
            y1 = int(SCREEN_HEIGHT * (t + 0.18) * 0.55)
            pygame.draw.rect(surface, c, (0, y0, SCREEN_WIDTH, max(1, y1 - y0)))

        ox, oy = self.camera.offset

        # stars / distant lights
        for sx, sy, sz, bright in self._stars:
            px = int((sx - ox * (0.15 + sz * 0.08)) % (SCREEN_WIDTH + 20) - 10)
            py = int(sy - oy * 0.12)
            if 0 <= py < SCREEN_HEIGHT:
                col = (bright, bright, min(255, bright + 20))
                pygame.draw.circle(surface, col, (px, py), sz)

        # chapter-specific distant props
        for prop in self._bg_props:
            kind, bx, bh, bw, by = prop
            px = int(bx - ox * 0.25)
            if kind == "building":
                base_y = SCREEN_HEIGHT - 80
                pygame.draw.rect(surface, (35, 28, 22), (px, base_y - bh, bw, bh))
                for wy in range(8, bh - 10, 18):
                    for wx in range(6, bw - 8, 14):
                        if (wx + wy) % 3 != 0:
                            pygame.draw.rect(surface, (60, 50, 35), (px + wx, base_y - bh + wy, 6, 8))
            elif kind == "rock":
                base_y = SCREEN_HEIGHT - 100
                pts = [(px, base_y), (px + bw // 3, base_y - bh), (px + bw, base_y)]
                pygame.draw.polygon(surface, (90, 40, 25), pts)

        # subtle horizon line for horizontal levels
        if self.chapter_id != 7:
            pygame.draw.line(surface, tuple(min(255, c + 15) for c in sky),
                             (0, SCREEN_HEIGHT - 90), (SCREEN_WIDTH, SCREEN_HEIGHT - 90), 1)

        ground_col = d.get("ground_col", Colors.GRAY)
        top_col = tuple(min(255, c + 45) for c in ground_col[:3])
        edge_col = tuple(min(255, c + 25) for c in ground_col[:3])

        for s in self.solids:
            r = self.camera.apply(s)
            if r.bottom < -20 or r.top > SCREEN_HEIGHT + 20 or r.right < -20 or r.left > SCREEN_WIDTH + 20:
                continue
            # main body
            pygame.draw.rect(surface, ground_col, r)
            # top highlight strip
            if r.height > 12:
                pygame.draw.rect(surface, top_col, (r.x, r.y, r.w, min(6, r.h // 3)))
            # edge outline
            pygame.draw.rect(surface, edge_col, r, 1)
            # small rivets / detail on larger platforms
            if r.w > 60 and r.h <= 24:
                for dx in range(12, r.w - 8, 28):
                    pygame.draw.circle(surface, edge_col, (r.x + dx, r.y + 4), 2)

        # goal flag (animated)
        gx, gy = self.camera.world_to_screen(self.goal_rect.x, self.goal_rect.y)
        wave = math.sin(self.tick * 0.12) * 4
        pygame.draw.rect(surface, (40, 50, 40), (gx, gy, 5, 55))
        flag_pts = [
            (gx + 5, gy + 2),
            (gx + 28 + wave, gy + 12),
            (gx + 5, gy + 22),
        ]
        pygame.draw.polygon(surface, Colors.GOLD, flag_pts)
        pygame.draw.polygon(surface, Colors.SUCCESS, [(gx + 5, gy + 6), (gx + 20 + wave * 0.6, gy + 12), (gx + 5, gy + 18)])

        # terminals
        for i, (tx, ty) in enumerate(self.data.get("terminals", [])):
            sx, sy = self.camera.world_to_screen(tx, ty)
            active = i in self.terminals_activated
            col = Colors.ACCENT if active else (70, 75, 95)
            pygame.draw.rect(surface, col, (sx - 12, sy - 22, 28, 32), border_radius=3)
            pygame.draw.rect(surface, Colors.BLACK, (sx - 8, sy - 16, 20, 14))
            if active:
                pygame.draw.rect(surface, Colors.SUCCESS, (sx - 6, sy - 14, 16, 10))
            else:
                pygame.draw.line(surface, (40, 45, 55), (sx - 5, sy - 10), (sx + 5, sy - 10), 1)

        for c in self.collectibles:
            c.draw(surface, self.camera)
        for e in self.enemies:
            e.draw(surface, self.camera)
        self.player.draw(surface, self.camera)

        self.engine.particles.draw(surface, *self.camera.offset)
        self._draw_hud(surface)

        if self.narration_timer > 0 and self.current_narration:
            n = self.engine.font_md.render(self.current_narration, True, Colors.WHITE)
            bg = pygame.Surface((n.get_width() + 28, n.get_height() + 16), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 170))
            surface.blit(bg, (SCREEN_WIDTH // 2 - bg.get_width() // 2, 72))
            surface.blit(n, (SCREEN_WIDTH // 2 - n.get_width() // 2, 80))

        if self.msg_timer > 0:
            m = self.engine.font_sm.render(self.msg, True, Colors.ACCENT)
            surface.blit(m, (SCREEN_WIDTH // 2 - m.get_width() // 2, 125))

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
            pygame.draw.rect(surface, col, (16 + i * 22, 14, 18, 14), border_radius=3)
            pygame.draw.rect(surface, tuple(min(255, c + 40) for c in col), (16 + i * 22, 14, 18, 14), 1, border_radius=3)

        books = self.engine.font_sm.render(f"Books {self.player.books}", True, (150, 180, 220))
        parts = self.engine.font_sm.render(f"Parts {self.player.parts}", True, Colors.GOLD)
        surface.blit(books, (16, 36))
        surface.blit(parts, (110, 36))

        if self.player.can_double_jump:
            dj = self.engine.font_sm.render("2x Jump", True, Colors.ACCENT)
            surface.blit(dj, (200, 36))

        ch = next((c for c in CHAPTERS if c["id"] == self.chapter_id), None)
        if ch:
            tag = self.engine.font_sm.render(f"Ch.{ch['id']}  {ch['title']}", True, Colors.GRAY)
            surface.blit(tag, (SCREEN_WIDTH - tag.get_width() - 16, 14))

        if self.objective:
            obj = self.engine.font_sm.render(self.objective, True, (180, 180, 190))
            surface.blit(obj, (16, SCREEN_HEIGHT - 28))
