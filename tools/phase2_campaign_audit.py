#!/usr/bin/env python3
"""Audit truthful Phase 2 campaign architecture and current promotion state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH, validate_campaign_catalog
from game.core.save import SaveData
from game.data.campaign import (
    CAMPAIGN_ID,
    CAMPAIGN_MISSIONS,
    MISSION_STATUS_IMPLEMENTED,
    MISSION_STATUS_PLANNED,
    START_MISSION_ID,
)
from game.data.levels import LEVELS
from game.data.phase1_slice import SLICE_ID
from game.data.relay_echo import (
    RELAY_ECHO_LIFECYCLE,
    RELAY_ECHO_MISSION_ID,
    validate_relay_echo_contract,
)

ROOT = Path(__file__).resolve().parents[1]
_SUPPORTED_ENTRYPOINTS = {"vertical_slice", "relay_echo"}
_REQUIRED_FILES = {
    "game/core/accessibility.py",
    "game/core/campaign.py",
    "game/core/input_profiles.py",
    "game/core/relay_echo_accessibility.py",
    "game/core/relay_echo_promotion.py",
    "game/core/relay_echo_state.py",
    "game/core/save.py",
    "game/data/campaign.py",
    "game/data/relay_echo.py",
    "game/data/relay_echo_candidate.py",
    "game/scenes/campaign.py",
    "game/scenes/relay_echo.py",
    "game/scenes/relay_echo_accessible.py",
    "game/scenes/relay_echo_promoted.py",
    "game/scenes/settings.py",
    "game/scenes/vertical_slice.py",
    "tools/phase2_campaign_audit.py",
    "tools/relay_echo_accessibility_audit.py",
    "tools/relay_echo_candidate_audit.py",
    "tools/relay_echo_promotion_audit.py",
    "tools/relay_echo_promotion_replay.py",
    "tools/relay_echo_runtime_audit.py",
    "tests/test_phase2_campaign_audit.py",
    "tests/test_relay_echo_promotion.py",
    "tests/test_relay_echo_promotion_audit.py",
    "tests/test_relay_echo_promotion_replay.py",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_campaign(manifest: dict[str, Any]) -> dict[str, Any]:
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
        "manifest_identity",
        manifest.get("schema_version") == 1
        and manifest.get("phase") == "Phase 2"
        and manifest.get("campaign_id") == CAMPAIGN_ID,
        {
            "schema_version": manifest.get("schema_version"),
            "phase": manifest.get("phase"),
            "campaign_id": manifest.get("campaign_id"),
        },
    )
    record(
        "truthful_claims",
        manifest.get("status") == "in_progress"
        and manifest.get("full_campaign_claim") == "not_achieved"
        and manifest.get("aaa_claim") == "target_not_achieved",
        {
            "status": manifest.get("status"),
            "full_campaign_claim": manifest.get("full_campaign_claim"),
            "aaa_claim": manifest.get("aaa_claim"),
        },
    )

    catalog_errors = validate_campaign_catalog()
    record("campaign_catalog_valid", not catalog_errors, catalog_errors)

    implemented = [
        mission["id"]
        for mission in CAMPAIGN_MISSIONS
        if mission["status"] == MISSION_STATUS_IMPLEMENTED
    ]
    planned = [
        mission["id"]
        for mission in CAMPAIGN_MISSIONS
        if mission["status"] == MISSION_STATUS_PLANNED
    ]
    record(
        "manifest_matches_catalog",
        manifest.get("implemented_missions") == implemented
        and manifest.get("planned_missions") == planned,
        {
            "implemented": implemented,
            "planned": planned,
        },
    )

    relay = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
    phobos = CAMPAIGN_GRAPH.mission("phobos_vector")
    contract_errors = validate_relay_echo_contract()
    promotion_verification = manifest.get("relay_echo_campaign_promotion_verification")
    record(
        "relay_echo_contract_and_promotion_truth",
        manifest.get("current_tranche") == "relay_echo_campaign_promotion"
        and manifest.get("contracted_missions") == [RELAY_ECHO_MISSION_ID]
        and manifest.get("relay_echo_contract_verification") == "passed"
        and manifest.get("relay_echo_runtime_state_verification") == "passed"
        and manifest.get("relay_echo_playable_candidate_verification") == "passed"
        and manifest.get("relay_echo_accessibility_parity_verification") == "passed"
        and promotion_verification in {"pending", "passed"}
        and relay["contract"] == RELAY_ECHO_MISSION_ID
        and relay["status"] == MISSION_STATUS_IMPLEMENTED
        and relay["entrypoint"] == "relay_echo"
        and RELAY_ECHO_LIFECYCLE == "implemented_playable"
        and phobos["status"] == MISSION_STATUS_PLANNED
        and phobos["entrypoint"] is None
        and not contract_errors,
        {
            "relay": relay,
            "phobos": phobos,
            "lifecycle": RELAY_ECHO_LIFECYCLE,
            "contract_errors": contract_errors,
            "promotion_verification": promotion_verification,
        },
    )

    route_errors: list[str] = []
    for mission in CAMPAIGN_MISSIONS:
        entrypoint = mission["entrypoint"]
        if mission["status"] == MISSION_STATUS_IMPLEMENTED:
            if entrypoint not in _SUPPORTED_ENTRYPOINTS:
                route_errors.append(
                    f"implemented mission {mission['id']} has unsupported entrypoint {entrypoint!r}"
                )
        elif entrypoint is not None:
            route_errors.append(f"planned mission {mission['id']} claims entrypoint {entrypoint!r}")
    record("runtime_routes_truthful", not route_errors, route_errors)

    record(
        "phase1_is_campaign_start",
        START_MISSION_ID == "ares_reach"
        and CAMPAIGN_GRAPH.mission(START_MISSION_ID)["entrypoint"] == "vertical_slice"
        and SLICE_ID == "fictionalized_mars_landing",
        {
            "start_mission": START_MISSION_ID,
            "slice_id": SLICE_ID,
        },
    )

    default_state = SaveData().campaign
    record(
        "transactional_save_default",
        CAMPAIGN_GRAPH.normalize_state(default_state) == CAMPAIGN_GRAPH.default_state(),
        default_state,
    )

    completed_save = SaveData()
    completed_save.update_phase1_slice(
        checkpoint_id=4,
        best_phase="complete",
        completed=True,
        resource_gate_open=True,
    )
    phase1_transaction_ok = (
        completed_save.campaign["completed_missions"] == ["ares_reach"]
        and "relay_echo" in completed_save.campaign["unlocked_missions"]
        and "relay_echo"
        in CAMPAIGN_GRAPH.playable_mission_ids(completed_save.campaign["completed_missions"])
    )
    record(
        "phase1_completion_transaction",
        phase1_transaction_ok,
        completed_save.campaign,
    )

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_evidence_files", not missing_files, missing_files)
    record("classic_mode_preserved", sorted(LEVELS) == list(range(1, 9)), sorted(LEVELS))

    carried = manifest.get("carried_release_gates", {})
    record(
        "release_gates_truthful",
        carried.get("keyboard_gamepad_completion_parity") is True
        and carried.get("accessibility_path_verified") is True
        and carried.get("founder_direct_play_approval") is False
        and carried.get("external_playtests_run") == 0
        and carried.get("authored_final_assets_complete") is False
        and carried.get("packaged_build_soak_complete") is False,
        carried,
    )

    engine_source = (ROOT / "game/core/engine.py").read_text(encoding="utf-8")
    promotion_source = (ROOT / "game/core/relay_echo_promotion.py").read_text(encoding="utf-8")
    title_source = (ROOT / "game/scenes/title.py").read_text(encoding="utf-8")
    record(
        "runtime_campaign_integration",
        "PromotedRelayEchoScene" in engine_source
        and "prepare_relay_echo_launch" in engine_source
        and "complete_relay_echo_campaign" in promotion_source
        and phase1_transaction_ok
        and '("campaign", "Frontier Campaign")' in title_source,
        {
            "promoted_scene_route": "PromotedRelayEchoScene" in engine_source,
            "combined_launch": "prepare_relay_echo_launch" in engine_source,
            "combined_completion": "complete_relay_echo_campaign" in promotion_source,
            "phase1_unlock": phase1_transaction_ok,
        },
    )

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 2",
        "status": "pass" if not failures else "fail",
        "campaign_id": CAMPAIGN_ID,
        "implemented_missions": implemented,
        "contracted_missions": manifest.get("contracted_missions", []),
        "planned_missions": planned,
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "Phase 2 has two implemented campaign missions: Ares Reach and Relay Echo. "
            "Phobos Vector and Frontier Burn remain planned. Full-campaign and AAA-quality "
            "claims remain unachieved."
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
        report = audit_campaign(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 2",
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
