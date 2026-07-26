"""Atomic in-memory transactions for Relay Echo campaign promotion."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from game.core.campaign import CAMPAIGN_GRAPH
from game.core.relay_echo_state import RELAY_ECHO_RUNTIME
from game.data.relay_echo import RELAY_ECHO_MISSION_ID

_FINAL_OBJECTIVE_ID = "extract_before_collapse"


class RelayEchoPromotionError(ValueError):
    """Raised when promoted Relay Echo progression would be inconsistent."""


class PromotionSave(Protocol):
    campaign: dict[str, Any]
    relay_echo: dict[str, Any]


def _resume_transition(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": "attempt_resumed",
        "revision": state["revision"],
        "attempt": state["attempts"],
        "objective_id": state["current_objective"],
        "failure_id": None,
        "checkpoint_id": state["checkpoint_id"],
        "current_state": state["current_state"],
        "current_objective": state["current_objective"],
        "completed_objectives": list(state["completed_objectives"]),
        "recovery": None,
    }


def prepare_relay_echo_launch(save: PromotionSave) -> dict[str, Any]:
    """Prepare campaign and Relay Echo launch state without partial mutation."""

    campaign, campaign_transition = CAMPAIGN_GRAPH.record_attempt(
        save.campaign,
        RELAY_ECHO_MISSION_ID,
    )
    relay_state = RELAY_ECHO_RUNTIME.normalize_state(save.relay_echo)
    if relay_state["completion_eligible"]:
        raise RelayEchoPromotionError(
            "completed Relay Echo cannot launch until an explicit replay reset exists"
        )
    if relay_state["active"]:
        relay = relay_state
        relay_transition = _resume_transition(relay_state)
    else:
        relay, transition = RELAY_ECHO_RUNTIME.begin_attempt(relay_state)
        relay_transition = transition.to_dict()

    save.campaign = campaign
    save.relay_echo = relay
    return {
        "event": "relay_echo_launch_prepared",
        "campaign": campaign_transition.to_dict(),
        "relay_echo": relay_transition,
    }


def complete_relay_echo_campaign(
    save: PromotionSave,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Commit extraction and campaign completion as one validated state change."""

    relay, relay_transition = RELAY_ECHO_RUNTIME.complete_objective(
        save.relay_echo,
        _FINAL_OBJECTIVE_ID,
        evidence,
    )
    if not relay["completion_eligible"]:
        raise RelayEchoPromotionError("Relay Echo extraction did not reach completion eligibility")

    campaign, campaign_transition = CAMPAIGN_GRAPH.complete_mission(
        save.campaign,
        RELAY_ECHO_MISSION_ID,
    )
    if RELAY_ECHO_MISSION_ID not in campaign["completed_missions"]:
        raise RelayEchoPromotionError("campaign completion did not record Relay Echo")
    if "phobos_vector" not in campaign["unlocked_missions"]:
        raise RelayEchoPromotionError("Relay Echo completion did not unlock Phobos Vector")

    save.relay_echo = relay
    save.campaign = campaign
    return {
        "event": "relay_echo_campaign_completed",
        "relay_echo": relay_transition.to_dict(),
        "campaign": campaign_transition.to_dict(),
        "unlocked_mission": "phobos_vector",
    }
