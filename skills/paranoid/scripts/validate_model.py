"""Validate document structure and recorded consistency, not security effectiveness."""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    print("Install jsonschema or use the uv command in SKILL.md.", file=sys.stderr)
    sys.exit(2)


COLLECTIONS = (
    "assets", "actors", "components", "boundaries", "flows", "invariants",
    "evidence", "assumptions", "threats", "controls", "checks", "coverage",
)


def validate(model, expected_snapshot=None):
    schema = json.loads((Path(__file__).resolve().parents[1] / "references" / "model.schema.json").read_text())
    errors = [f"schema {list(e.absolute_path)}: {e.message}"
              for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(model)]
    if errors:
        return errors
    index = {name: {r["id"]: r for r in model[name]} for name in COLLECTIONS}
    all_ids = set()
    for name in COLLECTIONS:
        for r in model[name]:
            if r["id"] in all_ids:
                errors.append(f"Duplicate ID: {r['id']}")
            all_ids.add(r["id"])

    def refs(record, field, target, scalar=False):
        values = [record[field]] if scalar else record[field]
        for value in values:
            if value not in index[target]:
                errors.append(f"{record['id']}.{field}: unknown {target} ID {value}")

    for name in COLLECTIONS:
        for r in model[name]:
            for field, target in (("evidence_ids", "evidence"), ("assumption_ids", "assumptions"),
                                  ("asset_ids", "assets"), ("boundary_ids", "boundaries"),
                                  ("control_ids", "controls"), ("check_ids", "checks"),
                                  ("threat_ids", "threats")):
                if field in r:
                    refs(r, field, target)
            for field, target in (("actor_id", "actors"), ("entry_component_id", "components"),
                                  ("from_component_id", "components"), ("to_component_id", "components"),
                                  ("invariant_id", "invariants"), ("control_id", "controls"),
                                  ("boundary_id", "boundaries")):
                if field in r:
                    refs(r, field, target, scalar=True)
    if errors:
        return errors

    snapshot = model["scope"]["snapshot"]
    if expected_snapshot is not None and snapshot != expected_snapshot:
        errors.append("Scope snapshot does not match expected snapshot")

    def current_evidence(ids):
        return bool(ids) and all(index["evidence"][i]["snapshot"] == snapshot for i in ids)

    for c in model["controls"]:
        if c["status"] == "implemented" and not current_evidence(c["evidence_ids"]):
            errors.append(f"{c['id']}: implemented control needs current evidence")
        if c["status"] == "implemented" and not any(
            index["evidence"][i]["kind"] in ("code", "config", "runtime", "test") for i in c["evidence_ids"]
        ):
            errors.append(f"{c['id']}: design/external evidence alone cannot establish implementation")
        for check_id in c["check_ids"]:
            if index["checks"][check_id]["control_id"] != c["id"]:
                errors.append(f"{c['id']}: check {check_id} belongs to another control")
    for check in model["checks"]:
        if check["id"] not in index["controls"][check["control_id"]]["check_ids"]:
            errors.append(f"{check['id']}: control must link back to this check")
        if check["outcome"] in ("pass", "fail"):
            if not check["evidence_ids"]:
                errors.append(f"{check['id']}: executed outcome needs evidence")
            if not any(index["evidence"][i]["kind"] in ("test", "runtime") for i in check["evidence_ids"]):
                errors.append(f"{check['id']}: executed outcome needs actual check-result evidence")
            if any(index["evidence"][i]["snapshot"] != check["snapshot"] for i in check["evidence_ids"]):
                errors.append(f"{check['id']}: evidence snapshot differs from check snapshot")
        if check["outcome"] == "blocked" and not check.get("reason"):
            errors.append(f"{check['id']}: blocked check needs a reason")

    for t in model["threats"]:
        if not set(t["asset_ids"]).intersection(index["invariants"][t["invariant_id"]]["asset_ids"]):
            errors.append(f"{t['id']}: threatened assets do not overlap the violated invariant's protected assets")
        if t["status"] in ("confirmed", "dismissed") and not current_evidence(t["evidence_ids"]):
            errors.append(f"{t['id']}: {t['status']} needs current supporting evidence")
        if t["status"] == "dismissed" and not t.get("disposition_reason"):
            errors.append(f"{t['id']}: dismissal needs a reason")
        if t["status"] == "accepted":
            if "acceptance" not in t or t["response"] != "accept":
                errors.append(f"{t['id']}: accepted threat needs acceptance record and accept response")
        elif "acceptance" in t:
            errors.append(f"{t['id']}: acceptance record requires accepted state")
        if t["response"] == "accept" and t["status"] != "accepted":
            errors.append(f"{t['id']}: accept response requires accepted state")
        if t["status"] == "mitigated":
            if t["response"] not in ("reduce", "avoid"):
                errors.append(f"{t['id']}: mitigated response must be reduce or avoid")
            if not t["control_ids"]:
                errors.append(f"{t['id']}: mitigated threat needs controls")
            for control_id in t["control_ids"]:
                c = index["controls"][control_id]
                if c["status"] != "implemented" or not c["check_ids"]:
                    errors.append(f"{t['id']}: control {control_id} needs implementation and checks")
                for check_id in c["check_ids"]:
                    check = index["checks"][check_id]
                    if check["outcome"] != "pass" or check["snapshot"] != snapshot or not current_evidence(check["evidence_ids"]):
                        errors.append(f"{t['id']}: check {check_id} needs current passing evidence")

    required_lenses = {"security", "privacy", "business_abuse", "operations"}
    if "ai" in model["scope"]["profiles"]:
        required_lenses.add("ai")
    covered = set()
    for row in model["coverage"]:
        key = (row["boundary_id"], row["lens"])
        if key in covered:
            errors.append(f"{row['id']}: duplicate boundary/lens coverage")
        covered.add(key)
        if row["disposition"] != "reviewed" and row["threat_ids"]:
            errors.append(f"{row['id']}: only reviewed coverage can link threats")
        for threat_id in row["threat_ids"]:
            if row["boundary_id"] not in index["threats"][threat_id]["boundary_ids"]:
                errors.append(f"{row['id']}: linked threat does not involve this boundary")
    for boundary in model["boundaries"]:
        for lens in required_lenses:
            if (boundary["id"], lens) not in covered:
                errors.append(f"Missing coverage: {boundary['id']} / {lens}")
    return errors


