from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core import gfx


class GlowCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.Surface((32, 32))
        gfx._glow_cache.clear()

    def tearDown(self) -> None:
        gfx._glow_cache.clear()
        pygame.quit()

    def test_soft_circle_survives_cache_rollover(self) -> None:
        for index in range(gfx._GLOW_CACHE_LIMIT + 10):
            color = (index % 256, (index * 3) % 256, (index * 7) % 256)
            gfx.soft_circle(self.surface, color, (16, 16), 2, layers=4)

        final_index = gfx._GLOW_CACHE_LIMIT + 9
        final_color = (
            final_index % 256,
            (final_index * 3) % 256,
            (final_index * 7) % 256,
        )
        self.assertIn((2, *final_color, 4), gfx._glow_cache)
        self.assertLessEqual(len(gfx._glow_cache), gfx._GLOW_CACHE_LIMIT)

    def test_additive_glows_share_the_bounded_cache_safely(self) -> None:
        for index in range(gfx._GLOW_CACHE_LIMIT + 10):
            color = ((index * 5) % 256, (index * 11) % 256, (index * 13) % 256)
            gfx.soft_circle_additive(self.surface, color, (16, 16), 2, layers=5)

        self.assertLessEqual(len(gfx._glow_cache), gfx._GLOW_CACHE_LIMIT)


if __name__ == "__main__":
    unittest.main()
