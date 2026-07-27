from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.phase3_renderer_audit import audit_phase3_renderer

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase3_renderer.json"


class Phase3RendererAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_native_foundation_passes_truthful_audit(self) -> None:
        report = audit_phase3_renderer(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["phase"], "Phase 3")

    def test_aaa_claim_cannot_be_promoted(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aaa_claim"] = "achieved"
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_visual_kernel_cannot_be_called_final_quality(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["visual_quality_claim"] = "aaa"
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("visual_claim_fail_closed", report["failures"])

    def test_gpu_runtime_evidence_cannot_be_fabricated(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["validation_clean_runtime"] = "passed"
        manifest["indexed_mesh_rendered"] = "passed"
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("visual_claim_fail_closed", report["failures"])

    def test_three_js_cannot_become_shipping_runtime(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["three_js_shipping_runtime"] = True
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])

    def test_remaining_phase_count_is_finite_and_locked(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["remaining_phase_count_after_phase2"] = 0
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_truth", report["failures"])


if __name__ == "__main__":
    unittest.main()
