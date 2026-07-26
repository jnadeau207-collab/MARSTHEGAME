"""Authored Phase 1 Mars-landing vertical-slice data."""

from __future__ import annotations

from typing import Final

SLICE_ID: Final = "fictionalized_mars_landing"
PHASE_ORDER: Final = (
    "arrival",
    "movement_mastery",
    "adaptive_combat",
    "failure_recovery",
    "resource_gate",
    "ascent",
    "complete",
)

MARS_LANDING_SLICE: Final = {
    "slice_id": SLICE_ID,
    "name": "Ares Reach: First Descent",
    "width": 6400,
    "height": 1200,
    "player_start": (170, 790),
    "goal": (5600, 740),
    "sky": (72, 24, 24),
    "ground_col": (112, 48, 34),
    "objective": "Land. Adapt. Restore the ascent relay. Reach the ridge.",
    "solids": [
        (0, 850, 980, 350),
        (1090, 850, 1160, 350),
        (2370, 850, 1230, 350),
        (3600, 850, 1420, 350),
        (5160, 850, 1240, 350),
        (420, 745, 170, 22),
        (690, 650, 170, 22),
        (1240, 760, 230, 22),
        (1580, 665, 190, 22),
        (1890, 585, 210, 22),
        (2560, 730, 190, 22),
        (2820, 640, 190, 22),
        (3090, 550, 180, 22),
        (3820, 735, 220, 22),
        (4180, 650, 220, 22),
        (4540, 565, 210, 22),
        (5280, 730, 220, 22),
        (5580, 620, 190, 22),
    ],
    "resource_gate": {
        "rect": (3440, 570, 58, 280),
        "required_parts": 3,
        "terminal": (3350, 806),
    },
    "checkpoints": [
        {"id": 0, "x": 170, "y": 790, "phase": "arrival"},
        {"id": 1, "x": 1180, "y": 790, "phase": "movement_mastery"},
        {"id": 2, "x": 2500, "y": 790, "phase": "adaptive_combat"},
        {"id": 3, "x": 3720, "y": 790, "phase": "resource_gate"},
        {"id": 4, "x": 5200, "y": 790, "phase": "ascent"},
    ],
    "sentinels": [
        {"id": "survey-1", "x": 1830, "y": 810, "tier": 1},
        {"id": "survey-2", "x": 2170, "y": 810, "tier": 1},
        {"id": "warden-1", "x": 4050, "y": 810, "tier": 2},
        {"id": "warden-2", "x": 4440, "y": 810, "tier": 2},
        {"id": "warden-3", "x": 4780, "y": 810, "tier": 3},
    ],
    "collectibles": [
        ("part", 760, 610),
        ("part", 1670, 625),
        ("part", 2920, 600),
        ("book", 1980, 545),
        ("book", 4620, 525),
    ],
    "narration": [
        (180, "Descent telemetry unstable. Keep moving."),
        (1120, "The suit learns the terrain as you do."),
        (1760, "Sentinels commit before they strike. Read the light."),
        (2440, "Failure keeps the telemetry. The next attempt begins informed."),
        (3220, "Three power cells can overload the relay shield."),
        (3700, "The cells changed the fight. The route is yours now."),
        (5150, "Ascent relay online. Carry the lesson upward."),
    ],
    "ascent": {
        "trigger_x": 5200,
        "platform_x": 5480,
        "platform_y": 810,
        "duration_frames": 240,
    },
}


def validate_slice_data(data: dict = MARS_LANDING_SLICE) -> list[str]:
    """Return deterministic structural errors for authored slice content."""

    errors: list[str] = []
    required = {
        "slice_id",
        "name",
        "width",
        "height",
        "player_start",
        "goal",
        "solids",
        "resource_gate",
        "checkpoints",
        "sentinels",
        "collectibles",
        "narration",
        "ascent",
    }
    missing = sorted(required.difference(data))
    if missing:
        errors.append(f"missing keys: {missing}")
        return errors

    width = data["width"]
    height = data["height"]
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        errors.append("world dimensions must be positive integers")
        return errors

    def inside(point) -> bool:
        return len(point) == 2 and 0 <= point[0] < width and 0 <= point[1] < height

    if not inside(data["player_start"]):
        errors.append("player_start is outside the world")
    if not inside(data["goal"]):
        errors.append("goal is outside the world")

    for index, solid in enumerate(data["solids"]):
        if len(solid) != 4 or solid[2] <= 0 or solid[3] <= 0:
            errors.append(f"solid {index} is invalid")

    checkpoints = data["checkpoints"]
    checkpoint_ids = [item.get("id") for item in checkpoints]
    if checkpoint_ids != list(range(len(checkpoints))):
        errors.append("checkpoint ids must be contiguous and ordered")
    checkpoint_x = [item.get("x") for item in checkpoints]
    if checkpoint_x != sorted(checkpoint_x):
        errors.append("checkpoints must progress from left to right")
    for item in checkpoints:
        if item.get("phase") not in PHASE_ORDER:
            errors.append(f"checkpoint {item.get('id')} has unknown phase")
        if not inside((item.get("x"), item.get("y"))):
            errors.append(f"checkpoint {item.get('id')} is outside the world")

    sentinel_ids = [item.get("id") for item in data["sentinels"]]
    if len(sentinel_ids) != len(set(sentinel_ids)):
        errors.append("sentinel ids must be unique")
    for item in data["sentinels"]:
        if item.get("tier") not in {1, 2, 3}:
            errors.append(f"sentinel {item.get('id')} has invalid tier")
        if not inside((item.get("x"), item.get("y"))):
            errors.append(f"sentinel {item.get('id')} is outside the world")

    gate = data["resource_gate"]
    gate_rect = gate.get("rect", ())
    if len(gate_rect) != 4 or gate_rect[2] <= 0 or gate_rect[3] <= 0:
        errors.append("resource gate rect is invalid")
    if gate.get("required_parts") != 3:
        errors.append("resource gate must require exactly three committed power cells")
    if not inside(gate.get("terminal", ())):
        errors.append("resource gate terminal is outside the world")

    ascent = data["ascent"]
    if ascent.get("duration_frames", 0) < 120:
        errors.append("ascent spectacle is too short")
    if not 0 <= ascent.get("trigger_x", -1) < width:
        errors.append("ascent trigger is outside the world")

    return errors
