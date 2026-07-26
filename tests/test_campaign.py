from __future__ import annotations

import copy
import unittest

from game.core.campaign import (
    CAMPAIGN_GRAPH,
    CampaignDefinitionError,
    CampaignGraph,
    CampaignStateError,
    validate_campaign_catalog,
)
from game.data.campaign import CAMPAIGN_MISSIONS, START_MISSION_ID


class CampaignCatalogTests(unittest.TestCase):
    def test_committed_catalog_is_valid_and_stably_ordered(self) -> None:
        self.assertEqual(validate_campaign_catalog(), [])
        self.assertEqual(CAMPAIGN_GRAPH.mission_ids[0], START_MISSION_ID)
        self.assertEqual(CAMPAIGN_GRAPH.mission_ids, tuple(CAMPAIGN_GRAPH.mission_ids))

    def test_missing_reference_fails_closed(self) -> None:
        missions = copy.deepcopy(list(CAMPAIGN_MISSIONS))
        missions[1]["prerequisites"] = ("missing_mission",)
        errors = validate_campaign_catalog(missions)
        self.assertTrue(any("missing prerequisite" in error for error in errors))
        with self.assertRaises(CampaignDefinitionError):
            CampaignGraph(missions)

    def test_cycle_fails_closed(self) -> None:
        missions = copy.deepcopy(list(CAMPAIGN_MISSIONS))
        missions[0]["prerequisites"] = ("relay_echo",)
        errors = validate_campaign_catalog(missions)
        self.assertTrue(any("cycle" in error for error in errors))

    def test_planned_mission_cannot_claim_entrypoint(self) -> None:
        missions = copy.deepcopy(list(CAMPAIGN_MISSIONS))
        missions[1]["entrypoint"] = "pretend_scene"
        errors = validate_campaign_catalog(missions)
        self.assertTrue(any("may not claim" in error for error in errors))


class CampaignProgressionTests(unittest.TestCase):
    def test_default_state_only_exposes_implemented_start_as_playable(self) -> None:
        state = CAMPAIGN_GRAPH.default_state()
        self.assertEqual(state["unlocked_missions"], ["ares_reach"])
        self.assertEqual(CAMPAIGN_GRAPH.playable_mission_ids([]), ("ares_reach",))

    def test_attempt_and_completion_emit_deterministic_transitions(self) -> None:
        state = CAMPAIGN_GRAPH.default_state()
        attempted, attempt = CAMPAIGN_GRAPH.record_attempt(state, "ares_reach")
        self.assertEqual(attempt.event, "attempt_started")
        self.assertEqual(attempted["attempts"], {"ares_reach": 1})
        self.assertEqual(attempted["revision"], 1)

        completed, transition = CAMPAIGN_GRAPH.complete_mission(attempted, "ares_reach")
        self.assertEqual(transition.event, "mission_completed")
        self.assertEqual(completed["completed_missions"], ["ares_reach"])
        self.assertEqual(completed["unlocked_missions"], ["ares_reach", "relay_echo"])
        self.assertEqual(completed["current_mission"], "relay_echo")
        self.assertEqual(completed["revision"], 2)
        self.assertEqual(CAMPAIGN_GRAPH.playable_mission_ids(completed["completed_missions"]), ("ares_reach",))

    def test_forged_unlocks_are_rejected(self) -> None:
        state = CAMPAIGN_GRAPH.default_state()
        state["unlocked_missions"].append("frontier_burn")
        with self.assertRaisesRegex(CampaignStateError, "unlocked_missions"):
            CAMPAIGN_GRAPH.normalize_state(state)

    def test_impossible_completion_is_rejected(self) -> None:
        state = CAMPAIGN_GRAPH.default_state()
        state["completed_missions"] = ["relay_echo"]
        state["unlocked_missions"] = ["ares_reach"]
        with self.assertRaisesRegex(CampaignStateError, "missing prerequisites"):
            CAMPAIGN_GRAPH.normalize_state(state)

    def test_planned_mission_cannot_start(self) -> None:
        state = CAMPAIGN_GRAPH.default_state()
        attempted, _transition = CAMPAIGN_GRAPH.record_attempt(state, "ares_reach")
        completed, _transition = CAMPAIGN_GRAPH.complete_mission(attempted, "ares_reach")
        with self.assertRaisesRegex(CampaignStateError, "not currently playable"):
            CAMPAIGN_GRAPH.record_attempt(completed, "relay_echo")


if __name__ == "__main__":
    unittest.main()
