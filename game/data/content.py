"""Stable content-key catalog for switchable narrative identity.

Gameplay and save data continue to use chapter ids and semantic system state. This
module is the only runtime authority for player-facing text that differs between
the real-world prototype and fictionalized production track.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final

from game.data.ip_tracks import FICTIONALIZED_TRACK, REAL_WORLD_TRACK, get_identity

_CHAPTER_YEARS: Final = {
    1: "1980s",
    2: "1989–1992",
    3: "1995",
    4: "1999–2002",
    5: "2008–2010",
    6: "2006–2010",
    7: "Near Future",
    8: "Frontier",
}

_CHAPTER_PALETTES: Final = {
    1: "preoria",
    2: "canada",
    3: "campus",
    4: "corporate",
    5: "tesla",
    6: "spacex",
    7: "starship",
    8: "mars",
}

_OBJECTIVES: Final = {
    1: "Reach the far end. Collect books & parts. Survive the bullies.",
    2: "Reach the arrival point. Activate code terminals (stand near + E).",
    3: "Ship {early_startup}. Reach the end. Clear rivals. Use terminals.",
    4: "Survive the corporate arena. Reach the far platform.",
    5: "Cross the factory. Collect parts. Reach the prototype bay.",
    6: "Gather parts for the next attempt. Climb to the pad.",
    7: "Climb the sequence. Double-jump (Space again in air). Reach orbit.",
    8: "Reach the habitat site. Claim the first outpost.",
}

_NARRATION: Final = {
    1: (
        "{origin_city}. The streets are hard.",
        "Books are armor. Parts are possibility.",
        "They push. You learn to move.",
        "Resolve is forged here.",
    ),
    2: (
        "North. Cold air. Odd jobs.",
        "First terminals. Patterns in the noise.",
        "Code opens doors.",
    ),
    3: (
        "Campus nights. Ideas denser than sleep.",
        "Match the symbols. Ship the product.",
        "Time pressure. Rivals close.",
    ),
    4: (
        "Corporate pressure. Waves of rivals.",
        "Negotiate or fight. Resources shift.",
        "The arena never sleeps.",
    ),
    5: (
        "Production hell. Funding cliffs.",
        "Defend the line. Automate.",
        "The prototype is almost ready.",
    ),
    6: (
        "Each failure teaches.",
        "Assemble. Launch. Recover.",
        "Failure is progress.",
        "The pad awaits.",
    ),
    7: (
        "Board {launch_vehicle}.",
        "G-force rhythm. System triage.",
        "Leaving Earth.",
        "Orbit is a choice, not a destination.",
    ),
    8: (
        "Mars. Dust and silence.",
        "Oxygen. Power. Water.",
        "First city begins.",
        "The frontier is open.",
    ),
}

_ORIGIN_CITIES: Final = {
    REAL_WORLD_TRACK: "Pretoria",
    FICTIONALIZED_TRACK: "Solara",
}


def _format_values(track: str) -> dict[str, str]:
    identity = get_identity(track)
    return {
        "protagonist": identity["protagonist"],
        "origin_city": _ORIGIN_CITIES[track],
        **identity["organizations"],
    }


def build_content(track: str | None = None) -> dict[str, str]:
    """Build an isolated stable-key catalog for one identity track."""

    identity = get_identity(track)
    resolved_track = REAL_WORLD_TRACK if identity["protagonist"] == "Elon" else FICTIONALIZED_TRACK
    values = _format_values(resolved_track)
    title_parts = identity["game_title"].split(": ", 1)
    short_title = title_parts[0]
    subtitle = title_parts[1] if len(title_parts) == 2 else ""

    content = {
        "game.title": identity["game_title"],
        "game.short_title": short_title,
        "game.subtitle": subtitle,
        "title.tagline": f"You are {identity['protagonist']}. Build the future.",
        "credits.you_are": f"You are {identity['protagonist']}.",
    }

    for chapter_id, chapter in identity["chapters"].items():
        prefix = f"chapter.{chapter_id}"
        content[f"{prefix}.title"] = chapter["title"]
        content[f"{prefix}.level_name"] = chapter["level_name"]
        content[f"{prefix}.subtitle"] = chapter["subtitle"]
        content[f"{prefix}.description"] = chapter["description"]
        content[f"{prefix}.year"] = _CHAPTER_YEARS[chapter_id]
        content[f"{prefix}.objective"] = _OBJECTIVES[chapter_id].format(**values)
        for index, text in enumerate(_NARRATION[chapter_id]):
            content[f"{prefix}.narration.{index}"] = text.format(**values)

    return content


def get_text(key: str, track: str | None = None) -> str:
    """Resolve one stable content key, failing closed for missing copy."""

    content = build_content(track)
    try:
        return content[key]
    except KeyError as exc:
        raise ValueError(f"Unknown content key: {key}") from exc


def build_chapters(track: str | None = None) -> list[dict]:
    """Build the chapter-select manifest from stable content keys."""

    content = build_content(track)
    chapters = []
    for chapter_id in range(1, 9):
        prefix = f"chapter.{chapter_id}"
        chapters.append(
            {
                "id": chapter_id,
                "title": content[f"{prefix}.title"],
                "subtitle": content[f"{prefix}.subtitle"],
                "year": content[f"{prefix}.year"],
                "description": content[f"{prefix}.description"],
                "palette": _CHAPTER_PALETTES[chapter_id],
                "playable": True,
            }
        )
    return chapters


def apply_level_content(levels: dict[int, dict], track: str | None = None) -> None:
    """Resolve level display copy in place without changing gameplay geometry."""

    content = build_content(track)
    for chapter_id, level in levels.items():
        prefix = f"chapter.{chapter_id}"
        level["content_keys"] = {
            "name": f"{prefix}.level_name",
            "objective": f"{prefix}.objective",
            "narration": [
                f"{prefix}.narration.{index}"
                for index, _item in enumerate(level.get("narration", []))
            ],
        }
        level["name"] = content[f"{prefix}.level_name"]
        level["objective"] = content[f"{prefix}.objective"]
        level["narration"] = [
            (trigger, content[f"{prefix}.narration.{index}"])
            for index, (trigger, _legacy_text) in enumerate(level.get("narration", []))
        ]


def build_credits_lines(track: str | None = None) -> list[tuple[str, str]]:
    """Build styled credits copy from the same stable catalog."""

    content = build_content(track)
    lines: list[tuple[str, str]] = [
        ("title", content["game.title"]),
        ("normal", ""),
        ("normal", "A narrative action game"),
        ("normal", "about resolve, iteration, and multiplanetary life."),
        ("normal", ""),
        ("emphasis", content["credits.you_are"]),
        ("normal", ""),
        ("normal", "Chapters"),
    ]
    for chapter_id in range(1, 9):
        lines.append(("normal", f"{chapter_id}  {content[f'chapter.{chapter_id}.title']}"))
    lines.extend(
        [
            ("normal", ""),
            ("normal", "Built with pure Python + Pygame"),
            ("normal", "Original art direction · procedural shapes"),
            ("normal", "No copyrighted assets"),
            ("normal", ""),
            ("emphasis", "Failure is progress."),
            ("emphasis", "The frontier is open."),
            ("normal", ""),
            ("normal", "Press Esc or Enter to return"),
        ]
    )
    return deepcopy(lines)
