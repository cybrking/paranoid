#!/usr/bin/env python3
"""Prove the hidden tests are fair before anyone spends a run on them.

For every build task: the untouched starter must fail, a secure reference must pass
both the functional and the abuse tests, and an insecure reference must pass the
functional tests but fail at least one abuse test. Every ticket and repo case must
have a well formed answer key. No model calls, standard library only.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from build_tests import run_hidden_tests, summarize  # noqa: E402
from cases import copy_workspace, load_cases, overlay  # noqa: E402

KEY_FIELDS = {"ticket": "expected", "repo": "flaws"}


def check_build(case):
    problems = []
    key = Path(case["key_dir"])
    has_abuse = (key / "test_abuse.py").exists()
    if has_abuse != bool(case.get("boundary")):
        return ["boundary flag and abuse tests disagree"]
    variants = [("starter", None, False, None), ("secure", key / "secure", True, True if has_abuse else None)]
    if has_abuse:
        variants.append(("insecure", key / "insecure", True, False))
    for name, files, want_works, want_secure in variants:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = copy_workspace(case, Path(tmp) / "w")
            if files is not None:
                overlay(workspace, files)
            summary = summarize(run_hidden_tests(workspace, key))
        if summary["works"] != want_works:
            problems.append("%s: works=%s, expected %s" % (name, summary["works"], want_works))
        if want_secure is not None and summary["secure"] != want_secure:
            problems.append("%s: secure=%s, expected %s (%d of %d abuse tests passed)" % (
                name, summary["secure"], want_secure, summary["abuse_passed"], summary["abuse_total"]))
    return problems


def check_key(case):
    path = Path(case["key_dir"]) / "key.json"
    if not path.exists():
        return ["missing key.json"]
    key = json.loads(path.read_text())
    items = key.get(KEY_FIELDS[case["kind"]], [])
    problems = []
    if len(items) < 3:
        problems.append("fewer than 3 key items")
    ids = [item.get("id") for item in items]
    if len(set(ids)) != len(ids) or not all(ids):
        problems.append("key item ids must be unique and present")
    for item in items:
        if not item.get("description"):
            problems.append("%s has no description" % item.get("id"))
    if not key.get("injection"):
        problems.append("no injection description")
    if case["kind"] == "repo":
        for item in items:
            if not item.get("location"):
                problems.append("%s has no location" % item.get("id"))
            elif not (Path(case["dir"]) / "workspace" / item["location"].split(":")[0]).exists():
                problems.append("%s points at a missing file" % item["id"])
    return problems


def main(argv):
    only = argv[1:] or None
    failed = 0
    cases = load_cases(only)
    for case in cases:
        if not (Path(case["dir"]) / "workspace").is_dir():
            problems = ["missing workspace"]
        elif case["kind"] == "build":
            problems = check_build(case)
        else:
            problems = check_key(case)
        status = "ok" if not problems else "FAIL"
        print("%-4s %s %s" % (status, case["id"], "; ".join(problems)))
        failed += bool(problems)
    print("%d cases, %d failed" % (len(cases), failed))
    return 1 if failed or not cases else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
