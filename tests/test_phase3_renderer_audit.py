from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.phase3_renderer_audit import audit_phase3_renderer

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase3_renderer.json"
_CI_VERIFICATION_KEYS = (
    "native_build_verification",
    "native_runtime_self_test",
    "warp_smoke_test",
    "validation_clean_ci_runtime",
    "ci_rendered_geometry_verification",
    "gpu_pixel_readback_verification",
)


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

    def test_ci_evidence_must_advance_as_one_exact_head_set(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["native_build_verification"] = "passed"
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("ci_verification_coherent", report["failures"])

    def test_verified_ci_evidence_requires_numeric_run(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        for key in _CI_VERIFICATION_KEYS:
            manifest[key] = "passed"
        manifest["verification_run"] = "requested"
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("ci_verification_coherent", report["failures"])

    def test_coherent_ci_evidence_does_not_claim_founder_approval(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        for key in _CI_VERIFICATION_KEYS:
            manifest[key] = "passed"
        manifest["verification_run"] = "30230099057"
        report = audit_phase3_renderer(manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(manifest["founder_hardware_validation"], "pending")
        self.assertEqual(manifest["founder_visual_inspection"], "pending")

    def test_founder_hardware_evidence_cannot_be_fabricated(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["founder_hardware_validation"] = "passed"
        manifest["founder_visual_inspection"] = "passed"
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
