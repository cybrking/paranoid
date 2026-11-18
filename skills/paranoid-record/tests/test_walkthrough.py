import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
WALKTHROUGH = ROOT / 'examples/control-evidence-walkthrough/walkthrough.py'


class WalkthroughTests(unittest.TestCase):
    def test_real_lifecycle_repeats_without_residue(self):
        with tempfile.TemporaryDirectory(prefix='walkthrough test ') as directory:
            temporary = Path(directory)
            workspaces = []
            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, '-B', str(WALKTHROUGH)], cwd=ROOT,
                    env=dict(os.environ, TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE='1'),
                    capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                workspaces.append(report['workspace'])
                failed, passed, stale = report['steps']
                self.assertEqual([step['label'] for step in report['steps']], ['fail', 'pass', 'stale'])
                self.assertEqual([step['outcome'] for step in report['steps']], ['fail', 'pass', 'pass'])
                self.assertEqual([step['freshness'] for step in report['steps']],
                                 ['matching', 'matching', 'stale'])
                self.assertEqual(failed['counts']['failed'], 1)
                self.assertEqual(passed['counts']['passed'], 1)
                self.assertNotEqual(failed['run_id'], passed['run_id'])
                self.assertEqual(stale['run_id'], passed['run_id'])
                self.assertEqual(report['history_runs'], 2)
                self.assertEqual(report['comparison']['outcome_changes'],
                                 [{'check_id': 'CHK1', 'before': 'fail', 'after': 'pass'}])
                self.assertTrue(report['cleaned_up'])
                self.assertFalse(Path(report['workspace']).exists())
                self.assertEqual(list(temporary.iterdir()), [])
                self.assertEqual(report['security_effectiveness'], 'not_assessed')
            self.assertNotEqual(*workspaces)


if __name__ == '__main__':
    unittest.main()
