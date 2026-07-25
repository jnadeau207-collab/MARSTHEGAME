"""
Level scene — cinematic procedural atmosphere.
Multi-layer parallax, bevel platforms, god rays, vignette, ambient particles.
"""

import math
import random
import pygame
from game.scenes.base import Scene
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, CHAPTERS
from game.core.camera import Camera
from game.core import gfx
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
        self.tick = 0.0
        self._stars = []
        self._far = []
        self._mid = []
        self._dust = []
        self._rays = []

    def on_enter(self):
        d = self.data
        self.player = Player(*d["player_start"])
        self.player.can_dash = self.chapter_id >= 2 or self.engine.save.unlocks.get("dash", False)
        self.player.can_double_jump = self.chapter_id >= 6

        self.solids = [pygame.Rect(*s) for s in d["solids"]]
        self.enemies = [Enemy(x, y, kind) for kind, x, y in d.get("enemies", [])]
        self.collectibles = [Collectible(x, y, kind) for kind, x, y in d.get("collectibles", [])]
        gx, gy = d["goal"]
        self.goal_rect = pygame.Rect(gx, gy, 48, 64)

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
        self.tick = 0.0

        rng = random.Random(self.chapter_id * 7919 + 3)
        w, h = d["width"], d["height"]

        n_stars = 140 if self.chapter_id in (6, 7) else 70
        self._stars = []
        for _ in range(n_stars):
            self._stars.append({
                "x": rng.uniform(0, w),
                "y": rng.uniform(0, max(200, h * 0.7)),
                "z": rng.choice([0.08, 0.12, 0.18, 0.28]),
                "s": rng.choice([1, 1, 1, 2, 2, 3]),
                "b": rng.randint(120, 255),
                "tw": rng.uniform(0, 6.28),
            })

        self._far = []
        self._mid = []
        if self.chapter_id == 1:
            for _ in range(16):
                self._far.append(("bld", rng.randint(0, w), rng.randint(100, 260),
                                  rng.randint(50, 110), rng.randint(0, 3)))
            for _ in range(8):
                self._mid.append(("bld", rng.randint(0, w), rng.randint(140, 320),
                                  rng.randint(60, 140), rng.randint(0, 3)))
        elif self.chapter_id == 2:
            for _ in range(20):
                self._far.append(("tree", rng.randint(0, w), rng.randint(40, 90),
                                  rng.randint(20, 40), 0))
            for _ in range(10):
                self._mid.append(("hill", rng.randint(0, w), rng.randint(60, 120),
                                  rng.randint(80, 180), 0))
        elif self.chapter_id in (4, 5):
            for _ in range(14):
                self._far.append(("tower", rng.randint(0, w), rng.randint(120, 300),
                                  rng.randint(40, 80), rng.randint(0, 2)))
            for _ in range(10):
                self._mid.append(("pipe", rng.randint(0, w), rng.randint(30, 60),
                                  rng.randint(100, 200), 0))
        elif self.chapter_id in (6, 7):
            for _ in range(6):
                self._far.append(("planet", rng.randint(0, w), rng.randint(20, 50),
                                  rng.randint(40, 90), 0))
        elif self.chapter_id == 8:
            for _ in range(22):
                self._far.append(("rock", rng.randint(0, w), rng.randint(40, 110),
                                  rng.randint(30, 80), 0))
            for _ in range(12):
                self._mid.append(("dune", rng.randint(0, w), rng.randint(50, 100),
                                  rng.randint(100, 220), 0))

        dust_cols = ([(180, 200, 255), (255, 200, 100), (200, 180, 255)]
                     if self.chapter_id >= 6 else
                     [(200, 180, 140), (180, 200, 220), (255, 160, 80)])
        self._dust = []
        for _ in range(50):
            self._dust.append({
                "x": rng.uniform(0, w),
                "y": rng.uniform(0, h),
                "vx": rng.uniform(-0.15, 0.15),
                "vy": rng.uniform(-0.25, -0.05),
                "s": rng.choice([1, 1, 2]),
                "c": rng.choice(dust_cols),
            })

        self._rays = []
        if self.chapter_id in (6, 7, 3):
            for _ in range(5):
                self._rays.append({
                    "x": rng.uniform(0.1, 0.9),
                    "w": rng.uniform(30, 90),
                    "a": rng.randint(12, 28),
                    "spd": rng.uniform(0.0003, 0.001),
                    "phase": rng.uniform(0, 6.28),
                })

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

        d = self.data
        for p in self._dust:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] < 0:
                p["y"] = d["height"]
                p["x"] = random.uniform(0, d["width"])
            if p["x"] < 0:
                p["x"] = d["width"]
            elif p["x"] > d["width"]:
                p["x"] = 0

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
                        particles.emit(tx, ty, count=16, color=Colors.ACCENT, speed=3.5, style="glow")

        self.player.update(dt, inp, self.solids, self.enemies, particles, self.camera, self.engine)

        for e in self.enemies:
            e.update(dt, self.player, self.solids)

        for c in self.collectibles:
            if c.update(dt, self.player):
                particles.emit(c.x, c.y, count=14, color=Colors.GOLD, speed=3, style="glow")
                if c.kind == "book":
                    self.engine.save.stats["books_collected"] = self.engine.save.stats.get("books_collected", 0) + 1

        if self.narration_queue:
            trigger_x, text = self.narration_queue[0]
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

    def _draw_prop(self, surface, prop, ox, parallax, base_y, col_far=True):
        kind, bx, bh, bw, variant = prop
        px = int(bx - ox * parallax)
        if px < -200 or px > SCREEN_WIDTH + 200:
            return
        if kind == "bld":
            base = (28, 22, 18) if col_far else (42, 32, 26)
            win = (55, 45, 30) if col_far else (90, 70, 40)
            pygame.draw.rect(surface, base, (px, base_y - bh, bw, bh))
            pygame.draw.rect(surface, gfx.shade(base, 15), (px, base_y - bh, bw, 4))
            for wy in range(12, bh - 8, 16):
                for wx in range(6, bw - 8, 12):
                    if (wx + wy + variant) % 3:
                        pygame.draw.rect(surface, win, (px + wx, base_y - bh + wy, 5, 7))
        elif kind == "tree":
            trunk = (40, 50, 30)
            pygame.draw.rect(surface, trunk, (px + bw // 2 - 3, base_y - bh // 3, 6, bh // 3))
            pygame.draw.circle(surface, (35, 70, 40), (px + bw // 2, base_y - bh // 2), bw // 2)
            pygame.draw.circle(surface, (45, 90, 50), (px + bw // 2 - 4, base_y - bh // 2 - 6), bw // 3)
        elif kind == "hill":
            pts = [(px, base_y), (px + bw // 2, base_y - bh), (px + bw, base_y)]
            pygame.draw.polygon(surface, (50, 70, 45), pts)
        elif kind == "tower":
            base = (25, 28, 40)
            pygame.draw.rect(surface, base, (px, base_y - bh, bw, bh))
            for wy in range(10, bh, 20):
                pygame.draw.rect(surface, (50, 60, 90), (px + 4, base_y - bh + wy, bw - 8, 3))
        elif kind == "pipe":
            pygame.draw.rect(surface, (60, 40, 40), (px, base_y - 20, bw, 14))
            pygame.draw.rect(surface, (90, 55, 50), (px, base_y - 20, bw, 4))
        elif kind == "planet":
            gfx.soft_circle(surface, (80, 100, 160), (px, base_y - 200), bh, layers=5)
            pygame.draw.circle(surface, (60, 80, 130), (px, base_y - 200), bh // 2)
            pygame.draw.circle(surface, (100, 120, 180), (px - bh // 6, base_y - 200 - bh // 8), bh // 5)
        elif kind == "rock":
            pts = [(px, base_y), (px + bw // 4, base_y - bh), (px + bw * 3 // 4, base_y - bh * 2 // 3),
                   (px + bw, base_y)]
            pygame.draw.polygon(surface, (100, 45, 28), pts)
            pygame.draw.polygon(surface, (130, 60, 35), [(px + bw // 4, base_y - bh),
                                                        (px + bw // 2, base_y - bh - 10),
                                                        (px + bw * 3 // 4, base_y - bh * 2 // 3)])
        elif kind == "dune":
            pts = [(px, base_y), (px + bw // 3, base_y - bh), (px + bw, base_y)]
            pygame.draw.polygon(surface, (140, 60, 35), pts)

    def draw(self, surface):
        d = self.data
        sky = d.get("sky", Colors.DARK)
        bottom = tuple(max(0, c - 40) for c in sky)
        gfx.gradient_sky(surface, sky, bottom, bands=28)

        ox, oy = self.camera.offset

        for ray in self._rays:
            a = ray["a"] + int(8 * math.sin(self.tick * 0.04 + ray["phase"]))
            rx = int(ray["x"] * SCREEN_WIDTH + math.sin(self.tick * ray["spd"] * 60 + ray["phase"]) * 40)
            s = pygame.Surface((int(ray["w"]), SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(8):
                alpha = max(0, a - i * 3)
                pygame.draw.rect(s, (255, 240, 200, alpha), (i * 2, 0, max(1, int(ray["w"]) - i * 4), SCREEN_HEIGHT))
            surface.blit(s, (rx - int(ray["w"]) // 2, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

        for st in self._stars:
            tw = 0.6 + 0.4 * math.sin(self.tick * 0.08 + st["tw"])
            bright = int(st["b"] * tw)
            px = int((st["x"] - ox * st["z"]) % (SCREEN_WIDTH + 40) - 20)
            py = int(st["y"] - oy * st["z"] * 0.5)
            if 0 <= py < SCREEN_HEIGHT:
                col = (bright, bright, min(255, bright + 30))
                if st["s"] >= 2:
                    gfx.soft_circle(surface, col, (px, py), st["s"] + 2, layers=2)
                pygame.draw.circle(surface, col, (px, py), st["s"])

        base_y = SCREEN_HEIGHT - 70
        for prop in self._far:
            self._draw_prop(surface, prop, ox, 0.18, base_y, col_far=True)
        for prop in self._mid:
            self._draw_prop(surface, prop, ox, 0.35, base_y + 10, col_far=False)

        if self.chapter_id != 7:
            haze = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
            for i in range(60):
                a = int(40 * (i / 60))
                pygame.draw.line(haze, (*sky, a), (0, i), (SCREEN_WIDTH, i))
            surface.blit(haze, (0, SCREEN_HEIGHT - 100))

        ground_col = d.get("ground_col", Colors.GRAY)
        for s in self.solids:
            r = self.camera.apply(s)
            if r.bottom < -30 or r.top > SCREEN_HEIGHT + 30 or r.right < -30 or r.left > SCREEN_WIDTH + 30:
                continue
            gfx.bevel_rect(surface, r, ground_col, top_h=6)
            if r.w > 50 and r.h <= 28:
                for dx in range(14, r.w - 10, 22):
                    pygame.draw.circle(surface, gfx.shade(ground_col, 30), (r.x + dx, r.y + 4), 2)
                    pygame.draw.circle(surface, gfx.shade(ground_col, -20), (r.x + dx, r.y + 5), 1)
            if r.h > 40:
                for wy in range(8, r.h - 4, 12):
                    pygame.draw.line(surface, gfx.shade(ground_col, -15),
                                     (r.x + 2, r.y + wy), (r.right - 2, r.y + wy), 1)

        gx, gy = self.camera.world_to_screen(self.goal_rect.x, self.goal_rect.y)
        wave = math.sin(self.tick * 0.14) * 5
        gfx.soft_circle_additive(surface, (80, 255, 120), (gx + 8, gy + 20), 28)
        pygame.draw.rect(surface, (30, 50, 35), (gx, gy, 6, 58))
        pygame.draw.rect(surface, (60, 100, 70), (gx, gy, 6, 4))
        flag = [(gx + 6, gy + 2), (gx + 32 + wave, gy + 14), (gx + 6, gy + 26)]
        pygame.draw.polygon(surface, Colors.GOLD, flag)
        pygame.draw.polygon(surface, Colors.SUCCESS,
                            [(gx + 6, gy + 6), (gx + 24 + wave * 0.7, gy + 14), (gx + 6, gy + 22)])

        for i, (tx, ty) in enumerate(self.data.get("terminals", [])):
            sx, sy = self.camera.world_to_screen(tx, ty)
            active = i in self.terminals_activated
            if active:
                gfx.soft_circle(surface, Colors.ACCENT, (sx, sy - 5), 18, layers=3)
            col = Colors.ACCENT if active else (55, 60, 80)
            pygame.draw.rect(surface, gfx.shade(col, -30), (sx - 14, sy - 24, 30, 36), border_radius=4)
            pygame.draw.rect(surface, col, (sx - 12, sy - 22, 26, 32), border_radius=3)
            pygame.draw.rect(surface, (5, 8, 12), (sx - 9, sy - 17, 20, 14), border_radius=2)
            if active:
                pygame.draw.rect(surface, Colors.SUCCESS, (sx - 7, sy - 15, 16, 10), border_radius=1)
                if int(self.tick * 0.2) % 2:
                    pygame.draw.rect(surface, (200, 255, 220), (sx - 5, sy - 13, 4, 2))
            else:
                for ly in range(3):
                    pygame.draw.line(surface, (30, 35, 45),
                                     (sx - 6, sy - 14 + ly * 3), (sx + 6, sy - 14 + ly * 3), 1)

        for c in self.collectibles:
            c.draw(surface, self.camera)
        for e in self.enemies:
            e.draw(surface, self.camera)
        self.player.draw(surface, self.camera)

        for p in self._dust:
            px = int(p["x"] - ox * 0.6)
            py = int(p["y"] - oy * 0.6)
            if -5 < px < SCREEN_WIDTH + 5 and -5 < py < SCREEN_HEIGHT + 5:
                pygame.draw.circle(surface, p["c"], (px % (SCREEN_WIDTH + 10) - 5, py), p["s"])

        self.engine.particles.draw(surface, *self.camera.offset)
        gfx.draw_vignette(surface, strength=100)
        self._draw_hud(surface)

        if self.narration_timer > 0 and self.current_narration:
            n = self.engine.font_md.render(self.current_narration, True, Colors.WHITE)
            bw, bh = n.get_width() + 36, n.get_height() + 20
            bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 175))
            pygame.draw.rect(bg, (0, 200, 255, 80), (0, 0, bw, bh), 1, border_radius=4)
            surface.blit(bg, (SCREEN_WIDTH // 2 - bw // 2, 68))
            surface.blit(n, (SCREEN_WIDTH // 2 - n.get_width() // 2, 78))

        if self.msg_timer > 0:
            m = self.engine.font_sm.render(self.msg, True, Colors.ACCENT)
            surface.blit(m, (SCREEN_WIDTH // 2 - m.get_width() // 2, 125))

        if self.fade > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, min(255, int(self.fade))))
            surface.blit(overlay, (0, 0))

        if self.won:
            glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            glow.fill((40, 120, 60, 60))
            surface.blit(glow, (0, 0))
            t = self.engine.font_lg.render("CHAPTER COMPLETE", True, Colors.SUCCESS)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 24))
            sub = self.engine.font_sm.render("Continuing the odyssey...", True, Colors.WHITE)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 28))

        if not self.player.alive and not self.won:
            t = self.engine.font_lg.render("FALLEN", True, Colors.DANGER)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 24))
            sub = self.engine.font_sm.render("Resolve remains. Restarting...", True, Colors.WHITE)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 28))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            surface.blit(overlay, (0, 0))
            t = self.engine.font_lg.render("PAUSED", True, Colors.WHITE)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
            s = self.engine.font_sm.render("Esc resume  ·  Q quit to title", True, Colors.GRAY)
            surface.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def _draw_hud(self, surface):
        panel = pygame.Surface((130, 54), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        pygame.draw.rect(panel, (0, 200, 255, 60), (0, 0, 130, 54), 1, border_radius=4)
        surface.blit(panel, (10, 8))

        for i in range(self.player.max_hp):
            x = 18 + i * 22
            if i < self.player.hp:
                pygame.draw.rect(surface, (20, 80, 40), (x, 16, 18, 14), border_radius=3)
                pygame.draw.rect(surface, Colors.SUCCESS, (x, 16, 18, 12), border_radius=3)
                pygame.draw.rect(surface, (180, 255, 200), (x + 2, 18, 8, 3), border_radius=1)
            else:
                pygame.draw.rect(surface, (35, 35, 45), (x, 16, 18, 14), border_radius=3)
                pygame.draw.rect(surface, (50, 50, 60), (x, 16, 18, 14), 1, border_radius=3)

        books = self.engine.font_sm.render(f"Books {self.player.books}", True, (150, 190, 240))
        parts = self.engine.font_sm.render(f"Parts {self.player.parts}", True, Colors.GOLD)
        surface.blit(books, (18, 36))
        surface.blit(parts, (90, 36))

        if self.player.can_double_jump:
            dj = self.engine.font_sm.render("2x Jump", True, Colors.ACCENT)
            surface.blit(dj, (150, 18))

        ch = next((c for c in CHAPTERS if c["id"] == self.chapter_id), None)
        if ch:
            tag = self.engine.font_sm.render(f"Ch.{ch['id']}  {ch['title']}", True, (160, 165, 180))
            tw = tag.get_width() + 16
            tp = pygame.Surface((tw, 24), pygame.SRCALPHA)
            tp.fill((0, 0, 0, 110))
            surface.blit(tp, (SCREEN_WIDTH - tw - 10, 10))
            surface.blit(tag, (SCREEN_WIDTH - tag.get_width() - 18, 14))

        if self.objective:
            obj = self.engine.font_sm.render(self.objective, True, (190, 190, 200))
            ow = obj.get_width() + 20
            op = pygame.Surface((ow, 22), pygame.SRCALPHA)
            op.fill((0, 0, 0, 100))
            surface.blit(op, (12, SCREEN_HEIGHT - 30))
            surface.blit(obj, (22, SCREEN_HEIGHT - 28))
