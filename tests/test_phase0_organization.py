from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_phase0_organization import validate_manifest

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase0_organization.json"


class Phase0OrganizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_manifest_is_valid(self) -> None:
        report = validate_manifest(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["vertical_slice_seats"], 14)
        self.assertEqual(report["human_headcount_claim"], 1)

    def test_too_few_operating_seats_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["vertical_slice_seats"] = manifest["vertical_slice_seats"][:11]
        manifest["truthfulness"]["functional_seat_count"] = 11
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("12 to 20" in error for error in report["errors"]))

    def test_agent_lane_without_human_accountability_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["vertical_slice_seats"][2].pop("accountable_to")
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("accountable" in error for error in report["errors"]))

    def test_human_headcount_cannot_be_inflated(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["truthfulness"]["claimed_human_headcount"] = 14
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("human headcount" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
