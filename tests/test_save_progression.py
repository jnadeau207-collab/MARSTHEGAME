from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from game.core.save import SaveData


class SaveProgressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "savegame.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_save(self) -> SaveData:
        return SaveData(self.path)

    def test_completion_is_monotonic(self) -> None:
        save = self.make_save()
        save.complete_chapter(4)
        save.complete_chapter(2)
        self.assertEqual(save.chapter_completed, 4)
        self.assertEqual(save.chapter_unlocked, 5)

    def test_round_trip_preserves_progress_stats_and_generation(self) -> None:
        original = self.make_save()
        original.complete_chapter(6)
        original.current_chapter = 7
        original.unlocks["dash"] = True
        original.stats["rockets_failed"] = 3
        self.assertTrue(original.save())
        self.assertEqual(original.generation, 1)

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.to_dict(), original.to_dict())
        self.assertEqual(loaded.generation, 1)
        self.assertEqual(loaded.last_load_source, "primary")
        self.assertFalse(loaded.repaired_primary)

    def test_corrupt_primary_recovers_previous_generation_from_backup(self) -> None:
        save = self.make_save()
        save.complete_chapter(2)
        self.assertTrue(save.save())
        first_state = save.to_dict()
        save.complete_chapter(4)
        self.assertTrue(save.save())

        self.path.write_text("{not-json", encoding="utf-8")
        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.to_dict(), first_state)
        self.assertEqual(loaded.last_load_source, "backup")
        self.assertTrue(loaded.repaired_primary)

        verified = self.make_save()
        self.assertTrue(verified.load())
        self.assertEqual(verified.to_dict(), first_state)
        self.assertEqual(verified.last_load_source, "primary")

    def test_checksum_tampering_falls_back_to_backup(self) -> None:
        save = self.make_save()
        self.assertTrue(save.save())
        save.complete_chapter(3)
        self.assertTrue(save.save())

        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        envelope["payload"]["chapter_completed"] = 8
        self.path.write_text(json.dumps(envelope), encoding="utf-8")

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.chapter_completed, 0)
        self.assertEqual(loaded.last_load_source, "backup")

    def test_semantically_invalid_primary_falls_back_to_valid_backup(self) -> None:
        save = self.make_save()
        save.complete_chapter(2)
        self.assertTrue(save.save())
        save.complete_chapter(3)
        self.assertTrue(save.save())
        valid_state = save.to_dict()

        invalid = dict(valid_state)
        invalid["current_chapter"] = 8
        invalid["chapter_unlocked"] = 2
        save.store.save(invalid, save.generation + 1)

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.to_dict(), valid_state)
        self.assertEqual(loaded.last_load_source, "backup")
        self.assertTrue(loaded.repaired_primary)

    def test_legacy_flat_json_loads_and_migrates_on_next_save(self) -> None:
        legacy = self.make_save()
        legacy.complete_chapter(5)
        legacy.current_chapter = 6
        self.path.write_text(json.dumps(legacy.to_dict()), encoding="utf-8")

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.last_load_source, "legacy")
        self.assertEqual(loaded.generation, 0)
        self.assertTrue(loaded.save())

        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(envelope["schema_version"], 1)
        self.assertEqual(envelope["generation"], 1)
        self.assertIn("sha256", envelope)
        self.assertEqual(envelope["payload"], loaded.to_dict())

    def test_interrupted_temporary_file_does_not_replace_primary(self) -> None:
        save = self.make_save()
        save.complete_chapter(3)
        self.assertTrue(save.save())
        save.store.temp_path.write_text("partial", encoding="utf-8")

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.chapter_completed, 3)
        self.assertEqual(loaded.last_load_source, "primary")

    def test_invalid_in_memory_state_does_not_damage_existing_checkpoint(self) -> None:
        save = self.make_save()
        save.complete_chapter(2)
        self.assertTrue(save.save())
        original_bytes = self.path.read_bytes()

        save.stats["deaths"] = object()
        self.assertFalse(save.save())
        self.assertEqual(self.path.read_bytes(), original_bytes)
        self.assertIsNotNone(save.last_error)

    def test_reset_removes_primary_backup_and_temporary_files(self) -> None:
        save = self.make_save()
        self.assertTrue(save.save())
        save.complete_chapter(2)
        self.assertTrue(save.save())
        save.store.temp_path.write_text("partial", encoding="utf-8")

        save.reset()
        self.assertFalse(save.path.exists())
        self.assertFalse(save.store.backup_path.exists())
        self.assertFalse(save.store.temp_path.exists())
        self.assertEqual(save.to_dict(), self.make_save().to_dict())


if __name__ == "__main__":
    unittest.main()
