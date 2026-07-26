"""Playable Phase 1 fictionalized Mars-landing vertical slice."""

from __future__ import annotations

from copy import deepcopy

import pygame

from game.core import gfx
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Colors
from game.data.phase1_slice import MARS_LANDING_SLICE, PHASE_ORDER
from game.entities.mars_sentinel import MarsSentinel
from game.entities.player import Player
from game.scenes.level import LevelScene


class VerticalSliceScene(LevelScene):
    """Own the Phase 1 journey without entering Classic Mode progression."""

    def __init__(self, engine) -> None:
        super().__init__(engine, 8)
        self.data = deepcopy(MARS_LANDING_SLICE)
        self.objective = self.data["objective"]
        self.slice_id = self.data["slice_id"]
        self.phase = "arrival"
        self.current_checkpoint = 0
        self.failure_count = 0
        self.insight_level = 0
        self.resource_gate_open = False
        self.resource_gate_rect: pygame.Rect | None = None
        self.resource_terminal = (0, 0)
        self.required_parts = 3
        self.arrival_timer = 0.0
        self.ascent_active = False
        self.ascent_timer = 0.0
        self.slice_complete = False
        self.completion_timer = 0.0
        self.completion_transitioned = False
        self._landing_y = 790.0
        self._last_checkpoint_message = -1

    def on_enter(self) -> None:
        super().on_enter()
        progress = dict(self.engine.save.phase1_slice)
        self.current_checkpoint = min(
            int(progress.get("checkpoint_id", 0)),
            len(self.data["checkpoints"]) - 1,
        )
        self.failure_count = int(progress.get("failures", 0))
        self.insight_level = min(3, self.failure_count)
        self.resource_gate_open = bool(progress.get("resource_gate_open", False))
        self.phase = progress.get("best_phase", "arrival")
        if self.phase not in PHASE_ORDER:
            self.phase = "arrival"

        gate = self.data["resource_gate"]
        self.resource_gate_rect = pygame.Rect(*gate["rect"])
        self.resource_terminal = tuple(gate["terminal"])
        self.required_parts = int(gate["required_parts"])
        if not self.resource_gate_open:
            self.solids.append(self.resource_gate_rect)

        self.enemies = [
            MarsSentinel(item["id"], item["x"], item["y"], item["tier"])
            for item in self.data["sentinels"]
        ]
        self._configure_sentinels()

        checkpoint = self.data["checkpoints"][self.current_checkpoint]
        self.player.x = float(checkpoint["x"])
        self.player.y = float(checkpoint["y"])
        self.player.can_dash = True
        self.player.can_double_jump = True
        if self.resource_gate_open:
            self.player.parts = self.required_parts

        self.goal_rect = pygame.Rect(self.data["width"] + 500, 0, 40, 40)
        self.arrival_timer = 150.0 if self.current_checkpoint == 0 else 0.0
        self.ascent_active = False
        self.ascent_timer = 0.0
        self.slice_complete = False
        self.completion_timer = 0.0
        self.completion_transitioned = False
        self.won = False
        self.dead_timer = 0.0
        self.engine.presentation.set_cinematic(self.arrival_timer > 0)
        self.camera.set_target(self.player.x, self.player.y)
        self.camera.update()

    def on_exit(self) -> None:
        self.engine.presentation.set_cinematic(False)

    def _configure_sentinels(self) -> None:
        for sentinel in self.enemies:
            sentinel.configure_encounter(self.insight_level, self.resource_gate_open)

    def _phase_index(self, phase: str) -> int:
        return PHASE_ORDER.index(phase)

    def _set_phase(self, phase: str, *, persist: bool = True) -> None:
        if phase not in PHASE_ORDER:
            raise ValueError(f"Unknown Phase 1 slice phase: {phase}")
        if self._phase_index(phase) < self._phase_index(self.phase):
            return
        if phase == self.phase:
            return
        self.phase = phase
        if persist:
            self.engine.save.update_phase1_slice(
                checkpoint_id=self.current_checkpoint,
                failures=self.failure_count,
                best_phase=phase,
                resource_gate_open=self.resource_gate_open,
            )
            self.engine.save.save()

    def _checkpoint_for_player(self) -> int:
        checkpoint_id = self.current_checkpoint
        for checkpoint in self.data["checkpoints"]:
            if self.player.x >= checkpoint["x"]:
                checkpoint_id = max(checkpoint_id, checkpoint["id"])
        return checkpoint_id

    def _commit_checkpoint(self) -> None:
        checkpoint_id = self._checkpoint_for_player()
        if checkpoint_id <= self.current_checkpoint:
            return
        self.current_checkpoint = checkpoint_id
        checkpoint = self.data["checkpoints"][checkpoint_id]
        self._set_phase(checkpoint["phase"], persist=False)
        self.engine.save.update_phase1_slice(
            checkpoint_id=checkpoint_id,
            failures=self.failure_count,
            best_phase=self.phase,
            resource_gate_open=self.resource_gate_open,
        )
        self.engine.save.save()
        self.msg = f"Telemetry checkpoint {checkpoint_id} secured"
        self.msg_timer = 120
        self.engine.presentation.cue("terminal", 0.8)
        self.engine.audio.play("terminal", 0.75)
        self._last_checkpoint_message = checkpoint_id

    def _near_resource_terminal(self) -> bool:
        tx, ty = self.resource_terminal
        return abs(self.player.x - tx) < 55 and abs(self.player.y - ty) < 70

    def _open_resource_gate(self) -> bool:
        if self.resource_gate_open:
            return True
        if self.player.parts < self.required_parts:
            missing = self.required_parts - self.player.parts
            self.msg = f"Relay shield requires {missing} more power cell{'s' if missing != 1 else ''}"
            self.msg_timer = 140
            self.engine.audio.play("ui_move", 0.55)
            return False

        self.resource_gate_open = True
        if self.resource_gate_rect in self.solids:
            self.solids.remove(self.resource_gate_rect)
        self._configure_sentinels()
        self._set_phase("resource_gate", persist=False)
        self.engine.save.update_phase1_slice(
            checkpoint_id=self.current_checkpoint,
            failures=self.failure_count,
            best_phase=self.phase,
            resource_gate_open=True,
        )
        self.engine.save.save()
        self.msg = "Relay shield disrupted — warden armor and charge speed reduced"
        self.msg_timer = 210
        self.engine.presentation.cue("terminal", 1.35)
        self.engine.audio.play("terminal", 1.25)
        self.engine.particles.emit_burst(
            self.resource_gate_rect.centerx,
            self.resource_gate_rect.centery,
            Colors.ACCENT,
        )
        return True

    def _recover_from_failure(self) -> None:
        previous_parts = self.player.parts
        previous_books = self.player.books
        self.failure_count += 1
        self.insight_level = min(3, self.failure_count)
        checkpoint = self.data["checkpoints"][self.current_checkpoint]
        self.player = Player(checkpoint["x"], checkpoint["y"])
        self.player.can_dash = True
        self.player.can_double_jump = True
        self.player.parts = previous_parts
        self.player.books = previous_books
        self.player.invuln = 90

        for sentinel in self.enemies:
            sentinel.configure_encounter(self.insight_level, self.resource_gate_open)
            if sentinel.spawn_x >= checkpoint["x"]:
                sentinel.reset(preserve_damage=False)

        self.dead_timer = 0.0
        self._set_phase("failure_recovery", persist=False)
        self.engine.save.stats["deaths"] = self.engine.save.stats.get("deaths", 0) + 1
        self.engine.save.update_phase1_slice(
            checkpoint_id=self.current_checkpoint,
            failures=self.failure_count,
            best_phase=self.phase,
            resource_gate_open=self.resource_gate_open,
        )
        self.engine.save.save()
        learned_seconds = self.insight_level * 0.15
        self.msg = f"Telemetry retained — sentinel warning extended by {learned_seconds:.2f}s"
        self.msg_timer = 210
        self.engine.presentation.cue("terminal", 1.0)
        self.engine.audio.play("terminal", 0.9)
        self.camera.set_target(self.player.x, self.player.y)

    def _final_wardens_defeated(self) -> bool:
        return all(not enemy.alive for enemy in self.enemies if enemy.spawn_x >= 3800)

    def _start_ascent(self) -> None:
        if self.ascent_active or self.slice_complete:
            return
        self.ascent_active = True
        self.ascent_timer = 0.0
        self._set_phase("ascent")
        self.player.invuln = 10_000
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.engine.presentation.set_cinematic(True)
        self.engine.presentation.cue("goal", 1.1)
        self.engine.audio.play("goal", 1.0)

    def _update_arrival(self, dt: float) -> None:
        self.tick += dt
        self.arrival_timer = max(0.0, self.arrival_timer - dt)
        descent_progress = 1.0 - self.arrival_timer / 150.0
        self.player.x = 170.0
        self.player.y = self._landing_y - max(0.0, 1.0 - descent_progress) * 180.0
        self.camera.set_target(420.0 + descent_progress * 180.0, 650.0)
        self.camera.update()
        self.fade = max(0.0, self.fade - 5.0 * dt)
        if self.arrival_timer <= 0:
            self.player.y = self._landing_y
            self.engine.presentation.set_cinematic(False)
            self._set_phase("movement_mastery")
            self.msg = "Landing stable. Movement control returned."
            self.msg_timer = 150

    def _update_ascent(self, dt: float) -> None:
        self.tick += dt
        self.ascent_timer += dt
        ascent = self.data["ascent"]
        progress = min(1.0, self.ascent_timer / ascent["duration_frames"])
        self.player.x = float(ascent["platform_x"])
        self.player.y = float(ascent["platform_y"] - progress * 520.0)
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.camera.set_target(self.player.x, self.player.y - 100.0)
        self.camera.update()
        if int(self.ascent_timer) % 3 == 0:
            self.engine.particles.emit(
                self.player.x + self.player.w / 2,
                self.player.y + self.player.h + 24,
                count=3,
                speed=3.5,
                color=(255, 150, 70),
                life=26,
                size=4,
                gravity=0.08,
            )
        if progress >= 1.0:
            self.ascent_active = False
            self.slice_complete = True
            self.completion_timer = 0.0
            self._set_phase("complete", persist=False)
            self.engine.save.update_phase1_slice(
                checkpoint_id=self.current_checkpoint,
                failures=self.failure_count,
                best_phase="complete",
                completed=True,
                resource_gate_open=self.resource_gate_open,
            )
            self.engine.save.save()
            self.engine.presentation.cue("goal", 1.5)
            self.engine.audio.play("goal", 1.35)

    def update(self, dt) -> None:
        if self.paused:
            return
        if self.slice_complete:
            self.tick += dt
            self.completion_timer += dt
            if self.completion_timer > 300 and not self.completion_transitioned:
                self.completion_transitioned = True
                self.engine.go_title()
            return
        if self.arrival_timer > 0:
            self._update_arrival(dt)
            return
        if self.ascent_active:
            self._update_ascent(dt)
            return
        if not self.player.alive:
            self.tick += dt
            self.dead_timer += dt
            if self.dead_timer > 60:
                self._recover_from_failure()
            return

        if self.engine.input.just_pressed("interact") and self._near_resource_terminal():
            self._open_resource_gate()

        super().update(dt)
        self._commit_checkpoint()

        if self.player.x >= 1550:
            self._set_phase("adaptive_combat")
        if self.resource_gate_open and self.player.x >= 3600:
            self._set_phase("resource_gate")

        ascent = self.data["ascent"]
        if (
            self.resource_gate_open
            and self.player.x >= ascent["trigger_x"]
            and self._final_wardens_defeated()
        ):
            self._start_ascent()
        elif self.player.x >= ascent["trigger_x"] and not self._final_wardens_defeated():
            self.msg = "Ascent relay contested — disable the remaining wardens"
            self.msg_timer = max(self.msg_timer, 45)

    def _draw_resource_gate(self, surface) -> None:
        tx, ty = self.resource_terminal
        sx, sy = self.camera.world_to_screen(tx, ty)
        active = self.resource_gate_open
        color = Colors.SUCCESS if active else Colors.ACCENT
        if active:
            gfx.soft_circle_additive(surface, color, (sx, sy - 12), 22)
        pygame.draw.rect(surface, (24, 30, 38), (sx - 18, sy - 36, 36, 48), border_radius=5)
        pygame.draw.rect(surface, color, (sx - 14, sy - 32, 28, 32), 2, border_radius=4)
        cell_text = self.engine.font_sm.render(
            f"{min(self.player.parts, self.required_parts)}/{self.required_parts}",
            True,
            color,
        )
        surface.blit(cell_text, (sx - cell_text.get_width() // 2, sy - 25))

        if not active and self.resource_gate_rect is not None:
            gx, gy = self.camera.world_to_screen(
                self.resource_gate_rect.x,
                self.resource_gate_rect.y,
            )
            glow = 70 + int(35 * abs(pygame.math.Vector2(1, 0).rotate(self.tick * 2).y))
            barrier = pygame.Surface(self.resource_gate_rect.size, pygame.SRCALPHA)
            barrier.fill((30, 170, 255, glow))
            for y in range(0, barrier.get_height(), 18):
                pygame.draw.line(
                    barrier,
                    (150, 235, 255, min(220, glow + 70)),
                    (0, y),
                    (barrier.get_width(), y + 10),
                    2,
                )
            surface.blit(barrier, (gx, gy), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_lander(self, surface) -> None:
        ascent = self.data["ascent"]
        if self.ascent_active or self.slice_complete:
            world_x = self.player.x + self.player.w / 2
            world_y = self.player.y + 8
        else:
            world_x = ascent["platform_x"] + self.player.w / 2
            world_y = ascent["platform_y"] + 8
        sx, sy = self.camera.world_to_screen(world_x, world_y)
        pygame.draw.polygon(
            surface,
            (42, 48, 58),
            [(sx - 22, sy + 20), (sx - 13, sy - 28), (sx + 13, sy - 28), (sx + 22, sy + 20)],
        )
        pygame.draw.polygon(
            surface,
            (116, 128, 144),
            [(sx - 14, sy + 12), (sx - 8, sy - 23), (sx + 8, sy - 23), (sx + 14, sy + 12)],
        )
        pygame.draw.circle(surface, Colors.ACCENT, (int(sx), int(sy - 6)), 5)
        pygame.draw.line(surface, (140, 150, 165), (sx - 16, sy + 18), (sx - 28, sy + 34), 4)
        pygame.draw.line(surface, (140, 150, 165), (sx + 16, sy + 18), (sx + 28, sy + 34), 4)
        if self.ascent_active:
            flame = 22 + int((self.ascent_timer % 7) * 2)
            gfx.soft_circle_additive(surface, (255, 120, 40), (sx, sy + 30), flame)
            pygame.draw.polygon(
                surface,
                (255, 210, 90),
                [(sx - 8, sy + 20), (sx + 8, sy + 20), (sx, sy + 20 + flame)],
            )

    def _draw_slice_hud(self, surface) -> None:
        label = self.engine.font_sm.render(
            f"PHASE 1  ·  {self.phase.replace('_', ' ').upper()}",
            True,
            Colors.GOLD,
        )
        panel = pygame.Surface((label.get_width() + 24, 28), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        pygame.draw.rect(panel, (255, 190, 70, 80), panel.get_rect(), 1, border_radius=4)
        x = SCREEN_WIDTH - panel.get_width() - 12
        surface.blit(panel, (x, 40))
        surface.blit(label, (x + 12, 46))

        insight = self.engine.font_sm.render(
            f"Telemetry insight {self.insight_level}/3  ·  Cells {self.player.parts}/{self.required_parts}",
            True,
            (190, 205, 220),
        )
        surface.blit(insight, (SCREEN_WIDTH - insight.get_width() - 18, 74))

    def draw(self, surface) -> None:
        super().draw(surface)
        self._draw_resource_gate(surface)
        self._draw_lander(surface)
        self._draw_slice_hud(surface)

        if self.arrival_timer > 0:
            title = self.engine.font_lg.render("ARES REACH", True, Colors.WHITE)
            subtitle = self.engine.font_sm.render(
                "FIRST DESCENT  ·  GUIDANCE PARTIAL  ·  MANUAL CONTROL PENDING",
                True,
                Colors.ACCENT,
            )
            surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
            surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 172))

        if self.slice_complete:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 14, 24, 205))
            surface.blit(overlay, (0, 0))
            title = self.engine.font_lg.render("ASCENT RELAY RESTORED", True, Colors.SUCCESS)
            line_one = self.engine.font_md.render(
                "Failure kept the telemetry. The next frontier begins informed.",
                True,
                Colors.WHITE,
            )
            line_two = self.engine.font_sm.render(
                "PHASE 1 PLAYABLE PATH COMPLETE  ·  AAA-QUALITY EVIDENCE STILL PENDING",
                True,
                Colors.GOLD,
            )
            surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 270))
            surface.blit(line_one, (SCREEN_WIDTH // 2 - line_one.get_width() // 2, 332))
            surface.blit(line_two, (SCREEN_WIDTH // 2 - line_two.get_width() // 2, 378))
