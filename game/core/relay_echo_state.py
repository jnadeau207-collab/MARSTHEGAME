"""Transactional Relay Echo objective, checkpoint, and failure state machine."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from game.data.relay_echo import (
    RELAY_ECHO_CONTRACT,
    RELAY_ECHO_MISSION_ID,
    validate_relay_echo_contract,
)

RELAY_ECHO_RUNTIME_SCHEMA_VERSION = 1
_STABLE_VALUE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class RelayEchoStateError(ValueError):
    """Raised when Relay Echo runtime state or a transition is invalid."""


@dataclass(frozen=True)
class RelayEchoTransition:
    """Deterministic evidence emitted by a Relay Echo state transaction."""

    event: str
    revision: int
    attempt: int
    objective_id: str | None
    failure_id: str | None
    checkpoint_id: int
    current_state: str
    current_objective: str | None
    completed_objectives: tuple[str, ...]
    telemetry_insight: int
    completion_eligible: bool
    recovery: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "revision": self.revision,
            "attempt": self.attempt,
            "objective_id": self.objective_id,
            "failure_id": self.failure_id,
            "checkpoint_id": self.checkpoint_id,
            "current_state": self.current_state,
            "current_objective": self.current_objective,
            "completed_objectives": list(self.completed_objectives),
            "telemetry_insight": self.telemetry_insight,
            "completion_eligible": self.completion_eligible,
            "recovery": self.recovery,
        }


class RelayEchoRuntime:
    """Validated state machine generated from the committed mission contract."""

    def __init__(self, contract: Mapping[str, Any] = RELAY_ECHO_CONTRACT) -> None:
        contract_copy = deepcopy(dict(contract))
        errors = validate_relay_echo_contract(contract_copy)
        if errors:
            raise RelayEchoStateError("invalid Relay Echo contract: " + "; ".join(errors))
        self.contract = contract_copy
        self.objectives = tuple(item["id"] for item in contract_copy["objectives"])
        self.objective_by_id = {
            item["id"]: deepcopy(item) for item in contract_copy["objectives"]
        }
        self.failure_states = deepcopy(contract_copy["failure_states"])

    def default_state(self) -> dict[str, Any]:
        return {
            "schema_version": RELAY_ECHO_RUNTIME_SCHEMA_VERSION,
            "mission_id": RELAY_ECHO_MISSION_ID,
            "revision": 0,
            "attempts": 0,
            "active": False,
            "current_state": self.objective_by_id[self.objectives[0]]["state"],
            "current_objective": self.objectives[0],
            "completed_objectives": [],
            "checkpoint_id": 0,
            "checkpoint_history": [0],
            "failures": 0,
            "failure_history": [],
            "telemetry_insight": 0,
            "signal_fragments": 0,
            "echo_source": None,
            "relay_core_open": False,
            "echo_alignment": None,
            "completion_eligible": False,
        }

    @staticmethod
    def _non_negative_int(value: Any, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RelayEchoStateError(f"{field} must be a non-negative integer")
        return value

    @staticmethod
    def _stable_value(value: Any, field: str) -> str:
        if not isinstance(value, str) or not _STABLE_VALUE_PATTERN.fullmatch(value):
            raise RelayEchoStateError(f"{field} must be a stable lowercase identifier")
        return value

    def _derived_position(
        self, completed: tuple[str, ...]
    ) -> tuple[int, str, str | None, bool]:
        checkpoint_id = len(completed)
        completion_eligible = checkpoint_id == len(self.objectives)
        if completion_eligible:
            return checkpoint_id, "complete", None, True
        next_objective = self.objectives[checkpoint_id]
        return (
            checkpoint_id,
            self.objective_by_id[next_objective]["state"],
            next_objective,
            False,
        )

    def normalize_state(self, value: Any) -> dict[str, Any]:
        if value is None:
            return self.default_state()
        if not isinstance(value, dict):
            raise RelayEchoStateError("Relay Echo state must be an object")
        if value.get("schema_version", RELAY_ECHO_RUNTIME_SCHEMA_VERSION) != (
            RELAY_ECHO_RUNTIME_SCHEMA_VERSION
        ):
            raise RelayEchoStateError("Relay Echo state schema version is unsupported")
        if value.get("mission_id", RELAY_ECHO_MISSION_ID) != RELAY_ECHO_MISSION_ID:
            raise RelayEchoStateError("Relay Echo state belongs to another mission")

        revision = self._non_negative_int(value.get("revision", 0), "relay_echo.revision")
        attempts = self._non_negative_int(value.get("attempts", 0), "relay_echo.attempts")
        failures = self._non_negative_int(value.get("failures", 0), "relay_echo.failures")

        completed_value = value.get("completed_objectives", [])
        if not isinstance(completed_value, list) or not all(
            isinstance(item, str) for item in completed_value
        ):
            raise RelayEchoStateError("completed_objectives must be a string list")
        if len(completed_value) != len(set(completed_value)):
            raise RelayEchoStateError("completed_objectives contains duplicates")
        completed = tuple(completed_value)
        if completed != self.objectives[: len(completed)]:
            raise RelayEchoStateError("completed_objectives must be an ordered objective prefix")

        checkpoint_id, current_state, current_objective, completion_eligible = (
            self._derived_position(completed)
        )
        persisted_checkpoint = self._non_negative_int(
            value.get("checkpoint_id", checkpoint_id), "relay_echo.checkpoint_id"
        )
        if persisted_checkpoint != checkpoint_id:
            raise RelayEchoStateError("checkpoint_id does not match completed objectives")
        checkpoint_history = value.get(
            "checkpoint_history", list(range(checkpoint_id + 1))
        )
        if checkpoint_history != list(range(checkpoint_id + 1)):
            raise RelayEchoStateError("checkpoint_history must be contiguous and derived")
        if value.get("current_state", current_state) != current_state:
            raise RelayEchoStateError("current_state does not match objective progress")
        if value.get("current_objective", current_objective) != current_objective:
            raise RelayEchoStateError("current_objective does not match objective progress")
        if value.get("completion_eligible", completion_eligible) is not completion_eligible:
            raise RelayEchoStateError("completion_eligible does not match objective progress")

        failure_history = value.get("failure_history", [])
        if not isinstance(failure_history, list) or not all(
            isinstance(item, dict) for item in failure_history
        ):
            raise RelayEchoStateError("failure_history must be an object list")
        if len(failure_history) != failures:
            raise RelayEchoStateError("failure_history length must equal failures")
        normalized_failures: list[dict[str, Any]] = []
        expected_insight = 0
        last_failure_revision = 0
        for index, item in enumerate(failure_history, start=1):
            if item.get("sequence") != index:
                raise RelayEchoStateError("failure_history sequence must be contiguous")
            failure_id = item.get("failure_id")
            if failure_id not in self.failure_states:
                raise RelayEchoStateError(
                    f"failure_history contains unknown failure {failure_id!r}"
                )
            objective_id = item.get("objective_id")
            if objective_id not in self.objectives:
                raise RelayEchoStateError("failure_history contains an unknown objective")
            objective_index = self.objectives.index(objective_id)
            objective = self.objective_by_id[objective_id]
            if failure_id not in objective["failure_modes"]:
                raise RelayEchoStateError(
                    f"failure {failure_id!r} is not valid for objective {objective_id!r}"
                )
            history_checkpoint = self._non_negative_int(
                item.get("checkpoint_id"), "failure_history.checkpoint_id"
            )
            if history_checkpoint != objective_index:
                raise RelayEchoStateError(
                    "failure_history checkpoint must identify the objective start"
                )
            if history_checkpoint > checkpoint_id:
                raise RelayEchoStateError(
                    "failure_history checkpoint exceeds committed progress"
                )
            history_revision = self._non_negative_int(
                item.get("revision"), "failure_history.revision"
            )
            expected_history_revision = attempts + history_checkpoint + index
            if history_revision != expected_history_revision:
                raise RelayEchoStateError(
                    "failure_history revision does not match transaction order"
                )
            if history_revision > revision:
                raise RelayEchoStateError(
                    "failure_history revision exceeds current revision"
                )
            if history_revision <= last_failure_revision:
                raise RelayEchoStateError("failure_history revisions must increase")
            last_failure_revision = history_revision
            recovery = item.get("recovery")
            if recovery != self.failure_states[failure_id]["recovery"]:
                raise RelayEchoStateError(
                    "failure_history recovery does not match the contract"
                )
            expected_insight += self.failure_states[failure_id]["insight_delta"]
            normalized_failures.append(
                {
                    "sequence": index,
                    "failure_id": failure_id,
                    "objective_id": objective_id,
                    "checkpoint_id": history_checkpoint,
                    "revision": history_revision,
                    "recovery": recovery,
                }
            )

        telemetry_insight = self._non_negative_int(
            value.get("telemetry_insight", expected_insight),
            "relay_echo.telemetry_insight",
        )
        if telemetry_insight != expected_insight:
            raise RelayEchoStateError(
                "telemetry_insight must be derived from failure history"
            )

        signal_fragments = self._non_negative_int(
            value.get("signal_fragments", 0), "relay_echo.signal_fragments"
        )
        echo_source = value.get("echo_source")
        relay_core_open = value.get("relay_core_open", False)
        echo_alignment = value.get("echo_alignment")
        if not isinstance(relay_core_open, bool):
            raise RelayEchoStateError("relay_echo.relay_core_open must be boolean")

        fragments_complete = "recover_signal_fragments" in completed
        source_complete = "triangulate_echo_source" in completed
        breach_complete = "breach_relay_core" in completed
        alignment_complete = "align_the_echo" in completed
        if fragments_complete:
            if signal_fragments < 3:
                raise RelayEchoStateError(
                    "completed signal recovery requires three fragments"
                )
        elif signal_fragments != 0:
            raise RelayEchoStateError(
                "signal fragments may persist only after objective commit"
            )
        if source_complete:
            echo_source = self._stable_value(echo_source, "relay_echo.echo_source")
        elif echo_source is not None:
            raise RelayEchoStateError(
                "echo_source may persist only after objective commit"
            )
        if relay_core_open is not breach_complete:
            raise RelayEchoStateError(
                "relay_core_open must match breach objective completion"
            )
        if alignment_complete:
            echo_alignment = self._stable_value(
                echo_alignment, "relay_echo.echo_alignment"
            )
        elif echo_alignment is not None:
            raise RelayEchoStateError(
                "echo_alignment may persist only after objective commit"
            )

        expected_revision = attempts + len(completed) + failures
        if revision != expected_revision:
            raise RelayEchoStateError(
                "revision must equal attempts plus objective and failure transactions"
            )
        if attempts == 0 and (completed or failures):
            raise RelayEchoStateError("objective or failure progress requires an attempt")
        active = attempts > 0 and not completion_eligible
        if value.get("active", active) is not active:
            raise RelayEchoStateError(
                "active must be derived from attempts and completion"
            )

        return {
            "schema_version": RELAY_ECHO_RUNTIME_SCHEMA_VERSION,
            "mission_id": RELAY_ECHO_MISSION_ID,
            "revision": revision,
            "attempts": attempts,
            "active": active,
            "current_state": current_state,
            "current_objective": current_objective,
            "completed_objectives": list(completed),
            "checkpoint_id": checkpoint_id,
            "checkpoint_history": list(range(checkpoint_id + 1)),
            "failures": failures,
            "failure_history": normalized_failures,
            "telemetry_insight": telemetry_insight,
            "signal_fragments": signal_fragments,
            "echo_source": echo_source,
            "relay_core_open": relay_core_open,
            "echo_alignment": echo_alignment,
            "completion_eligible": completion_eligible,
        }

    def begin_attempt(
        self, state: Any
    ) -> tuple[dict[str, Any], RelayEchoTransition]:
        normalized = self.normalize_state(state)
        if normalized["active"]:
            raise RelayEchoStateError(
                "an active Relay Echo attempt cannot begin again"
            )
        if normalized["completion_eligible"]:
            raise RelayEchoStateError(
                "completed Relay Echo state cannot begin another attempt"
            )
        normalized["attempts"] += 1
        normalized["revision"] += 1
        normalized["active"] = True
        normalized = self.normalize_state(normalized)
        return normalized, self._transition("attempt_prepared", normalized)

    def complete_objective(
        self,
        state: Any,
        objective_id: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], RelayEchoTransition]:
        normalized = self.normalize_state(state)
        if not normalized["active"]:
            raise RelayEchoStateError(
                "Relay Echo objective progress requires an active attempt"
            )
        if objective_id != normalized["current_objective"]:
            raise RelayEchoStateError(
                f"objective {objective_id!r} is not the current Relay Echo objective"
            )
        evidence = dict(evidence or {})
        self._apply_objective_evidence(normalized, objective_id, evidence)
        normalized["completed_objectives"].append(objective_id)
        normalized["revision"] += 1
        checkpoint_id, current_state, current_objective, completion_eligible = (
            self._derived_position(tuple(normalized["completed_objectives"]))
        )
        normalized["checkpoint_id"] = checkpoint_id
        normalized["checkpoint_history"] = list(range(checkpoint_id + 1))
        normalized["current_state"] = current_state
        normalized["current_objective"] = current_objective
        normalized["completion_eligible"] = completion_eligible
        normalized["active"] = not completion_eligible
        normalized = self.normalize_state(normalized)
        event = (
            self.contract["exit_contract"]["completion_event"]
            if completion_eligible
            else self.objective_by_id[objective_id]["completion_event"]
        )
        return normalized, self._transition(
            event,
            normalized,
            objective_id=objective_id,
        )

    def record_failure(
        self, state: Any, failure_id: str
    ) -> tuple[dict[str, Any], RelayEchoTransition]:
        normalized = self.normalize_state(state)
        if not normalized["active"] or normalized["current_objective"] is None:
            raise RelayEchoStateError(
                "Relay Echo failure requires an active objective"
            )
        objective_id = normalized["current_objective"]
        objective = self.objective_by_id[objective_id]
        if failure_id not in objective["failure_modes"]:
            raise RelayEchoStateError(
                f"failure {failure_id!r} is not valid for objective {objective_id!r}"
            )
        policy = self.failure_states[failure_id]
        normalized["failures"] += 1
        normalized["revision"] += 1
        normalized["failure_history"].append(
            {
                "sequence": normalized["failures"],
                "failure_id": failure_id,
                "objective_id": objective_id,
                "checkpoint_id": normalized["checkpoint_id"],
                "revision": normalized["revision"],
                "recovery": policy["recovery"],
            }
        )
        normalized["telemetry_insight"] += policy["insight_delta"]
        normalized = self.normalize_state(normalized)
        return normalized, self._transition(
            "failure_recorded",
            normalized,
            objective_id=objective_id,
            failure_id=failure_id,
            recovery=policy["recovery"],
        )

    def _apply_objective_evidence(
        self,
        state: dict[str, Any],
        objective_id: str,
        evidence: dict[str, Any],
    ) -> None:
        allowed: set[str] = set()
        if objective_id == "recover_signal_fragments":
            allowed = {"signal_fragments"}
            fragments = self._non_negative_int(
                evidence.get("signal_fragments"), "signal_fragments"
            )
            if fragments < 3:
                raise RelayEchoStateError(
                    "signal recovery requires at least three fragments"
                )
            state["signal_fragments"] = fragments
        elif objective_id == "triangulate_echo_source":
            allowed = {"echo_source"}
            state["echo_source"] = self._stable_value(
                evidence.get("echo_source"), "echo_source"
            )
        elif objective_id == "breach_relay_core":
            allowed = {"relay_core_open"}
            if evidence.get("relay_core_open") is not True:
                raise RelayEchoStateError(
                    "relay breach requires relay_core_open evidence"
                )
            state["relay_core_open"] = True
        elif objective_id == "align_the_echo":
            allowed = {"echo_alignment"}
            state["echo_alignment"] = self._stable_value(
                evidence.get("echo_alignment"), "echo_alignment"
            )
        unexpected = sorted(set(evidence).difference(allowed))
        if unexpected:
            raise RelayEchoStateError(
                f"objective {objective_id!r} received unexpected evidence keys {unexpected}"
            )

    def _transition(
        self,
        event: str,
        state: dict[str, Any],
        *,
        objective_id: str | None = None,
        failure_id: str | None = None,
        recovery: str | None = None,
    ) -> RelayEchoTransition:
        return RelayEchoTransition(
            event=event,
            revision=state["revision"],
            attempt=state["attempts"],
            objective_id=objective_id,
            failure_id=failure_id,
            checkpoint_id=state["checkpoint_id"],
            current_state=state["current_state"],
            current_objective=state["current_objective"],
            completed_objectives=tuple(state["completed_objectives"]),
            telemetry_insight=state["telemetry_insight"],
            completion_eligible=state["completion_eligible"],
            recovery=recovery,
        )


RELAY_ECHO_RUNTIME = RelayEchoRuntime()
