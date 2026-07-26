#!/usr/bin/env python3
"""Audit the verified Relay Echo playable-candidate layer after promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH
from game.data.campaign import MISSION_STATUS_IMPLEMENTED
from game.data.levels import LEVELS
from game.data.relay_echo import RELAY_ECHO_MISSION_ID
from game.data.relay_echo_candidate import (
    RELAY_ECHO_CANDIDATE,
    validate_relay_echo_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = {
    "game/data/relay_echo_candidate.py",
    "game/scenes/relay_echo.py",
    "game/scenes/relay_echo_accessible.py",
    "game/scenes/relay_echo_promoted.py",
    "tools/relay_echo_candidate_audit.py",
    "tools/relay_echo_replay.py",
    "tests/test_relay_echo_candidate.py",
    "tests/test_relay_echo_candidate_audit.py",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_relay_candidate(manifest: dict[str, Any]) -> dict[str, Any]:
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

    candidate_errors = validate_relay_echo_candidate()
    record(
        "candidate_data_valid",
        not candidate_errors,
        {
            "errors": candidate_errors,
            "status": RELAY_ECHO_CANDIDATE.get("candidate_status"),
            "checkpoint_count": len(RELAY_ECHO_CANDIDATE.get("checkpoints", ())),
        },
    )

    mission = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
    engine_source = (ROOT / "game/core/engine.py").read_text(encoding="utf-8")
    promoted_source = (ROOT / "game/scenes/relay_echo_promoted.py").read_text(
        encoding="utf-8"
    )
    record(
        "candidate_promoted_through_wrapper",
        mission["status"] == MISSION_STATUS_IMPLEMENTED
        and mission["entrypoint"] == "relay_echo"
        and RELAY_ECHO_MISSION_ID
        in CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",))
        and "from game.scenes.relay_echo_promoted import PromotedRelayEchoScene"
        in engine_source
        and "AccessibleRelayEchoScene" in promoted_source
        and "complete_relay_echo_campaign" in promoted_source,
        {
            "catalog_status": mission["status"],
            "entrypoint": mission["entrypoint"],
            "playable_after_ares": CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
            "promoted_wrapper_routed": "PromotedRelayEchoScene" in engine_source,
        },
    )

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing_files, missing_files)
    record("classic_mode_preserved", sorted(LEVELS) == list(range(1, 9)), sorted(LEVELS))

    carried = manifest.get("carried_release_gates", {})
    record(
        "release_evidence_truthful",
        carried.get("keyboard_gamepad_completion_parity") is True
        and carried.get("accessibility_path_verified") is True
        and carried.get("founder_direct_play_approval") is False
        and carried.get("external_playtests_run") == 0
        and carried.get("authored_final_assets_complete") is False
        and carried.get("packaged_build_soak_complete") is False,
        carried,
    )

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 2",
        "tranche": "relay_echo_playable_candidate",
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "The verified Relay Echo candidate remains the gameplay base of the promoted "
            "mission. Campaign mutation is confined to the promoted wrapper and transaction layer."
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
        report = audit_relay_candidate(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 2",
            "tranche": "relay_echo_playable_candidate",
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
