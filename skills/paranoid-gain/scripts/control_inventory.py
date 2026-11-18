"""Read a threat model's controls and linked checks for a gain card."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys


def inventory(model):
    controls = model["controls"]
    checks = model["checks"]
    if not isinstance(controls, list) or not isinstance(checks, list):
        raise ValueError("controls and checks must be arrays")
    if len({control["id"] for control in controls}) != len(controls):
        raise ValueError("duplicate control ID")
    check_by_id = {check["id"]: check for check in checks}
    if len(check_by_id) != len(checks):
        raise ValueError("duplicate check ID")

    rows = []
    for control in controls:
        linked = []
        for check_id in control["check_ids"]:
            check = check_by_id.get(check_id)
            if check is None or check["control_id"] != control["id"]:
                raise ValueError(f"invalid check link for {control['id']}: {check_id}")
            linked.append({"id": check_id, "outcome": check["outcome"],
                           "procedure": check["procedure"], "expected": check["expected"]})
        rows.append({"id": control["id"], "requirement": control["requirement"],
                     "status": control["status"], "checks": linked})

    outcomes = Counter(check["outcome"] for row in rows for check in row["checks"])
    return {"model_id": model["model_id"], "snapshot": model["scope"]["snapshot"],
            "identified_controls": len(rows),
            "controls_with_recorded_checks": sum(bool(row["checks"]) for row in rows),
            "recorded_check_outcomes": dict(outcomes),
            "controls": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="threat-model/model.json")
    parser.add_argument('--history', action='store_true', help='Read validated local execution history')
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Local repository root for freshness')
    parser.add_argument('--compare', nargs='?', const='previous', help='Compare previous or specified run')
    parser.add_argument('--control', help='Explain one exact control ID')
    args = parser.parse_args()
    try:
        if args.history or args.compare or args.control:
            core = Path(__file__).resolve().parents[2] / 'paranoid' / 'scripts'
            if not (core / 'control_history.py').is_file() or not (core / 'validate_model.py').is_file():
                raise ImportError('installed history component unavailable')
            sys.dont_write_bytecode = True
            sys.path.insert(0, str(core))
            from control_history import history_report
            result = history_report(args.root, args.model, compare=args.compare, control=args.control)
        else:
            result = inventory(json.loads(args.model.read_text()))
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        print(f"control inventory unavailable: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
