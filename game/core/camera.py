"""
Smooth camera with screen shake.
"""

import random
import pygame
from game.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, SHAKE_DECAY


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.shake = 0.0
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.lerp = 0.12
        self.bounds = None  # (min_x, min_y, max_x, max_y)

    def set_target(self, x, y):
        self.target_x = x - SCREEN_WIDTH // 2
        self.target_y = y - SCREEN_HEIGHT // 2

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.bounds = (min_x, min_y, max_x - SCREEN_WIDTH, max_y - SCREEN_HEIGHT)

    def add_shake(self, amount):
        self.shake = max(self.shake, amount)

    def update(self):
        self.x += (self.target_x - self.x) * self.lerp
        self.y += (self.target_y - self.y) * self.lerp

        if self.bounds:
            self.x = max(self.bounds[0], min(self.bounds[2], self.x))
            self.y = max(self.bounds[1], min(self.bounds[3], self.y))

        if self.shake > 0.5:
            self.shake_x = random.uniform(-self.shake, self.shake)
            self.shake_y = random.uniform(-self.shake, self.shake)
            self.shake *= SHAKE_DECAY
        else:
            self.shake = 0
            self.shake_x = 0
            self.shake_y = 0

    @property
    def offset(self):
        return self.x + self.shake_x, self.y + self.shake_y

    def apply(self, rect):
        ox, oy = self.offset
        return rect.move(-ox, -oy)

    def world_to_screen(self, wx, wy):
        ox, oy = self.offset
        return wx - ox, wy - oy
