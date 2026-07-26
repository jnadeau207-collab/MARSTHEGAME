#!/usr/bin/env python3
"""Audit Relay Echo accessibility and keyboard/gamepad parity before promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.core.campaign import CAMPAIGN_GRAPH
from game.core.input_profiles import INPUT_PROFILES, validate_input_profiles
from game.core.relay_echo_accessibility import (
    RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS,
    relay_echo_accessibility_profile,
    validate_relay_echo_accessibility_profile,
)
from game.data.campaign import MISSION_STATUS_PLANNED
from game.data.levels import LEVELS
from game.data.relay_echo import RELAY_ECHO_MISSION_ID
from tools.relay_echo_accessibility_replay import run_replay

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_FILES = {
    "game/core/accessibility.py",
    "game/core/input.py",
    "game/core/input_profiles.py",
    "game/core/relay_echo_accessibility.py",
    "game/scenes/relay_echo_accessible.py",
    "game/scenes/settings.py",
    "tools/relay_echo_accessibility_audit.py",
    "tools/relay_echo_accessibility_replay.py",
    "tests/test_input_profiles.py",
    "tests/test_relay_echo_accessibility.py",
    "tests/test_relay_echo_accessibility_audit.py",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_relay_accessibility(
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

    parity_verification = manifest.get("relay_echo_accessibility_parity_verification")
    carried = manifest.get("carried_release_gates", {})
    record(
        "manifest_truth",
        manifest.get("phase") == "Phase 2"
        and manifest.get("status") == "in_progress"
        and manifest.get("current_tranche") == "relay_echo_accessibility_parity"
        and manifest.get("relay_echo_contract_verification") == "passed"
        and manifest.get("relay_echo_runtime_state_verification") == "passed"
        and manifest.get("relay_echo_playable_candidate_verification") == "passed"
        and parity_verification in {"pending", "passed"}
        and manifest.get("implemented_missions") == ["ares_reach"]
        and manifest.get("contracted_missions") == [RELAY_ECHO_MISSION_ID]
        and manifest.get("full_campaign_claim") == "not_achieved"
        and manifest.get("aaa_claim") == "target_not_achieved",
        {
            "current_tranche": manifest.get("current_tranche"),
            "parity_verification": parity_verification,
            "implemented_missions": manifest.get("implemented_missions"),
            "contracted_missions": manifest.get("contracted_missions"),
        },
    )
    parity_verified = parity_verification == "passed"
    verification_run = manifest.get("verification_run")
    record(
        "pending_release_gates_truthful",
        carried.get("keyboard_gamepad_completion_parity") is parity_verified
        and carried.get("accessibility_path_verified") is parity_verified
        and carried.get("founder_direct_play_approval") is False
        and carried.get("external_playtests_run") == 0
        and carried.get("authored_final_assets_complete") is False
        and carried.get("packaged_build_soak_complete") is False
        and (
            not parity_verified
            or (isinstance(verification_run, str) and verification_run.isdigit())
        ),
        {
            "carried": carried,
            "parity_verified": parity_verified,
            "verification_run": verification_run,
        },
    )

    profile = relay_echo_accessibility_profile(
        {
            "accessibility": {
                "assist_mode": True,
                "reduced_motion": True,
                "screen_shake": 0.0,
                "flash_intensity": 0.2,
                "subtitles": True,
                "subtitle_background": True,
                "subtitle_scale": 1.5,
                "high_contrast": True,
                "hold_assist": True,
            }
        }
    )
    accessibility_errors = validate_relay_echo_accessibility_profile(profile)
    evidence_keys = set(profile.evidence())
    record(
        "accessibility_contract_covered",
        not accessibility_errors
        and set(RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS).issubset(evidence_keys),
        {
            "requirements": RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS,
            "evidence_keys": sorted(evidence_keys),
            "errors": accessibility_errors,
        },
    )

    input_errors = validate_input_profiles()
    record(
        "input_profiles_complete",
        not input_errors and INPUT_PROFILES == ("keyboard", "gamepad"),
        {
            "profiles": INPUT_PROFILES,
            "errors": input_errors,
        },
    )

    engine_source = (ROOT / "game/core/engine.py").read_text(encoding="utf-8")
    title_source = (ROOT / "game/scenes/title.py").read_text(encoding="utf-8")
    settings_source = (ROOT / "game/scenes/settings.py").read_text(encoding="utf-8")
    record(
        "settings_surface_routed",
        "SettingsScene" in engine_source
        and "def go_settings" in engine_source
        and "self.engine.go_settings()" in title_source
        and "Assist Mode" in settings_source
        and "High-Contrast Objectives" in settings_source
        and "Subtitle Background" in settings_source,
        {
            "engine_settings_scene": "SettingsScene" in engine_source,
            "engine_route": "def go_settings" in engine_source,
            "title_route": "self.engine.go_settings()" in title_source,
        },
    )

    mission = CAMPAIGN_GRAPH.mission(RELAY_ECHO_MISSION_ID)
    record(
        "candidate_remains_hidden",
        mission["status"] == MISSION_STATUS_PLANNED
        and mission["entrypoint"] is None
        and RELAY_ECHO_MISSION_ID not in CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",))
        and "RelayEchoScene" not in engine_source
        and "AccessibleRelayEchoScene" not in engine_source,
        {
            "status": mission["status"],
            "entrypoint": mission["entrypoint"],
            "engine_imports_candidate": "RelayEchoScene" in engine_source,
            "engine_imports_accessible_candidate": "AccessibleRelayEchoScene" in engine_source,
        },
    )

    report = replay_report if replay_report is not None else run_replay()
    profiles = report.get("profiles", {}) if isinstance(report, dict) else {}
    accessible = report.get("accessibility", {}) if isinstance(report, dict) else {}
    accessible_state = accessible.get("relay_echo", {}) if isinstance(accessible, dict) else {}
    accessible_campaign = accessible.get("campaign", {}) if isinstance(accessible, dict) else {}
    record(
        "executable_parity_evidence",
        report.get("status") == "pass"
        and report.get("deterministic") is True
        and report.get("input_parity") is True
        and report.get("accessibility_path_verified") is True
        and report.get("campaign_promoted") is False
        and set(profiles) == set(INPUT_PROFILES)
        and all(
            profile_report.get("relay_echo", {}).get("completion_eligible") is True
            and profile_report.get("transition") == ["campaign"]
            for profile_report in profiles.values()
        )
        and accessible_state.get("completion_eligible") is True
        and accessible.get("transition") == ["campaign"]
        and RELAY_ECHO_MISSION_ID not in accessible_campaign.get("completed_missions", ())
        and "phobos_vector" not in accessible_campaign.get("unlocked_missions", ()),
        {
            "status": report.get("status"),
            "input_parity": report.get("input_parity"),
            "accessibility_path_verified": report.get("accessibility_path_verified"),
            "campaign_promoted": report.get("campaign_promoted"),
            "profiles": sorted(profiles),
            "accessible_checkpoint": accessible_state.get("checkpoint_id"),
        },
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
        "tranche": "relay_echo_accessibility_parity",
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "Relay Echo has executable keyboard/gamepad and accessibility evidence under "
            "verification, but remains a hidden planned candidate. Parity evidence does not "
            "promote the campaign node or satisfy external release-quality gates."
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
        report = audit_relay_accessibility(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 2",
            "tranche": "relay_echo_accessibility_parity",
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
