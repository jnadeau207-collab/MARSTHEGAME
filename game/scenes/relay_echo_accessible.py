"""Accessibility-compliant Relay Echo candidate layered over the verified scene."""

from __future__ import annotations

from typing import Any

import pygame

from game.core import gfx
from game.core.accessibility import subtitle_policy
from game.core.relay_echo_accessibility import relay_echo_accessibility_profile
from game.core.settings import SCREEN_WIDTH
from game.scenes.relay_echo import RelayEchoScene


class AccessibleRelayEchoScene(RelayEchoScene):
    """Apply the complete Relay Echo accessibility contract without promotion."""

    slice_id = "relay_echo_accessibility_candidate"

    def __init__(self, engine) -> None:
        super().__init__(engine)
        self.accessibility = relay_echo_accessibility_profile(engine.settings)

    def on_enter(self) -> None:
        self.accessibility = relay_echo_accessibility_profile(self.engine.settings)
        super().on_enter()
        if self.accessibility.reduced_motion:
            self.engine.presentation.set_cinematic(False)

    def on_exit(self) -> None:
        self.engine.presentation.set_cinematic(False)

    def accessibility_evidence(self) -> dict[str, Any]:
        base_radius = tuple(self.data["interactions"]["interaction_radius"])
        base_overload = int(self.data["interactions"]["overload_frames"])
        return {
            **self.accessibility.evidence(),
            "effective_interaction_radius": self.accessibility.interaction_radius(base_radius),
            "effective_overload_frames": self.accessibility.overload_frames(base_overload),
            "recovery_invulnerability_frames": (
                self.accessibility.recovery_invulnerability_frames()
            ),
            "objective_palette": self.accessibility.objective_palette(),
        }

    def _near(self, point: tuple[int, int]) -> bool:
        radius_x, radius_y = self.accessibility.interaction_radius(
            tuple(self.data["interactions"]["interaction_radius"])
        )
        return (
            abs(self.player.x - point[0]) <= radius_x
            and abs(self.player.y - point[1]) <= radius_y
        )

    def _persist_objective(
        self,
        objective_id: str,
        evidence: dict | None = None,
    ) -> bool:
        persisted = super()._persist_objective(objective_id, evidence)
        if persisted and self.accessibility.reduced_motion:
            self.engine.presentation.set_cinematic(False)
        return persisted

    def _restore_checkpoint(self) -> None:
        super()._restore_checkpoint()
        self.player.invuln = self.accessibility.recovery_invulnerability_frames()

    def _update_objective(self, dt: float) -> None:
        objective_id = self.current_objective
        interactions = self.data["interactions"]
        interact = self.accessibility.accepts_interact(self.engine.input)
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
                    if self.overload_timer >= self.accessibility.overload_frames(
                        int(interactions["overload_frames"])
                    ):
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

    def _draw_terminal(
        self,
        surface,
        point: tuple[int, int],
        label: str,
        active: bool,
    ) -> None:
        palette = self.accessibility.objective_palette()
        sx, sy = self.camera.world_to_screen(*point)
        color = palette["complete"] if active else palette["active"]
        if active and not self.accessibility.reduced_motion:
            gfx.soft_circle_additive(surface, color, (sx, sy - 16), 24)
        pygame.draw.rect(
            surface,
            (6, 8, 12) if self.accessibility.high_contrast_objectives else (18, 22, 36),
            (sx - 20, sy - 48, 40, 56),
            border_radius=5,
        )
        pygame.draw.rect(
            surface,
            color,
            (sx - 16, sy - 44, 32, 34),
            3 if self.accessibility.high_contrast_objectives else 2,
            border_radius=4,
        )
        text = self.engine.font_sm.render(label, True, color)
        surface.blit(text, (sx - text.get_width() // 2, sy - 68))

    def _draw_candidate_hud(self, surface) -> None:
        state = self.mission_state
        palette = self.accessibility.objective_palette()
        objective = (state["current_objective"] or "candidate_complete").replace("_", " ")
        heading = self.engine.font_sm.render(
            f"RELAY ECHO ACCESSIBLE  ·  {state['current_state'].replace('_', ' ').upper()}",
            True,
            palette["active"],
        )
        detail = self.engine.font_sm.render(
            f"Objective: {objective}  ·  Checkpoint {state['checkpoint_id']}/6  ·  "
            f"Insight {state['telemetry_insight']}",
            True,
            palette["detail"],
        )
        mode = self.engine.font_sm.render(
            "ASSIST ON" if self.accessibility.assist_mode else "STANDARD ASSIST",
            True,
            palette["complete"],
        )
        panel = pygame.Surface(
            (max(heading.get_width(), detail.get_width(), mode.get_width()) + 24, 74),
            pygame.SRCALPHA,
        )
        panel.fill((0, 0, 0, 220 if self.accessibility.high_contrast_objectives else 165))
        pygame.draw.rect(panel, (*palette["active"], 150), panel.get_rect(), 2, 5)
        x = SCREEN_WIDTH - panel.get_width() - 12
        surface.blit(panel, (x, 40))
        surface.blit(heading, (x + 12, 47))
        surface.blit(detail, (x + 12, 69))
        surface.blit(mode, (x + 12, 91))

    def _draw_accessible_narration(self, surface, text: str) -> None:
        policy = subtitle_policy(self.engine.settings.get("accessibility"))
        if not policy["visible"] or not text:
            return
        base = self.engine.font_md.render(text, True, (255, 255, 255))
        scale = float(policy["scale"])
        rendered = base
        if scale != 1.0:
            rendered = pygame.transform.smoothscale(
                base,
                (
                    max(1, round(base.get_width() * scale)),
                    max(1, round(base.get_height() * scale)),
                ),
            )
        x = SCREEN_WIDTH // 2 - rendered.get_width() // 2
        y = 78
        if policy["background"]:
            padding_x = 18
            padding_y = 10
            background = pygame.Surface(
                (rendered.get_width() + padding_x * 2, rendered.get_height() + padding_y * 2),
                pygame.SRCALPHA,
            )
            background.fill((0, 0, 0, 220))
            pygame.draw.rect(
                background,
                (255, 255, 255, 170),
                background.get_rect(),
                2,
                border_radius=5,
            )
            surface.blit(background, (x - padding_x, y - padding_y))
        else:
            shadow = self.engine.font_md.render(text, True, (0, 0, 0))
            if scale != 1.0:
                shadow = pygame.transform.smoothscale(shadow, rendered.get_size())
            surface.blit(shadow, (x + 2, y + 2))
        surface.blit(rendered, (x, y))

    def draw(self, surface) -> None:
        narration = self.current_narration
        narration_timer = self.narration_timer
        self.current_narration = ""
        try:
            super().draw(surface)
        finally:
            self.current_narration = narration
        if narration_timer > 0:
            self._draw_accessible_narration(surface, narration)
