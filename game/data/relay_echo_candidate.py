"""Authored world and interaction data for the Relay Echo playable candidate."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Final

from game.data.relay_echo import RELAY_ECHO_CONTRACT, RELAY_ECHO_MISSION_ID

RELAY_ECHO_CANDIDATE_SCHEMA_VERSION: Final = 1

RELAY_ECHO_CANDIDATE: Final = {
    "schema_version": RELAY_ECHO_CANDIDATE_SCHEMA_VERSION,
    "mission_id": RELAY_ECHO_MISSION_ID,
    "candidate_status": "playable_not_promoted",
    "width": 5_600,
    "height": 900,
    "player_start": (120, 780),
    "sky": (18, 16, 34),
    "ground_col": (68, 54, 72),
    "objective": "Trace the echo through Noctis Relay and extract before collapse.",
    "solids": (
        (0, 840, 5_600, 60),
        (420, 760, 260, 24),
        (980, 720, 220, 24),
        (1_330, 680, 240, 24),
        (1_720, 740, 260, 24),
        (2_120, 700, 300, 24),
        (2_620, 760, 260, 24),
        (3_040, 720, 300, 24),
        (3_480, 680, 280, 24),
        (3_920, 740, 260, 24),
        (4_360, 700, 300, 24),
        (4_860, 750, 260, 24),
    ),
    "enemies": (
        ("rival", 2_760, 800),
        ("rival", 3_020, 800),
        ("rival", 3_280, 800),
        ("rival", 3_520, 800),
    ),
    "collectibles": (
        ("part", 1_080, 680),
        ("part", 1_430, 640),
        ("part", 1_820, 700),
        ("health", 3_880, 700),
    ),
    "terminals": (),
    "goal": (6_400, 760),
    "narration": (
        (500, "Noctis Relay is broadcasting through a dead channel."),
        (2_050, "The fragments agree on a source beneath the array."),
        (3_900, "The echo is not a recording. It is waiting for alignment."),
    ),
    "checkpoints": (
        {"id": 0, "objective_id": None, "position": (120, 780)},
        {"id": 1, "objective_id": "reach_noctis_relay", "position": (860, 780)},
        {"id": 2, "objective_id": "recover_signal_fragments", "position": (2_020, 780)},
        {"id": 3, "objective_id": "triangulate_echo_source", "position": (2_650, 780)},
        {"id": 4, "objective_id": "breach_relay_core", "position": (3_850, 780)},
        {"id": 5, "objective_id": "align_the_echo", "position": (4_650, 780)},
        {"id": 6, "objective_id": "extract_before_collapse", "position": (5_320, 780)},
    ),
    "interactions": {
        "reach_x": 820,
        "triangulation_terminal": (2_420, 800),
        "breach_terminal": (3_720, 800),
        "alignment_terminal": (4_620, 800),
        "extraction_x": 5_280,
        "interaction_radius": (62, 76),
        "overload_frames": 90,
        "completion_frames": 180,
    },
    "guardian_range": (2_600, 3_700),
}


def relay_echo_candidate() -> dict[str, Any]:
    return deepcopy(RELAY_ECHO_CANDIDATE)


def _point_x(value: Any) -> int | None:
    if (
        isinstance(value, (tuple, list))
        and len(value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
    ):
        return value[0]
    return None


def validate_relay_echo_candidate(
    data: dict[str, Any] = RELAY_ECHO_CANDIDATE,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Relay Echo candidate must be an object"]
    if data.get("schema_version") != RELAY_ECHO_CANDIDATE_SCHEMA_VERSION:
        errors.append("unsupported Relay Echo candidate schema")
    if data.get("mission_id") != RELAY_ECHO_MISSION_ID:
        errors.append("candidate belongs to another mission")
    if data.get("candidate_status") != "playable_not_promoted":
        errors.append("candidate may not claim campaign promotion")
    width = data.get("width")
    height = data.get("height")
    if isinstance(width, bool) or not isinstance(width, int) or width < 4_000:
        errors.append("candidate width is insufficient for the authored path")
    if isinstance(height, bool) or not isinstance(height, int) or height < 720:
        errors.append("candidate height is invalid")

    contract_objectives = tuple(item["id"] for item in RELAY_ECHO_CONTRACT["objectives"])
    checkpoints = data.get("checkpoints")
    if not isinstance(checkpoints, (tuple, list)):
        errors.append("candidate checkpoints must be a sequence")
        checkpoints = ()
    checkpoint_ids = [item.get("id") for item in checkpoints if isinstance(item, dict)]
    if checkpoint_ids != list(range(len(contract_objectives) + 1)):
        errors.append("candidate checkpoints must be contiguous from zero")
    checkpoint_objectives = tuple(
        item.get("objective_id") for item in checkpoints[1:] if isinstance(item, dict)
    )
    if checkpoint_objectives != contract_objectives:
        errors.append("candidate checkpoint objectives must match the mission contract")
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, dict):
            errors.append("candidate checkpoint entries must be objects")
            continue
        if _point_x(checkpoint.get("position")) is None:
            errors.append(f"checkpoint {checkpoint.get('id')} has an invalid position")

    solids = data.get("solids")
    if not isinstance(solids, (tuple, list)) or not solids:
        errors.append("candidate requires authored collision geometry")
    interactions = data.get("interactions")
    required_interactions = {
        "reach_x",
        "triangulation_terminal",
        "breach_terminal",
        "alignment_terminal",
        "extraction_x",
        "interaction_radius",
        "overload_frames",
        "completion_frames",
    }
    if not isinstance(interactions, dict):
        errors.append("candidate interactions must be an object")
    else:
        missing = sorted(required_interactions.difference(interactions))
        if missing:
            errors.append(f"candidate interactions are incomplete: {missing}")
        ordered_x = [
            interactions.get("reach_x"),
            _point_x(interactions.get("triangulation_terminal")),
            _point_x(interactions.get("breach_terminal")),
            _point_x(interactions.get("alignment_terminal")),
            interactions.get("extraction_x"),
        ]
        if not all(
            isinstance(value, int) and not isinstance(value, bool) for value in ordered_x
        ) or ordered_x != sorted(ordered_x):
            errors.append("candidate interactions must advance left to right")
        if _point_x(interactions.get("interaction_radius")) is None:
            errors.append("candidate interaction radius is invalid")
        if (
            not isinstance(interactions.get("overload_frames"), int)
            or isinstance(interactions.get("overload_frames"), bool)
            or interactions.get("overload_frames", 0) < 30
        ):
            errors.append("candidate overload timing is invalid")
        if (
            not isinstance(interactions.get("completion_frames"), int)
            or isinstance(interactions.get("completion_frames"), bool)
            or interactions.get("completion_frames", 0) < 60
        ):
            errors.append("candidate completion timing is invalid")

    collectibles = data.get("collectibles")
    if not isinstance(collectibles, (tuple, list)):
        errors.append("candidate collectibles must be a sequence")
        collectibles = ()
    parts = [
        item
        for item in collectibles
        if isinstance(item, (tuple, list)) and len(item) == 3 and item[0] == "part"
    ]
    if len(parts) != 3:
        errors.append("candidate must contain exactly three signal fragments")
    guardian_range = data.get("guardian_range")
    if (
        not isinstance(guardian_range, (tuple, list))
        or len(guardian_range) != 2
        or not all(
            isinstance(value, int) and not isinstance(value, bool) for value in guardian_range
        )
        or guardian_range[0] >= guardian_range[1]
    ):
        errors.append("candidate guardian range is invalid")
    return sorted(set(errors))
