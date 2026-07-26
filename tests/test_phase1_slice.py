from __future__ import annotations

import copy
import unittest

from game.data.levels import LEVELS
from game.data.phase1_slice import MARS_LANDING_SLICE, SLICE_ID, validate_slice_data
from game.entities.mars_sentinel import MarsSentinel
from tools.phase1_slice_replay import run_replay


class Phase1SliceDataTests(unittest.TestCase):
    def test_committed_slice_data_is_valid(self) -> None:
        self.assertEqual(validate_slice_data(), [])
        self.assertEqual(MARS_LANDING_SLICE["slice_id"], SLICE_ID)
        self.assertEqual(len(MARS_LANDING_SLICE["checkpoints"]), 5)
        self.assertEqual(MARS_LANDING_SLICE["resource_gate"]["required_parts"], 3)

    def test_slice_is_not_a_ninth_classic_mode_chapter(self) -> None:
        self.assertEqual(sorted(LEVELS), list(range(1, 9)))
        self.assertNotIn(SLICE_ID, LEVELS)

    def test_invalid_checkpoint_order_fails_validation(self) -> None:
        data = copy.deepcopy(MARS_LANDING_SLICE)
        data["checkpoints"][2]["x"] = 100
        errors = validate_slice_data(data)
        self.assertTrue(any("left to right" in error for error in errors))

    def test_duplicate_sentinel_ids_fail_validation(self) -> None:
        data = copy.deepcopy(MARS_LANDING_SLICE)
        data["sentinels"][1]["id"] = data["sentinels"][0]["id"]
        errors = validate_slice_data(data)
        self.assertTrue(any("unique" in error for error in errors))


class MarsSentinelTests(unittest.TestCase):
    def test_sentinel_only_takes_damage_during_recovery(self) -> None:
        sentinel = MarsSentinel("test", 100, 100, tier=2)
        sentinel.state = "scan"
        sentinel.take_damage(1)
        self.assertEqual(sentinel.hp, sentinel.max_hp)

        sentinel.state = "recover"
        sentinel.take_damage(1)
        self.assertEqual(sentinel.hp, sentinel.max_hp - 1)

    def test_resource_disruption_changes_warden_combat_profile(self) -> None:
        sentinel = MarsSentinel("warden", 100, 100, tier=3)
        original_hp = sentinel.max_hp
        sentinel.configure_encounter(insight_level=2, resource_disrupted=True)
        self.assertEqual(sentinel.insight_level, 2)
        self.assertTrue(sentinel.resource_disrupted)
        self.assertLess(sentinel.max_hp, original_hp)

    def test_invalid_tier_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "tier"):
            MarsSentinel("invalid", 0, 0, tier=4)


class Phase1SliceReplayTests(unittest.TestCase):
    def test_complete_reference_journey_is_deterministic(self) -> None:
        report = run_replay()
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["deterministic"])
        reference = report["reference"]
        self.assertEqual(reference["slice_id"], SLICE_ID)
        self.assertEqual(reference["phase"], "complete")
        self.assertEqual(reference["failures"], 1)
        self.assertEqual(reference["insight"], 1)
        self.assertTrue(reference["resource_gate_open"])
        self.assertEqual(reference["sentinels_alive"], ["survey-1", "survey-2"])
        self.assertTrue(reference["save"]["completed"])
        self.assertEqual(reference["transition"], ["title"])
        self.assertEqual(
            reference["milestones"],
            [
                "cinematic_arrival_completed",
                "movement_mastery_reached",
                "power_cells_collected",
                "failure_advanced_understanding",
                "resource_changed_final_encounter",
                "adaptive_combat_completed",
                "ascent_started",
                "resolved_ending_beat",
            ],
        )


if __name__ == "__main__":
    unittest.main()
