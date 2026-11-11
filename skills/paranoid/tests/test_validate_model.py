import copy
import json
from pathlib import Path
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_model import validate
from validate_model import review_gaps
from datetime import date


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads((Path(__file__).resolve().parents[1] / "assets" / "example.json").read_text())

    def test_open_hypothesis_and_explicit_gaps_are_valid(self):
        self.assertEqual(validate(self.model), [])

    def test_invalid_inputs(self):
        mutations = {
            "broken_reference": lambda m: m["threats"][0].update(actor_id="missing"),
            "duplicate_id": lambda m: m["actors"][0].update(id="A1"),
            "unknown_field": lambda m: m.update(security_proven=True),
            "invalid_date": lambda m: m["threats"][0].update(due_date="2026-99-99"),
            "missing_coverage": lambda m: m["coverage"].pop(),
            "unsupported_mitigation": lambda m: m["threats"][0].update(status="mitigated", response="reduce"),
            "unsupported_acceptance": lambda m: m["threats"][0].update(status="accepted", response="accept"),
            "unsupported_dismissal": lambda m: m["threats"][0].update(status="dismissed"),
            "invented_test_pass_without_evidence": lambda m: m["checks"][0].update(outcome="pass"),
            "blocked_without_reason": lambda m: m["checks"][0].update(outcome="blocked"),
            "check_backlink_missing": lambda m: m["controls"][0].update(check_ids=[]),
            "duplicate_coverage": lambda m: m["coverage"].append({**m["coverage"][0], "id": "COV99"}),
            "missing_repositories": lambda m: m["scope"].pop("repositories"),
            "empty_repositories": lambda m: m["scope"].update(repositories=[]),
            "unapproved_accept_response": lambda m: m["threats"][0].update(response="accept"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                model = copy.deepcopy(self.model)
                mutate(model)
                self.assertTrue(validate(model))

    def test_non_code_inputs_without_repositories(self):
        for kind in ["ticket", "feature", "idea", "design"]:
            with self.subTest(kind=kind):
                model = copy.deepcopy(self.model)
                model["scope"].update(repositories=[], sources=[{
                    "kind": kind, "locator": "fictional:input-text", "revision": "fictional-v1",
                    "description": "Fictional supplied input for this validator test."}])
                self.assertEqual(validate(model), [])
                self.assertEqual(model["threats"][0]["status"], "hypothesis")
                model["scope"]["sources"][0]["revision"] = ""
                self.assertTrue(validate(model))

    def test_source_contract_and_mixed_inputs(self):
        self.model["scope"]["sources"] = [{
            "kind": "ticket", "locator": "fictional:ticket", "revision": "fictional-v1",
            "description": "Fictional ticket"}]
        self.assertEqual(validate(self.model), [])
        self.model["scope"]["sources"][0]["kind"] = "unknown"
        self.assertTrue(validate(self.model))

    def test_old_schema_requires_migration(self):
        self.model["schema_version"] = "0.1"
        self.assertTrue(validate(self.model))

    def test_threat_must_affect_invariant_assets(self):
        self.model["assets"].append({"id": "A_OTHER", "description": "Different asset",
                                     "owner": "Example owner", "harm": "Different harm"})
        self.model["threats"][0]["asset_ids"] = ["A_OTHER"]
        self.assertTrue(validate(self.model))
        self.model["threats"][0]["asset_ids"].append(self.model["invariants"][0]["asset_ids"][0])
        self.assertEqual(validate(self.model), [])

    def test_snapshot_mismatch(self):
        self.assertTrue(validate(self.model, "another-revision"))

    def test_optional_aws_read_access_contract(self):
        self.model["scope"]["aws_access"] = {
            "read_only": True, "status": "partial", "identity_ref": "profile:example-readonly",
            "accounts": ["fictional-account"], "regions": ["fictional-region"],
            "collected_at": "2026-10-01T12:00:00Z", "visibility_gaps": ["IAM inventory denied"]}
        self.assertEqual(validate(self.model), [])
        self.model["scope"]["aws_access"]["read_only"] = False
        self.assertTrue(validate(self.model))

    def test_valid_recorded_mitigation_and_stale_check(self):
        model = self.model
        snapshot = model["scope"]["snapshot"]
        model["evidence"].append({"id": "E2", "kind": "test", "locator": "fictional:test-output",
                                  "snapshot": snapshot, "observation": "Fictional passing test, for validator exercise only."})
        model["threats"][0].update(status="mitigated", response="reduce")
        model["controls"][0].update(status="implemented", evidence_ids=["E2"])
        model["checks"][0].update(outcome="pass", evidence_ids=["E2"])
        self.assertEqual(validate(model), [])
        model["checks"][0]["snapshot"] = "previous-revision"
        self.assertTrue(validate(model))

    def test_valid_acceptance_record(self):
        self.model["threats"][0].update(status="accepted", response="accept", acceptance={
            "authorized_owner": "Example owner", "rationale": "Fictional acceptance for this test only.",
            "review_date": "2026-10-15"})
        self.assertEqual(validate(self.model), [])

    def test_review_reports_expired_acceptance(self):
        self.model["threats"][0].update(status="accepted", response="accept", acceptance={
            "authorized_owner": "Example owner", "rationale": "Fictional acceptance",
            "review_date": "2020-01-01"})
        self.assertIn("acceptance_overdue", {g["code"] for g in review_gaps(self.model, date(2026, 10, 1))})
        self.assertNotIn("acceptance_overdue", {g["code"] for g in review_gaps(self.model, date(2019, 10, 1))})

    def test_design_only_mitigation_is_rejected(self):
        self.model["threats"][0].update(status="mitigated", response="reduce")
        self.model["controls"][0].update(status="implemented", evidence_ids=["E1"])
        self.model["checks"][0].update(outcome="pass", evidence_ids=["E1"])
        self.assertTrue(validate(self.model))
        codes = {g["code"] for g in review_gaps(self.model, date(2026, 10, 1))}
        self.assertTrue({"implementation_evidence", "execution_evidence"}.issubset(codes))

    def test_review_reports_missing_inventory(self):
        self.model["boundaries"] = []
        self.model["coverage"] = []
        for r in self.model["flows"] + self.model["threats"]:
            r["boundary_ids"] = []
        self.model["flows"] = []
        self.assertEqual(validate(self.model), [])
        codes = {g["code"] for g in review_gaps(self.model, date(2026, 10, 1))}
        self.assertTrue({"boundary_inventory", "flow_inventory"}.issubset(codes))

    def test_review_reports_incomplete_aws_observation(self):
        self.model["scope"]["aws_access"] = {
            "read_only": True, "status": "available", "identity_ref": "profile:example",
            "accounts": [], "regions": [], "collected_at": None, "visibility_gaps": []}
        self.assertEqual(validate(self.model), [])
        self.assertIn("aws_observation_scope", {g["code"] for g in review_gaps(self.model, date(2026, 10, 1))})


if __name__ == "__main__":
    unittest.main()
