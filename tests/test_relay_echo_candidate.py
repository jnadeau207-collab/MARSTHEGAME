from __future__ import annotations

import copy
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.campaign import CAMPAIGN_GRAPH
from game.data.relay_echo import RELAY_ECHO_CONTRACT
from game.data.relay_echo_candidate import (
    RELAY_ECHO_CANDIDATE,
    relay_echo_candidate,
    validate_relay_echo_candidate,
)
from tools.relay_echo_replay import ReferenceDriver, run_replay


class RelayEchoCandidateDataTests(unittest.TestCase):
    def test_committed_candidate_is_valid_and_isolated(self) -> None:
        self.assertEqual(validate_relay_echo_candidate(), [])
        copied = relay_echo_candidate()
        copied["checkpoints"][1]["position"] = (9_999, 9_999)
        self.assertEqual(RELAY_ECHO_CANDIDATE["checkpoints"][1]["position"], (860, 780))

    def test_checkpoint_objectives_match_contract_exactly(self) -> None:
        contract_objectives = [item["id"] for item in RELAY_ECHO_CONTRACT["objectives"]]
        candidate_objectives = [
            item["objective_id"] for item in RELAY_ECHO_CANDIDATE["checkpoints"][1:]
        ]
        self.assertEqual(candidate_objectives, contract_objectives)

    def test_candidate_cannot_claim_campaign_promotion(self) -> None:
        data = relay_echo_candidate()
        data["candidate_status"] = "implemented"
        errors = validate_relay_echo_candidate(data)
        self.assertTrue(any("may not claim" in error for error in errors))

    def test_malformed_terminal_fails_without_crashing_validator(self) -> None:
        data = relay_echo_candidate()
        data["interactions"]["triangulation_terminal"] = None
        errors = validate_relay_echo_candidate(data)
        self.assertTrue(any("left to right" in error for error in errors))

    def test_candidate_requires_exactly_three_signal_fragments(self) -> None:
        data = relay_echo_candidate()
        data["collectibles"] = tuple(
            item for item in data["collectibles"] if item[0] != "part"
        )
        errors = validate_relay_echo_candidate(data)
        self.assertTrue(any("exactly three" in error for error in errors))

    def test_campaign_catalog_still_hides_candidate(self) -> None:
        mission = CAMPAIGN_GRAPH.mission("relay_echo")
        self.assertEqual(mission["status"], "planned")
        self.assertIsNone(mission["entrypoint"])
        self.assertNotIn(
            "relay_echo",
            CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
        )


class RelayEchoCandidateReplayTests(unittest.TestCase):
    def test_complete_candidate_reference_path_is_deterministic(self) -> None:
        report = run_replay()
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["deterministic"])
        self.assertTrue(report["candidate_only"])
        self.assertFalse(report["campaign_promoted"])
        reference = report["reference"]
        state = reference["relay_echo"]
        campaign = reference["campaign"]
        self.assertTrue(state["completion_eligible"])
        self.assertEqual(state["checkpoint_history"], list(range(7)))
        self.assertEqual(
            [entry["failure_id"] for entry in state["failure_history"]],
            ["player_down", "relay_overload"],
        )
        self.assertEqual(state["telemetry_insight"], 2)
        self.assertEqual(reference["transition"], ["campaign"])
        self.assertNotIn("relay_echo", campaign["completed_missions"])
        self.assertNotIn("phobos_vector", campaign["unlocked_missions"])

    def test_failure_before_fragment_commit_restores_all_fragments(self) -> None:
        pygame.init()
        try:
            driver = ReferenceDriver()
            driver.force_player_down()
            driver.reach_relay()
            fragment = next(
                collectible
                for collectible in driver.scene.collectibles
                if collectible.kind == "part" and collectible.alive
            )
            driver.place_player(fragment.x, fragment.y)
            driver.step()
            self.assertEqual(driver.scene.player.parts, 1)
            driver.scene.player.invuln = 0
            driver.scene.player.take_damage(99)
            driver.step()
            driver.advance(61)
            alive_fragments = [
                collectible
                for collectible in driver.scene.collectibles
                if collectible.kind == "part" and collectible.alive
            ]
            self.assertEqual(driver.scene.player.parts, 0)
            self.assertEqual(len(alive_fragments), 3)
            self.assertEqual(driver.engine.save.stats["deaths"], 2)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
