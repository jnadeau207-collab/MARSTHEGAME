from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from game.core.campaign import CAMPAIGN_GRAPH
from game.core.save import SaveData


class CampaignSaveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "savegame.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_save(self) -> SaveData:
        return SaveData(self.path)

    def test_legacy_payload_without_campaign_migrates_to_default(self) -> None:
        save = self.make_save()
        legacy = save.to_dict()
        legacy.pop("campaign")
        self.path.write_text(json.dumps(legacy), encoding="utf-8")

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.campaign, CAMPAIGN_GRAPH.default_state())
        self.assertTrue(loaded.save())
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(
            envelope["payload"]["campaign"],
            CAMPAIGN_GRAPH.default_state(),
        )

    def test_completed_phase1_legacy_save_unlocks_campaign_successor(self) -> None:
        save = self.make_save()
        legacy = save.to_dict()
        legacy.pop("campaign")
        legacy["phase1_slice"].update(
            {
                "checkpoint_id": 4,
                "best_phase": "complete",
                "completed": True,
                "resource_gate_open": True,
            }
        )
        self.path.write_text(json.dumps(legacy), encoding="utf-8")

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.campaign["completed_missions"], ["ares_reach"])
        self.assertIn("relay_echo", loaded.campaign["unlocked_missions"])
        self.assertEqual(loaded.campaign["current_mission"], "relay_echo")

    def test_phase1_completion_synchronizes_campaign_transaction(self) -> None:
        save = self.make_save()
        save.update_phase1_slice(
            checkpoint_id=4,
            best_phase="complete",
            completed=True,
            resource_gate_open=True,
        )
        self.assertEqual(save.campaign["completed_missions"], ["ares_reach"])
        self.assertIn("relay_echo", save.campaign["unlocked_missions"])
        self.assertTrue(save.save())

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.campaign, save.campaign)

    def test_attempt_and_completion_round_trip_transactionally(self) -> None:
        save = self.make_save()
        attempt = save.record_campaign_attempt("ares_reach")
        self.assertEqual(attempt["event"], "attempt_started")
        self.assertTrue(save.save())

        completion = save.complete_campaign_mission("ares_reach")
        self.assertEqual(completion["event"], "mission_completed")
        self.assertTrue(save.save())

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.campaign, save.campaign)
        self.assertEqual(loaded.campaign["completed_missions"], ["ares_reach"])
        self.assertIn("relay_echo", loaded.campaign["unlocked_missions"])

    def test_corrupt_campaign_state_does_not_mutate_existing_values(self) -> None:
        save = self.make_save()
        original = save.to_dict()
        corrupt = save.to_dict()
        corrupt["campaign"]["unlocked_missions"] = ["frontier_burn"]
        with self.assertRaisesRegex(ValueError, "campaign state"):
            save.from_dict(corrupt)
        self.assertEqual(save.to_dict(), original)

    def test_reset_restores_campaign_default(self) -> None:
        save = self.make_save()
        save.record_campaign_attempt("ares_reach")
        save.complete_campaign_mission("ares_reach")
        save.reset()
        self.assertEqual(save.campaign, CAMPAIGN_GRAPH.default_state())


if __name__ == "__main__":
    unittest.main()
