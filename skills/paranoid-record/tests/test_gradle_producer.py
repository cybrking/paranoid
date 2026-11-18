import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gradle"
RECORDER = ROOT / "skills" / "paranoid-record" / "scripts" / "record_check.py"


class GradleProducerTests(unittest.TestCase):
    def test_real_gradle_pass_repeat_and_failure(self):
        gradle = os.environ.get("PARANOID_GRADLE")
        if not gradle:
            if os.environ.get("PARANOID_REQUIRE_GRADLE") == "1":
                self.fail("required_gradle_tool_unavailable")
            self.skipTest("Set PARANOID_GRADLE to the pinned producer tool; CI producer job requires it")
        with tempfile.TemporaryDirectory(prefix="gradle producer ") as directory:
            root = Path(directory)
            shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text("threat-model/\nbuild/\n.gradle/\n")
            (root / "threat-model").mkdir()
            model = json.loads((ROOT / "skills/paranoid/assets/example.json").read_text())
            (root / "threat-model/model.json").write_text(json.dumps(model))
            (root / "mapping.json").write_text(json.dumps({
                "CHK1": [["example.AuthorizationTest", "example.AuthorizationTest", "deniesOtherTenant"]]
            }))
            command = [sys.executable, "-B", str(RECORDER), "--root", str(root),
                       "--mapping", "mapping.json", "--adapter", "junit", "--exclude", "build",
                       "--exclude", ".gradle", "--", gradle, "--no-daemon", "--no-watch-fs",
                       "--no-configuration-cache", "--no-build-cache", "--offline", "--rerun-tasks",
                       "--console=plain", "--warning-mode=none", "-PparanoidReportDir={report_dir}", "test"]
            env = dict(os.environ)
            env.setdefault("GRADLE_USER_HOME", str(root / "threat-model" / "gradle-cache"))
            version = subprocess.run([gradle, "--version"], cwd=root, env=env,
                                     capture_output=True, text=True, timeout=60)
            self.assertEqual(version.returncode, 0, version.stdout + version.stderr)
            self.assertIn("Gradle 9.9.1", version.stdout)
            prepared = subprocess.run([gradle, "--no-daemon", "--no-watch-fs", "--no-configuration-cache",
                                       "--console=plain", "--warning-mode=none", "prepareTests"],
                                      cwd=root, env=env, capture_output=True, text=True, timeout=180)
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            for expected in ("pass", "pass", "fail"):
                if expected == "fail":
                    source = root / "src/main/java/example/Export.java"
                    source.write_text(source.read_text().replace("return 403", "return 200"))
                done = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=330)
                self.assertEqual(done.returncode, int(expected == "fail"), done.stdout + done.stderr)
                result = json.loads(done.stdout)
                self.assertEqual(result["publication_state"], "committed")
                self.assertEqual(result["freshness"], "matching")
                self.assertEqual(result["checks"]["CHK1"]["outcome"], expected)
                self.assertEqual(result["checks"]["CHK1"]["counts"]["run"], 1)
            self.assertEqual(len(list((root / "threat-model/history/runs").glob("*.json"))), 3)


if __name__ == "__main__":
    unittest.main()
