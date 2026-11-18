"""Run explicitly selected unittest cases and write private normalized results."""

import argparse
import json
from pathlib import Path
import sys
import unittest

from result_adapters import MAX_BYTES, MAX_CASES, test_id


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "native_result_unavailable\n")


class RecordedResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.cases = {}

    def startTest(self, test):
        ident = test_id("unittest", test.id())
        if ident in self.cases or len(self.cases) >= MAX_CASES:
            raise ValueError("duplicate_or_excessive_tests")
        super().startTest(test)
        self.cases[ident] = "pass"

    def _set_outcome(self, test, status):
        owner = getattr(test, "test_case", test)
        ident = test_id("unittest", owner.id())
        if ident not in self.cases and len(self.cases) >= MAX_CASES:
            raise ValueError("case_count_limit")
        rank = {"pass": 0, "skipped": 1, "expected_failure": 1,
                "unexpected_success": 2, "fail": 3, "error": 4}
        if rank[status] >= rank[self.cases.get(ident, "pass")]:
            self.cases[ident] = status

    def addFailure(self, test, err):
        self._set_outcome(test, "fail")

    def addError(self, test, err):
        self._set_outcome(test, "error")

    def addSkip(self, test, reason):
        self._set_outcome(test, "skipped")

    def addExpectedFailure(self, test, err):
        self._set_outcome(test, "expected_failure")

    def addUnexpectedSuccess(self, test):
        self._set_outcome(test, "unexpected_success")

    def addSubTest(self, test, subtest, err):
        if err is not None:
            status = "fail" if issubclass(err[0], test.failureException) else "error"
            self._set_outcome(test, status)


def main():
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("tests", nargs="+")
    args = parser.parse_args()
    try:
        if len(set(args.tests)) != len(args.tests):
            raise ValueError("duplicate_test_selection")
        sys.path.insert(0, str(Path.cwd()))
        try:
            suite = unittest.defaultTestLoader.loadTestsFromNames(args.tests)
        except Exception:
            # Imported test code can raise arbitrary exceptions containing secrets.
            print("native_result_unavailable", file=sys.stderr)
            return 2
        if not 0 < suite.countTestCases() <= MAX_CASES:
            raise ValueError("no_tests")
        result = RecordedResult()
        suite.run(result)
        data = json.dumps({"format_version": 1, "cases": [
            {"test_id": ident, "outcome": status} for ident, status in sorted(result.cases.items())
        ]}).encode()
        if len(data) > MAX_BYTES:
            raise ValueError("result_size_limit")
        with args.result.open("xb") as output:
            output.write(data)
        return int(any(status in ("fail", "error", "unexpected_success")
                       for status in result.cases.values()))
    except (OSError, ValueError, TypeError, RecursionError):
        print("native_result_unavailable", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
