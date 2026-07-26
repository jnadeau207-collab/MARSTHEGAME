from __future__ import annotations

import copy
import unittest
from pathlib import Path

from game.core.campaign import CAMPAIGN_GRAPH, CampaignStateError
from game.core.relay_echo_promotion import (
    RelayEchoPromotionError,
    complete_relay_echo_campaign,
    prepare_relay_echo_launch,
)
from game.core.save import SaveData
from game.data.campaign import MISSION_STATUS_IMPLEMENTED, MISSION_STATUS_PLANNED
from game.scenes.campaign import CampaignScene

ROOT = Path(__file__).resolve().parents[1]


class SilentDirector:
    def play(self, *_args, **_kwargs) -> None:
        pass

    def cue(self, *_args, **_kwargs) -> None:
        pass


class FakeCampaignEngine:
    def __init__(self, save: SaveData) -> None:
        self.save = save
        self.audio = SilentDirector()
        self.presentation = SilentDirector()
        self.started: list[str] = []

    def start_campaign_mission(self, mission_id: str) -> None:
        self.started.append(mission_id)

    def go_title(self) -> None:
        pass


class RelayEchoPromotionTests(unittest.TestCase):
    def make_unlocked_save(self) -> SaveData:
        save = SaveData()
        save.update_phase1_slice(
            checkpoint_id=4,
            best_phase="complete",
            completed=True,
            resource_gate_open=True,
        )
        return save

    def prepare_final_objective(self) -> SaveData:
        save = self.make_unlocked_save()
        prepare_relay_echo_launch(save)
        objectives = (
            ("reach_noctis_relay", {}),
            ("recover_signal_fragments", {"signal_fragments": 3}),
            ("triangulate_echo_source", {"echo_source": "subsurface_array"}),
            ("breach_relay_core", {"relay_core_open": True}),
            ("align_the_echo", {"echo_alignment": "redirect"}),
        )
        for objective_id, evidence in objectives:
            save.complete_relay_echo_objective(objective_id, evidence)
        return save

    def test_catalog_promotes_only_relay_echo(self) -> None:
        relay = CAMPAIGN_GRAPH.mission("relay_echo")
        phobos = CAMPAIGN_GRAPH.mission("phobos_vector")
        self.assertEqual(relay["status"], MISSION_STATUS_IMPLEMENTED)
        self.assertEqual(relay["entrypoint"], "relay_echo")
        self.assertEqual(phobos["status"], MISSION_STATUS_PLANNED)
        self.assertIsNone(phobos["entrypoint"])
        self.assertEqual(
            CAMPAIGN_GRAPH.playable_mission_ids(("ares_reach",)),
            ("ares_reach", "relay_echo"),
        )

    def test_launch_prepares_campaign_and_mission_together(self) -> None:
        save = self.make_unlocked_save()
        transition = prepare_relay_echo_launch(save)
        self.assertEqual(transition["event"], "relay_echo_launch_prepared")
        self.assertEqual(transition["campaign"]["event"], "attempt_started")
        self.assertEqual(transition["relay_echo"]["event"], "attempt_prepared")
        self.assertEqual(save.campaign["attempts"]["relay_echo"], 1)
        self.assertEqual(save.campaign["current_mission"], "relay_echo")
        self.assertEqual(save.relay_echo["attempts"], 1)
        self.assertTrue(save.relay_echo["active"])

    def test_active_attempt_resumes_without_incrementing_relay_attempt(self) -> None:
        save = self.make_unlocked_save()
        first = prepare_relay_echo_launch(save)
        second = prepare_relay_echo_launch(save)
        self.assertEqual(first["relay_echo"]["event"], "attempt_prepared")
        self.assertEqual(second["relay_echo"]["event"], "attempt_resumed")
        self.assertEqual(save.relay_echo["attempts"], 1)
        self.assertEqual(save.campaign["attempts"]["relay_echo"], 2)

    def test_locked_launch_fails_without_partial_mutation(self) -> None:
        save = SaveData()
        campaign = copy.deepcopy(save.campaign)
        relay = copy.deepcopy(save.relay_echo)
        with self.assertRaises(CampaignStateError):
            prepare_relay_echo_launch(save)
        self.assertEqual(save.campaign, campaign)
        self.assertEqual(save.relay_echo, relay)

    def test_completion_atomically_unlocks_phobos_vector(self) -> None:
        save = self.prepare_final_objective()
        transition = complete_relay_echo_campaign(save)
        self.assertEqual(transition["event"], "relay_echo_campaign_completed")
        self.assertEqual(transition["relay_echo"]["event"], "relay_echo_completed")
        self.assertEqual(transition["campaign"]["event"], "mission_completed")
        self.assertEqual(transition["unlocked_mission"], "phobos_vector")
        self.assertTrue(save.relay_echo["completion_eligible"])
        self.assertEqual(
            save.campaign["completed_missions"],
            ["ares_reach", "relay_echo"],
        )
        self.assertIn("phobos_vector", save.campaign["unlocked_missions"])
        self.assertEqual(save.campaign["current_mission"], "phobos_vector")

    def test_premature_completion_fails_without_partial_mutation(self) -> None:
        save = self.make_unlocked_save()
        prepare_relay_echo_launch(save)
        campaign = copy.deepcopy(save.campaign)
        relay = copy.deepcopy(save.relay_echo)
        with self.assertRaisesRegex(Exception, "current Relay Echo objective"):
            complete_relay_echo_campaign(save)
        self.assertEqual(save.campaign, campaign)
        self.assertEqual(save.relay_echo, relay)

    def test_completed_state_cannot_silently_start_unsupported_replay(self) -> None:
        save = self.prepare_final_objective()
        complete_relay_echo_campaign(save)
        campaign = copy.deepcopy(save.campaign)
        relay = copy.deepcopy(save.relay_echo)
        with self.assertRaises(RelayEchoPromotionError):
            prepare_relay_echo_launch(save)
        self.assertEqual(save.campaign, campaign)
        self.assertEqual(save.relay_echo, relay)

    def test_campaign_scene_does_not_launch_completed_mission(self) -> None:
        save = self.prepare_final_objective()
        complete_relay_echo_campaign(save)
        engine = FakeCampaignEngine(save)
        scene = CampaignScene(engine)
        scene.selected = scene.mission_ids.index("relay_echo")
        scene._activate()
        self.assertEqual(engine.started, [])
        self.assertIn("REPLAY TRANSACTION", scene.message)

    def test_engine_routes_promoted_scene_and_combined_launch(self) -> None:
        source = (ROOT / "game/core/engine.py").read_text(encoding="utf-8")
        self.assertIn("prepare_relay_echo_launch", source)
        self.assertIn("PromotedRelayEchoScene", source)
        self.assertIn('entrypoint not in {"vertical_slice", "relay_echo"}', source)


if __name__ == "__main__":
    unittest.main()
