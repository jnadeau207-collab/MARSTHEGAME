from __future__ import annotations

import unittest
from copy import deepcopy

from game.data.content import apply_level_content, build_chapters, build_content, get_text
from game.data.ip_tracks import FICTIONALIZED_TRACK, REAL_WORLD_TRACK
from game.data.levels import LEVELS


class ContentCatalogTests(unittest.TestCase):
    def test_tracks_expose_identical_stable_keys(self) -> None:
        real_world = build_content(REAL_WORLD_TRACK)
        fictionalized = build_content(FICTIONALIZED_TRACK)

        self.assertEqual(set(real_world), set(fictionalized))
        self.assertGreater(len(real_world), 50)

    def test_fictionalized_catalog_removes_protected_identity_names(self) -> None:
        rendered = repr(build_content(FICTIONALIZED_TRACK))

        for protected_name in ("Elon", "Tesla", "SpaceX", "PayPal", "Zip2", "Starship"):
            self.assertNotIn(protected_name, rendered)

    def test_chapter_manifests_keep_ids_and_change_only_copy(self) -> None:
        real_world = build_chapters(REAL_WORLD_TRACK)
        fictionalized = build_chapters(FICTIONALIZED_TRACK)

        self.assertEqual([chapter["id"] for chapter in real_world], list(range(1, 9)))
        self.assertEqual([chapter["id"] for chapter in fictionalized], list(range(1, 9)))
        self.assertEqual(
            [chapter["palette"] for chapter in real_world],
            [chapter["palette"] for chapter in fictionalized],
        )
        self.assertNotEqual(real_world[0]["title"], fictionalized[0]["title"])

    def test_level_content_resolution_preserves_gameplay_data(self) -> None:
        real_world = deepcopy(LEVELS)
        fictionalized = deepcopy(LEVELS)

        apply_level_content(real_world, REAL_WORLD_TRACK)
        apply_level_content(fictionalized, FICTIONALIZED_TRACK)

        for chapter_id in range(1, 9):
            with self.subTest(chapter_id=chapter_id):
                real_level = real_world[chapter_id]
                fictional_level = fictionalized[chapter_id]
                for key in (
                    "width",
                    "height",
                    "player_start",
                    "goal",
                    "sky",
                    "ground_col",
                    "solids",
                    "enemies",
                    "collectibles",
                ):
                    self.assertEqual(real_level.get(key), fictional_level.get(key))
                self.assertEqual(
                    set(real_level["content_keys"]),
                    {"name", "objective", "narration"},
                )

    def test_unknown_content_key_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown content key"):
            get_text("chapter.99.title", REAL_WORLD_TRACK)


if __name__ == "__main__":
    unittest.main()
