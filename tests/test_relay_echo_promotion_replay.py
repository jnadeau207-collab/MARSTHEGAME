from __future__ import annotations

import unittest

from tools.relay_echo_promotion_replay import run_replay


class RelayEchoPromotionReplayTests(unittest.TestCase):
    def test_promoted_campaign_path_is_deterministic(self) -> None:
        report = run_replay()
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["deterministic"])
        self.assertTrue(report["campaign_promoted"])
        self.assertTrue(report["relay_echo_completed"])
        self.assertTrue(report["phobos_vector_unlocked"])
        reference = report["reference"]
        self.assertEqual(
            reference["campaign"]["completed_missions"],
            ["ares_reach", "relay_echo"],
        )
        self.assertEqual(reference["campaign"]["current_mission"], "phobos_vector")
        self.assertIn("phobos_vector", reference["campaign"]["unlocked_missions"])
        self.assertEqual(reference["transition"], ["campaign"])
        self.assertEqual(
            reference["completion_transition"]["event"],
            "relay_echo_campaign_completed",
        )
        self.assertEqual(
            reference["completion_transition"]["unlocked_mission"],
            "phobos_vector",
        )


if __name__ == "__main__":
    unittest.main()
