from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.relay_echo_candidate_audit import audit_relay_candidate

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase2_campaign.json"


class RelayEchoCandidateAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_candidate_layer_passes_after_promotion(self) -> None:
        report = audit_relay_candidate(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["tranche"], "relay_echo_playable_candidate")

    def test_candidate_layer_cannot_claim_phase_completion(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["status"] = "complete"
        report = audit_relay_candidate(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_candidate_requires_verified_runtime_state(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["relay_echo_runtime_state_verification"] = "pending"
        report = audit_relay_candidate(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_candidate_verification_must_remain_passed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["relay_echo_playable_candidate_verification"] = "pending"
        report = audit_relay_candidate(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_manifest_cannot_remove_promoted_relay_echo(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"] = ["ares_reach"]
        report = audit_relay_candidate(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_external_playtest_fabrication_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["external_playtests_run"] = 20
        report = audit_relay_candidate(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("release_evidence_truthful", report["failures"])


if __name__ == "__main__":
    unittest.main()
