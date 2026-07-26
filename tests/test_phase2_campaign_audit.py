from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.phase2_campaign_audit import audit_campaign

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "config" / "phase2_campaign.json"


class Phase2CampaignAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_manifest_passes_truthful_audit(self) -> None:
        report = audit_campaign(self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["implemented_missions"], ["ares_reach", "relay_echo"])
        self.assertEqual(report["contracted_missions"], ["relay_echo"])
        self.assertEqual(report["planned_missions"], ["phobos_vector", "frontier_burn"])

    def test_full_campaign_claim_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["full_campaign_claim"] = "achieved"
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("truthful_claims", report["failures"])

    def test_fabricated_playtests_fail(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["carried_release_gates"]["external_playtests_run"] = 25
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("release_gates_truthful", report["failures"])

    def test_manifest_cannot_demote_relay_echo(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].remove("relay_echo")
        manifest["planned_missions"].insert(0, "relay_echo")
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_matches_catalog", report["failures"])

    def test_manifest_cannot_promote_phobos_vector(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].append("phobos_vector")
        manifest["planned_missions"].remove("phobos_vector")
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_matches_catalog", report["failures"])

    def test_manifest_cannot_fabricate_a_contract(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["contracted_missions"] = ["relay_echo", "phobos_vector"]
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("relay_echo_contract_and_promotion_truth", report["failures"])

    def test_unknown_tranche_identity_fails(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["current_tranche"] = "invented_tranche"
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("relay_echo_contract_and_promotion_truth", report["failures"])

    def test_promotion_requires_verified_prerequisites(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["relay_echo_accessibility_parity_verification"] = "pending"
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("relay_echo_contract_and_promotion_truth", report["failures"])


if __name__ == "__main__":
    unittest.main()
