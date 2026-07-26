from __future__ import annotations

import copy
import unittest

from game.core.relay_echo_state import (
    RELAY_ECHO_RUNTIME,
    RelayEchoStateError,
)


class RelayEchoRuntimeStateTests(unittest.TestCase):
    def begin(self) -> dict:
        state, transition = RELAY_ECHO_RUNTIME.begin_attempt(RELAY_ECHO_RUNTIME.default_state())
        self.assertEqual(transition.event, "attempt_prepared")
        self.assertEqual(state["attempts"], 1)
        self.assertTrue(state["active"])
        return state

    def complete_reference_path(self) -> tuple[dict, list[dict]]:
        state = self.begin()
        transitions: list[dict] = []
        sequence = (
            ("reach_noctis_relay", {}),
            ("recover_signal_fragments", {"signal_fragments": 3}),
            ("triangulate_echo_source", {"echo_source": "subsurface_array"}),
            ("breach_relay_core", {"relay_core_open": True}),
            ("align_the_echo", {"echo_alignment": "redirect"}),
            ("extract_before_collapse", {}),
        )
        for objective_id, evidence in sequence:
            state, transition = RELAY_ECHO_RUNTIME.complete_objective(state, objective_id, evidence)
            transitions.append(transition.to_dict())
        return state, transitions

    def test_default_state_is_valid_and_not_active(self) -> None:
        state = RELAY_ECHO_RUNTIME.default_state()
        self.assertEqual(RELAY_ECHO_RUNTIME.normalize_state(state), state)
        self.assertFalse(state["active"])
        self.assertEqual(state["current_objective"], "reach_noctis_relay")
        self.assertEqual(state["checkpoint_history"], [0])

    def test_attempt_is_a_single_transaction(self) -> None:
        state = self.begin()
        self.assertEqual(state["revision"], 1)
        with self.assertRaisesRegex(RelayEchoStateError, "active"):
            RELAY_ECHO_RUNTIME.begin_attempt(state)

    def test_objectives_must_complete_in_contract_order(self) -> None:
        state = self.begin()
        with self.assertRaisesRegex(RelayEchoStateError, "not the current"):
            RELAY_ECHO_RUNTIME.complete_objective(
                state,
                "recover_signal_fragments",
                {"signal_fragments": 3},
            )

    def test_objective_evidence_fails_closed(self) -> None:
        state = self.begin()
        state, _ = RELAY_ECHO_RUNTIME.complete_objective(state, "reach_noctis_relay")
        with self.assertRaisesRegex(RelayEchoStateError, "three fragments"):
            RELAY_ECHO_RUNTIME.complete_objective(
                state,
                "recover_signal_fragments",
                {"signal_fragments": 2},
            )
        with self.assertRaisesRegex(RelayEchoStateError, "unexpected evidence"):
            RELAY_ECHO_RUNTIME.complete_objective(
                state,
                "recover_signal_fragments",
                {"signal_fragments": 3, "invented": True},
            )

    def test_failure_is_retained_after_objective_eventually_completes(self) -> None:
        state = self.begin()
        state, _ = RELAY_ECHO_RUNTIME.complete_objective(state, "reach_noctis_relay")
        state, failure = RELAY_ECHO_RUNTIME.record_failure(state, "fragment_chain_broken")
        self.assertEqual(failure.event, "failure_recorded")
        self.assertEqual(failure.recovery, "objective_restart")
        self.assertEqual(state["telemetry_insight"], 1)
        state, _ = RELAY_ECHO_RUNTIME.complete_objective(
            state,
            "recover_signal_fragments",
            {"signal_fragments": 3},
        )
        normalized = RELAY_ECHO_RUNTIME.normalize_state(state)
        self.assertEqual(normalized["failures"], 1)
        self.assertEqual(
            normalized["failure_history"][0]["objective_id"],
            "recover_signal_fragments",
        )
        self.assertEqual(normalized["checkpoint_id"], 2)

    def test_failure_must_be_authorized_for_current_objective(self) -> None:
        state = self.begin()
        with self.assertRaisesRegex(RelayEchoStateError, "not valid"):
            RELAY_ECHO_RUNTIME.record_failure(state, "relay_overload")

    def test_complete_path_emits_exit_event_but_not_campaign_completion(self) -> None:
        state, transitions = self.complete_reference_path()
        self.assertTrue(state["completion_eligible"])
        self.assertFalse(state["active"])
        self.assertIsNone(state["current_objective"])
        self.assertEqual(state["current_state"], "complete")
        self.assertEqual(state["checkpoint_history"], list(range(7)))
        self.assertEqual(transitions[-1]["event"], "relay_echo_completed")
        self.assertNotIn("campaign", state)
        with self.assertRaisesRegex(RelayEchoStateError, "cannot begin"):
            RELAY_ECHO_RUNTIME.begin_attempt(state)

    def test_revision_is_fully_derived(self) -> None:
        state = self.begin()
        state, _ = RELAY_ECHO_RUNTIME.record_failure(state, "player_down")
        state, _ = RELAY_ECHO_RUNTIME.complete_objective(state, "reach_noctis_relay")
        self.assertEqual(state["revision"], 3)
        corrupt = copy.deepcopy(state)
        corrupt["revision"] += 1
        with self.assertRaisesRegex(RelayEchoStateError, "revision must equal"):
            RELAY_ECHO_RUNTIME.normalize_state(corrupt)

    def test_forged_checkpoint_and_completion_are_rejected(self) -> None:
        state = self.begin()
        corrupt = copy.deepcopy(state)
        corrupt["checkpoint_id"] = 6
        corrupt["completion_eligible"] = True
        with self.assertRaisesRegex(RelayEchoStateError, "checkpoint_id"):
            RELAY_ECHO_RUNTIME.normalize_state(corrupt)

    def test_committed_evidence_cannot_appear_before_its_objective(self) -> None:
        state = self.begin()
        corrupt = copy.deepcopy(state)
        corrupt["echo_alignment"] = "redirect"
        with self.assertRaisesRegex(RelayEchoStateError, "only after objective commit"):
            RELAY_ECHO_RUNTIME.normalize_state(corrupt)


if __name__ == "__main__":
    unittest.main()
