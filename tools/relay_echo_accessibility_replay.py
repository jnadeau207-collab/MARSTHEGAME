#!/usr/bin/env python3
"""Prove Relay Echo keyboard/gamepad parity and its accessibility path."""

from __future__ import annotations

import argparse
import json
import os
import random
import traceback
from copy import deepcopy
from pathlib import Path
from typing import Any

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.accessibility import normalize_runtime_settings
from game.core.input import InputManager
from game.core.input_profiles import (
    INPUT_PROFILE_GAMEPAD,
    INPUT_PROFILE_KEYBOARD,
    INPUT_PROFILES,
    REQUIRED_GAMEPLAY_ACTIONS,
    input_frame,
    validate_input_profiles,
)
from game.core.presentation import PresentationDirector
from game.data.relay_echo import RELAY_ECHO_CONTRACT
from game.data.relay_echo_candidate import RELAY_ECHO_CANDIDATE
from game.scenes.relay_echo_accessible import AccessibleRelayEchoScene
from tools.relay_echo_replay import ReferenceDriver, RelayReplayEngine

_STANDARD_SETTINGS = normalize_runtime_settings({})
_ACCESSIBLE_SETTINGS = normalize_runtime_settings(
    {
        "accessibility": {
            "assist_mode": True,
            "reduced_motion": True,
            "screen_shake": 0.0,
            "hit_stop": 0.5,
            "flash_intensity": 0.2,
            "subtitles": True,
            "subtitle_background": True,
            "subtitle_scale": 1.5,
            "high_contrast": True,
            "hold_assist": True,
        }
    }
)


class ParityReplayEngine(RelayReplayEngine):
    def __init__(self, settings: dict[str, Any]) -> None:
        super().__init__()
        self.settings = normalize_runtime_settings(deepcopy(settings))
        self.presentation = PresentationDirector(self.settings)


class ParityDriver(ReferenceDriver):
    """Run the production candidate through a concrete device profile."""

    def __init__(
        self,
        profile: str,
        settings: dict[str, Any],
        *,
        hold_interactions: bool = False,
    ) -> None:
        random.seed(RELAY_ECHO_CONTRACT["deterministic_replay"]["seed"])
        self.profile = profile
        self.hold_interactions = hold_interactions
        self.engine = ParityReplayEngine(settings)
        self.scene = AccessibleRelayEchoScene(self.engine)
        self.scene.on_enter()
        self.steps = 0
        self.milestones: list[str] = []

    def step(self, actions=()) -> None:
        semantic_actions = tuple(actions)
        self.engine.input.update_from_actions(input_frame(self.profile, *semantic_actions))
        self.scene.update(1.0)
        self.engine.audio.observe(self.scene)
        self.engine.presentation.observe(self.scene)
        self.engine.audio.update(1.0)
        self.engine.presentation.update(1.0)
        self.steps += 1

    def _hold_into_interaction(self, point: tuple[int, int], *, offset_x: float = 0.0) -> None:
        self.place_player(120.0, 780.0)
        self.step({"interact"})
        self.place_player(point[0] + offset_x, point[1])
        self.step({"interact"})
        self.step()

    def force_relay_overload(self) -> None:
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["triangulation_terminal"]
        self.place_player(*terminal)
        frames = self.scene.accessibility.overload_frames(
            int(RELAY_ECHO_CANDIDATE["interactions"]["overload_frames"])
        )
        self.advance(frames + 1)
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
        if self.hold_interactions:
            base_radius = RELAY_ECHO_CANDIDATE["interactions"]["interaction_radius"][0]
            self._hold_into_interaction(terminal, offset_x=float(base_radius + 12))
        else:
            self.place_player(*terminal)
            self.tap("interact")
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 3 or state["echo_source"] != "subsurface_array":
            raise AssertionError("echo source triangulation did not commit")
        self.milestones.append("echo_source_triangulated")

    def breach_core(self) -> None:
        for enemy in self.scene.enemies:
            enemy.alive = False
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["breach_terminal"]
        if self.hold_interactions:
            self._hold_into_interaction(terminal)
        else:
            self.place_player(*terminal)
            self.tap("interact")
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 4 or not state["relay_core_open"]:
            raise AssertionError("relay-core breach did not commit")
        self.milestones.append("relay_core_breached")

    def align_echo(self) -> None:
        terminal = RELAY_ECHO_CANDIDATE["interactions"]["alignment_terminal"]
        if self.hold_interactions:
            self._hold_into_interaction(terminal)
        else:
            self.place_player(*terminal)
            self.tap("interact")
        state = self.engine.save.relay_echo
        if state["checkpoint_id"] != 5 or state["echo_alignment"] != "redirect":
            raise AssertionError("echo alignment did not commit")
        self.milestones.append("echo_alignment_committed")

    def run(self) -> dict[str, Any]:
        result = super().run()
        result["input_profile"] = self.profile
        result["accessibility"] = self.scene.accessibility_evidence()
        return result


