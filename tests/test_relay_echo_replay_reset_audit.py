from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.relay_echo_replay_reset_audit import audit_relay_replay_reset
from tools.relay_echo_replay_reset_replay import run_replay

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase2_campaign.json"


class RelayEchoReplayResetAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.replay_report = run_replay()

    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def audit(self, manifest: dict, replay: dict | None = None) -> dict:
        return audit_relay_replay_reset(
            manifest,
            self.replay_report if replay is None else replay,
        )

    def test_committed_subtranche_and_replay_pass(self) -> None:
        report = self.audit(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["subtranche"], "relay_echo_completed_mission_replay")

    def test_replay_gate_cannot_be_claimed_before_verification(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["completed_mission_replay_verified"] = True
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_gate_truth", report["failures"])

    def test_verified_replay_requires_numeric_run(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["relay_echo_completed_mission_replay_verification"] = "passed"
        manifest["carried_release_gates"]["completed_mission_replay_verified"] = True
        manifest["verification_run"] = "requested"
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_gate_truth", report["failures"])

    def test_unknown_active_subtranche_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["active_subtranche"] = "phobos_vector_runtime"
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_corrupt_replay_evidence_fails(self) -> None:
        replay = copy.deepcopy(self.replay_report)
        replay["phobos_unlock_preserved"] = False
        replay["reference"]["replay_completion"]["campaign"]["completed_missions"] = ["ares_reach"]
        report = self.audit(self.manifest, replay)
        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_evidence", report["failures"])

    def test_external_release_gate_fabrication_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["external_playtests_run"] = 12
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_gate_truth", report["failures"])

    def test_manifest_cannot_promote_phobos_vector(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].append("phobos_vector")
        manifest["planned_missions"].remove("phobos_vector")
        report = self.audit(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])


if __name__ == "__main__":
    unittest.main()
