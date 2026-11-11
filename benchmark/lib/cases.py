"""Load benchmark cases and their answer keys."""

import json
import shutil
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
CASES = BENCH / "cases"
KEYS = BENCH / "keys"
KINDS = ("ticket", "repo", "build")


def load_cases(only=None):
    cases = []
    for case_file in sorted(CASES.glob("*/*/case.json")):
        case = json.loads(case_file.read_text())
        case["dir"] = case_file.parent
        case["key_dir"] = KEYS / case_file.parent.parent.name / case_file.parent.name
        if only and not any(case["id"].startswith(prefix) for prefix in only):
            continue
        cases.append(case)
    return cases


def copy_workspace(case, target):
    """Copy only what the agent may see into a fresh directory."""
    source = Path(case["dir"]) / "workspace"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return Path(target)


def overlay(target, files_dir):
    """Copy a reference solution over a workspace copy."""
    for path in Path(files_dir).rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            destination = Path(target) / path.relative_to(files_dir)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, destination)
