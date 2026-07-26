"""Durable completed-run archive and atomic Relay Echo replay transactions."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Protocol

from game.core.campaign import CAMPAIGN_GRAPH, CampaignTransition
from game.core.relay_echo_state import RELAY_ECHO_RUNTIME
from game.data.relay_echo import RELAY_ECHO_MISSION_ID

RELAY_ECHO_REPLAY_SCHEMA_VERSION = 1
_FINAL_OBJECTIVE_ID = "extract_before_collapse"


class RelayEchoReplayError(ValueError):
    """Raised when replay archive or replay progression is inconsistent."""


class ReplaySave(Protocol):
    campaign: dict[str, Any]
    relay_echo: dict[str, Any]
    relay_echo_replay: dict[str, Any]


def default_relay_echo_replay() -> dict[str, Any]:
    return {
        "schema_version": RELAY_ECHO_REPLAY_SCHEMA_VERSION,
        "mission_id": RELAY_ECHO_MISSION_ID,
        "current_run_id": 1,
        "completed_runs": [],
    }


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RelayEchoReplayError(f"{field} must be a non-negative integer")
    return value


def _positive_int(value: Any, field: str) -> int:
    result = _non_negative_int(value, field)
    if result < 1:
        raise RelayEchoReplayError(f"{field} must be a positive integer")
    return result


def summarize_completed_run(state: Any, run_id: int) -> dict[str, Any]:
    normalized = RELAY_ECHO_RUNTIME.normalize_state(state)
    run_id = _positive_int(run_id, "relay_echo_replay.run_id")
    if not normalized["completion_eligible"]:
        raise RelayEchoReplayError("only completed Relay Echo state can be archived")
    return {
        "run_id": run_id,
        "attempts": normalized["attempts"],
        "revision": normalized["revision"],
        "failures": normalized["failures"],
        "telemetry_insight": normalized["telemetry_insight"],
        "completed_objectives": list(normalized["completed_objectives"]),
        "checkpoint_history": list(normalized["checkpoint_history"]),
        "signal_fragments": normalized["signal_fragments"],
        "echo_source": normalized["echo_source"],
        "relay_core_open": normalized["relay_core_open"],
        "echo_alignment": normalized["echo_alignment"],
    }


def normalize_relay_echo_replay(value: Any) -> dict[str, Any]:
    if value is None:
        return default_relay_echo_replay()
    if not isinstance(value, dict):
        raise RelayEchoReplayError("Relay Echo replay archive must be an object")
    if value.get("schema_version", RELAY_ECHO_REPLAY_SCHEMA_VERSION) != (
        RELAY_ECHO_REPLAY_SCHEMA_VERSION
    ):
        raise RelayEchoReplayError("Relay Echo replay archive schema is unsupported")
    if value.get("mission_id", RELAY_ECHO_MISSION_ID) != RELAY_ECHO_MISSION_ID:
        raise RelayEchoReplayError("Relay Echo replay archive belongs to another mission")

    completed_value = value.get("completed_runs", [])
    if not isinstance(completed_value, list) or not all(
        isinstance(item, dict) for item in completed_value
    ):
        raise RelayEchoReplayError("completed_runs must be an object list")

    completed_runs: list[dict[str, Any]] = []
    for expected_run_id, item in enumerate(completed_value, start=1):
        run_id = _positive_int(item.get("run_id"), "completed_runs.run_id")
        if run_id != expected_run_id:
            raise RelayEchoReplayError("completed run ids must be contiguous from one")
        summary = {
            "run_id": run_id,
            "attempts": _positive_int(item.get("attempts"), "completed_runs.attempts"),
            "revision": _positive_int(item.get("revision"), "completed_runs.revision"),
            "failures": _non_negative_int(
                item.get("failures"), "completed_runs.failures"
            ),
            "telemetry_insight": _non_negative_int(
                item.get("telemetry_insight"), "completed_runs.telemetry_insight"
            ),
            "completed_objectives": item.get("completed_objectives"),
            "checkpoint_history": item.get("checkpoint_history"),
            "signal_fragments": _non_negative_int(
                item.get("signal_fragments"), "completed_runs.signal_fragments"
            ),
            "echo_source": item.get("echo_source"),
            "relay_core_open": item.get("relay_core_open"),
            "echo_alignment": item.get("echo_alignment"),
        }
        if summary["completed_objectives"] != list(RELAY_ECHO_RUNTIME.objectives):
            raise RelayEchoReplayError(
                "completed run objectives must match the Relay Echo contract"
            )
        if summary["checkpoint_history"] != list(
            range(len(RELAY_ECHO_RUNTIME.objectives) + 1)
        ):
            raise RelayEchoReplayError("completed run checkpoints must be contiguous")
        if summary["signal_fragments"] < 3:
            raise RelayEchoReplayError("completed run requires three signal fragments")
        if not isinstance(summary["echo_source"], str) or not summary["echo_source"]:
            raise RelayEchoReplayError("completed run requires echo-source evidence")
        if summary["relay_core_open"] is not True:
            raise RelayEchoReplayError("completed run requires an open relay core")
        if not isinstance(summary["echo_alignment"], str) or not summary["echo_alignment"]:
            raise RelayEchoReplayError("completed run requires echo-alignment evidence")
        completed_runs.append(summary)

    current_run_id = _positive_int(
        value.get("current_run_id", len(completed_runs) + 1),
        "relay_echo_replay.current_run_id",
    )
    if current_run_id != len(completed_runs) + 1:
        raise RelayEchoReplayError(
            "current_run_id must immediately follow archived completed runs"
        )
    return {
        "schema_version": RELAY_ECHO_REPLAY_SCHEMA_VERSION,
        "mission_id": RELAY_ECHO_MISSION_ID,
        "current_run_id": current_run_id,
        "completed_runs": completed_runs,
    }


def _next_incomplete_mission(campaign: Mapping[str, Any]) -> str:
    completed = set(campaign["completed_missions"])
    for mission_id in campaign["unlocked_missions"]:
        if mission_id not in completed:
            return mission_id
    return RELAY_ECHO_MISSION_ID


def prepare_relay_echo_replay(save: ReplaySave) -> dict[str, Any]:
    """Archive the completed run and prepare a clean replay attempt atomically."""

    campaign_before = CAMPAIGN_GRAPH.normalize_state(save.campaign)
    relay_before = RELAY_ECHO_RUNTIME.normalize_state(save.relay_echo)
    archive_before = normalize_relay_echo_replay(save.relay_echo_replay)
    if RELAY_ECHO_MISSION_ID not in campaign_before["completed_missions"]:
        raise RelayEchoReplayError("Relay Echo replay requires campaign completion")
    if "phobos_vector" not in campaign_before["unlocked_missions"]:
        raise RelayEchoReplayError("Relay Echo replay requires the preserved Phobos unlock")
    if not relay_before["completion_eligible"]:
        raise RelayEchoReplayError("Relay Echo replay requires a completed current run")

    archive = deepcopy(archive_before)
    archived_summary = summarize_completed_run(
        relay_before,
        archive["current_run_id"],
    )
    archive["completed_runs"].append(archived_summary)
    archive["current_run_id"] += 1
    archive = normalize_relay_echo_replay(archive)

    relay, relay_transition = RELAY_ECHO_RUNTIME.begin_attempt(
        RELAY_ECHO_RUNTIME.default_state()
    )
    campaign, campaign_transition = CAMPAIGN_GRAPH.record_attempt(
        campaign_before,
        RELAY_ECHO_MISSION_ID,
    )
    if campaign["completed_missions"] != campaign_before["completed_missions"]:
        raise RelayEchoReplayError("replay launch changed campaign completion history")
    if campaign["unlocked_missions"] != campaign_before["unlocked_missions"]:
        raise RelayEchoReplayError("replay launch changed campaign unlock history")

    save.campaign = campaign
    save.relay_echo = relay
    save.relay_echo_replay = archive
    return {
        "event": "relay_echo_replay_prepared",
        "archived_run": archived_summary,
        "current_run_id": archive["current_run_id"],
        "campaign": campaign_transition.to_dict(),
        "relay_echo": relay_transition.to_dict(),
    }


def complete_relay_echo_replay(
    save: ReplaySave,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Complete a replay while preserving campaign completion and unlock history."""

    campaign_before = CAMPAIGN_GRAPH.normalize_state(save.campaign)
    archive = normalize_relay_echo_replay(save.relay_echo_replay)
    if RELAY_ECHO_MISSION_ID not in campaign_before["completed_missions"]:
        raise RelayEchoReplayError("Relay Echo replay completion requires campaign completion")
    relay, relay_transition = RELAY_ECHO_RUNTIME.complete_objective(
        save.relay_echo,
        _FINAL_OBJECTIVE_ID,
        evidence,
    )
    if not relay["completion_eligible"]:
        raise RelayEchoReplayError("Relay Echo replay did not reach completion eligibility")

    campaign = deepcopy(campaign_before)
    campaign["revision"] += 1
    campaign["current_mission"] = _next_incomplete_mission(campaign)
    campaign = CAMPAIGN_GRAPH.normalize_state(campaign)
    if campaign["completed_missions"] != campaign_before["completed_missions"]:
        raise RelayEchoReplayError("replay completion changed campaign completion history")
    if campaign["unlocked_missions"] != campaign_before["unlocked_missions"]:
        raise RelayEchoReplayError("replay completion changed campaign unlock history")

    campaign_transition = CampaignTransition(
        event="mission_replay_completed",
        mission_id=RELAY_ECHO_MISSION_ID,
        revision=campaign["revision"],
        completed_missions=tuple(campaign["completed_missions"]),
        unlocked_missions=tuple(campaign["unlocked_missions"]),
        current_mission=campaign["current_mission"],
    )
    save.campaign = campaign
    save.relay_echo = relay
    save.relay_echo_replay = archive
    return {
        "event": "relay_echo_replay_completed",
        "run_id": archive["current_run_id"],
        "relay_echo": relay_transition.to_dict(),
        "campaign": campaign_transition.to_dict(),
        "preserved_completed_missions": list(campaign["completed_missions"]),
        "preserved_unlocked_missions": list(campaign["unlocked_missions"]),
    }
