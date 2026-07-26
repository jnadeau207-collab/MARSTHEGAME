from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from game.core.relay_echo_state import RELAY_ECHO_RUNTIME
from game.core.save import SaveData


class RelayEchoSaveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "savegame.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_save(self) -> SaveData:
        return SaveData(self.path)

    @staticmethod
    def unlock_relay(save: SaveData) -> None:
        save.update_phase1_slice(
            checkpoint_id=4,
            best_phase="complete",
            completed=True,
            resource_gate_open=True,
        )

    @staticmethod
    def complete_runtime_path(save: SaveData) -> None:
        sequence = (
            ("reach_noctis_relay", {}),
            ("recover_signal_fragments", {"signal_fragments": 3}),
            ("triangulate_echo_source", {"echo_source": "subsurface_array"}),
            ("breach_relay_core", {"relay_core_open": True}),
            ("align_the_echo", {"echo_alignment": "redirect"}),
            ("extract_before_collapse", {}),
        )
        for objective_id, evidence in sequence:
            save.complete_relay_echo_objective(objective_id, evidence)

    def test_legacy_payload_without_relay_state_migrates_to_default(self) -> None:
        save = self.make_save()
        legacy = save.to_dict()
        legacy.pop("relay_echo")
        self.path.write_text(json.dumps(legacy), encoding="utf-8")

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.relay_echo, RELAY_ECHO_RUNTIME.default_state())
        self.assertTrue(loaded.save())
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(
            envelope["payload"]["relay_echo"],
            RELAY_ECHO_RUNTIME.default_state(),
        )

    def test_attempt_preparation_requires_campaign_prerequisite(self) -> None:
        save = self.make_save()
        with self.assertRaisesRegex(ValueError, "Ares Reach"):
            save.prepare_relay_echo_attempt()
        self.unlock_relay(save)
        transition = save.prepare_relay_echo_attempt()
        self.assertEqual(transition["event"], "attempt_prepared")
        self.assertEqual(save.relay_echo["attempts"], 1)

    def test_progress_and_failure_round_trip_transactionally(self) -> None:
        save = self.make_save()
        self.unlock_relay(save)
        save.prepare_relay_echo_attempt()
        save.complete_relay_echo_objective("reach_noctis_relay")
        failure = save.record_relay_echo_failure("fragment_chain_broken")
        self.assertEqual(failure["recovery"], "objective_restart")
        save.complete_relay_echo_objective(
            "recover_signal_fragments",
            {"signal_fragments": 3},
        )
        self.assertTrue(save.save())

        loaded = self.make_save()
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.relay_echo, save.relay_echo)
        self.assertEqual(loaded.relay_echo["telemetry_insight"], 1)
        self.assertEqual(loaded.relay_echo["checkpoint_id"], 2)

    def test_corrupt_relay_state_does_not_mutate_existing_values(self) -> None:
        save = self.make_save()
        original = save.to_dict()
        corrupt = copy.deepcopy(original)
        corrupt["relay_echo"]["checkpoint_id"] = 6
        with self.assertRaisesRegex(ValueError, "Relay Echo state"):
            save.from_dict(corrupt)
        self.assertEqual(save.to_dict(), original)

    def test_runtime_progress_without_campaign_unlock_is_rejected(self) -> None:
        save = self.make_save()
        state, _ = RELAY_ECHO_RUNTIME.begin_attempt(save.relay_echo)
        corrupt = save.to_dict()
        corrupt["relay_echo"] = state
        with self.assertRaisesRegex(ValueError, "requires completed Ares Reach"):
            save.from_dict(corrupt)

    def test_runtime_completion_does_not_mutate_campaign_automatically(self) -> None:
        save = self.make_save()
        self.unlock_relay(save)
        save.prepare_relay_echo_attempt()
        self.complete_runtime_path(save)
        self.assertTrue(save.relay_echo["completion_eligible"])
        self.assertNotIn("relay_echo", save.campaign["completed_missions"])
        self.assertNotIn("phobos_vector", save.campaign["unlocked_missions"])

        transition = save.complete_campaign_mission("relay_echo")
        self.assertEqual(transition["event"], "mission_completed")
        self.assertIn("relay_echo", save.campaign["completed_missions"])
        self.assertIn("phobos_vector", save.campaign["unlocked_missions"])

    def test_reset_restores_relay_runtime_default(self) -> None:
        save = self.make_save()
        self.unlock_relay(save)
        save.prepare_relay_echo_attempt()
        save.reset()
        self.assertEqual(save.relay_echo, RELAY_ECHO_RUNTIME.default_state())


if __name__ == "__main__":
    unittest.main()
