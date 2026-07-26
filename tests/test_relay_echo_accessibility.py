from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.accessibility import normalize_accessibility, normalize_runtime_settings
from game.core.input import InputManager
from game.core.presentation import PresentationDirector
from game.core.relay_echo_accessibility import (
    RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS,
    relay_echo_accessibility_profile,
    validate_relay_echo_accessibility_profile,
)
from game.scenes.settings import SettingsScene
from tools.relay_echo_accessibility_replay import run_replay


class FakeAudio:
    def __init__(self) -> None:
        self.events: list[str] = []

    def play(self, event: str, strength: float = 1.0) -> None:
        self.events.append(event)


class FakeSettingsEngine:
    def __init__(self) -> None:
        pygame.font.init()
        self.settings = normalize_runtime_settings({})
        self.input = InputManager(initialize_joystick=False)
        self.presentation = PresentationDirector(self.settings)
        self.audio = FakeAudio()
        self.font_sm = pygame.font.Font(None, 16)
        self.font_md = pygame.font.Font(None, 24)
        self.font_lg = pygame.font.Font(None, 40)
        self.transitions: list[str] = []

    def go_title(self) -> None:
        self.transitions.append("title")


class RelayEchoAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_normalization_adds_all_mission_accessibility_capabilities(self) -> None:
        normalized = normalize_accessibility({})
        profile = relay_echo_accessibility_profile({"accessibility": normalized})
        self.assertEqual(validate_relay_echo_accessibility_profile(profile), [])
        self.assertTrue(set(RELAY_ECHO_ACCESSIBILITY_REQUIREMENTS).issubset(profile.evidence()))

    def test_reduced_motion_assist_and_contrast_are_derived(self) -> None:
        profile = relay_echo_accessibility_profile(
            {
                "accessibility": {
                    "assist_mode": True,
                    "reduced_motion": True,
                    "screen_shake": 1.0,
                    "flash_intensity": 0.9,
                    "high_contrast": True,
                    "hold_assist": True,
                    "subtitle_background": True,
                    "subtitle_scale": 1.5,
                }
            }
        )
        self.assertEqual(validate_relay_echo_accessibility_profile(profile), [])
        self.assertEqual(profile.camera_shake_scale, 0.0)
        self.assertGreaterEqual(profile.flash_reduction, 0.65)
        self.assertEqual(profile.interaction_radius((62, 76)), (93, 114))
        self.assertEqual(profile.overload_frames(90), 158)
        self.assertEqual(profile.recovery_invulnerability_frames(), 180)
        self.assertEqual(profile.objective_palette()["active"], (255, 255, 255))

    def test_hold_alternative_accepts_preheld_interaction(self) -> None:
        manager = InputManager(initialize_joystick=False)
        manager.update_from_actions({"interact"})
        manager.update_from_actions({"interact"})
        assisted = relay_echo_accessibility_profile({"accessibility": {"hold_assist": True}})
        standard = relay_echo_accessibility_profile({})
        self.assertFalse(manager.just_pressed("interact"))
        self.assertTrue(manager.is_held("interact"))
        self.assertTrue(assisted.accepts_interact(manager))
        self.assertFalse(standard.accepts_interact(manager))

    def test_settings_scene_changes_and_persists_normalized_values(self) -> None:
        engine = FakeSettingsEngine()
        scene = SettingsScene(engine)
        scene.on_enter()
        self.assertFalse(engine.settings["accessibility"]["assist_mode"])
        engine.input.update_from_actions({"confirm"})
        scene.update(1.0)
        self.assertTrue(engine.settings["accessibility"]["assist_mode"])
        self.assertIn("ui_move", engine.audio.events)

        scene.selected = 9
        engine.input.update_from_actions(())
        engine.input.update_from_actions({"confirm"})
        scene.update(1.0)
        self.assertEqual(engine.transitions, ["title"])

    def test_complete_accessibility_and_input_parity_replay(self) -> None:
        report = run_replay()
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["input_parity"])
        self.assertTrue(report["accessibility_path_verified"])
        self.assertFalse(report["campaign_promoted"])
        self.assertEqual(set(report["profiles"]), {"keyboard", "gamepad"})
        accessible = report["accessibility"]
        self.assertTrue(accessible["relay_echo"]["completion_eligible"])
        self.assertEqual(accessible["transition"], ["campaign"])
        self.assertEqual(accessible["accessibility"]["camera_shake_scale"], 0.0)
        self.assertTrue(accessible["accessibility"]["hold_toggle_alternatives"])
        self.assertTrue(accessible["accessibility"]["high_contrast_objectives"])
        self.assertNotIn("relay_echo", accessible["campaign"]["completed_missions"])


if __name__ == "__main__":
    unittest.main()
