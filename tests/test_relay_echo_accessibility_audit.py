from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.relay_echo_accessibility_audit import audit_relay_accessibility
from tools.relay_echo_accessibility_replay import run_replay

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase2_campaign.json"


class RelayEchoAccessibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.replay_report = run_replay()

    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def audit(self, manifest: dict, replay_report: dict | None = None) -> dict:
        return audit_relay_accessibility(
            manifest,
            self.replay_report if replay_report is None else replay_report,
        )

    def test_committed_manifest_and_replay_pass(self) -> None:
        report = self.audit(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["tranche"], "relay_echo_accessibility_parity")

    def test_parity_cannot_be_claimed_before_exact_verification(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["keyboard_gamepad_completion_parity"] = True
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("pending_release_gates_truthful", report["failures"])

    def test_accessibility_path_cannot_be_claimed_before_exact_verification(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["accessibility_path_verified"] = True
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("pending_release_gates_truthful", report["failures"])

    def test_unknown_tranche_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["current_tranche"] = "relay_echo_promoted"
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_corrupt_replay_evidence_fails(self) -> None:
        replay = copy.deepcopy(self.replay_report)
        replay["campaign_promoted"] = True
        replay["input_parity"] = False
        report = self.audit(self.manifest, replay)
        self.assertEqual(report["status"], "fail")
        self.assertIn("executable_parity_evidence", report["failures"])

    def test_manifest_cannot_fabricate_relay_echo_implementation(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].append("relay_echo")
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])


if __name__ == "__main__":
    unittest.main()
