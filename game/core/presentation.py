"""Deterministic presentation cues with accessibility-aware intensity."""

from __future__ import annotations

from collections import deque
from typing import Any

import pygame

from game.core.accessibility import normalize_accessibility

_CUES = {
    "ui_move": ((80, 180, 255), 22, 0.0),
    "jump": ((80, 190, 255), 34, 0.0),
    "dash": ((40, 220, 255), 48, 3.0),
    "attack": ((255, 205, 80), 42, 1.5),
    "hit": ((255, 235, 150), 85, 5.0),
    "hurt": ((255, 70, 60), 80, 5.0),
    "pickup": ((255, 205, 70), 46, 1.0),
    "terminal": ((0, 220, 255), 58, 2.5),
    "goal": ((90, 255, 150), 110, 7.0),
    "death": ((170, 20, 30), 95, 7.0),
}


class PresentationDirector:
    """Own global flashes, letterbox beats, cue history, and camera motion policy."""

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        settings = settings or {}
        self.accessibility = normalize_accessibility(settings.get("accessibility"))
        self.flash_color = (255, 255, 255)
        self.flash_alpha = 0.0
        self.letterbox = 0.0
        self.letterbox_target = 0.0
        self.event_log: deque[dict[str, Any]] = deque(maxlen=256)
        self._last_state: dict[str, Any] = {}
        self._pending_shake = 0.0
        self._scene_token: int | None = None

    def refresh_settings(self, settings: dict[str, Any]) -> None:
        self.accessibility = normalize_accessibility(settings.get("accessibility"))

    def hit_stop_frames(self, frames: int) -> int:
        return max(0, round(frames * self.accessibility["hit_stop"]))

    def cue(self, name: str, strength: float = 1.0) -> None:
        strength = max(0.0, min(2.0, float(strength)))
        color, alpha, shake = _CUES.get(name, ((255, 255, 255), 24, 0.0))
        scaled_alpha = alpha * strength * self.accessibility["flash_intensity"]
        scaled_shake = shake * strength * self.accessibility["screen_shake"]
        self.flash_color = color
        self.flash_alpha = max(self.flash_alpha, scaled_alpha)
        self._pending_shake = max(self._pending_shake, scaled_shake)
        self.event_log.append(
            {
                "name": name,
                "strength": strength,
                "flash_alpha": scaled_alpha,
                "shake": scaled_shake,
            }
        )

    def set_cinematic(self, enabled: bool) -> None:
        self.letterbox_target = 54.0 if enabled else 0.0

    def _reset_scene_state(self, scene: Any) -> None:
        token = id(scene)
        if token == self._scene_token:
            return
        self._scene_token = token
        self._last_state.clear()
        self._pending_shake = 0.0
        self.set_cinematic(False)

    def observe(self, scene: Any) -> None:
        """Translate meaningful scene transitions into presentation cues."""

        if scene is None:
            return
        self._reset_scene_state(scene)
        camera = getattr(scene, "camera", None)
        if camera is not None and hasattr(camera, "configure_accessibility"):
            camera.configure_accessibility(self.accessibility)

        selected = getattr(scene, "selected", None)
        if selected is not None and selected != self._last_state.get("selected"):
            if "selected" in self._last_state:
                self.cue("ui_move", 0.5)
            self._last_state["selected"] = selected

        player = getattr(scene, "player", None)
        if player is not None:
            state = getattr(player, "state", None)
            previous_state = self._last_state.get("player_state")
            if state != previous_state:
                if state in {"jump", "dash", "attack", "hurt"}:
                    self.cue(state)
                self._last_state["player_state"] = state

            hp = getattr(player, "hp", None)
            previous_hp = self._last_state.get("player_hp")
            if previous_hp is not None and hp is not None and hp < previous_hp:
                self.cue("hurt", 1.15)
            self._last_state["player_hp"] = hp

            alive = bool(getattr(player, "alive", True))
            if self._last_state.get("player_alive", True) and not alive:
                self.cue("death")
            self._last_state["player_alive"] = alive

            collectible_total = int(getattr(player, "books", 0)) + int(
                getattr(player, "parts", 0)
            )
            previous_collectibles = self._last_state.get("collectibles")
            if previous_collectibles is not None and collectible_total > previous_collectibles:
                self.cue("pickup")
            self._last_state["collectibles"] = collectible_total

            terminals = len(getattr(scene, "terminals_activated", ()))
            previous_terminals = self._last_state.get("terminals")
            if previous_terminals is not None and terminals > previous_terminals:
                self.cue("terminal")
            self._last_state["terminals"] = terminals

            won = bool(getattr(scene, "won", False))
            if won and not self._last_state.get("won", False):
                self.cue("goal")
                self.set_cinematic(True)
            self._last_state["won"] = won

        if camera is not None and self._pending_shake > 0 and hasattr(camera, "add_shake"):
            camera.add_shake(self._pending_shake)
            self._pending_shake = 0.0

    def update(self, dt: float) -> None:
        dt = max(0.0, min(4.0, float(dt)))
        self.flash_alpha = max(0.0, self.flash_alpha - 13.0 * dt)
        self.letterbox += (self.letterbox_target - self.letterbox) * min(1.0, 0.12 * dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.flash_alpha > 0.5:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((*self.flash_color, int(min(255, self.flash_alpha))))
            surface.blit(overlay, (0, 0))

        bar = int(self.letterbox)
        if bar > 0:
            width, height = surface.get_size()
            pygame.draw.rect(surface, (0, 0, 0), (0, 0, width, bar))
            pygame.draw.rect(surface, (0, 0, 0), (0, height - bar, width, bar))
