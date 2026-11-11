import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED


class ArchivePortabilityTests(unittest.TestCase):
    def test_extracted_skill_runs_without_original_tree(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="threat model package ") as temporary:
            root = Path(temporary)
            archive = root / "skill.zip"
            with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
                for item in source.rglob("*"):
                    if item.is_file() and "__pycache__" not in item.parts:
                        bundle.write(item, Path("paranoid") / item.relative_to(source))
            with ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                bundle.extractall(root / "install with spaces")
            installed = root / "install with spaces" / "paranoid"
            fixture = installed / "assets" / "example.json"
            model = json.loads(fixture.read_text())
            model["scope"].update(repositories=[], sources=[{
                "kind": "idea", "locator": "fictional:idea", "revision": "fictional-v1",
                "description": "Fictional design input for package portability."}])
            fixture.write_text(json.dumps(model))
            result = subprocess.run([
                sys.executable, "-B", str(installed / "scripts" / "validate_model.py"),
                str(fixture), "--expected-snapshot", model["scope"]["snapshot"],
                "--as-of", "2026-10-01"], cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(json.loads(result.stdout)["document_valid"])
            self.assertEqual(json.loads(result.stdout)["security_effectiveness"], "not_assessed")


if __name__ == "__main__":
    unittest.main()
