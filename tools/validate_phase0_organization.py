#!/usr/bin/env python3
"""Validate the Phase 0 leadership and vertical-slice operating manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_REQUIRED_LEADERSHIP = {
    "product_creative",
    "executive_production",
    "technical_direction",
    "quality_release",
}
_REQUIRED_DISCIPLINES = {
    "product_creative",
    "production",
    "technical_direction",
    "gameplay_engineering",
    "rendering_performance",
    "tools_build",
    "quality_automation",
    "level_design",
    "narrative_design",
    "ui_ux_accessibility",
    "technical_art_vfx",
    "audio_systems",
}
_VALID_STATUSES = {"active", "filled", "interim"}


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a machine-readable verdict without inflating human headcount."""

    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("organization manifest must use schema version 1")

    accountable_human = manifest.get("accountable_human", {}).get("id")
    if not accountable_human:
        errors.append("one accountable human authority is required")

    leadership = manifest.get("leadership", [])
    leadership_ids = [role.get("role_id") for role in leadership]
    missing_leadership = sorted(_REQUIRED_LEADERSHIP.difference(leadership_ids))
    if missing_leadership:
        errors.append(f"missing leadership roles: {missing_leadership}")
    if len(leadership_ids) != len(set(leadership_ids)):
        errors.append("leadership role ids must be unique")

    seats = manifest.get("vertical_slice_seats", [])
    if not 12 <= len(seats) <= 20:
        errors.append("vertical-slice operating cell must contain 12 to 20 seats")
    seat_ids = [seat.get("seat_id") for seat in seats]
    if len(seat_ids) != len(set(seat_ids)):
        errors.append("vertical-slice seat ids must be unique")

    disciplines = {seat.get("discipline") for seat in seats}
    missing_disciplines = sorted(_REQUIRED_DISCIPLINES.difference(disciplines))
    if missing_disciplines:
        errors.append(f"missing required disciplines: {missing_disciplines}")

    for collection_name, entries in (("leadership", leadership), ("seat", seats)):
        for entry in entries:
            identifier = entry.get("role_id") or entry.get("seat_id") or "unknown"
            if not entry.get("owner"):
                errors.append(f"{collection_name} {identifier} has no owner")
            if entry.get("status") not in _VALID_STATUSES:
                errors.append(f"{collection_name} {identifier} is not active")
            if (
                entry.get("owner_type") == "agent"
                and entry.get("accountable_to") != accountable_human
            ):
                errors.append(
                    f"{collection_name} {identifier} must be accountable to the named human"
                )

    truthfulness = manifest.get("truthfulness", {})
    claimed_human_headcount = truthfulness.get("claimed_human_headcount")
    human_owners = {
        entry.get("owner") for entry in [*leadership, *seats] if entry.get("owner_type") == "human"
    }
    if claimed_human_headcount != len(human_owners):
        errors.append("claimed human headcount must equal unique named human owners")
    if truthfulness.get("functional_seat_count") != len(seats):
        errors.append("functional seat count does not match the manifest")

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "accountable_human": accountable_human,
        "leadership_roles": len(leadership),
        "vertical_slice_seats": len(seats),
        "human_headcount_claim": claimed_human_headcount,
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
            "schema_version": 1,
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
