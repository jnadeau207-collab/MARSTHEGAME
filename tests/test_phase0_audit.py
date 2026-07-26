from __future__ import annotations

import unittest

from tools.phase0_audit import run_audit


class Phase0AuditTests(unittest.TestCase):
    def test_committed_phase0_evidence_is_complete(self) -> None:
        report = run_audit()
        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["failures"])
        self.assertGreaterEqual(len(report["checks"]), 8)
        self.assertTrue(all(check["status"] == "pass" for check in report["checks"]))

    def test_audit_preserves_truthful_collaboration_boundary(self) -> None:
        report = run_audit()
        self.assertIn("one human founder", report["truthfulness_note"])
        self.assertIn("zero employees", report["truthfulness_note"])
        self.assertIn("one AI collaborator", report["truthfulness_note"])
        self.assertIn("not people or headcount", report["truthfulness_note"])
        self.assertIn("legal clearance", report["truthfulness_note"])


if __name__ == "__main__":
    unittest.main()
