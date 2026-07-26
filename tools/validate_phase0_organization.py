#!/usr/bin/env python3
"""Validate the truthful sole-founder and AI-collaborator operating model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_REQUIRED_WORKSTREAMS = {
    "product_and_creative_direction",
    "gameplay_and_systems",
    "rendering_and_performance",
    "audio",
    "tools_and_build",
    "quality_and_release",
    "level_and_narrative_design",
    "ui_ux_and_accessibility",
}
_FORBIDDEN_STAFFING_KEYS = {
    "vertical_slice_seats",
    "functional_seat_count",
    "leadership",
    "departments",
    "fte_count",
}


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a fail-closed verdict without inventing people or headcount."""

    errors: list[str] = []
    if manifest.get("schema_version") != 2:
        errors.append("operating manifest must use schema version 2")
    if manifest.get("operating_model") != "sole founder plus AI collaborator":
        errors.append("operating model must name the sole-founder plus AI collaboration")

    forbidden = sorted(_FORBIDDEN_STAFFING_KEYS.intersection(manifest))
    if forbidden:
        errors.append(f"forbidden staffing constructs remain: {forbidden}")

    truth = manifest.get("truthfulness", {})
    expected_counts = {
        "human_count": 1,
        "employee_count": 0,
        "contractor_count": 0,
        "other_human_contributor_count": 0,
        "ai_collaborator_count": 1,
    }
    for key, expected in expected_counts.items():
        if truth.get(key) != expected:
            errors.append(f"{key} must equal {expected}")

    founder = manifest.get("founder", {})
    founder_id = founder.get("id")
    if not founder_id or founder.get("human") is not True:
        errors.append("one named human founder is required")
    founder_authority = set(founder.get("authority", []))
    required_founder_authority = {
        "product vision",
        "scope",
        "budget",
        "legal decisions",
        "release decisions",
        "merge decisions",
    }
    if not required_founder_authority.issubset(founder_authority):
        errors.append("founder retains incomplete final authority")

    collaborator = manifest.get("ai_collaborator", {})
    if collaborator.get("human") is not False or collaborator.get("employee") is not False:
        errors.append("AI collaborator must not be represented as a human or employee")
    if collaborator.get("accountable_to") != founder_id:
        errors.append("AI collaborator must be accountable to the founder")
    prohibited = set(collaborator.get("prohibited_authority", []))
    required_prohibitions = {
        "spending approval",
        "legal approval",
        "hiring",
        "public release approval",
        "final product scope approval",
        "merging without founder instruction",
    }
    if not required_prohibitions.issubset(prohibited):
        errors.append("AI collaborator authority is not sufficiently bounded")

    workstreams = manifest.get("workstreams", [])
    if len(workstreams) != len(set(workstreams)):
        errors.append("workstreams must be unique")
    missing_workstreams = sorted(_REQUIRED_WORKSTREAMS.difference(workstreams))
    if missing_workstreams:
        errors.append(f"missing workstreams: {missing_workstreams}")
    rule = str(manifest.get("workstream_rule", "")).lower()
    if "not" not in rule or "headcount" not in rule:
        errors.append("workstream rule must explicitly reject headcount interpretation")

    return {
        "schema_version": 2,
        "status": "pass" if not errors else "fail",
        "founder": founder_id,
        "human_count": truth.get("human_count"),
        "employee_count": truth.get("employee_count"),
        "ai_collaborator_count": truth.get("ai_collaborator_count"),
        "workstream_count": len(workstreams),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path("config/phase0_organization.json"),
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        report = validate_manifest(manifest)
    except Exception as exc:
        report = {
            "schema_version": 2,
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
