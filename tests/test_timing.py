from __future__ import annotations

import unittest

from game.core.timing import FixedStepScheduler, FramePacingMonitor


class FixedStepSchedulerTests(unittest.TestCase):
    def test_two_half_frames_produce_one_simulation_step(self) -> None:
        scheduler = FixedStepScheduler(simulation_hz=60)
        first = scheduler.plan(1.0 / 120.0)
        second = scheduler.plan(1.0 / 120.0)

        self.assertEqual(first.simulation_steps, 0)
        self.assertAlmostEqual(first.interpolation_alpha, 0.5)
        self.assertEqual(second.simulation_steps, 1)
        self.assertAlmostEqual(second.interpolation_alpha, 0.0, places=9)

    def test_reference_sequence_is_deterministic(self) -> None:
        frames = [1.0 / 60.0, 1.0 / 120.0, 1.0 / 120.0, 0.05, 0.0]
        first = FixedStepScheduler().replay(frames)
        second = FixedStepScheduler().replay(frames)
        self.assertEqual(first, second)

    def test_catch_up_is_bounded_and_excess_time_is_reported(self) -> None:
        scheduler = FixedStepScheduler(simulation_hz=60, max_catch_up_steps=5)
        plan = scheduler.plan(0.25)

        self.assertEqual(plan.simulation_steps, 5)
        self.assertAlmostEqual(plan.dropped_seconds, 10.0 / 60.0, places=9)
        self.assertAlmostEqual(plan.interpolation_alpha, 0.0, places=9)
        self.assertAlmostEqual(
            scheduler.monitor.snapshot()["dropped_ms"],
            plan.dropped_seconds * 1000.0,
            places=6,
        )

    def test_unbounded_wall_time_is_clamped_and_reported(self) -> None:
        scheduler = FixedStepScheduler(
            simulation_hz=60,
            max_catch_up_steps=5,
            max_frame_seconds=0.25,
        )
        plan = scheduler.plan(1.0)
        self.assertEqual(plan.accepted_seconds, 0.25)
        self.assertGreater(plan.dropped_seconds, 0.9)

    def test_invalid_elapsed_time_fails_closed(self) -> None:
        scheduler = FixedStepScheduler()
        for value in (-0.1, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "finite and non-negative"):
                    scheduler.plan(value)


class FramePacingMonitorTests(unittest.TestCase):
    def test_snapshot_reports_percentiles_hitches_and_dropped_time(self) -> None:
        monitor = FramePacingMonitor(history_size=5, hitch_seconds=0.03)
        for value in (0.010, 0.016, 0.020, 0.040, 0.050):
            monitor.record(value, dropped_seconds=0.001)
        snapshot = monitor.snapshot()

        self.assertEqual(snapshot["sample_count"], 5)
        self.assertEqual(snapshot["total_frames"], 5)
        self.assertEqual(snapshot["hitch_count"], 2)
        self.assertAlmostEqual(snapshot["hitch_ratio"], 0.4)
        self.assertAlmostEqual(snapshot["maximum_ms"], 50.0)
        self.assertAlmostEqual(snapshot["dropped_ms"], 5.0)
        self.assertGreaterEqual(snapshot["p99_ms"], snapshot["p95_ms"])
        self.assertGreaterEqual(snapshot["p95_ms"], snapshot["p50_ms"])

    def test_history_is_bounded(self) -> None:
        monitor = FramePacingMonitor(history_size=3)
        for value in (0.01, 0.02, 0.03, 0.04):
            monitor.record(value)
        self.assertEqual(monitor.samples(), (0.02, 0.03, 0.04))
        self.assertEqual(monitor.snapshot()["total_frames"], 4)


if __name__ == "__main__":
    unittest.main()
