#!/usr/bin/env python3
"""Audit Relay Echo campaign promotion and successor unlock truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH
from game.data.campaign import MISSION_STATUS_IMPLEMENTED, MISSION_STATUS_PLANNED
from game.data.levels import LEVELS
from game.data.relay_echo import RELAY_ECHO_MISSION_ID
from tools.relay_echo_promotion_replay import run_replay

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = {
    "game/core/relay_echo_promotion.py",
    "game/data/campaign.py",
    "game/scenes/relay_echo_promoted.py",
    "tools/relay_echo_promotion_audit.py",
    "tools/relay_echo_promotion_replay.py",
    "tests/test_relay_echo_promotion.py",
    "tests/test_relay_echo_promotion_audit.py",
    "tests/test_relay_echo_promotion_replay.py",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_relay_promotion(
    manifest: dict[str, Any],
    replay_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "evidence": evidence,
            }
        )

    promotion_verification = manifest.get("relay_echo_campaign_promotion_verification")
    record(
        "manifest_truth",
        manifest.get("schema_version") == 1
        and manifest.get("phase") == "Phase 2"
        and manifest.get("status") == "in_progress"
        and manifest.get("current_tranche") == "relay_echo_campaign_promotion"
        and manifest.get("relay_echo_contract_verification") == "passed"
        and manifest.get("relay_echo_runtime_state_verification") == "passed"
        and manifest.get("relay_echo_playable_candidate_verification") == "passed"
        and manifest.get("relay_echo_accessibility_parity_verification") == "passed"
        and promotion_verification in {"pending", "passed"}
        and manifest.get("implemented_missions") == ["ares_reach", "relay_echo"]
        and manifest.get("contracted_missions") == [RELAY_ECHO_MISSION_ID]
        and manifest.get("planned_missions") == ["phobos_vector", "frontier_burn"]
        and manifest.get("full_campaign_claim") == "not_achieved"
        and manifest.get("aaa_claim") == "target_not_achieved",
        {
            "current_tranche": manifest.get("current_tranche"),
            "promotion_verification": promotion_verification,
            "implemented_missions": manifest.get("implemented_missions"),
            "planned_missions": manifest.get("planned_missions"),
        },
    )

    relay = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
    phobos = CAMPAIGN_GRAPH.mission("phobos_vector")
    record(
        "catalog_promotion_truth",
        relay["status"] == MISSION_STATUS_IMPLEMENTED
        and relay["entrypoint"] == "relay_echo"
        and relay["prerequisites"] == ("ares_reach",)
        and phobos["status"] == MISSION_STATUS_PLANNED
        and phobos["entrypoint"] is None
        and phobos["prerequisites"] == (RELAY_ECHO_MISSION_ID,),
        {
            "relay_echo": relay,
            "phobos_vector": phobos,
        },
    )

    engine_source = (ROOT / "game/core/engine.py").read_text(encoding="utf-8")
    promoted_scene_source = (ROOT / "game/scenes/relay_echo_promoted.py").read_text(
        encoding="utf-8"
    )
    transaction_source = (ROOT / "game/core/relay_echo_promotion.py").read_text(
        encoding="utf-8"
    )
    record(
        "runtime_routing_and_transactions",
        "PromotedRelayEchoScene" in engine_source
        and "prepare_relay_echo_launch" in engine_source
        and 'entrypoint not in {"vertical_slice", "relay_echo"}' in engine_source
        and "complete_relay_echo_campaign" in promoted_scene_source
        and "CAMPAIGN_GRAPH.record_attempt" in transaction_source
        and "RELAY_ECHO_RUNTIME.begin_attempt" in transaction_source
        and "RELAY_ECHO_RUNTIME.complete_objective" in transaction_source
        and "CAMPAIGN_GRAPH.complete_mission" in transaction_source,
        {
            "engine_routes_promoted_scene": "PromotedRelayEchoScene" in engine_source,
            "engine_uses_combined_launch": "prepare_relay_echo_launch" in engine_source,
            "scene_uses_combined_completion": (
                "complete_relay_echo_campaign" in promoted_scene_source
            ),
        },
    )

    report = replay_report if replay_report is not None else run_replay()
    reference = report.get("reference", {}) if isinstance(report, dict) else {}
    campaign = reference.get("campaign", {}) if isinstance(reference, dict) else {}
    relay_state = reference.get("relay_echo", {}) if isinstance(reference, dict) else {}
    record(
        "promotion_replay_evidence",
        report.get("status") == "pass"
        and report.get("deterministic") is True
        and report.get("campaign_promoted") is True
        and report.get("relay_echo_completed") is True
        and report.get("phobos_vector_unlocked") is True
        and relay_state.get("completion_eligible") is True
        and campaign.get("completed_missions") == ["ares_reach", "relay_echo"]
        and "phobos_vector" in campaign.get("unlocked_missions", ())
        and campaign.get("current_mission") == "phobos_vector"
        and reference.get("transition") == ["campaign"],
        {
            "status": report.get("status"),
            "campaign": campaign,
            "relay_checkpoint": relay_state.get("checkpoint_id"),
            "transition": reference.get("transition"),
        },
    )

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

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing_files, missing_files)
    record(
        "classic_mode_preserved",
        sorted(LEVELS) == list(range(1, 9)),
        sorted(LEVELS),
    )

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 2",
        "tranche": "relay_echo_campaign_promotion",
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "Relay Echo is implemented and campaign-routed with deterministic promotion "
            "evidence. Phobos Vector is unlocked by completion but remains planned and "
            "non-playable. External release-quality and AAA claims remain unachieved."
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
        report = audit_relay_promotion(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 2",
            "tranche": "relay_echo_campaign_promotion",
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
