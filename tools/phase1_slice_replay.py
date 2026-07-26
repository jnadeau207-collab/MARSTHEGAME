#!/usr/bin/env python3
"""Deterministically verify the complete Phase 1 Mars-landing journey."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.audio import AudioDirector
from game.core.input import InputManager
from game.core.presentation import PresentationDirector
from game.core.save import SaveData
from game.data.phase1_slice import MARS_LANDING_SLICE, validate_slice_data
from game.scenes.vertical_slice import VerticalSliceScene
from tools.classic_mode_replay import NullParticles


class MemorySave(SaveData):
    """Keep transactional save semantics in memory during deterministic replay."""

    def save(self) -> bool:
        self.generation += 1
        self.last_load_source = "memory"
        self.last_error = None
        return True

    def load(self) -> bool:
        return False


class SliceReplayEngine:
    """Minimal production-compatible engine contract for the vertical slice."""

    def __init__(self) -> None:
        pygame.font.init()
        self.input = InputManager(initialize_joystick=False)
        self.particles = NullParticles()
        self.save = MemorySave()
        self.audio = AudioDirector(enabled=False)
        self.presentation = PresentationDirector()
        self.font_sm = pygame.font.Font(None, 16)
        self.font_md = pygame.font.Font(None, 24)
        self.font_lg = pygame.font.Font(None, 40)
        self.font_xl = pygame.font.Font(None, 56)
        self.transitions: list[str] = []
        self.hit_stops: list[int] = []

    def trigger_hit_stop(self, frames: int = 4) -> None:
        self.hit_stops.append(frames)

    def go_title(self) -> None:
        self.transitions.append("title")


class ReferenceDriver:
    def __init__(self) -> None:
        random.seed(1_048_583)
        self.engine = SliceReplayEngine()
        self.scene = VerticalSliceScene(self.engine)
        self.scene.on_enter()
        self.steps = 0
        self.milestones: list[str] = []

    def step(self, actions=()) -> None:
        self.engine.input.update_from_actions(actions)
        self.scene.update(1.0)
        self.engine.audio.observe(self.scene)
        self.engine.presentation.observe(self.scene)
        self.engine.audio.update(1.0)
        self.engine.presentation.update(1.0)
        self.steps += 1

    def advance(self, frames: int, actions=()) -> None:
        for _ in range(frames):
            self.step(actions)

    def place_player(self, x: float, y: float = 790.0) -> None:
        self.scene.player.x = float(x)
        self.scene.player.y = float(y)
        self.scene.player.vx = 0.0
        self.scene.player.vy = 0.0
        self.scene.player.invuln = max(self.scene.player.invuln, 120)

    def collect_power_cells(self) -> None:
        for collectible in list(self.scene.collectibles):
            if collectible.kind != "part" or not collectible.alive:
                continue
            self.place_player(collectible.x, collectible.y)
            self.step()
            if self.scene.player.parts >= self.scene.required_parts:
                break
        if self.scene.player.parts != self.scene.required_parts:
            raise AssertionError("reference path did not collect all committed power cells")
        self.milestones.append("power_cells_collected")

    def force_failure_and_recover(self) -> None:
        self.scene.player.invuln = 0
        self.scene.player.take_damage(99)
        self.step()
        self.advance(61)
        if not self.scene.player.alive or self.scene.failure_count != 1:
            raise AssertionError("failure did not recover with retained telemetry")
        if self.scene.insight_level != 1:
            raise AssertionError("failure did not increase telemetry insight")
        if self.scene.player.parts != self.scene.required_parts:
            raise AssertionError("failure discarded committed power-cell progress")
        self.milestones.append("failure_advanced_understanding")

    def disrupt_relay(self) -> None:
        tx, ty = self.scene.resource_terminal
        self.place_player(tx, ty)
        self.step({"interact"})
        self.step()
        if not self.scene.resource_gate_open:
            raise AssertionError("relay shield did not open after three power cells")
        final_wardens = [enemy for enemy in self.scene.enemies if enemy.spawn_x >= 3800]
        if not all(enemy.resource_disrupted for enemy in final_wardens):
            raise AssertionError("relay disruption did not alter the final encounter")
        self.milestones.append("resource_changed_final_encounter")

    def defeat_final_wardens(self) -> None:
        for sentinel in [enemy for enemy in self.scene.enemies if enemy.spawn_x >= 3800]:
            while sentinel.alive:
                sentinel.state = "recover"
                sentinel.timer = 0.0
                sentinel.vx = 0.0
                sentinel.vy = 0.0
                self.place_player(sentinel.x - self.scene.player.w, sentinel.y)
                self.scene.player.facing = 1
                self.scene.player.attack_cooldown = 0
                self.step({"attack"})
                self.step()
        if not self.scene._final_wardens_defeated():
            raise AssertionError("reference path did not defeat the final wardens")
        self.milestones.append("adaptive_combat_completed")

    def run(self) -> dict[str, Any]:
        errors = validate_slice_data()
        if errors:
            raise AssertionError(f"slice data failed validation: {errors}")

        self.advance(151)
        if self.scene.phase != "movement_mastery":
            raise AssertionError("arrival did not transition to movement mastery")
        self.milestones.append("cinematic_arrival_completed")

        self.place_player(1200)
        self.step()
        if self.scene.current_checkpoint < 1:
            raise AssertionError("movement checkpoint was not committed")
        self.milestones.append("movement_mastery_reached")

        self.collect_power_cells()
        self.place_player(2500)
        self.step()
        if self.scene.current_checkpoint < 2:
            raise AssertionError("combat checkpoint was not committed")

        self.force_failure_and_recover()
        self.disrupt_relay()
        self.place_player(3720)
        self.step()
        if self.scene.current_checkpoint < 3:
            raise AssertionError("resource checkpoint was not committed")

        self.defeat_final_wardens()
        self.place_player(MARS_LANDING_SLICE["ascent"]["trigger_x"])
        self.step()
        if not self.scene.ascent_active:
            raise AssertionError("ascent did not start after the final arena")
        self.milestones.append("ascent_started")

        self.advance(MARS_LANDING_SLICE["ascent"]["duration_frames"] + 1)
        if not self.scene.slice_complete:
            raise AssertionError("ascent did not complete the slice")
        if not self.engine.save.phase1_slice["completed"]:
            raise AssertionError("slice completion was not persisted")
        self.milestones.append("resolved_ending_beat")

        self.advance(301)
        if self.engine.transitions != ["title"]:
            raise AssertionError(f"slice transition mismatch: {self.engine.transitions}")

        return {
            "slice_id": self.scene.slice_id,
            "steps": self.steps,
            "milestones": self.milestones,
            "phase": self.scene.phase,
            "checkpoint": self.scene.current_checkpoint,
            "failures": self.scene.failure_count,
            "insight": self.scene.insight_level,
            "resource_gate_open": self.scene.resource_gate_open,
            "sentinels_alive": [enemy.sentinel_id for enemy in self.scene.enemies if enemy.alive],
            "save": dict(self.engine.save.phase1_slice),
            "save_generation": self.engine.save.generation,
            "transition": list(self.engine.transitions),
            "audio_events": [entry["event"] for entry in self.engine.audio.event_log],
            "presentation_events": [entry["name"] for entry in self.engine.presentation.event_log],
        }


def run_replay() -> dict[str, Any]:
    pygame.init()
    try:
        first = ReferenceDriver().run()
        second = ReferenceDriver().run()
    finally:
        pygame.quit()
    if first != second:
        raise AssertionError(
            f"Phase 1 slice replay is nondeterministic:\nfirst={first}\nsecond={second}"
        )
    return {
        "schema_version": 1,
        "status": "pass",
        "deterministic": True,
        "reference": first,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
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
