#!/usr/bin/env python3
"""Deterministically verify Relay Echo campaign launch, completion, and unlock."""

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

from game.core.accessibility import normalize_runtime_settings
from game.core.campaign import CAMPAIGN_GRAPH
from game.core.presentation import PresentationDirector
from game.core.relay_echo_promotion import prepare_relay_echo_launch
from game.core.relay_echo_state import RELAY_ECHO_RUNTIME
from game.data.campaign import MISSION_STATUS_PLANNED
from game.data.relay_echo import RELAY_ECHO_CONTRACT
from game.data.relay_echo_candidate import validate_relay_echo_candidate
from game.scenes.relay_echo_promoted import PromotedRelayEchoScene
from tools.relay_echo_replay import ReferenceDriver, RelayReplayEngine


class PromotionReplayEngine(RelayReplayEngine):
    """Prepare Relay Echo through the promoted launch transaction."""

    def __init__(self) -> None:
        super().__init__()
        self.save.relay_echo = RELAY_ECHO_RUNTIME.default_state()
        self.save.generation = 0
        self.settings = normalize_runtime_settings({})
        self.presentation = PresentationDirector(self.settings)
        self.launch_transition = prepare_relay_echo_launch(self.save)
        if not self.save.save():
            raise AssertionError(f"promotion launch did not persist: {self.save.last_error}")


class PromotionDriver(ReferenceDriver):
    def __init__(self) -> None:
        random.seed(RELAY_ECHO_CONTRACT["deterministic_replay"]["seed"])
        self.engine = PromotionReplayEngine()
        self.scene = PromotedRelayEchoScene(self.engine)
        self.scene.on_enter()
        self.steps = 0
        self.milestones: list[str] = []

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

        relay = self.engine.save.relay_echo
        campaign = self.engine.save.campaign
        relay_mission = CAMPAIGN_GRAPH.mission("relay_echo")
        phobos = CAMPAIGN_GRAPH.mission("phobos_vector")
        if not relay["completion_eligible"] or relay["checkpoint_id"] != 6:
            raise AssertionError("promoted Relay Echo did not commit mission completion")
        if campaign["completed_missions"] != ["ares_reach", "relay_echo"]:
            raise AssertionError(f"campaign completion mismatch: {campaign['completed_missions']}")
        if "phobos_vector" not in campaign["unlocked_missions"]:
            raise AssertionError("Relay Echo completion did not unlock Phobos Vector")
        if campaign["current_mission"] != "phobos_vector":
            raise AssertionError("campaign did not advance to Phobos Vector")
        if relay_mission["entrypoint"] != "relay_echo":
            raise AssertionError("Relay Echo catalog entrypoint is not promoted")
        if phobos["status"] != MISSION_STATUS_PLANNED or phobos["entrypoint"] is not None:
            raise AssertionError("Phobos Vector was incorrectly promoted")
        if self.engine.transitions != ["campaign"]:
            raise AssertionError(
                f"promoted completion transition mismatch: {self.engine.transitions}"
            )

        return {
            "mission_id": self.scene.mission_id,
            "slice_id": self.scene.slice_id,
            "steps": self.steps,
            "milestones": list(self.milestones),
            "phase": self.scene.phase,
            "launch_transition": self.engine.launch_transition,
            "completion_transition": self.scene._last_transition,
            "relay_echo": dict(relay),
            "campaign": dict(campaign),
            "save_generation": self.engine.save.generation,
            "transition": list(self.engine.transitions),
            "playable_after_completion": list(
                CAMPAIGN_GRAPH.playable_mission_ids(campaign["completed_missions"])
            ),
            "audio_events": [entry["event"] for entry in self.engine.audio.event_log],
            "presentation_events": [entry["name"] for entry in self.engine.presentation.event_log],
        }


def run_replay() -> dict[str, Any]:
    pygame.init()
    try:
        first = PromotionDriver().run()
        second = PromotionDriver().run()
    finally:
        pygame.quit()
    if first != second:
        raise AssertionError(
            f"Relay Echo promotion replay is nondeterministic:\nfirst={first}\nsecond={second}"
        )
    return {
        "schema_version": 1,
        "status": "pass",
        "deterministic": True,
        "campaign_promoted": True,
        "relay_echo_completed": True,
        "phobos_vector_unlocked": True,
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
