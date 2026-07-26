#!/usr/bin/env python3
"""Capture repeatable Python-runtime baselines for Classic Mode scenes."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from game.scenes.level import LevelScene
from tools.classic_mode_replay import ReplayEngine


def _measure_chapter(
    chapter_id: int,
    update_frames: int,
    draw_frames: int,
) -> dict[str, float]:
    engine = ReplayEngine()

    setup_started = time.perf_counter()
    scene = LevelScene(engine, chapter_id)
    scene.on_enter()
    setup_ms = (time.perf_counter() - setup_started) * 1000.0

    scene.player.invuln = 1_000_000
    update_started = time.perf_counter()
    for _ in range(update_frames):
        scene.update(1.0)
    update_elapsed = time.perf_counter() - update_started

    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    draw_started = time.perf_counter()
    for _ in range(draw_frames):
        scene.draw(surface)
    draw_elapsed = time.perf_counter() - draw_started

    return {
        "setup_ms": setup_ms,
        "update_ms_per_frame": (update_elapsed * 1000.0) / max(1, update_frames),
        "draw_ms_per_frame": (draw_elapsed * 1000.0) / max(1, draw_frames),
    }


def capture_baseline(
    update_frames: int = 120,
    draw_frames: int = 10,
    rounds: int = 3,
) -> dict[str, Any]:
    if update_frames < 1 or draw_frames < 1 or rounds < 1:
        raise ValueError("update_frames, draw_frames, and rounds must all be positive")

    pygame.init()
    try:
        chapters: list[dict[str, Any]] = []
        for chapter_id in range(1, 9):
            samples = [
                _measure_chapter(chapter_id, update_frames, draw_frames) for _ in range(rounds)
            ]
            chapters.append(
                {
                    "chapter_id": chapter_id,
                    "setup_ms_median": statistics.median(s["setup_ms"] for s in samples),
                    "update_ms_per_frame_median": statistics.median(
                        s["update_ms_per_frame"] for s in samples
                    ),
                    "draw_ms_per_frame_median": statistics.median(
                        s["draw_ms_per_frame"] for s in samples
                    ),
                }
            )
    finally:
        pygame.quit()

    return {
        "schema_version": 1,
        "git_sha": os.getenv("GITHUB_SHA", "local"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "parameters": {
            "update_frames": update_frames,
            "draw_frames": draw_frames,
            "rounds": rounds,
        },
        "chapters": chapters,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-frames", type=int, default=120)
    parser.add_argument("--draw-frames", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = capture_baseline(args.update_frames, args.draw_frames, args.rounds)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
