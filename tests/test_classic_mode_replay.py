from __future__ import annotations

import unittest

from tools.classic_mode_replay import run_replay


class ClassicModeReplayTests(unittest.TestCase):
    def test_all_eight_chapters_replay_complete_and_transition(self) -> None:
        report = run_replay()

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["classic_mode_chapters"], list(range(1, 9)))
        self.assertEqual(report["completed_through"], 8)
        self.assertEqual(len(report["input_replays"]), 8)
        self.assertEqual(len(report["chapter_results"]), 8)
        self.assertEqual(report["transitions"][-1], {"type": "credits"})

        for input_replay in report["input_replays"]:
            with self.subTest(chapter_id=input_replay["chapter_id"]):
                self.assertGreater(input_replay["frames"], 0)
                self.assertEqual(len(input_replay["track_sha256"]), 64)
                self.assertNotEqual(input_replay["start"], input_replay["end"])
                self.assertIn("jump", input_replay["actions"])
                self.assertIn("dash", input_replay["actions"])


if __name__ == "__main__":
    unittest.main()
