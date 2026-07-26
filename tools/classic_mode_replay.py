#!/usr/bin/env python3
"""Headless Classic Mode lifecycle replay for all eight chapters."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.save import SaveData
from game.data.levels import LEVELS
from game.scenes.level import LevelScene


class NeutralInput:
    """Input adapter that deliberately produces no player actions."""

    @staticmethod
    def has_buffer(_action: str) -> bool:
        return False

    @staticmethod
    def just_pressed(_action: str) -> bool:
        return False

    @staticmethod
    def consume_buffer(_action: str) -> bool:
        return False

    @staticmethod
    def is_held(_action: str) -> bool:
        return False

    @staticmethod
    def get_axis() -> tuple[int, int]:
        return 0, 0


class NullParticles:
    """Particle adapter used to exercise gameplay without a display loop."""

    @staticmethod
    def emit(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def emit_burst(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def emit_dust(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def draw(*_args: Any, **_kwargs: Any) -> None:
        return None


class MemorySave(SaveData):
    """Save state that preserves progression semantics without filesystem writes."""

    def save(self) -> bool:
        return True


class ReplayEngine:
    """Minimal engine contract required by LevelScene."""

    def __init__(self) -> None:
        pygame.font.init()
        self.input = NeutralInput()
        self.particles = NullParticles()
        self.save = MemorySave()
        self.font_sm = pygame.font.Font(None, 16)
        self.font_md = pygame.font.Font(None, 24)
        self.font_lg = pygame.font.Font(None, 40)
        self.transitions: list[dict[str, Any]] = []
        self.hit_stops: list[int] = []

    def trigger_hit_stop(self, frames: int = 4) -> None:
        self.hit_stops.append(frames)

    def start_chapter(self, chapter_id: int) -> None:
        self.transitions.append({"type": "chapter", "chapter_id": chapter_id})

    def go_credits(self) -> None:
        self.transitions.append({"type": "credits"})


def _inside_world(point: tuple[int, int], width: int, height: int) -> bool:
    x, y = point
    return 0 <= x < width and 0 <= y < height


def _validate_level_contract(chapter_id: int, data: dict[str, Any]) -> None:
    required = {
        "name",
        "width",
        "height",
        "player_start",
        "goal",
        "sky",
        "ground_col",
        "solids",
        "objective",
    }
    missing = required.difference(data)
    if missing:
        raise AssertionError(f"Chapter {chapter_id} missing keys: {sorted(missing)}")

    width = data["width"]
    height = data["height"]
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise AssertionError(f"Chapter {chapter_id} has invalid world dimensions")
    if not _inside_world(data["player_start"], width, height):
        raise AssertionError(f"Chapter {chapter_id} player_start is outside the world")
    if not _inside_world(data["goal"], width, height):
        raise AssertionError(f"Chapter {chapter_id} goal is outside the world")

    for index, solid in enumerate(data["solids"]):
        if len(solid) != 4 or solid[2] <= 0 or solid[3] <= 0:
            raise AssertionError(f"Chapter {chapter_id} solid {index} is invalid: {solid}")


def run_replay() -> dict[str, Any]:
    """Instantiate, complete, and transition through every Classic Mode chapter."""

    expected_ids = list(range(1, 9))
    if sorted(LEVELS) != expected_ids:
        raise AssertionError(f"Classic Mode chapter ids changed: {sorted(LEVELS)}")

    pygame.init()
    engine = ReplayEngine()
    chapter_results: list[dict[str, Any]] = []

    try:
        for chapter_id in expected_ids:
            data = LEVELS[chapter_id]
            _validate_level_contract(chapter_id, data)

            scene = LevelScene(engine, chapter_id)
            scene.on_enter()
            initial_counts = {
                "solids": len(scene.solids),
                "enemies": len(scene.enemies),
                "collectibles": len(scene.collectibles),
                "narration": len(scene.narration_queue),
            }

            if scene.player is None or scene.goal_rect is None:
                raise AssertionError(f"Chapter {chapter_id} failed to initialize")
            if len(scene.solids) != len(data["solids"]):
                raise AssertionError(f"Chapter {chapter_id} lost collision geometry during load")

            scene.player.x = float(scene.goal_rect.x)
            scene.player.y = float(scene.goal_rect.y)
            scene.player.vx = 0.0
            scene.player.vy = 0.0
            scene.player.invuln = 10_000
            scene.update(0.0)
            if not scene.won:
                raise AssertionError(f"Chapter {chapter_id} goal collision did not complete")

            scene.dead_timer = 91
            scene.update(0.0)
            if engine.save.chapter_completed != chapter_id:
                raise AssertionError(f"Chapter {chapter_id} did not persist completion")

            expected_transition = (
                {"type": "credits"}
                if chapter_id == 8
                else {"type": "chapter", "chapter_id": chapter_id + 1}
            )
            if engine.transitions[-1] != expected_transition:
                raise AssertionError(
                    f"Chapter {chapter_id} transition mismatch: {engine.transitions[-1]}"
                )

            chapter_results.append(
                {
                    "chapter_id": chapter_id,
                    "name": data["name"],
                    "world": [data["width"], data["height"]],
                    "counts": initial_counts,
                    "goal_completed": True,
                    "transition": expected_transition,
                }
            )
    finally:
        pygame.quit()

    return {
        "classic_mode_chapters": expected_ids,
        "chapter_results": chapter_results,
        "completed_through": engine.save.chapter_completed,
        "unlocked_through": engine.save.chapter_unlocked,
        "transitions": engine.transitions,
        "status": "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="Optional path for the replay report")
    args = parser.parse_args()

    report = run_replay()
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
