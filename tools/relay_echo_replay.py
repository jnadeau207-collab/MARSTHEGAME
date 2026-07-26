#!/usr/bin/env python3
"""Deterministically verify the complete Relay Echo playable candidate path."""

from __future__ import annotations

import argparse
import json
import os
import random
import traceback
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
from game.data.relay_echo import RELAY_ECHO_CONTRACT
from game.data.relay_echo_candidate import (
    RELAY_ECHO_CANDIDATE,
    validate_relay_echo_candidate,
)
from game.scenes.relay_echo import RelayEchoScene
from tools.classic_mode_replay import NullParticles


class MemorySave(SaveData):
    """Keep production save validation while avoiding disk I/O in replay."""

    def save(self) -> bool:
        self.generation += 1
        self.last_load_source = "memory"
        self.last_error = None
        return True

    def load(self) -> bool:
        return False


class RelayReplayEngine:
    """Minimal production-compatible engine contract for Relay Echo."""

    def __init__(self) -> None:
        pygame.font.init()
        self.input = InputManager(initialize_joystick=False)
        self.particles = NullParticles()
        self.save = MemorySave()
        self.save.update_phase1_slice(
            checkpoint_id=4,
            best_phase="complete",
            completed=True,
            resource_gate_open=True,
        )
        self.save.prepare_relay_echo_attempt()
        self.save.save()
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

    def go_campaign(self) -> None:
        self.transitions.append("campaign")

    def go_title(self) -> None:
        self.transitions.append("title")


class ReferenceDriver:
    def __init__(self) -> None:
        random.seed(RELAY_ECHO_CONTRACT["deterministic_replay"]["seed"])
        self.engine = RelayReplayEngine()
        self.scene = RelayEchoScene(self.engine)
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

    def place_player(self, x: float, y: float = 780.0) -> None:
        self.scene.player.x = float(x)
        self.scene.player.y = float(y)
        self.scene.player.vx = 0.0
        self.scene.player.vy = 0.0
        self.scene.player.invuln = max(self.scene.player.invuln, 120)

    def force_player_down(self) -> None:
        self.scene.player.invuln = 0
        self.scene.player.take_damage(99)
        self.step()
        self.advance(61)
        state = self.engine.save.relay_echo
        if not self.scene.player.alive:
            raise AssertionError("Relay Echo player-down recovery did not restore the player")
        if state["failures"] != 1 or state["telemetry_insight"] != 1:
            raise AssertionError("player-down recovery did not persist retained insight")
        if state["failure_history"][0]["failure_id"] != "player_down":
            raise AssertionError("player-down evidence was not recorded")
        self.milestones.append("player_down_retained_understanding")

    def reach_relay(self) -> None:
        self.place_player(RELAY_ECHO_CANDIDATE["interactions"]["reach_x"] + 20)
        self.step()
        if self.engine.save.relay_echo["checkpoint_id"] != 1:
            raise AssertionError("Noctis Relay checkpoint did not commit")
        self.milestones.append("noctis_relay_reached")

    def collect_signal_fragments(self) -> None:
        for collectible in list(self.scene.collectibles):
            if collectible.kind != "part" or not collectible.alive:
                continue
            self.place_player(collectible.x, collectible.y)
            self.step()
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 2 or state["signal_fragments"] != 3:
            raise AssertionError("three signal fragments were not transactionally committed")
        self.milestones.append("signal_fragments_committed")

    def force_relay_overload(self) -> None:
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["triangulation_terminal"]
        self.place_player(*terminal)
        self.advance(RELAY_ECHO_CANDIDATE["interactions"]["overload_frames"] + 1)
        state = self.engine.save.relay_echo
        if state["failures"] != 2 or state["telemetry_insight"] != 2:
            raise AssertionError("relay overload did not advance retained understanding")
        if state["failure_history"][-1]["failure_id"] != "relay_overload":
            raise AssertionError("relay overload evidence was not recorded")
        if state["checkpoint_id"] != 2:
            raise AssertionError("relay overload recovered to the wrong checkpoint")
        self.milestones.append("relay_overload_retained_understanding")

    def triangulate_source(self) -> None:
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["triangulation_terminal"]
        self.place_player(*terminal)
        self.step({"interact"})
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 3 or state["echo_source"] != "subsurface_array":
            raise AssertionError("echo source triangulation did not commit")
        self.milestones.append("echo_source_triangulated")

    def breach_core(self) -> None:
        for enemy in self.scene.enemies:
            enemy.alive = False
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["breach_terminal"]
        self.place_player(*terminal)
        self.step({"interact"})
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 4 or not state["relay_core_open"]:
            raise AssertionError("relay-core breach did not commit")
        self.milestones.append("relay_core_breached")

    def align_echo(self) -> None:
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["alignment_terminal"]
        self.place_player(*terminal)
        self.step({"interact"})
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 5 or state["echo_alignment"] != "redirect":
            raise AssertionError("echo alignment did not commit")
        self.milestones.append("echo_alignment_committed")

    def extract(self) -> None:
        self.place_player(RELAY_ECHO_CANDIDATE["interactions"]["extraction_x"] + 20)
        self.step()
        state = self.engine.save.relay_echo
        if not state["completion_eligible"] or state["checkpoint_id"] != 6:
            raise AssertionError("Relay Echo extraction did not complete the candidate path")
        self.milestones.append("noctis_extraction_completed")
        self.advance(RELAY_ECHO_CANDIDATE["interactions"]["completion_frames"] + 1)
        if self.engine.transitions != ["campaign"]:
            raise AssertionError(
                f"Relay Echo completion transition mismatch: {self.engine.transitions}"
            )

    def run(self) -> dict[str, Any]:
        errors = validate_relay_echo_candidate()
        if errors:
            raise AssertionError(f"Relay Echo candidate data failed validation: {errors}")
        self.force_player_down()
        self.reach_relay()
        self.collect_signal_fragments()
        self.force_relay_overload()
        self.triangulate_source()
        self.breach_core()
        self.align_echo()
        self.extract()

        state = self.engine.save.relay_echo
        campaign = self.engine.save.campaign
        if "relay_echo" in campaign["completed_missions"]:
            raise AssertionError("playable candidate illegally completed the campaign node")
        if "phobos_vector" in campaign["unlocked_missions"]:
            raise AssertionError("playable candidate illegally unlocked Phobos Vector")

        return {
            "mission_id": self.scene.mission_id,
            "slice_id": self.scene.slice_id,
            "steps": self.steps,
            "milestones": list(self.milestones),
            "phase": self.scene.phase,
            "relay_echo": dict(state),
            "campaign": dict(campaign),
            "save_generation": self.engine.save.generation,
            "transition": list(self.engine.transitions),
            "audio_events": [entry["event"] for entry in self.engine.audio.event_log],
            "presentation_events": [
                entry["name"] for entry in self.engine.presentation.event_log
            ],
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
            "Relay Echo candidate replay is nondeterministic:\n"
            f"first={first}\nsecond={second}"
        )
    return {
        "schema_version": 1,
        "status": "pass",
        "deterministic": True,
        "candidate_only": True,
        "campaign_promoted": False,
        "reference": first,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    try:
        report = run_replay()
    except Exception as exc:
        report = {
            "schema_version": 1,
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