def review_gaps(model, as_of):
    """Report detectable review needs without asserting assessment completeness."""
    gaps = []

    def add(record_id, code, message):
        gaps.append({"record_id": record_id, "code": code, "message": message})

    evidence = {r["id"]: r for r in model["evidence"]}
    if not model["boundaries"]:
        add(model["model_id"], "boundary_inventory", "No boundaries declared; explain and substantively review inventory.")
    if not model["flows"]:
        add(model["model_id"], "flow_inventory", "No flows declared; explain and substantively review inventory.")
    for component in model["components"]:
        if not component["evidence_ids"]:
            add(component["id"], "component_evidence", "Component has no supporting evidence.")
    snapshot = model["scope"]["snapshot"]
    for item in model["evidence"]:
        if item["snapshot"] != snapshot:
            add(item["id"], "evidence_snapshot", "Evidence is not bound to the current assessment bundle.")
    for threat in model["threats"]:
        acceptance = threat.get("acceptance")
        if acceptance and date.fromisoformat(acceptance["review_date"]) < as_of:
            add(threat["id"], "acceptance_overdue", "Risk acceptance review date is overdue; owner decision required.")
    for control in model["controls"]:
        if control["status"] == "implemented" and not any(
            evidence[i]["kind"] in ("code", "config", "runtime", "test") for i in control["evidence_ids"]
        ):
            add(control["id"], "implementation_evidence", "Design/external context alone does not establish implementation.")
    for check in model["checks"]:
        if check["outcome"] in ("pass", "fail"):
            if not any(evidence[i]["kind"] in ("test", "runtime") for i in check["evidence_ids"]):
                add(check["id"], "execution_evidence", "Executed outcome needs actual check-result evidence, not just source/design context.")
            if check["snapshot"] != snapshot:
                add(check["id"], "check_snapshot", "Executed check belongs to a different assessment bundle.")
        elif check["outcome"] in ("blocked", "not_run"):
            add(check["id"], "check_unexecuted", f"Control check is {check['outcome']}; effectiveness has not been established by this check.")
    aws = model["scope"].get("aws_access")
    if aws:
        status = aws["status"]
        if status in ("available", "partial") and (not aws["accounts"] or not aws["regions"] or aws["collected_at"] is None):
            add("scope.aws_access", "aws_observation_scope", "Available/partial AWS observations need accounts, regions, and collection time.")
        if status in ("partial", "denied") and not aws["visibility_gaps"]:
            add("scope.aws_access", "aws_visibility", "Partial/denied AWS access needs explicit visibility gaps.")
        if status == "not_requested" and aws["collected_at"] is not None:
            add("scope.aws_access", "aws_access_state", "Not-requested AWS access cannot imply a collection time.")
    return gaps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Model JSON file, or '-' to read JSON from stdin")
    parser.add_argument("--expected-snapshot")
    parser.add_argument("--as-of", type=date.fromisoformat,
                        default=datetime.now(timezone.utc).date(),
                        help="Assessment date for acceptance review (YYYY-MM-DD; defaults to UTC today)")
    args = parser.parse_args()
    try:
        model = json.load(sys.stdin) if str(args.model) == "-" else json.loads(args.model.read_text())
        errors = validate(model, args.expected_snapshot)
    except (OSError, ValueError) as exc:
        print(json.dumps({"document_valid": False, "input_error": str(exc)}))
        return 2
    gaps = [] if errors else [r["id"] for r in model["coverage"] if r["disposition"] == "deferred"]
    schema_path = Path(__file__).resolve().parents[1] / "references" / "model.schema.json"
    print(json.dumps({"document_valid": not errors, "errors": errors,
                      "coverage_gaps": gaps,
                      "review_gaps": [] if errors else review_gaps(model, args.as_of),
                      "as_of": args.as_of.isoformat(), "validator_version": "0.2.1",
                      "schema_sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
                      "security_effectiveness": "not_assessed"}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
