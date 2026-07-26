from __future__ import annotations

import unittest

from game.core.input import InputManager


class InputManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input = InputManager(initialize_joystick=False)

    def test_virtual_actions_drive_queries_and_axis(self) -> None:
        self.input.update_from_actions({"right", "jump"})

        self.assertTrue(self.input.is_held("right"))
        self.assertTrue(self.input.just_pressed("jump"))
        self.assertEqual(self.input.get_axis(), (1, 0))
        self.assertTrue(self.input.has_buffer("jump"))

        self.input.update_from_actions({"right", "jump"})
        self.assertFalse(self.input.just_pressed("jump"))
        self.assertTrue(self.input.is_held("jump"))

        self.input.update_from_actions(set())
        self.assertTrue(self.input.just_released("right"))
        self.assertTrue(self.input.just_released("jump"))

    def test_physical_binding_names_remain_supported(self) -> None:
        self.input.update_from_actions({"space", "d"})

        self.assertTrue(self.input.just_pressed("jump"))
        self.assertTrue(self.input.is_held("right"))
        self.assertEqual(self.input.get_axis(), (1, 0))

    def test_buffer_can_be_consumed_once(self) -> None:
        self.input.update_from_actions({"dash"})

        self.assertTrue(self.input.consume_buffer("dash"))
        self.assertFalse(self.input.consume_buffer("dash"))
        self.assertFalse(self.input.has_buffer("dash"))

    def test_gamepad_style_confirm_action_is_not_lost(self) -> None:
        self.input.update_from_actions({"jump", "confirm"})

        self.assertTrue(self.input.just_pressed("jump"))
        self.assertTrue(self.input.just_pressed("confirm"))


if __name__ == "__main__":
    unittest.main()
