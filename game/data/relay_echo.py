"""Authoritative non-playable mission contract for Relay Echo."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Final

from game.data.campaign import CAMPAIGN_ID

RELAY_ECHO_CONTRACT_SCHEMA_VERSION: Final = 1
RELAY_ECHO_MISSION_ID: Final = "relay_echo"
RELAY_ECHO_LIFECYCLE: Final = "contracted_not_playable"

_OBJECTIVE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_CONTENT_KEY_PATTERN = re.compile(r"^mission\.relay_echo\.[a-z0-9_.]+$")
_REQUIRED_ACCESSIBILITY = frozenset(
    {
        "assist_mode",
        "camera_shake_scale",
        "flash_reduction",
        "hold_toggle_alternatives",
        "high_contrast_objectives",
        "reduced_motion",
        "subtitle_background",
    }
)
_REQUIRED_CONTENT_PACKAGES = frozenset(
    {
        "audio",
        "encounters",
        "environment",
        "localization",
        "presentation",
        "ui",
        "vfx",
    }
)

RELAY_ECHO_CONTRACT: Final = {
    "schema_version": RELAY_ECHO_CONTRACT_SCHEMA_VERSION,
    "campaign_id": CAMPAIGN_ID,
    "mission_id": RELAY_ECHO_MISSION_ID,
    "lifecycle": RELAY_ECHO_LIFECYCLE,
    "title_key": "mission.relay_echo.title",
    "location_key": "mission.relay_echo.location",
    "objective_summary_key": "mission.relay_echo.objective.summary",
    "prerequisites": ("ares_reach",),
    "target_duration_minutes": (22, 32),
    "entry_contract": {
        "required_completed_missions": ("ares_reach",),
        "required_unlocked_mission": RELAY_ECHO_MISSION_ID,
        "spawn_id": "noctis_insertion",
        "inherited_capabilities": (
            "adaptive_combat",
            "checkpoint_recovery",
            "movement_mastery",
            "resource_interaction",
        ),
    },
    "exit_contract": {
        "completion_event": "relay_echo_completed",
        "campaign_completion_mission": RELAY_ECHO_MISSION_ID,
        "next_unlocked_mission": "phobos_vector",
        "return_destination": "campaign",
        "committed_save_keys": (
            "campaign.completed_missions",
            "campaign.current_mission",
            "campaign.revision",
            "campaign.unlocked_missions",
            "relay_echo.best_checkpoint",
            "relay_echo.echo_alignment",
            "relay_echo.telemetry_insight",
        ),
    },
    "state_order": (
        "insertion",
        "signal_hunt",
        "triangulation",
        "relay_breach",
        "echo_alignment",
        "extraction",
        "complete",
    ),
    "objectives": (
        {
            "id": "reach_noctis_relay",
            "state": "insertion",
            "kind": "traversal",
            "dependencies": (),
            "checkpoint_id": 1,
            "completion_event": "noctis_relay_reached",
            "title_key": "mission.relay_echo.objective.reach_relay.title",
            "detail_key": "mission.relay_echo.objective.reach_relay.detail",
            "failure_modes": ("player_down",),
        },
        {
            "id": "recover_signal_fragments",
            "state": "signal_hunt",
            "kind": "investigation_combat",
            "dependencies": ("reach_noctis_relay",),
            "checkpoint_id": 2,
            "completion_event": "signal_fragments_recovered",
            "title_key": "mission.relay_echo.objective.fragments.title",
            "detail_key": "mission.relay_echo.objective.fragments.detail",
            "failure_modes": ("player_down", "fragment_chain_broken"),
        },
        {
            "id": "triangulate_echo_source",
            "state": "triangulation",
            "kind": "systems_puzzle",
            "dependencies": ("recover_signal_fragments",),
            "checkpoint_id": 3,
            "completion_event": "echo_source_triangulated",
            "title_key": "mission.relay_echo.objective.triangulate.title",
            "detail_key": "mission.relay_echo.objective.triangulate.detail",
            "failure_modes": ("player_down", "relay_overload"),
        },
        {
            "id": "breach_relay_core",
            "state": "relay_breach",
            "kind": "adaptive_encounter",
            "dependencies": ("triangulate_echo_source",),
            "checkpoint_id": 4,
            "completion_event": "relay_core_breached",
            "title_key": "mission.relay_echo.objective.breach.title",
            "detail_key": "mission.relay_echo.objective.breach.detail",
            "failure_modes": ("player_down", "relay_overload"),
        },
        {
            "id": "align_the_echo",
            "state": "echo_alignment",
            "kind": "consequence_choice",
            "dependencies": ("breach_relay_core",),
            "checkpoint_id": 5,
            "completion_event": "echo_alignment_committed",
            "title_key": "mission.relay_echo.objective.align.title",
            "detail_key": "mission.relay_echo.objective.align.detail",
            "failure_modes": ("player_down", "alignment_desync"),
        },
        {
            "id": "extract_before_collapse",
            "state": "extraction",
            "kind": "timed_traversal",
            "dependencies": ("align_the_echo",),
            "checkpoint_id": 6,
            "completion_event": "noctis_extraction_completed",
            "title_key": "mission.relay_echo.objective.extract.title",
            "detail_key": "mission.relay_echo.objective.extract.detail",
            "failure_modes": ("player_down", "extraction_window_missed"),
        },
    ),
    "checkpoints": (
        {
            "id": 0,
            "state": "insertion",
            "objective_id": None,
            "commit_keys": ("relay_echo.best_checkpoint",),
        },
        {
            "id": 1,
            "state": "signal_hunt",
            "objective_id": "reach_noctis_relay",
            "commit_keys": ("relay_echo.best_checkpoint",),
        },
        {
            "id": 2,
            "state": "triangulation",
            "objective_id": "recover_signal_fragments",
            "commit_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.signal_fragments",
                "relay_echo.telemetry_insight",
            ),
        },
        {
            "id": 3,
            "state": "relay_breach",
            "objective_id": "triangulate_echo_source",
            "commit_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.echo_source",
                "relay_echo.telemetry_insight",
            ),
        },
        {
            "id": 4,
            "state": "echo_alignment",
            "objective_id": "breach_relay_core",
            "commit_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.relay_core_open",
                "relay_echo.telemetry_insight",
            ),
        },
        {
            "id": 5,
            "state": "extraction",
            "objective_id": "align_the_echo",
            "commit_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.echo_alignment",
                "relay_echo.telemetry_insight",
            ),
        },
        {
            "id": 6,
            "state": "complete",
            "objective_id": "extract_before_collapse",
            "commit_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.echo_alignment",
                "relay_echo.telemetry_insight",
            ),
        },
    ),
    "failure_states": {
        "player_down": {
            "recovery": "latest_checkpoint",
            "retained_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.echo_alignment",
                "relay_echo.signal_fragments",
                "relay_echo.telemetry_insight",
            ),
            "insight_delta": 1,
        },
        "fragment_chain_broken": {
            "recovery": "objective_restart",
            "retained_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.telemetry_insight",
            ),
            "insight_delta": 1,
        },
        "relay_overload": {
            "recovery": "latest_checkpoint",
            "retained_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.signal_fragments",
                "relay_echo.telemetry_insight",
            ),
            "insight_delta": 1,
        },
        "alignment_desync": {
            "recovery": "objective_restart",
            "retained_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.relay_core_open",
                "relay_echo.telemetry_insight",
            ),
            "insight_delta": 1,
        },
        "extraction_window_missed": {
            "recovery": "checkpoint_5",
            "retained_keys": (
                "relay_echo.best_checkpoint",
                "relay_echo.echo_alignment",
                "relay_echo.telemetry_insight",
            ),
            "insight_delta": 0,
        },
    },
    "encounters": (
        {
            "id": "fragment_hunters",
            "objective_id": "recover_signal_fragments",
            "purpose": "teach_signal_reading_under_pressure",
            "adaptive_inputs": ("failure_count", "telemetry_insight"),
            "required_archetypes": ("survey_sentinel", "signal_hunter"),
        },
        {
            "id": "relay_breach_defense",
            "objective_id": "breach_relay_core",
            "purpose": "test_mastery_and_prior_resource_choices",
            "adaptive_inputs": (
                "echo_source_solution",
                "failure_count",
                "telemetry_insight",
            ),
            "required_archetypes": ("relay_warden", "signal_hunter"),
        },
        {
            "id": "collapse_extraction",
            "objective_id": "extract_before_collapse",
            "purpose": "convert_committed_alignment_into_route_consequence",
            "adaptive_inputs": ("echo_alignment", "telemetry_insight"),
            "required_archetypes": ("environmental_collapse",),
        },
    ),
    "accessibility_requirements": tuple(sorted(_REQUIRED_ACCESSIBILITY)),
    "localization_keys": (
        "mission.relay_echo.title",
        "mission.relay_echo.location",
        "mission.relay_echo.objective.summary",
        "mission.relay_echo.objective.reach_relay.title",
        "mission.relay_echo.objective.reach_relay.detail",
        "mission.relay_echo.objective.fragments.title",
        "mission.relay_echo.objective.fragments.detail",
        "mission.relay_echo.objective.triangulate.title",
        "mission.relay_echo.objective.triangulate.detail",
        "mission.relay_echo.objective.breach.title",
        "mission.relay_echo.objective.breach.detail",
        "mission.relay_echo.objective.align.title",
        "mission.relay_echo.objective.align.detail",
        "mission.relay_echo.objective.extract.title",
        "mission.relay_echo.objective.extract.detail",
        "mission.relay_echo.failure.player_down",
        "mission.relay_echo.failure.fragment_chain_broken",
        "mission.relay_echo.failure.relay_overload",
        "mission.relay_echo.failure.alignment_desync",
        "mission.relay_echo.failure.extraction_window_missed",
    ),
    "deterministic_replay": {
        "seed": 2_047_119,
        "max_simulation_frames": 118_800,
        "required_objectives": (
            "reach_noctis_relay",
            "recover_signal_fragments",
            "triangulate_echo_source",
            "breach_relay_core",
            "align_the_echo",
            "extract_before_collapse",
        ),
        "required_checkpoints": (0, 1, 2, 3, 4, 5, 6),
        "required_failure_evidence": ("player_down", "relay_overload"),
        "required_transition": "relay_echo_completed",
        "evidence_fields": (
            "checkpoint_history",
            "completed_objectives",
            "failure_history",
            "final_campaign_transition",
            "frame_count",
            "state_history",
        ),
    },
    "performance_budgets": {
        "target_simulation_hz": 60,
        "update_p95_ms": 7.5,
        "draw_p95_ms": 7.5,
        "frame_hitch_ms": 25.0,
        "allocation_bytes_per_frame": 4096,
        "active_enemy_soft_cap": 14,
        "active_effect_soft_cap": 96,
    },
    "content_package_requirements": {
        "audio": "required",
        "encounters": "required",
        "environment": "required",
        "localization": "required",
        "presentation": "required",
        "ui": "required",
        "vfx": "required",
    },
    "procedural_authored_boundary": {
        "deterministic_seed_required": True,
        "authored_critical_path_required": True,
        "procedural_optional_routes_allowed": True,
        "procedural_objective_order_allowed": False,
        "procedural_checkpoint_layout_allowed": False,
    },
    "implementation_gates": (
        "runtime_entrypoint",
        "transactional_mission_save_state",
        "deterministic_reference_replay",
        "objective_and_failure_state_tests",
        "accessibility_path_verification",
        "performance_budget_evidence",
        "authored_content_package",
        "campaign_completion_transaction",
    ),
}


def relay_echo_contract() -> dict[str, Any]:
    """Return an isolated copy of the authoritative contract."""

    return deepcopy(RELAY_ECHO_CONTRACT)


def validate_relay_echo_contract(data: dict[str, Any] = RELAY_ECHO_CONTRACT) -> list[str]:
    """Return stable structural errors for the Relay Echo mission contract."""

    errors: list[str] = []
    required = {
        "schema_version",
        "campaign_id",
        "mission_id",
        "lifecycle",
        "title_key",
        "location_key",
        "objective_summary_key",
        "prerequisites",
        "target_duration_minutes",
        "entry_contract",
        "exit_contract",
        "state_order",
        "objectives",
        "checkpoints",
        "failure_states",
        "encounters",
        "accessibility_requirements",
        "localization_keys",
        "deterministic_replay",
        "performance_budgets",
        "content_package_requirements",
        "procedural_authored_boundary",
        "implementation_gates",
    }
    missing = sorted(required.difference(data))
    if missing:
        return [f"missing keys: {missing}"]

    if data.get("schema_version") != RELAY_ECHO_CONTRACT_SCHEMA_VERSION:
        errors.append("unsupported Relay Echo contract schema")
    if data.get("campaign_id") != CAMPAIGN_ID:
        errors.append("Relay Echo contract belongs to another campaign")
    if data.get("mission_id") != RELAY_ECHO_MISSION_ID:
        errors.append("Relay Echo contract has the wrong mission id")
    if data.get("lifecycle") != RELAY_ECHO_LIFECYCLE:
        errors.append("Relay Echo must remain contracted and non-playable")
    if tuple(data.get("prerequisites", ())) != ("ares_reach",):
        errors.append("Relay Echo must require completed Ares Reach")

    duration = data.get("target_duration_minutes")
    if (
        not isinstance(duration, (tuple, list))
        or len(duration) != 2
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in duration)
        or duration[0] < 15
        or duration[1] <= duration[0]
    ):
        errors.append("target duration must be an ordered integer minute range")

    state_order = tuple(data.get("state_order", ()))
    if not state_order or len(state_order) != len(set(state_order)):
        errors.append("mission states must be unique and ordered")
    if state_order[-1:] != ("complete",):
        errors.append("mission state order must end in complete")

    objectives = tuple(data.get("objectives", ()))
    objective_ids = [item.get("id") for item in objectives if isinstance(item, dict)]
    if len(objectives) != len(objective_ids) or not all(
        isinstance(objective_id, str) and _OBJECTIVE_ID_PATTERN.fullmatch(objective_id)
        for objective_id in objective_ids
    ):
        errors.append("every objective requires a stable id")
    if len(objective_ids) != len(set(objective_ids)):
        errors.append("objective ids must be unique")
    objective_index = {objective_id: index for index, objective_id in enumerate(objective_ids)}
    completion_events: list[str] = []
    declared_failure_modes = set(data.get("failure_states", {}))
    declared_localization = set(data.get("localization_keys", ()))

    for index, objective in enumerate(objectives):
        if not isinstance(objective, dict):
            continue
        objective_id = objective.get("id")
        if objective.get("state") not in state_order[:-1]:
            errors.append(f"objective {objective_id} has an invalid state")
        dependencies = objective.get("dependencies")
        if not isinstance(dependencies, (tuple, list)):
            errors.append(f"objective {objective_id} dependencies must be a sequence")
        else:
            for dependency in dependencies:
                dependency_index = objective_index.get(dependency)
                if dependency_index is None:
                    errors.append(
                        f"objective {objective_id} references unknown dependency {dependency}"
                    )
                elif dependency_index >= index:
                    errors.append(
                        f"objective {objective_id} dependency {dependency} must precede it"
                    )
        checkpoint_id = objective.get("checkpoint_id")
        if isinstance(checkpoint_id, bool) or not isinstance(checkpoint_id, int):
            errors.append(f"objective {objective_id} requires an integer checkpoint")
        completion_event = objective.get("completion_event")
        if not isinstance(completion_event, str) or not completion_event:
            errors.append(f"objective {objective_id} requires a completion event")
        else:
            completion_events.append(completion_event)
        failure_modes = objective.get("failure_modes")
        if not isinstance(failure_modes, (tuple, list)) or not set(failure_modes).issubset(
            declared_failure_modes
        ):
            errors.append(f"objective {objective_id} references unknown failure modes")
        for key_name in ("title_key", "detail_key"):
            content_key = objective.get(key_name)
            if content_key not in declared_localization:
                errors.append(f"objective {objective_id} {key_name} is not localized")

    if len(completion_events) != len(set(completion_events)):
        errors.append("objective completion events must be unique")

    checkpoints = tuple(data.get("checkpoints", ()))
    checkpoint_ids = [item.get("id") for item in checkpoints if isinstance(item, dict)]
    if checkpoint_ids != list(range(len(checkpoints))):
        errors.append("checkpoint ids must be contiguous and ordered")
    checkpoint_by_id = {
        item["id"]: item for item in checkpoints if isinstance(item, dict) and "id" in item
    }
    for objective in objectives:
        if not isinstance(objective, dict):
            continue
        checkpoint = checkpoint_by_id.get(objective.get("checkpoint_id"))
        if checkpoint is None:
            errors.append(f"objective {objective.get('id')} references a missing checkpoint")
        elif checkpoint.get("objective_id") != objective.get("id"):
            errors.append(f"checkpoint {checkpoint.get('id')} does not commit its objective")
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, dict):
            errors.append("checkpoint entries must be objects")
            continue
        if checkpoint.get("state") not in state_order:
            errors.append(f"checkpoint {checkpoint.get('id')} has an invalid state")
        commit_keys = checkpoint.get("commit_keys")
        if not isinstance(commit_keys, (tuple, list)) or not commit_keys:
            errors.append(f"checkpoint {checkpoint.get('id')} must commit save keys")

    failure_states = data.get("failure_states")
    if not isinstance(failure_states, dict) or not failure_states:
        errors.append("failure states must be a non-empty object")
    else:
        for failure_id, policy in failure_states.items():
            if not isinstance(policy, dict):
                errors.append(f"failure state {failure_id} must define a policy")
                continue
            if policy.get("recovery") not in {
                "checkpoint_5",
                "latest_checkpoint",
                "objective_restart",
            }:
                errors.append(f"failure state {failure_id} has invalid recovery semantics")
            insight_delta = policy.get("insight_delta")
            if (
                isinstance(insight_delta, bool)
                or not isinstance(insight_delta, int)
                or insight_delta < 0
            ):
                errors.append(f"failure state {failure_id} has invalid insight delta")
            retained = policy.get("retained_keys")
            if not isinstance(retained, (tuple, list)) or not retained:
                errors.append(f"failure state {failure_id} must retain explicit save keys")

    entry = data.get("entry_contract", {})
    if tuple(entry.get("required_completed_missions", ())) != ("ares_reach",):
        errors.append("entry contract must require Ares Reach completion")
    if entry.get("required_unlocked_mission") != RELAY_ECHO_MISSION_ID:
        errors.append("entry contract must require Relay Echo to be unlocked")

    exit_contract = data.get("exit_contract", {})
    if exit_contract.get("completion_event") != "relay_echo_completed":
        errors.append("exit contract must emit relay_echo_completed")
    if exit_contract.get("campaign_completion_mission") != RELAY_ECHO_MISSION_ID:
        errors.append("exit contract must complete Relay Echo")
    if exit_contract.get("next_unlocked_mission") != "phobos_vector":
        errors.append("exit contract must unlock Phobos Vector")

    accessibility = set(data.get("accessibility_requirements", ()))
    missing_accessibility = sorted(_REQUIRED_ACCESSIBILITY.difference(accessibility))
    if missing_accessibility:
        errors.append(f"missing accessibility requirements: {missing_accessibility}")

    localization_keys = tuple(data.get("localization_keys", ()))
    if len(localization_keys) != len(set(localization_keys)):
        errors.append("localization keys must be unique")
    invalid_localization = sorted(
        key
        for key in localization_keys
        if not isinstance(key, str) or not _CONTENT_KEY_PATTERN.fullmatch(key)
    )
    if invalid_localization:
        errors.append(f"invalid Relay Echo localization keys: {invalid_localization}")
    for key_name in ("title_key", "location_key", "objective_summary_key"):
        if data.get(key_name) not in declared_localization:
            errors.append(f"{key_name} is not present in localization_keys")

    replay = data.get("deterministic_replay", {})
    if tuple(replay.get("required_objectives", ())) != tuple(objective_ids):
        errors.append("replay objective order must match the mission contract")
    if tuple(replay.get("required_checkpoints", ())) != tuple(checkpoint_ids):
        errors.append("replay checkpoints must match the mission contract")
    if replay.get("required_transition") != exit_contract.get("completion_event"):
        errors.append("replay transition must match the exit contract")
    if not set(replay.get("required_failure_evidence", ())).issubset(declared_failure_modes):
        errors.append("replay references unknown failure evidence")
    seed = replay.get("seed")
    max_frames = replay.get("max_simulation_frames")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 1:
        errors.append("replay requires a positive deterministic seed")
    if isinstance(max_frames, bool) or not isinstance(max_frames, int) or max_frames < 60:
        errors.append("replay frame budget is invalid")

    budgets = data.get("performance_budgets", {})
    target_hz = budgets.get("target_simulation_hz")
    update_p95 = budgets.get("update_p95_ms")
    draw_p95 = budgets.get("draw_p95_ms")
    hitch_ms = budgets.get("frame_hitch_ms")
    allocation = budgets.get("allocation_bytes_per_frame")
    if target_hz != 60:
        errors.append("Relay Echo must target 60 Hz simulation")
    if not all(isinstance(value, (int, float)) and value > 0 for value in (update_p95, draw_p95)):
        errors.append("update and draw budgets must be positive")
    elif update_p95 + draw_p95 >= 1000 / target_hz:
        errors.append("update and draw p95 budgets must fit inside the simulation frame")
    if not isinstance(hitch_ms, (int, float)) or hitch_ms < 1000 / 60:
        errors.append("frame hitch threshold is invalid")
    if isinstance(allocation, bool) or not isinstance(allocation, int) or allocation < 0:
        errors.append("allocation budget must be a non-negative integer")

    packages = data.get("content_package_requirements", {})
    if not isinstance(packages, dict):
        errors.append("content package requirements must be an object")
    else:
        missing_packages = sorted(_REQUIRED_CONTENT_PACKAGES.difference(packages))
        if missing_packages:
            errors.append(f"missing content package requirements: {missing_packages}")
        invalid_packages = sorted(key for key, value in packages.items() if value != "required")
        if invalid_packages:
            errors.append(
                f"content packages may not be represented as complete: {invalid_packages}"
            )

    boundary = data.get("procedural_authored_boundary", {})
    if boundary.get("deterministic_seed_required") is not True:
        errors.append("procedural generation must require a deterministic seed")
    if boundary.get("authored_critical_path_required") is not True:
        errors.append("the critical path must remain authored")
    if boundary.get("procedural_objective_order_allowed") is not False:
        errors.append("procedural generation may not reorder objectives")
    if boundary.get("procedural_checkpoint_layout_allowed") is not False:
        errors.append("procedural generation may not alter checkpoint layout")

    implementation_gates = tuple(data.get("implementation_gates", ()))
    if len(implementation_gates) < 8 or len(implementation_gates) != len(set(implementation_gates)):
        errors.append("implementation gates must be unique and complete")

    return sorted(set(errors))
