import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_model.py"


class CliTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.directory = Path(self.workspace.name)
        self.model = json.loads((SKILL_DIR / "assets" / "example.json").read_text())
        self.model_path = self.directory / "model.json"
        self.model_path.write_text(json.dumps(self.model))

    def run_cli(self, *arguments, input_text=None):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *map(str, arguments)],
            input=input_text, text=True, capture_output=True,
            cwd=self.directory, timeout=20,
        )

    def assert_valid_result(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["document_valid"])
        self.assertEqual(output["errors"], [])
        self.assertEqual(output["as_of"], "2026-10-01")
        declared_version = re.search(
            r'^  version: "([^"]+)"$', (SKILL_DIR / "SKILL.md").read_text(), re.MULTILINE,
        )
        self.assertIsNotNone(declared_version)
        self.assertEqual(output["validator_version"], declared_version.group(1))
        self.assertEqual(
            output["schema_sha256"],
            hashlib.sha256((SKILL_DIR / "references" / "model.schema.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(output["security_effectiveness"], "not_assessed")
        self.assertTrue(output["coverage_gaps"])
        self.assertIn("check_unexecuted", {gap["code"] for gap in output["review_gaps"]})
        return output

    def test_valid_file_reports_contract_and_unresolved_checks(self):
        self.assert_valid_result(self.run_cli(
            self.model_path, "--as-of", "2026-10-01",
            "--expected-snapshot", self.model["scope"]["snapshot"],
        ))

    def test_stdin_matches_file_output(self):
        file_result = self.run_cli(self.model_path, "--as-of", "2026-10-01")
        stdin_result = self.run_cli(
            "-", "--as-of", "2026-10-01", input_text=json.dumps(self.model),
        )
        self.assertEqual(self.assert_valid_result(stdin_result), self.assert_valid_result(file_result))

    def test_invalid_model_exits_one_with_structural_errors(self):
        del self.model["assets"]
        self.model_path.write_text(json.dumps(self.model))
        result = self.run_cli(self.model_path)
        self.assertEqual(result.returncode, 1, result.stderr)
        output = json.loads(result.stdout)
        self.assertFalse(output["document_valid"])
        self.assertTrue(output["errors"])
        self.assertEqual(output["review_gaps"], [])

    def test_malformed_file_and_stdin_exit_two(self):
        self.model_path.write_text("{not valid JSON")
        results = [
            self.run_cli(self.model_path),
            self.run_cli("-", input_text="{not valid JSON"),
        ]
        for result in results:
            with self.subTest(input=result.args[-1]):
                self.assertEqual(result.returncode, 2, result.stderr)
                output = json.loads(result.stdout)
                self.assertFalse(output["document_valid"])
                self.assertTrue(output["input_error"])

    def test_missing_input_file_exits_two(self):
        result = self.run_cli(self.directory / "missing.json")
        self.assertEqual(result.returncode, 2, result.stderr)
        output = json.loads(result.stdout)
        self.assertFalse(output["document_valid"])
        self.assertTrue(output["input_error"])

    def test_expected_snapshot_mismatch_exits_one(self):
        result = self.run_cli(self.model_path, "--expected-snapshot", "different-assessment")
        self.assertEqual(result.returncode, 1, result.stderr)
        output = json.loads(result.stdout)
        self.assertFalse(output["document_valid"])
        self.assertTrue(output["errors"])

    def test_invalid_as_of_is_argument_error(self):
        result = self.run_cli(self.model_path, "--as-of", "2026-02-30")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("--as-of", result.stderr)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
