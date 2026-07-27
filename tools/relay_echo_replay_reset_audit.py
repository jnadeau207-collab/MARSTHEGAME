#!/usr/bin/env python3
"""Audit durable Relay Echo completed-mission replay/reset behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH
from game.core.relay_echo_replay import (
    default_relay_echo_replay,
    normalize_relay_echo_replay,
)
from game.data.levels import LEVELS
from game.data.relay_echo import RELAY_ECHO_MISSION_ID
from tools.relay_echo_replay_reset_replay import run_replay

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = {
    "game/core/replay_engine.py",
    "game/core/relay_echo_replay.py",
    "game/core/relay_echo_save.py",
    "game/scenes/campaign_replay.py",
    "game/scenes/relay_echo_promoted.py",
    "tools/relay_echo_replay_reset_audit.py",
    "tools/relay_echo_replay_reset_replay.py",
    "tests/test_relay_echo_replay_reset.py",
    "tests/test_relay_echo_replay_reset_audit.py",
    "tests/test_relay_echo_replay_reset_replay.py",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_relay_replay_reset(
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

    verification = manifest.get("relay_echo_completed_mission_replay_verification")
    verification_run = manifest.get("verification_run")
    replay_verified = verification == "passed"
    carried = manifest.get("carried_release_gates", {})
    record(
        "manifest_truth",
        manifest.get("schema_version") == 1
        and manifest.get("phase") == "Phase 2"
        and manifest.get("status") == "in_progress"
        and manifest.get("current_tranche") == "relay_echo_campaign_promotion"
        and manifest.get("active_subtranche") == "relay_echo_completed_mission_replay"
        and manifest.get("relay_echo_contract_verification") == "passed"
        and manifest.get("relay_echo_runtime_state_verification") == "passed"
        and manifest.get("relay_echo_playable_candidate_verification") == "passed"
        and manifest.get("relay_echo_accessibility_parity_verification") == "passed"
        and manifest.get("relay_echo_campaign_promotion_verification") == "passed"
        and verification in {"pending", "passed"}
        and manifest.get("implemented_missions") == ["ares_reach", "relay_echo"]
        and manifest.get("planned_missions") == ["phobos_vector", "frontier_burn"]
        and manifest.get("full_campaign_claim") == "not_achieved"
        and manifest.get("aaa_claim") == "target_not_achieved",
        {
            "current_tranche": manifest.get("current_tranche"),
            "active_subtranche": manifest.get("active_subtranche"),
            "verification": verification,
        },
    )
    record(
        "replay_gate_truth",
        carried.get("completed_mission_replay_verified") is replay_verified
        and carried.get("keyboard_gamepad_completion_parity") is True
        and carried.get("accessibility_path_verified") is True
        and carried.get("founder_direct_play_approval") is False
        and carried.get("external_playtests_run") == 0
        and carried.get("authored_final_assets_complete") is False
        and carried.get("packaged_build_soak_complete") is False
        and (
            not replay_verified
            or (isinstance(verification_run, str) and verification_run.isdigit())
        ),
        {
            "carried": carried,
            "replay_verified": replay_verified,
            "verification_run": verification_run,
        },
    )

    archive = default_relay_echo_replay()
    record(
        "archive_default_valid",
        normalize_relay_echo_replay(archive) == archive,
        archive,
    )

    engine_source = (ROOT / "game/core/replay_engine.py").read_text(encoding="utf-8")
    save_source = (ROOT / "game/core/relay_echo_save.py").read_text(encoding="utf-8")
    campaign_source = (ROOT / "game/scenes/campaign_replay.py").read_text(encoding="utf-8")
    promoted_source = (ROOT / "game/scenes/relay_echo_promoted.py").read_text(encoding="utf-8")
    entrypoint_source = (ROOT / "main.py").read_text(encoding="utf-8")
    record(
        "runtime_replay_routed",
        "ReplayCapableEngine" in entrypoint_source
        and "prepare_relay_echo_replay" in engine_source
        and "previous_archive" in engine_source
        and 'return "REPLAY"' in campaign_source
        and "complete_relay_echo_replay" in promoted_source
        and "RelayEchoSaveData" in save_source
        and "normalize_relay_echo_replay" in save_source,
        {
            "entrypoint_uses_replay_engine": "ReplayCapableEngine" in entrypoint_source,
            "engine_prepares_replay": "prepare_relay_echo_replay" in engine_source,
            "campaign_labels_replay": 'return "REPLAY"' in campaign_source,
            "scene_completes_replay": "complete_relay_echo_replay" in promoted_source,
            "save_persists_archive": "RelayEchoSaveData" in save_source,
        },
    )

    report = replay_report if replay_report is not None else run_replay()
    reference = report.get("reference", {}) if isinstance(report, dict) else {}
    completion = reference.get("replay_completion", {}) if isinstance(reference, dict) else {}
    campaign = completion.get("campaign", {}) if isinstance(completion, dict) else {}
    archive = completion.get("archive", {}) if isinstance(completion, dict) else {}
    transition = completion.get("completion_transition", {}) if isinstance(completion, dict) else {}
    record(
        "replay_evidence",
        report.get("status") == "pass"
        and report.get("deterministic") is True
        and report.get("completed_mission_replay") is True
        and report.get("campaign_completion_preserved") is True
        and report.get("phobos_unlock_preserved") is True
        and reference.get("archived_run_ids") == [1]
        and reference.get("current_run_id") == 2
        and campaign.get("completed_missions") == ["ares_reach", "relay_echo"]
        and "phobos_vector" in campaign.get("unlocked_missions", ())
        and campaign.get("current_mission") == "phobos_vector"
        and archive.get("current_run_id") == 2
        and transition.get("event") == "relay_echo_replay_completed"
        and transition.get("run_id") == 2
        and completion.get("transition") == ["campaign"],
        {
            "status": report.get("status"),
            "archived_run_ids": reference.get("archived_run_ids"),
            "current_run_id": reference.get("current_run_id"),
            "campaign": campaign,
            "transition": transition,
        },
    )

    relay = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
    phobos = CAMPAIGN_GRAPH.mission("phobos_vector")
    record(
        "campaign_scope_preserved",
        relay["status"] == "implemented"
        and relay["entrypoint"] == "relay_echo"
        and phobos["status"] == "planned"
        and phobos["entrypoint"] is None,
        {"relay_echo": relay, "phobos_vector": phobos},
    )

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_files_present", not missing_files, missing_files)
    record("classic_mode_preserved", sorted(LEVELS) == list(range(1, 9)), sorted(LEVELS))

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 2",
        "subtranche": "relay_echo_completed_mission_replay",
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "Relay Echo completed-mission replay archives prior run evidence and preserves "
            "campaign completion plus the Phobos unlock. Later missions and external "
            "release-quality gates remain unresolved."
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
        report = audit_relay_replay_reset(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 2",
            "subtranche": "relay_echo_completed_mission_replay",
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