def _probe_profile(profile: str) -> dict[str, bool]:
    manager = InputManager(initialize_joystick=False)
    evidence: dict[str, bool] = {}
    for action in REQUIRED_GAMEPLAY_ACTIONS:
        manager.update_from_actions(input_frame(profile, action))
        evidence[action] = manager.just_pressed(action) and manager.is_held(action)
        manager.update_from_actions(())
        evidence[f"{action}_released"] = manager.just_released(action)
    return evidence


def _canonical_outcome(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "milestones": result["milestones"],
        "phase": result["phase"],
        "relay_echo": result["relay_echo"],
        "campaign": result["campaign"],
        "transition": result["transition"],
        "audio_events": result["audio_events"],
        "presentation_events": result["presentation_events"],
    }


def _run_twice(
    profile: str,
    settings: dict[str, Any],
    *,
    hold_interactions: bool = False,
) -> dict[str, Any]:
    first = ParityDriver(
        profile,
        settings,
        hold_interactions=hold_interactions,
    ).run()
    second = ParityDriver(
        profile,
        settings,
        hold_interactions=hold_interactions,
    ).run()
    if first != second:
        raise AssertionError(
            f"Relay Echo {profile} replay is nondeterministic:\nfirst={first}\nsecond={second}"
        )
    return first


def run_replay() -> dict[str, Any]:
    profile_errors = validate_input_profiles()
    if profile_errors:
        raise AssertionError(f"input profiles failed validation: {profile_errors}")

    pygame.init()
    try:
        standard = {
            profile: _run_twice(profile, _STANDARD_SETTINGS) for profile in INPUT_PROFILES
        }
        accessible = _run_twice(
            INPUT_PROFILE_GAMEPAD,
            _ACCESSIBLE_SETTINGS,
            hold_interactions=True,
        )
    finally:
        pygame.quit()

    keyboard_outcome = _canonical_outcome(standard[INPUT_PROFILE_KEYBOARD])
    gamepad_outcome = _canonical_outcome(standard[INPUT_PROFILE_GAMEPAD])
    accessible_outcome = _canonical_outcome(accessible)
    if keyboard_outcome != gamepad_outcome:
        raise AssertionError(
            "keyboard/gamepad Relay Echo outcomes diverged:\n"
            f"keyboard={keyboard_outcome}\ngamepad={gamepad_outcome}"
        )
    if accessible_outcome != keyboard_outcome:
        raise AssertionError(
            "accessibility path changed the committed Relay Echo outcome:\n"
            f"standard={keyboard_outcome}\naccessible={accessible_outcome}"
        )

    profile_probes = {profile: _probe_profile(profile) for profile in INPUT_PROFILES}
    if not all(all(evidence.values()) for evidence in profile_probes.values()):
        raise AssertionError(f"input profile semantic probe failed: {profile_probes}")

    accessible_evidence = accessible["accessibility"]
    base_radius = tuple(RELAY_ECHO_CANDIDATE["interactions"]["interaction_radius"])
    base_overload = int(RELAY_ECHO_CANDIDATE["interactions"]["overload_frames"])
    if tuple(accessible_evidence["effective_interaction_radius"]) <= base_radius:
        raise AssertionError("assist mode did not increase interaction radius")
    if accessible_evidence["effective_overload_frames"] <= base_overload:
        raise AssertionError("assist mode did not extend the overload window")
    if accessible_evidence["camera_shake_scale"] != 0.0:
        raise AssertionError("reduced motion did not disable camera shake")
    if not accessible_evidence["hold_toggle_alternatives"]:
        raise AssertionError("hold/toggle alternative was not active")
    if not accessible_evidence["high_contrast_objectives"]:
        raise AssertionError("high-contrast objective mode was not active")
    if not accessible_evidence["subtitle_background"]:
        raise AssertionError("subtitle background was not active")
    if any(entry["shake"] != 0.0 for entry in accessible["presentation_detail"]):
        raise AssertionError("reduced-motion replay emitted camera shake")

    return {
        "schema_version": 1,
        "status": "pass",
        "deterministic": True,
        "input_parity": True,
        "accessibility_path_verified": True,
        "campaign_promoted": False,
        "profiles": standard,
        "profile_probes": profile_probes,
        "accessibility": accessible,
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
