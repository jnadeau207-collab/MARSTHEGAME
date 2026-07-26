from __future__ import annotations

import unittest

from tools.performance_baseline import summarize_samples
from tools.performance_guard import evaluate_reports

POLICY = {
    "schema_version": 1,
    "policy_name": "test-policy",
    "minimum_rounds": 7,
    "metrics": {
        "setup_ms": {
            "relative_floor": 0.35,
            "absolute_floor_ms": 0.15,
            "mad_multiplier": 8.0,
            "aggregate_relative_limit": 0.18,
        },
        "update_ms_per_frame": {
            "relative_floor": 0.25,
            "absolute_floor_ms": 0.02,
            "mad_multiplier": 8.0,
            "aggregate_relative_limit": 0.12,
        },
        "draw_ms_per_frame": {
            "relative_floor": 0.20,
            "absolute_floor_ms": 0.50,
            "mad_multiplier": 8.0,
            "aggregate_relative_limit": 0.10,
        },
    },
}


def make_report(scale: float = 1.0, noise: float = 0.0) -> dict:
    chapters = []
    for chapter_id in range(1, 9):
        bases = {
            "setup_ms": 1.0 + chapter_id * 0.05,
            "update_ms_per_frame": 0.10 + chapter_id * 0.005,
            "draw_ms_per_frame": 4.0 + chapter_id * 0.1,
        }
        metrics = {}
        for metric, base in bases.items():
            samples = [base * (scale + noise * offset) for offset in (-3, -2, -1, 0, 1, 2, 3)]
            metrics[metric] = summarize_samples(samples)
        chapters.append({"chapter_id": chapter_id, "metrics": metrics})
    return {
        "schema_version": 2,
        "status": "pass",
        "git_sha": "test",
        "python": "3.12.1",
        "platform": "test-runner",
        "parameters": {
            "update_frames": 90,
            "draw_frames": 5,
            "rounds": 7,
            "warmup_rounds": 2,
            "resolution": [1280, 720],
        },
        "chapters": chapters,
    }


class PerformanceGuardTests(unittest.TestCase):
    def test_stable_candidate_passes(self) -> None:
        report = evaluate_reports([make_report(), make_report()], make_report(1.03), POLICY)
        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["failures"])

    def test_broad_rendering_regression_fails_aggregate_gate(self) -> None:
        report = evaluate_reports([make_report(), make_report()], make_report(1.25), POLICY)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("aggregate ratio" in failure for failure in report["failures"]))

    def test_observed_variance_expands_individual_limit(self) -> None:
        baseline = make_report(noise=0.08)
        candidate = make_report(scale=1.30)
        report = evaluate_reports([baseline, baseline], candidate, POLICY)
        setup_chapter = report["metrics"]["setup_ms"]["chapters"][0]
        self.assertGreater(setup_chapter["allowed_delta"], 0.35)

    def test_parameter_mismatch_fails_closed(self) -> None:
        baseline = make_report()
        candidate = make_report()
        candidate["parameters"]["draw_frames"] = 6
        with self.assertRaisesRegex(ValueError, "parameters do not match"):
            evaluate_reports([baseline], candidate, POLICY)

    def test_empty_sample_summary_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty sample"):
            summarize_samples([])


if __name__ == "__main__":
    unittest.main()
