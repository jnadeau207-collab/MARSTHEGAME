#!/usr/bin/env python3
"""Capture repeatable Python-runtime baselines for Classic Mode scenes."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
import traceback
from pathlib import Path
from typing import Any

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.save import SaveData
from game.core.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from game.scenes.level import LevelScene


class NeutralInput:
    """Production-compatible input adapter that emits no actions."""

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
    """Particle adapter used to benchmark scene work without a display loop."""

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
    """Save state that preserves runtime contracts without filesystem writes."""

    def save(self) -> bool:
        return True


class BenchmarkEngine:
    """Minimal engine contract required by LevelScene during measurement."""

    def __init__(self) -> None:
        pygame.font.init()
        self.input = NeutralInput()
        self.particles = NullParticles()
        self.save = MemorySave()
        self.font_sm = pygame.font.Font(None, 16)
        self.font_md = pygame.font.Font(None, 24)
        self.font_lg = pygame.font.Font(None, 40)
        self.hit_stops: list[int] = []

    def trigger_hit_stop(self, frames: int = 4) -> None:
        self.hit_stops.append(frames)

    @staticmethod
    def start_chapter(_chapter_id: int) -> None:
        return None

    @staticmethod
    def go_credits() -> None:
        return None


def _measure_chapter(
    chapter_id: int,
    update_frames: int,
    draw_frames: int,
) -> dict[str, float]:
    engine = BenchmarkEngine()

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
        "update_ms_per_frame": (update_elapsed * 1000.0) / update_frames,
        "draw_ms_per_frame": (draw_elapsed * 1000.0) / draw_frames,
    }


def summarize_samples(values: list[float]) -> dict[str, Any]:
    """Return robust statistics and raw samples for same-runner comparison."""

    if not values:
        raise ValueError("cannot summarize an empty sample set")
    center = statistics.median(values)
    deviations = [abs(value - center) for value in values]
    return {
        "median": center,
        "mad": statistics.median(deviations),
        "minimum": min(values),
        "maximum": max(values),
        "sample_count": len(values),
        "samples": values,
    }


def capture_baseline(
    update_frames: int = 120,
    draw_frames: int = 10,
    rounds: int = 7,
    warmup_rounds: int = 2,
) -> dict[str, Any]:
    if update_frames < 1 or draw_frames < 1 or rounds < 1:
        raise ValueError("update_frames, draw_frames, and rounds must all be positive")
    if warmup_rounds < 0:
        raise ValueError("warmup_rounds cannot be negative")

    pygame.init()
    pygame.display.set_mode((1, 1))
    try:
        chapters: list[dict[str, Any]] = []
        for chapter_id in range(1, 9):
            for _ in range(warmup_rounds):
                _measure_chapter(chapter_id, update_frames, draw_frames)

            samples = [
                _measure_chapter(chapter_id, update_frames, draw_frames)
                for _ in range(rounds)
            ]
            metrics = {
                metric: summarize_samples([sample[metric] for sample in samples])
                for metric in (
                    "setup_ms",
                    "update_ms_per_frame",
                    "draw_ms_per_frame",
                )
            }
            chapters.append(
                {
                    "chapter_id": chapter_id,
                    "metrics": metrics,
                    "setup_ms_median": metrics["setup_ms"]["median"],
                    "update_ms_per_frame_median": metrics["update_ms_per_frame"][
                        "median"
                    ],
                    "draw_ms_per_frame_median": metrics["draw_ms_per_frame"]["median"],
                }
            )
    finally:
        pygame.quit()

    return {
        "schema_version": 2,
        "status": "pass",
        "git_sha": os.getenv("GITHUB_SHA", "local"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "parameters": {
            "update_frames": update_frames,
            "draw_frames": draw_frames,
            "rounds": rounds,
            "warmup_rounds": warmup_rounds,
            "resolution": [SCREEN_WIDTH, SCREEN_HEIGHT],
        },
        "chapters": chapters,
    }


def _write_report(report: dict[str, Any], path: Path | None) -> str:
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-frames", type=int, default=120)
    parser.add_argument("--draw-frames", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--warmup-rounds", type=int, default=2)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = capture_baseline(
            args.update_frames,
            args.draw_frames,
            args.rounds,
            args.warmup_rounds,
        )
    except Exception as exc:
        report = {
            "schema_version": 2,
            "status": "error",
            "git_sha": os.getenv("GITHUB_SHA", "local"),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        _write_report(report, args.json_out)
        return 1

    _write_report(report, args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
