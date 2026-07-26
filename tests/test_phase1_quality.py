from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.phase1_quality_audit import audit_quality

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase1_quality.json"


class Phase1QualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_quality_contract_is_truthful(self) -> None:
        report = audit_quality(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["aaa_claim"], "target_not_achieved")
        self.assertFalse(report["playable_start_to_finish"])
        self.assertFalse(report["pending_foundations"])
        self.assertEqual(
            set(report["implemented_foundations"]),
            set(self.manifest["runtime_foundation"]),
        )

    def test_unearned_aaa_claim_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aaa_claim"] = "achieved"
        report = audit_quality(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("AAA-quality" in error for error in report["errors"]))

    def test_fabricated_playtest_results_fail(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["external_evidence"]["completion_rate"] = 0.95
        report = audit_quality(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("playtests" in error for error in report["errors"]))

    def test_missing_journey_beat_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["slice"]["journey"].remove("vehicle_or_ascent_spectacle")
        report = audit_quality(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("journey" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
