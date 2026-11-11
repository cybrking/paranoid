"""Score a build task workspace against its hidden functional and abuse tests."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent
HIDDEN = "_bench_hidden"
MODULES = ("test_functional", "test_abuse")


def run_hidden_tests(workspace, key_dir, timeout=60):
    """Copy the hidden tests into a scratch copy of the workspace and run them.

    Returns {"test_functional": {"run": n, "failed": [...]}, "test_abuse": {...}}.
    A module that can't import or times out counts every test in it as failed.
    """
    workspace = Path(workspace)
    key_dir = Path(key_dir)
    target = workspace / HIDDEN
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    (target / "__init__.py").write_text("")
    shutil.copy(LIB / "hidden_runner.py", target / "hidden_runner.py")
    for helper in key_dir.glob("_*.py"):
        shutil.copy(helper, target / helper.name)
    results = {}
    try:
        for module in MODULES:
            source = key_dir / (module + ".py")
            if not source.exists():
                continue
            shutil.copy(source, target / source.name)
            expected = source.read_text().count("    def test_")
            try:
                done = subprocess.run(
                    [sys.executable, "-B", HIDDEN + "/hidden_runner.py", HIDDEN + "." + module],
                    cwd=workspace, capture_output=True, text=True, timeout=timeout,
                )
                line = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else ""
                parsed = json.loads(line) if line.startswith("{") else None
            except (subprocess.TimeoutExpired, ValueError):
                parsed = None
            if not parsed or parsed["run"] == 0:
                parsed = {"module": module, "run": expected, "failed": ["did not run"] * expected}
            results[module] = {"run": parsed["run"], "failed": parsed["failed"]}
    finally:
        shutil.rmtree(target, ignore_errors=True)
    return results


def summarize(results):
    def passed(module):
        r = results.get(module)
        return bool(r) and r["run"] > 0 and not r["failed"]

    return {
        "works": passed("test_functional"),
        "secure": passed("test_abuse"),
        "abuse_passed": (results.get("test_abuse", {}).get("run", 0) - len(results.get("test_abuse", {}).get("failed", []))),
        "abuse_total": results.get("test_abuse", {}).get("run", 0),
    }
