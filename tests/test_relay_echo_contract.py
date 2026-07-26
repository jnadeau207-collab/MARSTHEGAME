from __future__ import annotations

import copy
import unittest

from game.core.campaign import CAMPAIGN_GRAPH
from game.data.campaign import MISSION_STATUS_IMPLEMENTED
from game.data.relay_echo import (
    RELAY_ECHO_CONTRACT,
    RELAY_ECHO_LIFECYCLE,
    RELAY_ECHO_MISSION_ID,
    relay_echo_contract,
    validate_relay_echo_contract,
)


class RelayEchoContractTests(unittest.TestCase):
    def test_committed_contract_is_valid_and_isolated(self) -> None:
        self.assertEqual(validate_relay_echo_contract(), [])
        copied = relay_echo_contract()
        copied["objectives"][0]["state"] = "corrupt"
        self.assertEqual(RELAY_ECHO_CONTRACT["objectives"][0]["state"], "insertion")

    def test_campaign_catalog_references_implemented_contract(self) -> None:
        mission = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
        self.assertEqual(mission["status"], MISSION_STATUS_IMPLEMENTED)
        self.assertEqual(mission["entrypoint"], "relay_echo")
        self.assertEqual(mission["contract"], RELAY_ECHO_MISSION_ID)
        self.assertIn(
            RELAY_ECHO_MISSION_ID,
            CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
        )

    def test_lifecycle_must_match_promoted_content(self) -> None:
        data = relay_echo_contract()
        data["lifecycle"] = "contracted_not_playable"
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("lifecycle" in error for error in errors))
        self.assertEqual(RELAY_ECHO_LIFECYCLE, "implemented_playable")

    def test_duplicate_objective_ids_fail_closed(self) -> None:
        data = relay_echo_contract()
        data["objectives"][1]["id"] = data["objectives"][0]["id"]
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("objective ids must be unique" in error for error in errors))

    def test_forward_objective_dependency_fails_closed(self) -> None:
        data = relay_echo_contract()
        data["objectives"][0]["dependencies"] = ("recover_signal_fragments",)
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("must precede" in error for error in errors))

    def test_checkpoint_must_commit_its_objective(self) -> None:
        data = relay_echo_contract()
        data["checkpoints"][2]["objective_id"] = "triangulate_echo_source"
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("does not commit its objective" in error for error in errors))

    def test_accessibility_contract_cannot_be_reduced(self) -> None:
        data = relay_echo_contract()
        data["accessibility_requirements"] = tuple(
            item for item in data["accessibility_requirements"] if item != "reduced_motion"
        )
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("missing accessibility" in error for error in errors))

    def test_replay_must_cover_contract_objectives_and_checkpoints(self) -> None:
        data = relay_echo_contract()
        data["deterministic_replay"]["required_objectives"] = ("reach_noctis_relay",)
        data["deterministic_replay"]["required_checkpoints"] = (0, 1)
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("replay objective order" in error for error in errors))
        self.assertTrue(any("replay checkpoints" in error for error in errors))

    def test_frame_budgets_must_fit_target_simulation_step(self) -> None:
        data = relay_echo_contract()
        data["performance_budgets"]["update_p95_ms"] = 10.0
        data["performance_budgets"]["draw_p95_ms"] = 10.0
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("fit inside" in error for error in errors))

    def test_content_requirements_cannot_be_misrepresented_as_complete(self) -> None:
        data = relay_echo_contract()
        data["content_package_requirements"]["audio"] = "complete"
        errors = validate_relay_echo_contract(data)
        self.assertTrue(any("represented as complete" in error for error in errors))

    def test_contract_copy_is_deep(self) -> None:
        first = relay_echo_contract()
        second = copy.deepcopy(first)
        second["failure_states"]["player_down"]["insight_delta"] = 99
        self.assertEqual(first["failure_states"]["player_down"]["insight_delta"], 1)


if __name__ == "__main__":
    unittest.main()
