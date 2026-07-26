#!/usr/bin/env python3
"""Audit the Relay Echo transactional runtime-state layer after promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH
from game.core.relay_echo_state import RELAY_ECHO_RUNTIME
from game.core.save import SaveData
from game.data.campaign import MISSION_STATUS_IMPLEMENTED
from game.data.levels import LEVELS
from game.data.relay_echo import RELAY_ECHO_MISSION_ID

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = {
    "game/core/relay_echo_promotion.py",
    "game/core/relay_echo_state.py",
    "game/core/save.py",
    "game/data/relay_echo.py",
    "tools/relay_echo_runtime_audit.py",
    "tests/test_relay_echo_save.py",
    "tests/test_relay_echo_state.py",
}
_REFERENCE_OBJECTIVES = (
    ("reach_noctis_relay", {}),
    ("recover_signal_fragments", {"signal_fragments": 3}),
    ("triangulate_echo_source", {"echo_source": "subsurface_array"}),
    ("breach_relay_core", {"relay_core_open": True}),
    ("align_the_echo", {"echo_alignment": "redirect"}),
    ("extract_before_collapse", {}),
)


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_relay_runtime(manifest: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "evidence": evidence,
            }
        )

    record(
        "manifest_truth",
        manifest.get("phase") == "Phase 2"
        and manifest.get("status") == "in_progress"
        and manifest.get("current_tranche") == "relay_echo_campaign_promotion"
        and manifest.get("relay_echo_contract_verification") == "passed"
        and manifest.get("relay_echo_runtime_state_verification") == "passed"
        and manifest.get("relay_echo_playable_candidate_verification") == "passed"
        and manifest.get("relay_echo_accessibility_parity_verification") == "passed"
        and manifest.get("relay_echo_campaign_promotion_verification") in {"pending", "passed"}
        and manifest.get("implemented_missions") == ["ares_reach", "relay_echo"]
        and manifest.get("contracted_missions") == [RELAY_ECHO_MISSION_ID],
        {
            "current_tranche": manifest.get("current_tranche"),
            "implemented_missions": manifest.get("implemented_missions"),
        },
    )

    mission = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
    record(
        "mission_route_promoted",
        mission["status"] == MISSION_STATUS_IMPLEMENTED
        and mission["entrypoint"] == "relay_echo"
        and RELAY_ECHO_MISSION_ID in CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
        {
            "status": mission["status"],
            "entrypoint": mission["entrypoint"],
            "playable_after_ares": CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
        },
    )

    default_state = RELAY_ECHO_RUNTIME.default_state()
    record(
        "runtime_default_valid",
        RELAY_ECHO_RUNTIME.normalize_state(default_state) == default_state,
        default_state,
    )

    gated_save = SaveData()
    gated_error = None
    try:
        gated_save.prepare_relay_echo_attempt()
    except ValueError as exc:
        gated_error = str(exc)
    record(
        "campaign_prerequisite_enforced",
        gated_error is not None and "Ares Reach" in gated_error,
        gated_error,
    )

    save = SaveData()
    save.update_phase1_slice(
        checkpoint_id=4,
        best_phase="complete",
        completed=True,
        resource_gate_open=True,
    )
    transitions = [save.prepare_relay_echo_attempt()]
    transitions.append(save.complete_relay_echo_objective("reach_noctis_relay"))
    transitions.append(save.record_relay_echo_failure("fragment_chain_broken"))
    for objective_id, evidence in _REFERENCE_OBJECTIVES[1:]:
        transitions.append(save.complete_relay_echo_objective(objective_id, evidence))

    normalized = RELAY_ECHO_RUNTIME.normalize_state(save.relay_echo)
    record(
        "reference_transactions_valid",
        normalized["completion_eligible"] is True
        and normalized["checkpoint_history"] == list(range(7))
        and normalized["completed_objectives"]
        == [objective_id for objective_id, _evidence in _REFERENCE_OBJECTIVES]
        and normalized["failure_history"][0]["failure_id"] == "fragment_chain_broken"
        and normalized["telemetry_insight"] == 1
        and transitions[-1]["event"] == "relay_echo_completed",
        {
            "state": normalized,
            "events": [transition["event"] for transition in transitions],
        },
    )
    record(
        "state_layer_alone_does_not_mutate_campaign",
        RELAY_ECHO_MISSION_ID not in save.campaign["completed_missions"]
        and "phobos_vector" not in save.campaign["unlocked_missions"],
        save.campaign,
    )

    round_trip = SaveData()
    round_trip.from_dict(save.to_dict())
    record(
        "save_envelope_round_trip",
        round_trip.relay_echo == normalized and round_trip.campaign == save.campaign,
        {
            "relay_echo": round_trip.relay_echo,
            "campaign": round_trip.campaign,
        },
    )

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing_files, missing_files)
    record("classic_mode_preserved", sorted(LEVELS) == list(range(1, 9)), sorted(LEVELS))

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 2",
        "tranche": "relay_echo_runtime_state",
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "The Relay Echo state layer remains independently validated after campaign "
            "promotion. Campaign mutation occurs only through the separate promotion transaction."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=Path("config/phase2_campaign.json"),
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    try:
        report = audit_relay_runtime(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 2",
            "tranche": "relay_echo_runtime_state",
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
