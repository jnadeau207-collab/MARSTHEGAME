#!/usr/bin/env python3
"""Audit the truthful Phase 2 campaign foundation against executable evidence."""

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

ROOT = Path(__file__).resolve().parents[1]
_SUPPORTED_ENTRYPOINTS = {"vertical_slice"}
_REQUIRED_FILES = {
    "game/core/campaign.py",
    "game/data/campaign.py",
    "game/scenes/campaign.py",
    "game/scenes/vertical_slice.py",
    "tools/phase2_campaign_audit.py",
    "tests/test_campaign.py",
    "tests/test_campaign_save.py",
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

    route_errors = []
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
            "entrypoint": CAMPAIGN_GRAPH.mission(START_MISSION_ID)["entrypoint"],
            "slice_id": SLICE_ID,
        },
    )

    default_state = SaveData().campaign
    normalized_default = CAMPAIGN_GRAPH.normalize_state(default_state)
    record(
        "transactional_save_default",
        normalized_default == CAMPAIGN_GRAPH.default_state(),
        normalized_default,
    )

    missing_files = sorted(path for path in _REQUIRED_FILES if not (ROOT / path).is_file())
    record("required_evidence_files", not missing_files, missing_files)

    record(
        "classic_mode_preserved",
        sorted(LEVELS) == list(range(1, 9)),
        sorted(LEVELS),
    )

    carried = manifest.get("carried_release_gates", {})
    record(
        "unresolved_release_gates_not_fabricated",
        carried.get("founder_direct_play_approval") is False
        and carried.get("external_playtests_run") == 0
        and carried.get("authored_final_assets_complete") is False
        and carried.get("packaged_build_soak_complete") is False
        and carried.get("keyboard_gamepad_completion_parity") is False,
        carried,
    )

    engine_source = (ROOT / "game/core/engine.py").read_text(encoding="utf-8")
    scene_source = (ROOT / "game/scenes/vertical_slice.py").read_text(encoding="utf-8")
    title_source = (ROOT / "game/scenes/title.py").read_text(encoding="utf-8")
    record(
        "runtime_campaign_integration",
        "def start_campaign_mission" in engine_source
        and "CampaignScene" in engine_source
        and 'complete_campaign_mission("ares_reach")' in scene_source
        and '("campaign", "Frontier Campaign")' in title_source,
        {
            "engine_route": "def start_campaign_mission" in engine_source,
            "campaign_scene": "CampaignScene" in engine_source,
            "completion_transaction": 'complete_campaign_mission("ares_reach")' in scene_source,
            "title_route": '("campaign", "Frontier Campaign")' in title_source,
        },
    )

    failures = [check["check_id"] for check in checks if check["status"] != "pass"]
    return {
        "schema_version": 1,
        "phase": "Phase 2",
        "status": "pass" if not failures else "fail",
        "campaign_id": CAMPAIGN_ID,
        "implemented_missions": implemented,
        "planned_missions": planned,
        "checks": checks,
        "failures": failures,
        "truthfulness_note": (
            "Phase 2 has one implemented campaign mission. Planned missions are graph nodes, not "
            "playable content. Full-campaign and AAA-quality claims remain unachieved."
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
