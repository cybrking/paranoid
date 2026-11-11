#!/usr/bin/env python3
"""Run every benchmark case with and without paranoid in fresh Claude Code sessions.

Each run gets its own copy of the case workspace, a new non persistent session and the
same prompt in both conditions (the paranoid condition uses the skill command for tickets
and repositories, and the plain prompt for build tasks, where always on mode does the work).
Raw outputs are kept. Nothing is scored here: see score.py.

Runs spend your Claude usage. Start with --dry-run, then a pilot with --rounds 1.
"""

import argparse
import hashlib
import json
import os
import random
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from cases import copy_workspace, load_cases  # noqa: E402

BENCH = Path(__file__).resolve().parent
REPO = BENCH.parent
CONDITIONS = ("baseline", "paranoid")
PLUGIN_PARTS = (".claude-plugin", "hooks", "skills")
SAFE_TOOLS = [
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(python3 -m unittest:*)", "Bash(python -m unittest:*)",
    "Bash(python3 -B -m unittest:*)", "Bash(ls:*)", "Bash(cat:*)",
]
BLOCKED_TOOLS = ["WebFetch", "WebSearch"]


def tree_hash(root, parts):
    digest = hashlib.sha256()
    for part in parts:
        for path in sorted((Path(root) / part).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(str(path.relative_to(root)).encode())
                digest.update(path.read_bytes())
    return digest.hexdigest()


def build_plugin(target):
    """A clean copy of the plugin with no tests, examples or benchmark keys in reach."""
    for part in PLUGIN_PARTS:
        shutil.copytree(REPO / part, Path(target) / part,
                        ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc"))
    return Path(target)


def prompt_for(case, condition):
    if condition == "paranoid" and case.get("paranoid_prompt"):
        return case["paranoid_prompt"]
    return case["prompt"]


def command(args, case, condition, plugin_dir):
    cmd = [
        args.claude, "-p", prompt_for(case, condition),
        "--output-format", "json",
        "--no-session-persistence",
        "--setting-sources", "project,local",
        "--permission-mode", "acceptEdits",
        "--allowedTools", ",".join(SAFE_TOOLS),
        "--disallowedTools", ",".join(BLOCKED_TOOLS),
    ]
    if args.model:
        cmd += ["--model", args.model]
    if args.max_budget_usd:
        cmd += ["--max-budget-usd", str(args.max_budget_usd)]
    if args.bare:
        cmd.append("--bare")
    if condition == "paranoid":
        cmd += ["--plugin-dir", str(plugin_dir)]
    return cmd


def environment(condition):
    env = dict(os.environ)
    env["PARANOID_DEFAULT_MODE"] = "full" if condition == "paranoid" else "off"
    return env


def preflight(args):
    problems = []
    if shutil.which(args.claude) is None:
        problems.append("Claude Code CLI not found (%s). Install it or pass --claude." % args.claude)
    level_file = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / ".paranoid-mode"
    if level_file.exists() and level_file.read_text().strip() not in ("", "full"):
        problems.append("%s says %r, which would override the benchmark's level. Run /paranoid-mode full "
                        "in Claude Code first." % (level_file, level_file.read_text().strip()))
    return problems


def plan_runs(cases, args):
    runs = []
    for round_number in range(1, args.rounds + 1):
        for case in cases:
            for condition in args.conditions:
                runs.append({"case": case["id"], "condition": condition, "round": round_number})
    random.Random(args.seed).shuffle(runs)
    return runs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(BENCH / "results" / time.strftime("%Y%m%d-%H%M%S")),
                        help="results folder, reuse one to resume an interrupted benchmark")
    parser.add_argument("--cases", nargs="*", help="case id prefixes, like B T01 R02 (default: all)")
    parser.add_argument("--conditions", nargs="*", default=list(CONDITIONS), choices=CONDITIONS)
    parser.add_argument("--rounds", type=int, default=1, help="runs per case per condition (the plan calls for 5)")
    parser.add_argument("--model", help="model for every run, for example the one you use day to day")
    parser.add_argument("--max-budget-usd", type=float, default=None, help="per run spending cap (API key users)")
    parser.add_argument("--timeout", type=int, default=1200, help="seconds before a run is stopped")
    parser.add_argument("--seed", type=int, default=7, help="shuffles run order so conditions interleave")
    parser.add_argument("--claude", default="claude", help="path to the Claude Code CLI")
    parser.add_argument("--bare", action="store_true",
                        help="minimal mode with no user CLAUDE.md or other plugins; needs ANTHROPIC_API_KEY")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and the first command, run nothing")
    args = parser.parse_args(argv)

    cases = {case["id"]: case for case in load_cases(args.cases)}
    if not cases:
        parser.error("no cases matched")
    out = Path(args.out)
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        print("Resuming %s (%d runs planned)" % (out, len(manifest["runs"])))
    else:
        runs = plan_runs(list(cases.values()), args)
        for run in runs:
            run["run_id"] = secrets.token_hex(4)
        manifest = {
            "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "repo_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                          capture_output=True, text=True).stdout.strip() or "unknown",
            "plugin_hash": tree_hash(REPO, PLUGIN_PARTS),
            "cases_hash": tree_hash(BENCH, ("cases", "keys")),
            "model": args.model or "CLI default",
            "rounds": args.rounds,
            "conditions": args.conditions,
            "permissions": {"mode": "acceptEdits", "allowed": SAFE_TOOLS, "blocked": BLOCKED_TOOLS},
            "bare": args.bare,
            "runs": runs,
        }

    plugin_dir = out / "plugin" / "paranoid"
    todo = [r for r in manifest["runs"] if not (out / "runs" / r["run_id"] / "result.json").exists()]
    print("%d cases, %d runs, %d left to run" % (len(cases), len(manifest["runs"]), len(todo)))

    if args.dry_run:
        if todo:
            first = todo[0]
            print("First run:", first["case"], first["condition"])
            print(" ".join(json.dumps(part) if " " in part else part
                           for part in command(args, cases[first["case"]], first["condition"], plugin_dir)))
        return 0

    problems = preflight(args)
    if problems:
        print("\n".join("Stopped: " + p for p in problems))
        return 2
    out.mkdir(parents=True, exist_ok=True)
    manifest["claude_version"] = subprocess.run([args.claude, "--version"], capture_output=True, text=True).stdout.strip()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    if not plugin_dir.exists():
        build_plugin(plugin_dir)

    for index, run in enumerate(todo, 1):
        case = cases.get(run["case"])
        if case is None:
            continue
        run_dir = out / "runs" / run["run_id"]
        if run_dir.exists():
            shutil.rmtree(run_dir)
        workspace = copy_workspace(case, run_dir / "workspace")
        cmd = command(args, case, run["condition"], plugin_dir.resolve())
        started = time.time()
        print("[%d/%d] %s %s round %d" % (index, len(todo), run["case"], run["condition"], run["round"]), flush=True)
        try:
            done = subprocess.run(cmd, cwd=workspace, env=environment(run["condition"]),
                                  capture_output=True, text=True, timeout=args.timeout)
            stdout, stderr, code = done.stdout, done.stderr, done.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr, code = "timed out after %ds" % args.timeout, -1
        try:
            session = json.loads(stdout)
        except ValueError:
            session = {"result": stdout, "is_error": True}
        result = {
            "run_id": run["run_id"],
            "exit_code": code,
            "wall_seconds": round(time.time() - started, 1),
            "session": session,
            "stderr": stderr[-4000:],
        }
        (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Done. Score with: python3 benchmark/score.py all %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
