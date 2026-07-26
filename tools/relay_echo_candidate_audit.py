#!/usr/bin/env python3
"""Audit the Relay Echo playable candidate without promoting campaign truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH
from game.data.campaign import MISSION_STATUS_PLANNED
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

    tranche = manifest.get("current_tranche")
    candidate_verification = manifest.get("relay_echo_playable_candidate_verification")
    candidate_verification_valid = (
        candidate_verification in {"pending", "passed"}
        if tranche == "relay_echo_playable_candidate"
        else candidate_verification == "passed"
    )
    record(
        "manifest_truth",
        manifest.get("phase") == "Phase 2"
        and manifest.get("status") == "in_progress"
        and tranche
        in {
            "relay_echo_playable_candidate",
            "relay_echo_accessibility_parity",
        }
        and manifest.get("relay_echo_contract_verification") == "passed"
        and manifest.get("relay_echo_runtime_state_verification") == "passed"
        and candidate_verification_valid
        and manifest.get("implemented_missions") == ["ares_reach"]
        and manifest.get("contracted_missions") == [RELAY_ECHO_MISSION_ID]
        and manifest.get("full_campaign_claim") == "not_achieved"
        and manifest.get("aaa_claim") == "target_not_achieved",
        {
            "current_tranche": tranche,
            "contract_verification": manifest.get("relay_echo_contract_verification"),
            "runtime_verification": manifest.get("relay_echo_runtime_state_verification"),
            "candidate_verification": candidate_verification,
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
    campaign_scene_source = (ROOT / "game/scenes/campaign.py").read_text(encoding="utf-8")
    record(
        "candidate_not_promoted",
        mission["status"] == MISSION_STATUS_PLANNED
        and mission["entrypoint"] is None
        and RELAY_ECHO_MISSION_ID not in CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",))
        and "RelayEchoScene" not in engine_source
        and "AccessibleRelayEchoScene" not in engine_source
        and "relay_echo_playable_candidate" not in engine_source
        and "PLAYABLE_CANDIDATE" not in campaign_scene_source,
        {
            "catalog_status": mission["status"],
            "entrypoint": mission["entrypoint"],
            "playable_after_ares": CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
            "engine_imports_candidate": "RelayEchoScene" in engine_source,
            "engine_imports_accessible_candidate": "AccessibleRelayEchoScene" in engine_source,
        },
    )

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing_files, missing_files)
    record(
        "classic_mode_preserved",
        sorted(LEVELS) == list(range(1, 9)),
        sorted(LEVELS),
    )

    carried = manifest.get("carried_release_gates", {})
    parity_verified = manifest.get("relay_echo_accessibility_parity_verification") == "passed"
    record(
        "unresolved_evidence_not_fabricated",
        carried.get("founder_direct_play_approval") is False
        and carried.get("external_playtests_run") == 0
        and carried.get("authored_final_assets_complete") is False
        and carried.get("packaged_build_soak_complete") is False
        and carried.get("keyboard_gamepad_completion_parity") is parity_verified
        and carried.get("accessibility_path_verified") is parity_verified,
        {"carried": carried, "parity_verified": parity_verified},
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
            "Relay Echo has a verified complete playable candidate and deterministic replay, "
            "but remains planned and unavailable through campaign routing. Accessibility and "
            "input parity evidence do not promote the campaign node."
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
