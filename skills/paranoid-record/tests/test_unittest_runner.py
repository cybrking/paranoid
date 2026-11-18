import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "unittest_runner.py"
sys.path.insert(0, str(SCRIPT.parent))
import result_adapters as adapters


class NativeRunnerTests(unittest.TestCase):
    def run_fixture(self, selectors):
        with tempfile.TemporaryDirectory(prefix="native result ") as directory:
            root = Path(directory)
            (root / "broken_import.py").write_text('raise RuntimeError("secret-token")\n')
            (root / "empty.py").write_text('VALUE = 1\n')
            (root / "sample.py").write_text('''import unittest
class Cases(unittest.TestCase):
    def test_pass(self): pass
    def test_fail(self): self.fail("secret-token")
    def test_error(self): raise RuntimeError("secret-token")
    @unittest.skip("secret-token")
    def test_skip(self): pass
    @unittest.expectedFailure
    def test_xfail(self): self.fail("secret-token")
    @unittest.expectedFailure
    def test_unexpected(self): pass
    def test_subtests(self):
        for value in range(3):
            with self.subTest(value=value): self.assertEqual(value, 0, "secret-token")
    def test_subskip(self):
        with self.subTest(value="secret-token"): self.skipTest("secret-token")
class BrokenSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls): raise RuntimeError("secret-token")
    def test_never(self): pass
''')
            output = root / "result.json"
            done = subprocess.run([sys.executable, "-B", str(SCRIPT), "--result", str(output), *selectors],
                                  cwd=root, text=True, capture_output=True, timeout=20)
            raw = output.read_bytes() if output.exists() else b""
            self.assertNotIn("secret-token", raw.decode())
            self.assertNotIn("secret-token", done.stderr)
            return done, adapters.read_native(raw) if raw else {}

    def test_real_native_success(self):
        done, cases = self.run_fixture(["sample.Cases.test_pass"])
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(cases, {adapters.test_id("unittest", "sample.Cases.test_pass"): "pass"})

    def test_real_native_outcomes_and_subtest_aggregation(self):
        for name, outcome, code in (("fail", "fail", 1), ("error", "error", 1),
                                    ("skip", "skipped", 0), ("xfail", "expected_failure", 0),
                                    ("unexpected", "unexpected_success", 1), ("subtests", "fail", 1),
                                    ("subskip", "skipped", 0)):
            with self.subTest(name=name):
                ident = "sample.Cases.test_" + name
                done, cases = self.run_fixture([ident])
                self.assertEqual(done.returncode, code, done.stderr)
                self.assertEqual(cases, {adapters.test_id("unittest", ident): outcome})

    def test_import_or_selection_error_cannot_look_green(self):
        done, cases = self.run_fixture(["missing.Cases.test_missing"])
        self.assertNotEqual(done.returncode, 0)
        self.assertNotIn("pass", cases.values())
        done, cases = self.run_fixture(["sample.BrokenSetup.test_never"])
        self.assertNotEqual(done.returncode, 0)
        mapped = adapters.test_id("unittest", "sample.BrokenSetup.test_never")
        self.assertEqual(adapters.check_results({"K": [mapped]}, cases, done.returncode,
                                               "completed")["K"]["outcome"], "blocked")

    def test_import_exceptions_and_bad_arguments_use_private_diagnostics(self):
        for selectors in (["broken_import.test_never"], ["sample.Cases.test_pass", "--secret-token"]):
            with self.subTest(selectors=selectors):
                done, cases = self.run_fixture(selectors)
                self.assertEqual(done.returncode, 2)
                self.assertFalse(cases)

    def test_no_tests_or_duplicate_selection_is_rejected(self):
        done, cases = self.run_fixture([])
        self.assertEqual(done.returncode, 2)
        self.assertFalse(cases)
        done, cases = self.run_fixture(["empty"])
        self.assertEqual(done.returncode, 2)
        self.assertFalse(cases)
        done, cases = self.run_fixture(["sample.Cases.test_pass", "sample.Cases.test_pass"])
        self.assertNotEqual(done.returncode, 0)


if __name__ == "__main__":
    unittest.main()
