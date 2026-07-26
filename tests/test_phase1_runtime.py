from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from game.core.accessibility import normalize_accessibility, normalize_runtime_settings
from game.core.audio import AudioDirector
from game.core.camera import Camera
from game.core.presentation import PresentationDirector


class FakeCamera:
    def __init__(self) -> None:
        self.accessibility = None
        self.shakes: list[float] = []

    def configure_accessibility(self, value) -> None:
        self.accessibility = value

    def add_shake(self, amount: float) -> None:
        self.shakes.append(amount)


class FakePlayer:
    def __init__(self) -> None:
        self.state = "idle"
        self.hp = 5
        self.alive = True
        self.books = 0
        self.parts = 0


class FakeEnemy:
    alive = True


class FakeScene:
    def __init__(self) -> None:
        self.camera = FakeCamera()
        self.player = FakePlayer()
        self.enemies = [FakeEnemy()]
        self.terminals_activated: set[int] = set()
        self.won = False


class AccessibilityTests(unittest.TestCase):
    def test_reduced_motion_disables_shake_and_caps_flash(self) -> None:
        result = normalize_accessibility(
            {"reduced_motion": True, "screen_shake": 1.0, "flash_intensity": 1.0}
        )
        self.assertEqual(result["screen_shake"], 0.0)
        self.assertLessEqual(result["flash_intensity"], 0.35)

    def test_runtime_settings_clamp_audio_and_subtitle_scale(self) -> None:
        result = normalize_runtime_settings(
            {
                "volume_master": 5,
                "volume_music": -2,
                "accessibility": {"subtitle_scale": 9},
            }
        )
        self.assertEqual(result["volume_master"], 1.0)
        self.assertEqual(result["volume_music"], 0.0)
        self.assertEqual(result["accessibility"]["subtitle_scale"], 2.0)


class CameraTests(unittest.TestCase):
    def test_camera_shake_is_deterministic_for_same_seed(self) -> None:
        first = Camera(seed=42)
        second = Camera(seed=42)
        for camera in (first, second):
            camera.set_target(100, 100)
            camera.set_target(108, 95)
            camera.add_shake(6)
            camera.update()
        self.assertEqual(first.offset, second.offset)
        self.assertGreater(abs(first.lookahead_x), 0)

    def test_reduced_motion_blocks_camera_shake(self) -> None:
        camera = Camera(seed=4)
        camera.configure_accessibility({"reduced_motion": True})
        camera.add_shake(20)
        camera.update()
        self.assertEqual(camera.shake, 0.0)
        self.assertEqual((camera.shake_x, camera.shake_y), (0.0, 0.0))


class PresentationTests(unittest.TestCase):
    def test_impulse_is_consumed_once(self) -> None:
        director = PresentationDirector()
        scene = FakeScene()
        director.observe(scene)
        director.cue("dash")
        director.observe(scene)
        director.observe(scene)
        self.assertEqual(len(scene.camera.shakes), 1)
        self.assertGreater(scene.camera.shakes[0], 0)

    def test_hit_stop_obeys_accessibility(self) -> None:
        director = PresentationDirector(
            {"accessibility": {"hit_stop": 0.25, "reduced_motion": True}}
        )
        self.assertEqual(director.hit_stop_frames(8), 2)


class AudioTests(unittest.TestCase):
    def test_silent_fallback_records_gameplay_events(self) -> None:
        director = AudioDirector(enabled=False)
        scene = FakeScene()
        director.observe(scene)
        scene.player.state = "dash"
        scene.player.books = 1
        scene.terminals_activated.add(0)
        scene.won = True
        director.observe(scene)
        events = [item["event"] for item in director.event_log]
        self.assertIn("dash", events)
        self.assertIn("pickup", events)
        self.assertIn("terminal", events)
        self.assertIn("goal", events)
        self.assertEqual(director.state, "victory")

    def test_bus_volume_is_bounded(self) -> None:
        director = AudioDirector(enabled=False)
        director.set_bus_volume("sfx", 4)
        self.assertEqual(director.buses["sfx"], 1.0)
        with self.assertRaisesRegex(ValueError, "Unknown audio bus"):
            director.set_bus_volume("impossible", 0.5)


if __name__ == "__main__":
    unittest.main()
