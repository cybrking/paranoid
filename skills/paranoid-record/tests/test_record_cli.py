import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'skills/paranoid-record/scripts/record_check.py'
INVENTORY = ROOT / 'skills/paranoid-gain/scripts/control_inventory.py'


class RecordCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('threat-model/\n__pycache__/\n.pytest_cache/\n')
        model = json.loads((ROOT / 'skills/paranoid/assets/example.json').read_text())
        model['checks'][0]['procedure'] = 'Never execute this text: touch MODEL_COMMAND_EXECUTED'
        (self.root / 'threat-model').mkdir()
        (self.root / 'threat-model/model.json').write_text(json.dumps(model))
        (self.root / 'mapping.json').write_text(json.dumps({'CHK1': ['test_app.App.test_denies_other_tenant']}))
        self.write_test(False)

    def write_test(self, secure):
        (self.root / 'test_app.py').write_text('import unittest\nclass App(unittest.TestCase):\n def test_denies_other_tenant(self):\n  self.assertEqual(' + ('403' if secure else '200') + ', 403)\n')

    def invoke(self, *args, timeout=20):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', str(self.root),
                                 '--mapping', 'mapping.json', *args], cwd=ROOT,
                                capture_output=True, text=True, timeout=timeout)
        self.assertTrue(result.stdout, result.stderr)
        return result, json.loads(result.stdout)

    def test_actual_fail_pass_stale_flow_and_readonly_views(self):
        result, failed = self.invoke()
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(failed['publication_state'], 'committed')
        self.assertEqual(failed['checks']['CHK1']['outcome'], 'fail')
        self.write_test(True)
        result, passed = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(passed['checks']['CHK1']['outcome'], 'pass')
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        read = subprocess.run([sys.executable, '-B', str(INVENTORY), str(self.root / 'threat-model/model.json'),
                               '--history', '--root', str(self.root), '--compare', '--control', 'CTRL1'],
                              capture_output=True, text=True)
        self.assertEqual(read.returncode, 0, read.stderr)
        report = json.loads(read.stdout)
        self.assertEqual(report['control']['checks'][0]['freshness'], 'matching')
        self.assertEqual(report['comparison']['outcome_changes'][0]['after'], 'pass')
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        (self.root / 'app.py').write_text('changed = True\n')
        read = subprocess.run([sys.executable, '-B', str(INVENTORY), str(self.root / 'threat-model/model.json'),
                               '--history', '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(json.loads(read.stdout)['controls'][0]['checks'][0]['freshness'], 'stale')
        self.assertFalse((self.root / 'MODEL_COMMAND_EXECUTED').exists())
        history = '\n'.join(p.read_text() for p in (self.root / 'threat-model/history/runs').glob('*.json'))
        self.assertNotIn('test_denies_other_tenant', history)

    def test_missing_mapping_and_invalid_root_never_execute(self):
        (self.root / 'mapping.json').write_text(json.dumps({'missing': ['test_app.App.test_denies_other_tenant']}))
        result, data = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(data['publication_state'], 'not_committed')
        self.assertFalse((self.root / 'threat-model/history/HEAD.json').exists())

    def test_timeout_and_incomplete_test_selection_never_pass(self):
        (self.root / 'test_app.py').write_text('import unittest,time\nclass App(unittest.TestCase):\n def test_denies_other_tenant(self): time.sleep(60)\n')
        result, data = self.invoke('--timeout', '0.2')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(data['checks']['CHK1']['outcome'], 'blocked')
        self.assertEqual(data['termination'], 'timeout')

    def test_real_pytest_producer_in_fresh_directory(self):
        try:
            import pytest
        except ImportError:
            self.skipTest('pytest producer is installed in integration CI')
        (self.root / 'mapping.json').write_text(json.dumps({'CHK1': [['pytest', 'test_junit', 'test_pass']]}))
        (self.root / 'test_junit.py').write_text('def test_pass():\n assert 1 == 1\n')
        result, data = self.invoke('--adapter', 'junit', '--', sys.executable, '-B', '-m', 'pytest',
                                   '-p', 'no:cacheprovider', '-q', 'test_junit.py', '--junitxml={report_dir}/report.xml')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(data['checks']['CHK1']['outcome'], 'pass')

    def test_external_or_malformed_junit_reports_are_not_evidence(self):
        (self.root / 'mapping.json').write_text(json.dumps({'CHK1': [['s', 'C', 'test']]}))
        outside = self.root / 'old.xml'
        outside.write_text('<testsuite name="s"><testcase classname="C" name="test"/></testsuite>')
        result, data = self.invoke('--adapter', 'junit', '--', sys.executable, '-c', 'pass', '{report_dir}/missing.xml')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(data['checks']['CHK1']['outcome'], 'blocked')
        result, data = self.invoke('--adapter', 'junit', '--', sys.executable, '-c',
                                   'from pathlib import Path; import sys; Path(sys.argv[1]).symlink_to(sys.argv[2])',
                                   '{report_dir}/bad.xml', str(outside))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(data['checks']['CHK1']['outcome'], 'blocked')
