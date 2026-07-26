from __future__ import annotations

import unittest

from game.core.settings import CHAPTERS
from game.data.levels import LEVELS


class ClassicModeContractTests(unittest.TestCase):
    def test_exact_eight_chapter_sequence_is_preserved(self) -> None:
        expected = list(range(1, 9))
        self.assertEqual(sorted(LEVELS), expected)
        self.assertEqual([chapter["id"] for chapter in CHAPTERS], expected)

    def test_level_data_has_required_shape(self) -> None:
        required = {
            "name",
            "width",
            "height",
            "player_start",
            "goal",
            "sky",
            "ground_col",
            "solids",
            "objective",
        }
        for chapter_id, level in LEVELS.items():
            with self.subTest(chapter_id=chapter_id):
                self.assertFalse(required.difference(level))
                self.assertGreater(level["width"], 0)
                self.assertGreater(level["height"], 0)
                self.assertTrue(level["solids"])
                self.assertTrue(level["objective"].strip())

    def test_spawns_and_goals_are_inside_each_world(self) -> None:
        for chapter_id, level in LEVELS.items():
            with self.subTest(chapter_id=chapter_id):
                width, height = level["width"], level["height"]
                for label in ("player_start", "goal"):
                    x, y = level[label]
                    self.assertGreaterEqual(x, 0)
                    self.assertLess(x, width)
                    self.assertGreaterEqual(y, 0)
                    self.assertLess(y, height)

    def test_collision_geometry_has_positive_area(self) -> None:
        for chapter_id, level in LEVELS.items():
            for index, solid in enumerate(level["solids"]):
                with self.subTest(chapter_id=chapter_id, solid=index):
                    self.assertEqual(len(solid), 4)
                    self.assertGreater(solid[2], 0)
                    self.assertGreater(solid[3], 0)


if __name__ == "__main__":
    unittest.main()
