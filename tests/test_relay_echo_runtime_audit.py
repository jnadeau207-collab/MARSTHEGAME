from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.relay_echo_runtime_audit import audit_relay_runtime

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase2_campaign.json"


class RelayEchoRuntimeAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_runtime_state_passes_truthful_audit(self) -> None:
        report = audit_relay_runtime(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["tranche"], "relay_echo_runtime_state")

    def test_runtime_tranche_must_remain_in_progress(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["status"] = "complete"
        report = audit_relay_runtime(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_relay_echo_cannot_be_fabricated_as_implemented(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].append("relay_echo")
        report = audit_relay_runtime(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_runtime_verification_state_is_bounded(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["relay_echo_runtime_state_verification"] = "claimed_complete"
        report = audit_relay_runtime(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])


if __name__ == "__main__":
    unittest.main()
