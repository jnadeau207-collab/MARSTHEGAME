#!/usr/bin/env python3
"""Audit every repository-executable Phase 0 requirement against committed evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.data.classic_replays import CLASSIC_INPUT_TRACKS
from game.data.content import build_content
from game.data.ip_tracks import FICTIONALIZED_TRACK, REAL_WORLD_TRACK, get_identity
from game.data.levels import LEVELS
from tools.validate_phase0_organization import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_DOCUMENTS = (
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "docs/IP_AND_NAMING_BIBLE.md",
    "docs/PERFORMANCE_BASELINES.md",
    "docs/PHASE0_LEADERSHIP_AND_OWNERSHIP.md",
    "docs/VERTICAL_SLICE_TEAM_CHARTER.md",
    "docs/decisions/0001-phase0-foundation.md",
    "docs/decisions/0002-content-keys-and-deterministic-replay.md",
    "docs/decisions/0003-same-runner-performance-guard.md",
    "docs/decisions/0004-phase0-operating-cell.md",
)
_REQUIRED_METRICS = {"setup_ms", "update_ms_per_frame", "draw_ms_per_frame"}


def _load_json(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def run_audit() -> dict[str, Any]:
    """Return a fail-closed Phase 0 completion verdict."""

    checks: list[dict[str, Any]] = []

    def record(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "evidence": evidence,
            }
        )

    chapter_ids = list(range(1, 9))
    record("classic_mode_eight_chapters", sorted(LEVELS) == chapter_ids, sorted(LEVELS))
    record(
        "deterministic_replay_tracks",
        sorted(CLASSIC_INPUT_TRACKS) == chapter_ids,
        sorted(CLASSIC_INPUT_TRACKS),
    )

    real_identity = get_identity(REAL_WORLD_TRACK)
    fictional_identity = get_identity(FICTIONALIZED_TRACK)
    record(
        "dual_ip_tracks",
        sorted(real_identity["chapters"]) == chapter_ids
        and sorted(fictional_identity["chapters"]) == chapter_ids,
        [REAL_WORLD_TRACK, FICTIONALIZED_TRACK],
    )

    real_keys = set(build_content(REAL_WORLD_TRACK))
    fictional_keys = set(build_content(FICTIONALIZED_TRACK))
    record(
        "stable_content_key_parity",
        real_keys == fictional_keys and bool(real_keys),
        {"key_count": len(real_keys)},
    )

    organization = _load_json("config/phase0_organization.json")
    organization_report = validate_manifest(organization)
    record(
        "leadership_and_vertical_slice_cell",
        organization_report["status"] == "pass",
        organization_report,
    )

    performance_policy = _load_json("config/performance_thresholds.json")
    metrics = set(performance_policy.get("metrics", {}))
    record(
        "performance_variance_and_threshold_policy",
        performance_policy.get("schema_version") == 1
        and metrics == _REQUIRED_METRICS
        and performance_policy.get("minimum_rounds", 0) >= 7,
        {
            "policy_name": performance_policy.get("policy_name"),
            "metrics": sorted(metrics),
            "minimum_rounds": performance_policy.get("minimum_rounds"),
        },
    )

    missing_documents = [path for path in _REQUIRED_DOCUMENTS if not (ROOT / path).is_file()]
    record(
        "governance_and_architecture_documents",
        not missing_documents,
        {"required": len(_REQUIRED_DOCUMENTS), "missing": missing_documents},
    )

    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    required_workflow_markers = (
        "Quality (Python",
        "Replay all eight chapters",
        "Same-runner performance guard",
        "Validate Phase 0 organization",
        "Enforce performance regression policy",
    )
    missing_markers = [marker for marker in required_workflow_markers if marker not in workflow]
    record(
        "continuous_integration_gates",
        not missing_markers,
        {"missing_markers": missing_markers},
    )

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 0",
        "status": "pass" if not failures else "fail",
        "scope": "repository-executable legal/IP architecture, hardening, performance, ownership, and operating-cell requirements",
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "The fourteen functional seats are an active founder-accountable operating model, "
            "not a claim of fourteen human employees. Public real-world-track release remains "
            "blocked pending written legal clearance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = run_audit()
    except Exception as exc:
        report = {
            "schema_version": 1,
            "phase": "Phase 0",
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
