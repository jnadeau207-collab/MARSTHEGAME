"""Dual-track narrative identity registry.

The real-world track preserves the current non-commercial prototype. The
fictionalized track provides structurally equivalent original names so content
can switch identity without gameplay or level-architecture changes.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Final

IP_TRACK_ENV: Final = "STARMAN_IP_TRACK"
REAL_WORLD_TRACK: Final = "real_world"
FICTIONALIZED_TRACK: Final = "fictionalized"
DEFAULT_IP_TRACK: Final = REAL_WORLD_TRACK

_TRACKS: Final = {
    REAL_WORLD_TRACK: {
        "game_title": "STARMAN: An Elon Odyssey",
        "protagonist": "Elon",
        "organizations": {
            "early_startup": "Zip2",
            "payments_one": "X.com",
            "payments_two": "PayPal",
            "automotive": "Tesla",
            "spaceflight": "SpaceX",
            "launch_vehicle": "Starship",
        },
        "chapters": {
            1: {
                "title": "Pretoria Streets",
                "level_name": "Pretoria Streets",
                "subtitle": "Grit & Resolve",
                "description": (
                    "Young Elon. School bullying. Street survival. Books and parts become "
                    "weapons of the mind."
                ),
            },
            2: {
                "title": "Crossing",
                "level_name": "Crossing — Canada",
                "subtitle": "Canada & Arrival",
                "description": (
                    "Travel, odd jobs, first terminals. Timing and early code unlock the path "
                    "forward."
                ),
            },
            3: {
                "title": "College & Zip2",
                "level_name": "College & Zip2",
                "subtitle": "Ship the Product",
                "description": (
                    "Campus nights and startup pressure. Symbol matching, pipelines, time pressure."
                ),
            },
            4: {
                "title": "X.com / PayPal Wars",
                "level_name": "X.com / PayPal Wars",
                "subtitle": "Corporate Arena",
                "description": (
                    "Rival waves and negotiation choices. Resources shift with every decision."
                ),
            },
            5: {
                "title": "Tesla Factory Floor",
                "level_name": "Tesla Factory Floor",
                "subtitle": "Production Hell",
                "description": "Automation puzzles, defending the line, prototype unlock.",
            },
            6: {
                "title": "SpaceX: Failures Before Flight",
                "level_name": "SpaceX Workshop",
                "subtitle": "Each Boom Teaches",
                "description": "Assembly, launch windows, recovery. Failure is progress.",
            },
            7: {
                "title": "Starship to Mars",
                "level_name": "Starship Ascent",
                "subtitle": "Leaving Earth",
                "description": "Docking sequences, G-force rhythm, system triage. Spectacle.",
            },
            8: {
                "title": "Mars Colony",
                "level_name": "Mars Colony",
                "subtitle": "First City",
                "description": "Land, survive, expand. Oxygen, power, water. Open frontier.",
            },
        },
    },
    FICTIONALIZED_TRACK: {
        "game_title": "STARFORGE: An Elias Voss Odyssey",
        "protagonist": "Elias Voss",
        "organizations": {
            "early_startup": "LinkForge",
            "payments_one": "PulseNet",
            "payments_two": "VaultPay",
            "automotive": "Helios Motors",
            "spaceflight": "AstraForge",
            "launch_vehicle": "Vanguard",
        },
        "chapters": {
            1: {
                "title": "Solara Streets",
                "level_name": "Solara Streets",
                "subtitle": "Grit & Resolve",
                "description": (
                    "Young Elias. School bullying. Street survival. Books and parts become "
                    "weapons of the mind."
                ),
            },
            2: {
                "title": "Northern Crossing",
                "level_name": "Northern Crossing",
                "subtitle": "Arrival & Reinvention",
                "description": (
                    "Travel, odd jobs, first terminals. Timing and early code unlock the path "
                    "forward."
                ),
            },
            3: {
                "title": "College & LinkForge",
                "level_name": "College & LinkForge",
                "subtitle": "Ship the Product",
                "description": (
                    "Campus nights and startup pressure. Symbol matching, pipelines, time pressure."
                ),
            },
            4: {
                "title": "PulseNet / VaultPay Wars",
                "level_name": "PulseNet / VaultPay Wars",
                "subtitle": "Corporate Arena",
                "description": (
                    "Rival waves and negotiation choices. Resources shift with every decision."
                ),
            },
            5: {
                "title": "Helios Factory Floor",
                "level_name": "Helios Factory Floor",
                "subtitle": "Production Hell",
                "description": "Automation puzzles, defending the line, prototype unlock.",
            },
            6: {
                "title": "AstraForge: Failures Before Flight",
                "level_name": "AstraForge Workshop",
                "subtitle": "Each Failure Teaches",
                "description": "Assembly, launch windows, recovery. Failure is progress.",
            },
            7: {
                "title": "Vanguard to Mars",
                "level_name": "Vanguard Ascent",
                "subtitle": "Leaving Earth",
                "description": "Docking sequences, G-force rhythm, system triage. Spectacle.",
            },
            8: {
                "title": "Mars Colony",
                "level_name": "Mars Colony",
                "subtitle": "First City",
                "description": "Land, survive, expand. Oxygen, power, water. Open frontier.",
            },
        },
    },
}


def resolve_ip_track(value: str | None = None) -> str:
    """Resolve and validate the active narrative identity track."""

    requested = (value or os.getenv(IP_TRACK_ENV, DEFAULT_IP_TRACK)).strip().lower()
    if requested not in _TRACKS:
        valid = ", ".join(sorted(_TRACKS))
        raise ValueError(f"Unknown {IP_TRACK_ENV}={requested!r}; expected one of: {valid}")
    return requested


def get_identity(track: str | None = None) -> dict:
    """Return an isolated copy of the selected identity registry."""

    return deepcopy(_TRACKS[resolve_ip_track(track)])


def get_chapter_identity(chapter_id: int, track: str | None = None) -> dict:
    """Return identity metadata for one of the eight Classic Mode chapters."""

    identity = get_identity(track)
    try:
        return identity["chapters"][chapter_id]
    except KeyError as exc:
        raise ValueError(f"Unknown chapter id: {chapter_id}") from exc
