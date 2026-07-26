#!/usr/bin/env python3
"""Deterministically verify Relay Echo completed-mission replay/reset behavior."""

from __future__ import annotations

import argparse
import json
import os
import traceback
from copy import deepcopy
from pathlib import Path
from typing import Any

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.relay_echo_replay import prepare_relay_echo_replay
from game.scenes.relay_echo_promoted import PromotedRelayEchoScene
from tools.relay_echo_promotion_replay import PromotionDriver


def _drive_complete_path(driver: PromotionDriver) -> None:
    driver.force_player_down()
    driver.reach_relay()
    driver.collect_signal_fragments()
    driver.force_relay_overload()
    driver.triangulate_source()
    driver.breach_core()
    driver.align_echo()
    driver.extract()


def _current_run_report(driver: PromotionDriver) -> dict[str, Any]:
    return {
        "steps": driver.steps,
        "milestones": list(driver.milestones),
        "phase": driver.scene.phase,
        "relay_echo": deepcopy(driver.engine.save.relay_echo),
        "campaign": deepcopy(driver.engine.save.campaign),
        "archive": deepcopy(driver.engine.save.relay_echo_replay),
        "completion_transition": deepcopy(driver.scene._last_transition),
        "save_generation": driver.engine.save.generation,
        "transition": list(driver.engine.transitions),
    }


def run_sequence() -> dict[str, Any]:
    driver = PromotionDriver()
    first_completion = driver.run()
    first_campaign = deepcopy(driver.engine.save.campaign)
    first_relay = deepcopy(driver.engine.save.relay_echo)

    replay_preparation = prepare_relay_echo_replay(driver.engine.save)
    if not driver.engine.save.save():
        raise AssertionError(
            f"Relay Echo replay preparation did not persist: {driver.engine.save.last_error}"
        )
    archive = driver.engine.save.relay_echo_replay
    if archive["current_run_id"] != 2:
        raise AssertionError("replay preparation did not advance to run two")
    if [entry["run_id"] for entry in archive["completed_runs"]] != [1]:
        raise AssertionError("first completed run was not archived exactly once")
    if archive["completed_runs"][0]["revision"] != first_relay["revision"]:
        raise AssertionError("archived first-run revision does not match completed state")
    if driver.engine.save.campaign["completed_missions"] != first_campaign["completed_missions"]:
        raise AssertionError("replay preparation changed campaign completion history")
    if driver.engine.save.campaign["unlocked_missions"] != first_campaign["unlocked_missions"]:
        raise AssertionError("replay preparation changed campaign unlock history")

    driver.engine.transitions.clear()
    driver.scene = PromotedRelayEchoScene(driver.engine)
    driver.scene.on_enter()
    driver.steps = 0
    driver.milestones = []
    _drive_complete_path(driver)
    replay_completion = _current_run_report(driver)

    campaign = replay_completion["campaign"]
    relay = replay_completion["relay_echo"]
    archive = replay_completion["archive"]
    transition = replay_completion["completion_transition"]
    if campaign["completed_missions"] != ["ares_reach", "relay_echo"]:
        raise AssertionError("replay completion changed campaign completion history")
    if "phobos_vector" not in campaign["unlocked_missions"]:
        raise AssertionError("replay completion lost the Phobos Vector unlock")
    if campaign["current_mission"] != "phobos_vector":
        raise AssertionError("replay completion did not return campaign focus to Phobos")
    if not relay["completion_eligible"] or relay["checkpoint_id"] != 6:
        raise AssertionError("replay run did not complete the Relay Echo state path")
    if archive["current_run_id"] != 2 or len(archive["completed_runs"]) != 1:
        raise AssertionError("replay completion mutated archived-run sequencing")
    if transition["event"] != "relay_echo_replay_completed":
        raise AssertionError(f"replay completion event mismatch: {transition}")
    if transition["run_id"] != 2:
        raise AssertionError("replay completion did not identify run two")
    if replay_completion["transition"] != ["campaign"]:
        raise AssertionError(
            f"replay completion transition mismatch: {replay_completion['transition']}"
        )

    return {
        "first_completion": first_completion,
        "replay_preparation": replay_preparation,
        "replay_completion": replay_completion,
        "campaign_completion_preserved": True,
        "phobos_unlock_preserved": True,
        "archived_run_ids": [entry["run_id"] for entry in archive["completed_runs"]],
        "current_run_id": archive["current_run_id"],
    }


def run_replay() -> dict[str, Any]:
    pygame.init()
    try:
        first = run_sequence()
        second = run_sequence()
    finally:
        pygame.quit()
    if first != second:
        raise AssertionError(
            "Relay Echo replay/reset evidence is nondeterministic:\n"
            f"first={first}\nsecond={second}"
        )
    return {
        "schema_version": 1,
        "status": "pass",
        "deterministic": True,
        "completed_mission_replay": True,
        "campaign_completion_preserved": True,
        "phobos_unlock_preserved": True,
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
