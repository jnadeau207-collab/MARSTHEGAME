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

    def test_hardware_edge_is_exposed_to_one_simulation_step(self) -> None:
        hardware_frames = iter(({"jump"}, {"jump"}))
        self.input._poll_hardware = lambda: set(next(hardware_frames))

        self.input.poll_hardware_frame()
        self.assertFalse(self.input.just_pressed("jump"))

        self.input.begin_simulation_step()
        self.assertTrue(self.input.just_pressed("jump"))
        self.assertTrue(self.input.has_buffer("jump"))
        self.input.end_simulation_step()

        self.input.begin_simulation_step()
        self.assertFalse(self.input.just_pressed("jump"))
        self.assertTrue(self.input.is_held("jump"))
        self.input.end_simulation_step()

    def test_edges_survive_render_frames_without_a_simulation_step(self) -> None:
        hardware_frames = iter(({"jump"}, set()))
        self.input._poll_hardware = lambda: set(next(hardware_frames))

        self.input.poll_hardware_frame()
        self.input.poll_hardware_frame()
        self.input.begin_simulation_step()

        self.assertTrue(self.input.just_pressed("jump"))
        self.assertTrue(self.input.just_released("jump"))
        self.assertFalse(self.input.is_held("jump"))
        self.assertTrue(self.input.has_buffer("jump"))

    def test_buffer_lifetime_advances_in_simulation_steps(self) -> None:
        self.input._poll_hardware = lambda: {"dash"}
        self.input.poll_hardware_frame()
        self.input.begin_simulation_step()
        self.assertEqual(self.input.buffer["dash"], 10)
        self.input.end_simulation_step()
        self.assertEqual(self.input.buffer["dash"], 9)

        for _ in range(9):
            self.input.begin_simulation_step()
            self.input.end_simulation_step()
        self.assertNotIn("dash", self.input.buffer)


if __name__ == "__main__":
    unittest.main()
