import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import result_adapters as adapters


class ResultAdapterTests(unittest.TestCase):
    def test_identity_is_unambiguous_private_and_versioned(self):
        first = adapters.test_id("junit", "a", "b", "secret-token")
        self.assertRegex(first, r"^[a-f0-9]{64}$")
        self.assertEqual(first, adapters.test_id("junit", "a", "b", "secret-token"))
        self.assertNotEqual(adapters.test_id("junit", "a:b", "c"),
                            adapters.test_id("junit", "a", "b:c"))
        self.assertNotEqual(first, adapters.test_id("unittest", "a", "b", "secret-token"))
        with self.assertRaisesRegex(ValueError, "invalid_test_identity"):
            adapters.test_id("unittest", "bad\ud800identity")

    def test_junit_pytest_and_gradle_shapes(self):
        for root in ("testsuites", None):
            suite = ('<testsuite name="suite" tests="4" failures="1" errors="1" skipped="1">'
                     '<testcase classname="C" name="pass"/>'
                     '<testcase classname="C" name="fail"><failure message="secret-token">secret-token</failure></testcase>'
                     '<testcase classname="C" name="error"><error/></testcase>'
                     '<testcase classname="C" name="skip"><skipped/></testcase>'
                     '<system-out>secret-token</system-out>'
                     '<properties><property name="secret-token" value="secret-token"/></properties>'
                     '</testsuite>')
            data = (('<testsuites>' + suite + '</testsuites>') if root else suite).encode()
            cases = adapters.parse_junit(data)
            self.assertEqual(cases, {adapters.test_id("junit", "suite", "C", name): status
                                    for name, status in (("pass", "pass"), ("fail", "fail"),
                                                         ("error", "error"), ("skip", "skipped"))})
            self.assertNotIn("secret-token", json.dumps(cases))

    def test_nested_suite_summaries_are_not_double_counted(self):
        data = b'<testsuites tests="1"><testsuite name="outer" tests="1"><testsuite name="inner" tests="1"><testcase classname="C" name="one"/></testsuite></testsuite></testsuites>'
        self.assertEqual(adapters.parse_junit(data),
                         {adapters.test_id("junit", "inner", "C", "one"): "pass"})

    def test_junit_rejects_ambiguous_or_unsupported_results(self):
        cases = [
            b'', b'<html/>', b'<testsuite>',
            b'<testsuite name="s" tests="2"><testcase classname="C" name="t"/></testsuite>',
            b'<testsuite name="s"><testcase classname="C" name="t"/><testcase classname="C" name="t"/></testsuite>',
            b'<testsuite name="s"><testcase name="t"/></testsuite>',
            b'<testsuite name="s"><testcase classname="C" name="t"><failure/><skipped/></testcase></testsuite>',
            b'<testsuite name="s"><testcase classname="C" name="t"><flakyFailure/></testcase></testsuite>',
            b'<testsuite name="s"><testcase classname="C" name="t"><rerunFailure/></testcase></testsuite>',
            b'<testsuite name="s"><testcase classname="C" name="t" status="notrun"/></testsuite>',
            b'<testsuite name="s" disabled="1"><testcase classname="C" name="t"/></testsuite>',
            b'<testsuite xmlns="urn:other-format" name="s"><testcase classname="C" name="t"/></testsuite>',
            b'<testsuite name="s" tests="-1"/>',
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, r"^[a-z_]+$"):
                adapters.parse_junit(data)

    def test_xml_entity_and_doctype_attack_are_denied_in_both_encodings(self):
        text = '<!DOCTYPE testsuite [<!ENTITY secret SYSTEM "file:///etc/passwd">]><testsuite name="s"><testcase classname="C" name="t">&secret;</testcase></testsuite>'
        for encoding in ("utf-8", "utf-16"):
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                adapters.parse_junit(text.encode(encoding))
        with self.assertRaises(ValueError):
            adapters.parse_junit(b'<!DOCTYPE testsuite><testsuite name="s"/>')

    def test_xml_budgets_and_runtime_floor(self):
        for data in (b' ' * (2 * 1024 * 1024 + 1),
                     ('<testsuite name="s">' * 65 + '</testsuite>' * 65).encode(),
                     ('<testsuite name="' + 'x' * 4097 + '"/>').encode()):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                adapters.parse_junit(data)
        with patch.object(adapters.expat, "version_info", (2, 6, 4)):
            with self.assertRaisesRegex(ValueError, "unsupported_xml_runtime"):
                adapters.parse_junit(b'<testsuite name="s"/>')
        with patch.object(adapters, "MAX_ELEMENTS", 2):
            with self.assertRaisesRegex(ValueError, "xml_structure_limit"):
                adapters.parse_junit(b'<testsuite name="s"><testcase classname="C" name="a"/><testcase classname="C" name="b"/></testsuite>')
        with patch.object(adapters, "MAX_CASES", 1):
            with self.assertRaisesRegex(ValueError, "case_count_limit"):
                adapters.parse_junit(b'<testsuite name="s"><testcase classname="C" name="a"/><testcase classname="C" name="b"/></testsuite>')

    def test_native_format_rejects_extra_duplicate_and_invalid_values(self):
        ident = adapters.test_id("unittest", "sample.C.test_one")
        good = {"format_version": 1, "cases": [{"test_id": ident, "outcome": "pass"}]}
        self.assertEqual(adapters.read_native(json.dumps(good).encode()), {ident: "pass"})
        invalid = [dict(good, secret="secret-token"), dict(good, format_version=True),
                   dict(good, cases=good["cases"] * 2),
                   dict(good, cases=[{"test_id": ident, "outcome": "green"}]),
                   dict(good, cases=[{"test_id": ident, "outcome": "pass", "raw": "secret-token"}]),
                   dict(good, cases=[{"test_id": "no", "outcome": "pass"}])]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                adapters.read_native(json.dumps(value).encode())
        for data in (b'{"format_version":1,"format_version":1,"cases":[]}',
                     b'{"format_version":NaN,"cases":[]}', b'null', b' ' * (2 * 1024 * 1024 + 1)):
            with self.assertRaises(ValueError):
                adapters.read_native(data)

    def test_invalid_mapping_input_uses_safe_errors(self):
        ident = adapters.test_id("unittest", "one")
        for mapping, cases, code, term in (({}, {}, 0, "completed"),
                                           ({"K": []}, {}, 0, "completed"),
                                           ({"K": [ident, ident]}, {ident: "pass"}, 0, "completed"),
                                           ({"K": [ident]}, {ident: "green"}, 0, "completed"),
                                           ({"K": [ident]}, {ident: "pass"}, True, "completed"),
                                           ({"K": [ident]}, {ident: "pass"}, 0, "secret-token")):
            with self.subTest(mapping=mapping), self.assertRaisesRegex(ValueError, "invalid_result_mapping"):
                adapters.check_results(mapping, cases, code, term)

    def test_mapping_requires_actual_selected_green_cases(self):
        one = adapters.test_id("unittest", "one")
        other = adapters.test_id("unittest", "other")
        mapping = {"K": [one]}
        good = adapters.check_results(mapping, {one: "pass"}, 0, "completed")["K"]
        self.assertEqual(good["outcome"], "pass")
        self.assertEqual(good["counts"], {"run": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0})
        self.assertEqual(good["test_ids"], [one])
        for cases, code, term in (({}, 0, "completed"), ({other: "pass"}, 0, "completed"),
                                  ({one: "pass"}, 1, "completed"),
                                  ({one: "pass", other: "fail"}, 1, "completed"),
                                  ({one: "pass"}, 0, "timeout")):
            with self.subTest(cases=cases, term=term):
                self.assertEqual(adapters.check_results(mapping, cases, code, term)["K"]["outcome"], "blocked")

    def test_fail_errors_skips_and_incomplete_results_cannot_pass(self):
        one = adapters.test_id("unittest", "one")
        two = adapters.test_id("unittest", "two")
        for status in ("error", "skipped", "expected_failure", "unexpected_success"):
            with self.subTest(status=status):
                result = adapters.check_results({"K": [one]}, {one: status}, 0, "completed")["K"]
                self.assertEqual(result["outcome"], "blocked")
                self.assertEqual(sum(result["counts"][k] for k in ("passed", "failed", "errors", "skipped")), result["counts"]["run"])
        result = adapters.check_results({"K": [one, two]}, {one: "fail"}, 1, "completed")["K"]
        self.assertEqual(result["outcome"], "fail")

    def test_real_pytest_report_producer(self):
        with tempfile.TemporaryDirectory(prefix="pytest result ") as directory:
            root = Path(directory)
            (root / "test_sample.py").write_text('def test_pass(): pass\ndef test_fail(): assert False, "secret-token"\n')
            report = root / "result.xml"
            done = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "--junitxml", str(report),
                                   "-o", "cache_dir=" + str(root / "cache")],
                                  cwd=root, capture_output=True, timeout=30)
            self.assertEqual(done.returncode, 1)
            cases = adapters.parse_junit(report.read_bytes())
            self.assertEqual(cases[adapters.test_id("junit", "pytest", "test_sample", "test_pass")], "pass")
            self.assertEqual(cases[adapters.test_id("junit", "pytest", "test_sample", "test_fail")], "fail")
            self.assertNotIn("secret-token", json.dumps(cases))


if __name__ == "__main__":
    unittest.main()
