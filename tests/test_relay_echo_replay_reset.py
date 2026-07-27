from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from game.core.relay_echo_promotion import (
    complete_relay_echo_campaign,
    prepare_relay_echo_launch,
)
from game.core.relay_echo_replay import (
    RelayEchoReplayError,
    complete_relay_echo_replay,
    default_relay_echo_replay,
    normalize_relay_echo_replay,
    prepare_relay_echo_replay,
)
from game.core.relay_echo_save import RelayEchoSaveData

_OBJECTIVES_BEFORE_EXTRACTION = (
    ("reach_noctis_relay", {}),
    ("recover_signal_fragments", {"signal_fragments": 3}),
    ("triangulate_echo_source", {"echo_source": "subsurface_array"}),
    ("breach_relay_core", {"relay_core_open": True}),
    ("align_the_echo", {"echo_alignment": "redirect"}),
)


class RelayEchoReplayResetTests(unittest.TestCase):
    def make_completed_save(self) -> RelayEchoSaveData:
        save = RelayEchoSaveData()
        save.update_phase1_slice(
            checkpoint_id=4,
            best_phase="complete",
            completed=True,
            resource_gate_open=True,
        )
        prepare_relay_echo_launch(save)
        for objective_id, evidence in _OBJECTIVES_BEFORE_EXTRACTION:
            save.complete_relay_echo_objective(objective_id, evidence)
        complete_relay_echo_campaign(save)
        return save

    @staticmethod
    def complete_replay(save: RelayEchoSaveData) -> dict:
        for objective_id, evidence in _OBJECTIVES_BEFORE_EXTRACTION:
            save.complete_relay_echo_objective(objective_id, evidence)
        return complete_relay_echo_replay(save)

    def test_default_archive_is_valid(self) -> None:
        archive = default_relay_echo_replay()
        self.assertEqual(normalize_relay_echo_replay(archive), archive)
        self.assertEqual(archive["current_run_id"], 1)
        self.assertEqual(archive["completed_runs"], [])

    def test_replay_archives_first_run_and_preserves_campaign(self) -> None:
        save = self.make_completed_save()
        campaign_before = copy.deepcopy(save.campaign)
        first_run = copy.deepcopy(save.relay_echo)

        transition = prepare_relay_echo_replay(save)

        self.assertEqual(transition["event"], "relay_echo_replay_prepared")
        self.assertEqual(transition["archived_run"]["run_id"], 1)
        self.assertEqual(transition["current_run_id"], 2)
        self.assertEqual(save.relay_echo_replay["current_run_id"], 2)
        self.assertEqual(len(save.relay_echo_replay["completed_runs"]), 1)
        self.assertEqual(
            save.relay_echo_replay["completed_runs"][0]["revision"],
            first_run["revision"],
        )
        self.assertEqual(
            save.campaign["completed_missions"],
            campaign_before["completed_missions"],
        )
        self.assertEqual(
            save.campaign["unlocked_missions"],
            campaign_before["unlocked_missions"],
        )
        self.assertEqual(save.campaign["current_mission"], "relay_echo")
        self.assertEqual(save.relay_echo["checkpoint_id"], 0)
        self.assertEqual(save.relay_echo["attempts"], 1)
        self.assertTrue(save.relay_echo["active"])

    def test_replay_completion_preserves_campaign_history_and_phobos_unlock(self) -> None:
        save = self.make_completed_save()
        prepare_relay_echo_replay(save)
        transition = self.complete_replay(save)

        self.assertEqual(transition["event"], "relay_echo_replay_completed")
        self.assertEqual(transition["run_id"], 2)
        self.assertEqual(
            save.campaign["completed_missions"],
            ["ares_reach", "relay_echo"],
        )
        self.assertIn("phobos_vector", save.campaign["unlocked_missions"])
        self.assertEqual(save.campaign["current_mission"], "phobos_vector")
        self.assertTrue(save.relay_echo["completion_eligible"])
        self.assertEqual(len(save.relay_echo_replay["completed_runs"]), 1)

    def test_second_replay_archives_second_completed_run_sequentially(self) -> None:
        save = self.make_completed_save()
        prepare_relay_echo_replay(save)
        self.complete_replay(save)
        prepare_relay_echo_replay(save)

        archive = save.relay_echo_replay
        self.assertEqual(archive["current_run_id"], 3)
        self.assertEqual(
            [entry["run_id"] for entry in archive["completed_runs"]],
            [1, 2],
        )
        self.assertEqual(
            save.campaign["completed_missions"],
            ["ares_reach", "relay_echo"],
        )
        self.assertIn("phobos_vector", save.campaign["unlocked_missions"])

    def test_replay_requires_completed_campaign_and_current_run(self) -> None:
        save = RelayEchoSaveData()
        with self.assertRaisesRegex(RelayEchoReplayError, "campaign completion"):
            prepare_relay_echo_replay(save)

        save = self.make_completed_save()
        prepare_relay_echo_replay(save)
        with self.assertRaisesRegex(RelayEchoReplayError, "completed current run"):
            prepare_relay_echo_replay(save)

    def test_corrupt_archive_ids_fail_closed(self) -> None:
        save = self.make_completed_save()
        prepare_relay_echo_replay(save)
        corrupt = copy.deepcopy(save.relay_echo_replay)
        corrupt["completed_runs"][0]["run_id"] = 2
        with self.assertRaisesRegex(RelayEchoReplayError, "contiguous"):
            normalize_relay_echo_replay(corrupt)

    def test_legacy_save_migrates_archive_and_round_trips_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            legacy = RelayEchoSaveData(path)
            payload = legacy.to_dict()
            payload.pop("relay_echo_replay", None)
            path.write_text(json.dumps(payload), encoding="utf-8")

            loaded = RelayEchoSaveData(path)
            self.assertTrue(loaded.load())
            self.assertEqual(loaded.relay_echo_replay, default_relay_echo_replay())

            completed = self.make_completed_save()
            completed.path = path
            completed.store = loaded.store
            prepare_relay_echo_replay(completed)
            self.assertTrue(completed.save())

            round_trip = RelayEchoSaveData(path)
            self.assertTrue(round_trip.load())
            self.assertEqual(
                round_trip.relay_echo_replay,
                completed.relay_echo_replay,
            )


if __name__ == "__main__":
    unittest.main()
