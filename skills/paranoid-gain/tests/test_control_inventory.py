import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "control_inventory.py"
spec = importlib.util.spec_from_file_location("control_inventory", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ControlInventoryTest(unittest.TestCase):
    def test_counts_controls_and_preserves_check_status(self):
        model = {"model_id": "sample", "scope": {"snapshot": "v1"},
                 "controls": [{"id": "C1", "requirement": "Deny cross-tenant reads",
                               "status": "proposed", "check_ids": ["K1"]}],
                 "checks": [{"id": "K1", "control_id": "C1", "outcome": "not_run",
                             "procedure": "Request tenant B as tenant A",
                             "expected": "Denied"}]}
        result = module.inventory(model)
        self.assertEqual(result["identified_controls"], 1)
        self.assertEqual(result["controls_with_recorded_checks"], 1)
        self.assertEqual(result["recorded_check_outcomes"], {"not_run": 1})
        self.assertEqual(result["controls"][0]["checks"][0]["outcome"], "not_run")
        model["checks"][0]["control_id"] = "C2"
        with self.assertRaises(ValueError):
            module.inventory(model)
        model["checks"][0]["control_id"] = "C1"
        model["controls"].append(model["controls"][0].copy())
        with self.assertRaises(ValueError):
            module.inventory(model)
