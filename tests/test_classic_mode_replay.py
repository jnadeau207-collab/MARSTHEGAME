from __future__ import annotations

import unittest

from tools.classic_mode_replay import run_replay


class ClassicModeReplayTests(unittest.TestCase):
    def test_all_eight_chapters_load_complete_and_transition(self) -> None:
        report = run_replay()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["classic_mode_chapters"], list(range(1, 9)))
        self.assertEqual(report["completed_through"], 8)
        self.assertEqual(len(report["chapter_results"]), 8)
        self.assertEqual(report["transitions"][-1], {"type": "credits"})


if __name__ == "__main__":
    unittest.main()
