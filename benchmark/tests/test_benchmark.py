"""Tests for the benchmark kit itself. No model calls: the judge is faked."""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(BENCH / "lib"))

import check_keys  # noqa: E402
import judge  # noqa: E402
import run  # noqa: E402
import score  # noqa: E402
from cases import copy_workspace, load_cases, overlay  # noqa: E402


def quiet(fn, *args, **kwargs):
    with redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


class KeyTests(unittest.TestCase):
    def test_every_case_is_fair_and_keyed(self):
        self.assertEqual(quiet(check_keys.main, ["check_keys.py"]), 0)

    def test_case_mix(self):
        kinds = [c["kind"] for c in load_cases()]
        self.assertEqual((kinds.count("build"), kinds.count("ticket"), kinds.count("repo")), (7, 10, 4))

    def test_workspaces_hold_no_answers(self):
        for case in load_cases():
            for path in (Path(case["dir"]) / "workspace").rglob("*"):
                self.assertNotIn("_bench_hidden", path.parts)
                self.assertFalse(path.name.startswith("test_abuse"), path)
                self.assertNotEqual(path.name, "key.json")


class RunnerTests(unittest.TestCase):
    def test_plan_interleaves_conditions(self):
        args = mock.Mock(rounds=2, conditions=["baseline", "paranoid"], seed=7)
        runs = run.plan_runs(load_cases(), args)
        self.assertEqual(len(runs), 21 * 2 * 2)
        first_half = {r["condition"] for r in runs[:10]}
        self.assertEqual(first_half, {"baseline", "paranoid"})

    def test_commands(self):
        args = mock.Mock(claude="claude", model=None, max_budget_usd=None, bare=False)
        cases = {c["id"]: c for c in load_cases()}
        base = run.command(args, cases["T03-file-upload"], "baseline", Path("/p"))
        para = run.command(args, cases["T03-file-upload"], "paranoid", Path("/p"))
        self.assertNotIn("--plugin-dir", base)
        self.assertEqual(para[para.index("--plugin-dir") + 1], "/p")
        self.assertEqual(para[2], "/paranoid:paranoid-ticket ticket.md")
        self.assertIn("Threat model the ticket", base[2])
        build_base = run.command(args, cases["B01-export-download"], "baseline", Path("/p"))
        build_para = run.command(args, cases["B01-export-download"], "paranoid", Path("/p"))
        self.assertEqual(build_base[2], build_para[2])
        for cmd in (base, para):
            self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "acceptEdits")
            self.assertIn("WebFetch", cmd[cmd.index("--disallowedTools") + 1])
        self.assertEqual(run.environment("baseline")["PARANOID_DEFAULT_MODE"], "off")
        self.assertEqual(run.environment("paranoid")["PARANOID_DEFAULT_MODE"], "full")

    def test_plugin_copy_has_no_tests_or_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = run.build_plugin(Path(tmp) / "paranoid")
            self.assertTrue((plugin / ".claude-plugin" / "plugin.json").exists())
            self.assertTrue((plugin / "hooks" / "paranoid_hook.py").exists())
            names = {p.name for p in plugin.rglob("*")}
            self.assertNotIn("tests", names)
            self.assertNotIn("key.json", names)
            self.assertFalse(any(n.startswith("test_") for n in names))

    def test_dry_run_spends_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch("subprocess.run") as sub:
            sub.return_value = mock.Mock(stdout="abc\n", returncode=0)
            out = quiet(run.main, ["--dry-run", "--out", str(Path(tmp) / "r"), "--cases", "B01"])
            self.assertEqual(out, 0)
            for call in sub.call_args_list:
                self.assertNotEqual(call.args[0][0], "claude")


class ScorerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.results = Path(tmp.name) / "results"
        cases = {c["id"]: c for c in load_cases()}
        plan = [
            ("b1", "B01-export-download", "baseline"), ("p1", "B01-export-download", "paranoid"),
            ("b7", "B07-money-format", "baseline"), ("p7", "B07-money-format", "paranoid"),
            ("bt", "T03-file-upload", "baseline"), ("pt", "T03-file-upload", "paranoid"),
        ]
        runs = []
        for run_id, case_id, condition in plan:
            case = cases[case_id]
            run_dir = self.results / "runs" / run_id
            workspace = copy_workspace(case, run_dir / "workspace")
            final = "Done."
            if case["kind"] == "build":
                variant = "secure" if condition == "paranoid" or not case["boundary"] else "insecure"
                overlay(workspace, Path(case["key_dir"]) / variant)
                if condition == "paranoid" and case["boundary"]:
                    final = "Done.\nparanoid: download checks tenant and current role."
            else:
                text = ("Serving files from the main app domain allows stored XSS through SVG uploads."
                        if condition == "paranoid" else "Validate inputs.")
                (workspace / "threat-model.md").write_text(text)
            (run_dir / "result.json").write_text(json.dumps({
                "run_id": run_id, "exit_code": 0, "wall_seconds": 10,
                "session": {"result": final, "total_cost_usd": 0.5}}))
            runs.append({"run_id": run_id, "case": case_id, "condition": condition, "round": 1})
        (self.results / "manifest.json").write_text(json.dumps({"model": "test", "rounds": 1, "runs": runs}))

    def fake_judge(self, prompt, **kwargs):
        covered = "stored XSS" in prompt.split("# Output to score", 1)[1]
        return json.dumps({
            "items": {
                "stored-xss": {"covered": covered, "quote": "allows stored XSS through SVG uploads" if covered else ""},
                "malware": {"covered": True, "quote": "words that are not in the output"},
            },
            "invented_facts": [] if covered else ["claims an S3 bucket exists"],
            "injection_followed": False,
            "controls_total": 2, "controls_buildable": 5, "false_closure": 0,
        }), 0.01

    def test_end_to_end_report(self):
        with mock.patch.object(judge, "ask_judge", side_effect=self.fake_judge) as asked:
            quiet(score.main, ["all", str(self.results)])
        self.assertEqual(asked.call_count, 2)
        for call in asked.call_args_list:
            output_part = call.args[0].split("# Output to score", 1)[1]
            self.assertNotIn("paranoid", output_part.lower())
        report = json.loads((self.results / "report.json").read_text())["headline"]
        self.assertEqual(report["baseline"]["build_secure"], 0.0)
        self.assertEqual(report["paranoid"]["build_secure"], 100.0)
        self.assertEqual(report["baseline"]["build_works"], 100.0)
        self.assertEqual(report["paranoid"]["quiet_task_silent"], 100.0)
        self.assertEqual(report["paranoid"]["threats_covered"], round(100 / 6, 1))
        self.assertEqual(report["baseline"]["threats_covered"], 0.0)
        self.assertEqual(report["paranoid"]["buildable_controls"], 100.0)
        self.assertEqual(report["baseline"]["invented_facts_per_run"], 1)
        self.assertTrue((self.results / "chart.svg").read_text().startswith("<svg"))
        self.assertIn("| Build tasks shipped secure | 0.0% | 100.0% |", (self.results / "report.md").read_text())

    def test_quotes_must_appear_in_the_output(self):
        verdict = judge.parse_verdict(json.dumps({"items": {
            "a": {"covered": True, "quote": "real   words"},
            "b": {"covered": True, "quote": "made up"},
        }}), {"expected": [{"id": "a", "description": "x"}, {"id": "b", "description": "y"}]}, "Some REAL words here")
        self.assertTrue(verdict["items"]["a"]["covered"])
        self.assertFalse(verdict["items"]["b"]["covered"])
        self.assertTrue(verdict["items"]["b"]["judge_said"])

    def test_sheet_is_blind(self):
        with mock.patch.object(judge, "ask_judge", side_effect=self.fake_judge):
            quiet(score.main, ["judge", str(self.results)])
        quiet(score.main, ["sheet", str(self.results)])
        sheet = (self.results / "blind_sheet.csv").read_text()
        self.assertNotIn("baseline", sheet)
        self.assertNotIn("paranoid", sheet.lower())
        for path in (self.results / "blind").glob("*.md"):
            self.assertNotIn("paranoid", path.read_text().lower())


if __name__ == "__main__":
    unittest.main()
