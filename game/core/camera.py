"""Deterministic cinematic camera with accessibility-aware motion."""

from __future__ import annotations

import random
from typing import Any

from game.core.accessibility import normalize_accessibility
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH, SHAKE_DECAY


class Camera:
    def __init__(self, seed: int = 0):
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.shake = 0.0
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.lerp = 0.12
        self.bounds = None  # (min_x, min_y, max_x, max_y)
        self.lookahead_x = 0.0
        self.lookahead_y = 0.0
        self._previous_focus: tuple[float, float] | None = None
        self._rng = random.Random(seed)
        self._accessibility = normalize_accessibility(None)

    def configure_accessibility(self, value: dict[str, Any] | None) -> None:
        self._accessibility = normalize_accessibility(value)
        if self._accessibility["reduced_motion"]:
            self.shake = 0.0
            self.shake_x = 0.0
            self.shake_y = 0.0

    def set_target(self, x, y):
        focus = (float(x), float(y))
        if self._previous_focus is None:
            velocity_x = 0.0
            velocity_y = 0.0
        else:
            velocity_x = focus[0] - self._previous_focus[0]
            velocity_y = focus[1] - self._previous_focus[1]
        self._previous_focus = focus

        motion_scale = 0.0 if self._accessibility["reduced_motion"] else 1.0
        desired_lookahead_x = max(-120.0, min(120.0, velocity_x * 18.0)) * motion_scale
        desired_lookahead_y = max(-55.0, min(55.0, velocity_y * 8.0)) * motion_scale
        self.lookahead_x += (desired_lookahead_x - self.lookahead_x) * 0.18
        self.lookahead_y += (desired_lookahead_y - self.lookahead_y) * 0.12

        self.target_x = focus[0] - SCREEN_WIDTH // 2 + self.lookahead_x
        self.target_y = focus[1] - SCREEN_HEIGHT // 2 + self.lookahead_y

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.bounds = (
            min_x,
            min_y,
            max(min_x, max_x - SCREEN_WIDTH),
            max(min_y, max_y - SCREEN_HEIGHT),
        )

    def add_shake(self, amount):
        scaled = max(0.0, float(amount)) * self._accessibility["screen_shake"]
        self.shake = max(self.shake, scaled)

    def update(self, dt: float = 1.0):
        dt = max(0.0, min(4.0, float(dt)))
        smoothing = 1.0 - (1.0 - self.lerp) ** dt
        self.x += (self.target_x - self.x) * smoothing
        self.y += (self.target_y - self.y) * smoothing

        if self.bounds:
            self.x = max(self.bounds[0], min(self.bounds[2], self.x))
            self.y = max(self.bounds[1], min(self.bounds[3], self.y))

        if self.shake > 0.5 and self._accessibility["screen_shake"] > 0:
            self.shake_x = self._rng.uniform(-self.shake, self.shake)
            self.shake_y = self._rng.uniform(-self.shake, self.shake)
            self.shake *= SHAKE_DECAY**dt
        else:
            self.shake = 0.0
            self.shake_x = 0.0
            self.shake_y = 0.0

    @property
    def offset(self):
        return self.x + self.shake_x, self.y + self.shake_y

    def apply(self, rect):
        ox, oy = self.offset
        return rect.move(-ox, -oy)

    def world_to_screen(self, wx, wy):
        ox, oy = self.offset
        return wx - ox, wy - oy
