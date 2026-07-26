from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.relay_echo_promotion_audit import audit_relay_promotion
from tools.relay_echo_promotion_replay import run_replay

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase2_campaign.json"


class RelayEchoPromotionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.replay_report = run_replay()

    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def audit(self, manifest: dict, replay: dict | None = None) -> dict:
        return audit_relay_promotion(
            manifest,
            self.replay_report if replay is None else replay,
        )

    def test_committed_promotion_manifest_passes(self) -> None:
        report = self.audit(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["tranche"], "relay_echo_campaign_promotion")

    def test_manifest_cannot_remove_relay_from_implemented_missions(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"] = ["ares_reach"]
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_manifest_cannot_fabricate_phobos_implementation(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].append("phobos_vector")
        manifest["planned_missions"].remove("phobos_vector")
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_corrupt_promotion_replay_fails(self) -> None:
        replay = copy.deepcopy(self.replay_report)
        replay["phobos_vector_unlocked"] = False
        replay["reference"]["campaign"]["current_mission"] = "relay_echo"
        report = self.audit(self.manifest, replay)
        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_replay_evidence", report["failures"])

    def test_external_release_gate_fabrication_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["external_playtests_run"] = 25
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("release_gates_truthful", report["failures"])

    def test_unknown_promotion_verification_state_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["relay_echo_campaign_promotion_verification"] = "claimed"
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])


if __name__ == "__main__":
    unittest.main()
