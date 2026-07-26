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
        self.assertEqual(report["implemented_missions"], ["ares_reach"])
        self.assertEqual(
            report["planned_missions"],
            ["relay_echo", "phobos_vector", "frontier_burn"],
        )

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
        self.assertIn("unresolved_release_gates_not_fabricated", report["failures"])

    def test_manifest_cannot_promote_planned_mission(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["implemented_missions"].append("relay_echo")
        manifest["planned_missions"].remove("relay_echo")
        report = audit_campaign(manifest)
        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_matches_catalog", report["failures"])


if __name__ == "__main__":
    unittest.main()
