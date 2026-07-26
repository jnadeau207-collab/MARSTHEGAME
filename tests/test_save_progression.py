from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import game.core.save as save_module
from game.core.save import SaveData


class SaveProgressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_path = save_module.SAVE_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        save_module.SAVE_PATH = Path(self.temp_dir.name) / "savegame.json"

    def tearDown(self) -> None:
        save_module.SAVE_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_completion_is_monotonic(self) -> None:
        save = SaveData()
        save.complete_chapter(4)
        save.complete_chapter(2)
        self.assertEqual(save.chapter_completed, 4)
        self.assertEqual(save.chapter_unlocked, 5)

    def test_round_trip_preserves_progress_and_stats(self) -> None:
        original = SaveData()
        original.complete_chapter(6)
        original.current_chapter = 7
        original.unlocks["dash"] = True
        original.stats["rockets_failed"] = 3
        self.assertTrue(original.save())

        loaded = SaveData()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.to_dict(), original.to_dict())


if __name__ == "__main__":
    unittest.main()
