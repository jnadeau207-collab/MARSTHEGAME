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
        self.bounds = None
        self.lookahead_x = 0.0
        self.lookahead_y = 0.0
        self._previous_x: float | None = None
        self._previous_y: float | None = None
        self._rng = random.Random(seed)
        self._accessibility = normalize_accessibility(None)
        self._motion_enabled = True
        self._shake_scale = 1.0

    def configure_accessibility(self, value: dict[str, Any] | None) -> None:
        self._accessibility = normalize_accessibility(value)
        self._motion_enabled = not self._accessibility["reduced_motion"]
        self._shake_scale = self._accessibility["screen_shake"]
        if not self._motion_enabled:
            self.lookahead_x = 0.0
            self.lookahead_y = 0.0
            self.shake = 0.0
            self.shake_x = 0.0
            self.shake_y = 0.0

    def set_target(self, x, y):
        if self._previous_x is None:
            velocity_x = 0.0
            velocity_y = 0.0
        else:
            velocity_x = x - self._previous_x
            velocity_y = y - self._previous_y
        self._previous_x = x
        self._previous_y = y

        if self._motion_enabled:
            desired_x = velocity_x * 18.0
            if desired_x > 120.0:
                desired_x = 120.0
            elif desired_x < -120.0:
                desired_x = -120.0
            desired_y = velocity_y * 8.0
            if desired_y > 55.0:
                desired_y = 55.0
            elif desired_y < -55.0:
                desired_y = -55.0
            self.lookahead_x += (desired_x - self.lookahead_x) * 0.18
            self.lookahead_y += (desired_y - self.lookahead_y) * 0.12

        self.target_x = x - SCREEN_WIDTH // 2 + self.lookahead_x
        self.target_y = y - SCREEN_HEIGHT // 2 + self.lookahead_y

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.bounds = (
            min_x,
            min_y,
            max(min_x, max_x - SCREEN_WIDTH),
            max(min_y, max_y - SCREEN_HEIGHT),
        )

    def add_shake(self, amount):
        scaled = max(0.0, float(amount)) * self._shake_scale
        if scaled > self.shake:
            self.shake = scaled

    def update(self, dt: float = 1.0):
        if dt == 1.0:
            smoothing = self.lerp
            decay = SHAKE_DECAY
        else:
            dt = max(0.0, min(4.0, float(dt)))
            smoothing = 1.0 - (1.0 - self.lerp) ** dt
            decay = SHAKE_DECAY**dt
        self.x += (self.target_x - self.x) * smoothing
        self.y += (self.target_y - self.y) * smoothing

        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            if self.x < min_x:
                self.x = min_x
            elif self.x > max_x:
                self.x = max_x
            if self.y < min_y:
                self.y = min_y
            elif self.y > max_y:
                self.y = max_y

        if self.shake > 0.5 and self._shake_scale > 0.0:
            self.shake_x = self._rng.uniform(-self.shake, self.shake)
            self.shake_y = self._rng.uniform(-self.shake, self.shake)
            self.shake *= decay
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
