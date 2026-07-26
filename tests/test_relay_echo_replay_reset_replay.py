from __future__ import annotations

import unittest

from tools.relay_echo_replay_reset_replay import run_replay


class RelayEchoReplayResetReplayTests(unittest.TestCase):
    def test_completed_mission_replay_is_deterministic(self) -> None:
        report = run_replay()
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["deterministic"])
        self.assertTrue(report["completed_mission_replay"])
        self.assertTrue(report["campaign_completion_preserved"])
        self.assertTrue(report["phobos_unlock_preserved"])

        reference = report["reference"]
        self.assertEqual(reference["archived_run_ids"], [1])
        self.assertEqual(reference["current_run_id"], 2)
        replay = reference["replay_completion"]
        self.assertEqual(
            replay["campaign"]["completed_missions"],
            ["ares_reach", "relay_echo"],
        )
        self.assertIn("phobos_vector", replay["campaign"]["unlocked_missions"])
        self.assertEqual(replay["campaign"]["current_mission"], "phobos_vector")
        self.assertEqual(
            replay["completion_transition"]["event"],
            "relay_echo_replay_completed",
        )
        self.assertEqual(replay["completion_transition"]["run_id"], 2)
        self.assertEqual(replay["transition"], ["campaign"])


if __name__ == "__main__":
    unittest.main()
