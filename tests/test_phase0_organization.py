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
        self.assertEqual(report["human_count"], 1)
        self.assertEqual(report["employee_count"], 0)
        self.assertEqual(report["ai_collaborator_count"], 1)

    def test_fake_operating_seats_are_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["vertical_slice_seats"] = [{"seat_id": "fake-person"}]
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("forbidden staffing" in error for error in report["errors"]))

    def test_extra_human_contributor_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["truthfulness"]["other_human_contributor_count"] = 1
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(
            any("other_human_contributor_count" in error for error in report["errors"])
        )

    def test_ai_cannot_be_presented_as_employee(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["ai_collaborator"]["employee"] = True
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("human or employee" in error for error in report["errors"]))

    def test_ai_cannot_approve_merges(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["ai_collaborator"]["prohibited_authority"].remove(
            "merging without founder instruction"
        )
        report = validate_manifest(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("authority" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
