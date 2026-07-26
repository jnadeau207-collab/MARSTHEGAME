#!/usr/bin/env python3
"""Fail closed if Phase 1 quality state or AAA claims are misrepresented."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_JOURNEY = {
    "cinematic_arrival",
    "movement_mastery",
    "adaptive_combat",
    "failure_advances_understanding",
    "resource_changes_next_encounter",
    "vehicle_or_ascent_spectacle",
    "resolved_ending_beat",
}
_REQUIRED_RUNTIME_FILES = {
    "game/core/accessibility.py",
    "game/core/audio.py",
    "game/core/camera.py",
    "game/core/presentation.py",
}
_REQUIRED_GATES = {
    "classic_mode_compatibility",
    "deterministic_slice_replay",
    "keyboard_gamepad_completion_parity",
    "accessibility_checklist",
    "zero_progression_blockers",
    "zero_known_save_corruption",
    "release_candidate_soak_crashes",
    "target_simulation_hz",
    "external_playtest_completion_minimum",
    "emotional_target",
}


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_quality(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("Phase 1 quality manifest must use schema version 1")
    if manifest.get("phase") != "Phase 1":
        errors.append("quality manifest must identify Phase 1")
    if manifest.get("aaa_claim") not in {"target_not_achieved", "candidate_pending_evidence"}:
        errors.append("AAA-quality may not be claimed without completed external evidence")

    slice_data = manifest.get("slice", {})
    journey = set(slice_data.get("journey", []))
    missing_journey = sorted(_REQUIRED_JOURNEY.difference(journey))
    if missing_journey:
        errors.append(f"slice journey is incomplete: {missing_journey}")

    gates = set(manifest.get("quality_gates", {}))
    missing_gates = sorted(_REQUIRED_GATES.difference(gates))
    if missing_gates:
        errors.append(f"quality gates are incomplete: {missing_gates}")

    missing_files = sorted(path for path in _REQUIRED_RUNTIME_FILES if not (ROOT / path).is_file())
    if missing_files:
        errors.append(f"runtime foundation files are missing: {missing_files}")

    evidence = manifest.get("external_evidence", {})
    playtests_run = evidence.get("playtests_run")
    completion_rate = evidence.get("completion_rate")
    emotional_result = evidence.get("emotional_response_result")
    founder_approval = evidence.get("founder_direct_play_approval")
    if playtests_run == 0:
        if (
            completion_rate is not None
            or emotional_result is not None
            or founder_approval is not False
        ):
            errors.append("external evidence cannot be recorded before playtests exist")
    elif manifest.get("aaa_claim") == "target_not_achieved":
        errors.append("existing playtest evidence must move the claim to candidate review")

    runtime = manifest.get("runtime_foundation", {})
    implemented = sorted(key for key, value in runtime.items() if value == "implemented")
    pending = sorted(key for key, value in runtime.items() if value != "implemented")

    return {
        "schema_version": 1,
        "phase": "Phase 1",
        "status": "pass" if not errors else "fail",
        "aaa_claim": manifest.get("aaa_claim"),
        "playable_start_to_finish": bool(slice_data.get("playable_start_to_finish")),
        "implemented_foundations": implemented,
        "pending_foundations": pending,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=Path("config/phase1_quality.json"),
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = audit_quality(_load_manifest(args.manifest))
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 1",
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
