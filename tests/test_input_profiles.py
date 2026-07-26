from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.core.input import GAMEPAD_BUTTON_ACTIONS, InputManager
from game.core.input_profiles import (
    INPUT_PROFILE_GAMEPAD,
    INPUT_PROFILE_KEYBOARD,
    REQUIRED_GAMEPLAY_ACTIONS,
    input_frame,
    input_token,
    validate_input_profiles,
)


class FakeJoystick:
    def get_axis(self, axis: int) -> float:
        return 0.0

    def get_numhats(self) -> int:
        return 1

    def get_hat(self, hat: int) -> tuple[int, int]:
        return (-1, 1)

    def get_button(self, button: int) -> bool:
        return button in {1, 6}


class InputProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_profiles_cover_every_required_action(self) -> None:
        self.assertEqual(validate_input_profiles(), [])
        for action in REQUIRED_GAMEPLAY_ACTIONS:
            self.assertTrue(input_token(INPUT_PROFILE_KEYBOARD, action))
            self.assertEqual(input_token(INPUT_PROFILE_GAMEPAD, action), action)

    def test_keyboard_and_gamepad_frames_resolve_to_same_semantics(self) -> None:
        for profile in (INPUT_PROFILE_KEYBOARD, INPUT_PROFILE_GAMEPAD):
            manager = InputManager(initialize_joystick=False)
            for action in REQUIRED_GAMEPLAY_ACTIONS:
                manager.update_from_actions(input_frame(profile, action))
                self.assertTrue(manager.just_pressed(action), (profile, action))
                self.assertTrue(manager.is_held(action), (profile, action))
                manager.update_from_actions(())
                self.assertTrue(manager.just_released(action), (profile, action))

    def test_gamepad_mapping_includes_cancel_and_pause(self) -> None:
        self.assertIn("cancel", GAMEPAD_BUTTON_ACTIONS[1])
        self.assertIn("cancel", GAMEPAD_BUTTON_ACTIONS[6])
        self.assertIn("pause", GAMEPAD_BUTTON_ACTIONS[7])

    def test_dpad_and_cancel_are_present_at_hardware_boundary(self) -> None:
        manager = InputManager(initialize_joystick=False)
        manager.joy = FakeJoystick()
        manager.update()
        self.assertTrue(manager.is_held("left"))
        self.assertTrue(manager.is_held("up"))
        self.assertTrue(manager.is_held("attack"))
        self.assertTrue(manager.is_held("cancel"))
        self.assertFalse(manager.is_held("right"))
        self.assertFalse(manager.is_held("down"))

    def test_unknown_profiles_and_actions_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown input profile"):
            input_frame("touchscreen", "jump")
        with self.assertRaisesRegex(ValueError, "unknown gameplay action"):
            input_frame(INPUT_PROFILE_KEYBOARD, "skip_mission")


if __name__ == "__main__":
    unittest.main()
