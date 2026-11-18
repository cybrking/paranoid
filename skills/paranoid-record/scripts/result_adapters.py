"""Bounded result normalization; retained test identities are digests, not names."""

import hashlib
import json
import re
from xml.parsers import expat

MAX_BYTES = 2 * 1024 * 1024
MAX_CASES = 100000
MAX_ELEMENTS = 200000
MAX_DEPTH = 64
MAX_FIELD = 4096
OUTCOMES = {"pass", "fail", "error", "skipped", "expected_failure", "unexpected_success"}
DIGEST = re.compile(r"[a-f0-9]{64}\Z")


def test_id(adapter, *identity):
    if adapter not in ("unittest", "junit") or not identity or any(
        not isinstance(value, str) or not value or len(value) > MAX_FIELD for value in identity
    ):
        raise ValueError("invalid_test_identity")
    try:
        value = json.dumps([1, adapter, list(identity)], ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        raise ValueError("invalid_test_identity") from None


def _bounded(data):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError("result_size_limit")


def _unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("invalid_native")
        result[name] = value
    return result


def _invalid_constant(value):
    raise ValueError("invalid_native")


def read_native(data):
    _bounded(data)
    try:
        result = json.loads(data, object_pairs_hook=_unique, parse_constant=_invalid_constant)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise ValueError("invalid_native") from None
    if (not isinstance(result, dict) or set(result) != {"format_version", "cases"}
            or type(result["format_version"]) is not int or result["format_version"] != 1
            or not isinstance(result["cases"], list) or len(result["cases"]) > MAX_CASES):
        raise ValueError("invalid_native")
    cases = {}
    for case in result["cases"]:
        if (not isinstance(case, dict) or set(case) != {"test_id", "outcome"}
                or not isinstance(case["test_id"], str) or not DIGEST.fullmatch(case["test_id"])
                or not isinstance(case["outcome"], str) or case["outcome"] not in OUTCOMES
                or case["test_id"] in cases):
            raise ValueError("invalid_native")
        cases[case["test_id"]] = case["outcome"]
    return cases


def parse_junit(data):
    _bounded(data)
    if expat.version_info < (2, 7, 2):
        raise ValueError("unsupported_xml_runtime")
    cases, stack = {}, []
    elements = 0
    children = {
        "testsuites": {"testsuite"},
        "testsuite": {"testsuite", "testcase", "properties", "system-out", "system-err"},
        "testcase": {"failure", "error", "skipped", "properties", "system-out", "system-err"},
        "properties": {"property"},
    }
    summaries = {"name", "tests", "failures", "errors", "skipped", "time", "timestamp",
                 "hostname", "package", "id"}
    attributes = {"testsuite": summaries, "testsuites": summaries,
                  "testcase": {"classname", "name", "time", "file", "line", "assertions"},
                  "failure": {"message", "type"}, "error": {"message", "type"},
                  "skipped": {"message", "type"}, "property": {"name", "value"}}

    def start(tag, attrs):
        nonlocal elements
        elements += 1
        if len(stack) >= MAX_DEPTH or elements > MAX_ELEMENTS:
            raise ValueError("xml_structure_limit")
        if any(len(name) > MAX_FIELD or len(value) > MAX_FIELD for name, value in attrs.items()):
            raise ValueError("xml_field_limit")
        if set(attrs) - attributes.get(tag, set()):
            raise ValueError("unsupported_junit")
        if (not stack and tag not in ("testsuite", "testsuites")) or (
            stack and tag not in children.get(stack[-1]["tag"], set())
        ):
            raise ValueError("unsupported_junit")
        frame = {"tag": tag, "attrs": attrs, "counts": [0, 0, 0, 0], "statuses": set()}
        if tag == "testsuite" and not attrs.get("name"):
            raise ValueError("invalid_test_identity")
        if tag == "testcase":
            if not attrs.get("classname") or not attrs.get("name"):
                raise ValueError("invalid_test_identity")
            frame["id"] = test_id("junit", stack[-1]["attrs"]["name"], attrs["classname"], attrs["name"])
        if tag in ("failure", "error", "skipped"):
            stack[-1]["statuses"].add(tag)
        stack.append(frame)

    def end(tag):
        frame = stack.pop()
        if tag == "testcase":
            if len(frame["statuses"]) > 1:
                raise ValueError("conflicting_junit_outcomes")
            outcome = next(iter(frame["statuses"]), "pass")
            outcome = "fail" if outcome == "failure" else outcome
            if frame["id"] in cases:
                raise ValueError("duplicate_test_identity")
            cases[frame["id"]] = outcome
            if len(cases) > MAX_CASES:
                raise ValueError("case_count_limit")
            for parent in stack:
                if parent["tag"] in ("testsuite", "testsuites"):
                    parent["counts"][0] += 1
                    if outcome != "pass":
                        parent["counts"][{"fail": 1, "error": 2, "skipped": 3}[outcome]] += 1
        if tag in ("testsuite", "testsuites"):
            for index, name in enumerate(("tests", "failures", "errors", "skipped")):
                if name in frame["attrs"]:
                    text = frame["attrs"][name]
                    if not re.fullmatch(r"[0-9]+", text) or int(text) != frame["counts"][index]:
                        raise ValueError("junit_count_mismatch")

    def declaration(*args):
        raise ValueError("xml_declarations_forbidden")

    parser = expat.ParserCreate()
    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.StartDoctypeDeclHandler = declaration
    parser.EntityDeclHandler = declaration
    parser.ExternalEntityRefHandler = declaration
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(data, True)
    except (expat.ExpatError, UnicodeDecodeError, RecursionError):
        raise ValueError("invalid_junit") from None
    return cases


def check_results(mapping, cases, exit_code, termination):
    if (not isinstance(mapping, dict) or not mapping or not isinstance(cases, dict)
            or len(cases) > MAX_CASES or type(exit_code) not in (int, type(None))
            or not isinstance(termination, str) or not re.fullmatch(r"[a-z_]+", termination)):
        raise ValueError("invalid_result_mapping")
    if any(not isinstance(key, str) or not DIGEST.fullmatch(key)
           or not isinstance(status, str) or status not in OUTCOMES for key, status in cases.items()):
        raise ValueError("invalid_result_mapping")
    result = {}
    run_conflict = exit_code != 0 or any(status in ("fail", "error", "unexpected_success")
                                         for status in cases.values())
    for check, wanted in mapping.items():
        if (not isinstance(check, str) or not check or len(check) > MAX_FIELD
                or not isinstance(wanted, list) or not wanted or len(wanted) > MAX_CASES
                or any(not isinstance(value, str) or not DIGEST.fullmatch(value) for value in wanted)
                or len(set(wanted)) != len(wanted)):
            raise ValueError("invalid_result_mapping")
        statuses = [cases[value] for value in wanted if value in cases]
        counts = {"run": len(statuses), "passed": statuses.count("pass"),
                  "failed": statuses.count("fail"),
                  "errors": statuses.count("error") + statuses.count("unexpected_success"),
                  "skipped": statuses.count("skipped") + statuses.count("expected_failure")}
        if counts["failed"]:
            outcome, reason = "fail", "assertion_failed"
        elif termination != "completed":
            outcome, reason = "blocked", termination
        elif len(statuses) != len(wanted):
            outcome, reason = "blocked", "missing_tests"
        elif counts["passed"] != len(wanted):
            outcome, reason = "blocked", "tests_not_passed"
        elif run_conflict:
            outcome, reason = "blocked", "runner_disagreement"
        else:
            outcome, reason = "pass", "passed"
        result[check] = {"outcome": outcome, "reason": reason, "counts": counts,
                         "test_ids": sorted(wanted)}
    return result
