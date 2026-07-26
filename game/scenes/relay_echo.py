"""Playable Relay Echo candidate backed by transactional mission state."""

from __future__ import annotations

from copy import deepcopy

import pygame

from game.core import gfx
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Colors
from game.data.relay_echo_candidate import RELAY_ECHO_CANDIDATE
from game.entities.enemy import Enemy
from game.entities.player import Player
from game.scenes.level import LevelScene


class RelayEchoScene(LevelScene):
    """Complete candidate path kept outside campaign routing until promotion."""

    mission_id = "relay_echo"
    slice_id = "relay_echo_playable_candidate"

    def __init__(self, engine) -> None:
        super().__init__(engine, 8)
        self.data = deepcopy(RELAY_ECHO_CANDIDATE)
        self.objective = self.data["objective"]
        self.phase = "insertion"
        self.overload_timer = 0.0
        self.completion_timer = 0.0
        self.completion_transitioned = False
        self.mission_complete = False
        self._last_transition: dict | None = None

    @property
    def mission_state(self) -> dict:
        return self.engine.save.relay_echo

    @property
    def current_objective(self) -> str | None:
        return self.mission_state["current_objective"]

    def on_enter(self) -> None:
        super().on_enter()
        state = self.mission_state
        if state["attempts"] == 0:
            raise ValueError("Relay Echo candidate requires a prepared mission attempt")
        checkpoint = self.data["checkpoints"][state["checkpoint_id"]]
        self.player.x = float(checkpoint["position"][0])
        self.player.y = float(checkpoint["position"][1])
        self.player.can_dash = True
        self.player.can_double_jump = True
        self.player.parts = int(state["signal_fragments"])
        if state["signal_fragments"] >= 3:
            for collectible in self.collectibles:
                if collectible.kind == "part":
                    collectible.alive = False
        if state["relay_core_open"]:
            for enemy in self._guardians():
                enemy.alive = False
        self.phase = state["current_state"]
        self.mission_complete = bool(state["completion_eligible"])
        self.completion_timer = 0.0
        self.completion_transitioned = False
        self.dead_timer = 0.0
        self.won = False
        self.goal_rect = pygame.Rect(self.data["goal"][0], self.data["goal"][1], 48, 64)
        self.camera.set_target(self.player.x, self.player.y)
        self.camera.update()

    def _guardians(self) -> list[Enemy]:
        lower, upper = self.data["guardian_range"]
        return [enemy for enemy in self.enemies if lower <= enemy.x <= upper]

    def _guardians_defeated(self) -> bool:
        return all(not enemy.alive for enemy in self._guardians())

    def _near(self, point: tuple[int, int]) -> bool:
        radius_x, radius_y = self.data["interactions"]["interaction_radius"]
        return (
            abs(self.player.x - point[0]) <= radius_x
            and abs(self.player.y - point[1]) <= radius_y
        )

    def _persist_objective(
        self,
        objective_id: str,
        evidence: dict | None = None,
    ) -> bool:
        previous = deepcopy(self.engine.save.relay_echo)
        transition = self.engine.save.complete_relay_echo_objective(
            objective_id,
            evidence,
        )
        if not self.engine.save.save():
            self.engine.save.relay_echo = previous
            self.msg = f"Mission checkpoint failed to persist: {self.engine.save.last_error}"
            self.msg_timer = 240
            return False
        self._last_transition = transition
        self.phase = self.mission_state["current_state"]
        self.msg = self._objective_message(objective_id)
        self.msg_timer = 180
        self.engine.presentation.cue("terminal", 1.0)
        self.engine.audio.play("terminal", 0.9)
        if self.mission_state["completion_eligible"]:
            self.mission_complete = True
            self.completion_timer = 0.0
            self.player.invuln = 10_000
            self.engine.presentation.set_cinematic(True)
            self.engine.presentation.cue("goal", 1.3)
            self.engine.audio.play("goal", 1.2)
        return True

    def _objective_message(self, objective_id: str) -> str:
        messages = {
            "reach_noctis_relay": "Noctis Relay reached — signal hunt authorized",
            "recover_signal_fragments": "Three signal fragments committed",
            "triangulate_echo_source": "Echo source triangulated beneath the array",
            "breach_relay_core": "Relay core breached — alignment chamber exposed",
            "align_the_echo": "Echo alignment committed: redirect",
            "extract_before_collapse": "Extraction complete — candidate path verified",
        }
        return messages[objective_id]

    def _persist_failure(self, failure_id: str) -> bool:
        previous = deepcopy(self.engine.save.relay_echo)
        transition = self.engine.save.record_relay_echo_failure(failure_id)
        if not self.engine.save.save():
            self.engine.save.relay_echo = previous
            self.msg = f"Failure telemetry could not persist: {self.engine.save.last_error}"
            self.msg_timer = 240
            return False
        self._last_transition = transition
        self.phase = self.mission_state["current_state"]
        self.engine.save.stats["deaths"] = self.engine.save.stats.get("deaths", 0) + (
            1 if failure_id == "player_down" else 0
        )
        self._restore_checkpoint()
        self.msg = (
            f"Telemetry retained — {failure_id.replace('_', ' ')}; "
            f"insight {self.mission_state['telemetry_insight']}"
        )
        self.msg_timer = 210
        self.engine.presentation.cue("terminal", 1.0)
        self.engine.audio.play("terminal", 0.85)
        return True

    def _restore_checkpoint(self) -> None:
        state = self.mission_state
        checkpoint = self.data["checkpoints"][state["checkpoint_id"]]
        previous_books = self.player.books
        self.player = Player(*checkpoint["position"])
        self.player.can_dash = True
        self.player.can_double_jump = True
        self.player.invuln = 90
        self.player.parts = int(state["signal_fragments"])
        self.player.books = previous_books
        self.enemies = [
            Enemy(x, y, kind) for kind, x, y in self.data.get("enemies", ())
        ]
        if state["relay_core_open"]:
            for enemy in self._guardians():
                enemy.alive = False
        if state["signal_fragments"] >= 3:
            for collectible in self.collectibles:
                if collectible.kind == "part":
                    collectible.alive = False
        self.dead_timer = 0.0
        self.overload_timer = 0.0
        self.camera.set_target(self.player.x, self.player.y)
        self.camera.update()

    def _update_objective(self, dt: float) -> None:
        objective_id = self.current_objective
        interactions = self.data["interactions"]
        interact = self.engine.input.just_pressed("interact")
        if objective_id == "reach_noctis_relay":
            if self.player.x >= interactions["reach_x"]:
                self._persist_objective(objective_id)
            return
        if objective_id == "recover_signal_fragments":
            if self.player.parts >= 3:
                self._persist_objective(
                    objective_id,
                    {"signal_fragments": 3},
                )
            return
        if objective_id == "triangulate_echo_source":
            terminal = interactions["triangulation_terminal"]
            if self._near(terminal):
                if interact:
                    self.overload_timer = 0.0
                    self._persist_objective(
                        objective_id,
                        {"echo_source": "subsurface_array"},
                    )
                else:
                    self.overload_timer += dt
                    if self.overload_timer >= interactions["overload_frames"]:
                        self._persist_failure("relay_overload")
            else:
                self.overload_timer = max(0.0, self.overload_timer - dt * 2)
            return
        if objective_id == "breach_relay_core":
            terminal = interactions["breach_terminal"]
            if interact and self._near(terminal):
                if self._guardians_defeated():
                    self._persist_objective(
                        objective_id,
                        {"relay_core_open": True},
                    )
                else:
                    remaining = sum(1 for enemy in self._guardians() if enemy.alive)
                    self.msg = f"Relay core defended — {remaining} guardian(s) remain"
                    self.msg_timer = 90
            return
        if objective_id == "align_the_echo":
            terminal = interactions["alignment_terminal"]
            if interact and self._near(terminal):
                self._persist_objective(
                    objective_id,
                    {"echo_alignment": "redirect"},
                )
            return
        if objective_id == "extract_before_collapse":
            if self.player.x >= interactions["extraction_x"]:
                self._persist_objective(objective_id)

    def update(self, dt) -> None:
        if self.paused:
            return
        if self.mission_complete:
            self.tick += dt
            self.completion_timer += dt
            if (
                self.completion_timer >= self.data["interactions"]["completion_frames"]
                and not self.completion_transitioned
            ):
                self.completion_transitioned = True
                self.engine.presentation.set_cinematic(False)
                self.engine.go_campaign()
            return
        if not self.player.alive:
            self.tick += dt
            self.dead_timer += dt
            if self.dead_timer > 60:
                self._persist_failure("player_down")
            return
        super().update(dt)
        self.won = False
        self._update_objective(dt)

    def _draw_terminal(
        self,
        surface,
        point: tuple[int, int],
        label: str,
        active: bool,
    ) -> None:
        sx, sy = self.camera.world_to_screen(*point)
        color = Colors.SUCCESS if active else Colors.ACCENT
        if active:
            gfx.soft_circle_additive(surface, color, (sx, sy - 16), 24)
        pygame.draw.rect(
            surface,
            (18, 22, 36),
            (sx - 20, sy - 48, 40, 56),
            border_radius=5,
        )
        pygame.draw.rect(
            surface,
            color,
            (sx - 16, sy - 44, 32, 34),
            2,
            border_radius=4,
        )
        text = self.engine.font_sm.render(label, True, color)
        surface.blit(text, (sx - text.get_width() // 2, sy - 68))

    def _draw_candidate_hud(self, surface) -> None:
        state = self.mission_state
        objective = (state["current_objective"] or "candidate_complete").replace(
            "_", " "
        )
        heading = self.engine.font_sm.render(
            f"RELAY ECHO CANDIDATE  ·  {state['current_state'].replace('_', ' ').upper()}",
            True,
            Colors.GOLD,
        )
        detail = self.engine.font_sm.render(
            f"Objective: {objective}  ·  Checkpoint {state['checkpoint_id']}/6  ·  "
            f"Insight {state['telemetry_insight']}",
            True,
            (190, 205, 225),
        )
        panel = pygame.Surface(
            (max(heading.get_width(), detail.get_width()) + 24, 54),
            pygame.SRCALPHA,
        )
        panel.fill((0, 0, 0, 165))
        pygame.draw.rect(panel, (255, 190, 70, 80), panel.get_rect(), 1, 5)
        x = SCREEN_WIDTH - panel.get_width() - 12
        surface.blit(panel, (x, 40))
        surface.blit(heading, (x + 12, 47))
        surface.blit(detail, (x + 12, 69))

    def draw(self, surface) -> None:
        super().draw(surface)
        state = self.mission_state
        completed = set(state["completed_objectives"])
        interactions = self.data["interactions"]
        self._draw_terminal(
            surface,
            interactions["triangulation_terminal"],
            "TRIANGULATE",
            "triangulate_echo_source" in completed,
        )
        self._draw_terminal(
            surface,
            interactions["breach_terminal"],
            "BREACH",
            "breach_relay_core" in completed,
        )
        self._draw_terminal(
            surface,
            interactions["alignment_terminal"],
            "ALIGN",
            "align_the_echo" in completed,
        )
        self._draw_candidate_hud(surface)

        if self.current_objective == "triangulate_echo_source" and self.overload_timer > 0:
            remaining = max(
                0,
                self.data["interactions"]["overload_frames"] - self.overload_timer,
            )
            warning = self.engine.font_sm.render(
                f"RELAY OVERLOAD IN {remaining / 60:.1f}s — INTERACT TO COMMIT",
                True,
                Colors.DANGER,
            )
            surface.blit(
                warning,
                (SCREEN_WIDTH // 2 - warning.get_width() // 2, 150),
            )

        if self.mission_complete:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 8, 28, 215))
            surface.blit(overlay, (0, 0))
            title = self.engine.font_lg.render(
                "RELAY ECHO CANDIDATE COMPLETE",
                True,
                Colors.SUCCESS,
            )
            line_one = self.engine.font_md.render(
                "The complete path is playable and transactionally verified.",
                True,
                Colors.WHITE,
            )
            line_two = self.engine.font_sm.render(
                "CAMPAIGN PROMOTION, FINAL CONTENT, ACCESSIBILITY PARITY, AND AAA EVIDENCE PENDING",
                True,
                Colors.GOLD,
            )
            surface.blit(
                title,
                (SCREEN_WIDTH // 2 - title.get_width() // 2, 270),
            )
            surface.blit(
                line_one,
                (SCREEN_WIDTH // 2 - line_one.get_width() // 2, 332),
            )
            surface.blit(
                line_two,
                (SCREEN_WIDTH // 2 - line_two.get_width() // 2, 378),
            )
