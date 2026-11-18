import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class HistoryPackageTests(unittest.TestCase):
    def test_installed_siblings_and_legacy_inventory_without_validation_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            install = work / 'installed with spaces/skills'
            for name in ('paranoid', 'paranoid-gain', 'paranoid-record'):
                shutil.copytree(ROOT / 'skills' / name, install / name,
                                ignore=shutil.ignore_patterns('__pycache__'))
            model = work / 'model.json'
            model.write_text(json.dumps({'model_id': 'partial', 'scope': {'snapshot': 's'},
                                         'controls': [], 'checks': []}))
            gain = install / 'paranoid-gain/scripts/control_inventory.py'
            plain = subprocess.run([sys.executable, '-I', '-S', '-B', str(gain), str(model)],
                                   cwd=work, capture_output=True, text=True)
            self.assertEqual(plain.returncode, 0, plain.stderr)
            self.assertEqual(json.loads(plain.stdout)['identified_controls'], 0)
            repo = work / 'project'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / '.gitignore').write_text('threat-model/\n')
            (repo / 'threat-model').mkdir()
            (repo / 'threat-model/model.json').write_bytes((install / 'paranoid/assets/example.json').read_bytes())
            mapping = repo / 'mapping.json'
            mapping.write_text(json.dumps({'CHK1': ['test_app.App.test_ok']}))
            (repo / 'test_app.py').write_text('import unittest\nclass App(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
            record = install / 'paranoid-record/scripts/record_check.py'
            result = subprocess.run([sys.executable, '-B', str(record), '--root', str(repo), '--mapping', 'mapping.json'],
                                    cwd=work, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            read = subprocess.run([sys.executable, str(gain), str(repo / 'threat-model/model.json'),
                                   '--history', '--root', str(repo)], cwd=work, capture_output=True, text=True)
            self.assertEqual(read.returncode, 0, read.stderr)
            self.assertEqual(json.loads(read.stdout)['controls'][0]['checks'][0]['freshness'], 'matching')
            self.assertFalse(list(install.rglob('*.pyc')), 'read-only reports must not write plugin caches')
            shutil.rmtree(install / 'paranoid')
            marker = work / 'POISON_EXECUTED'
            (work / 'control_history.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').touch()\nraise ImportError("poison")\n')
            missing = subprocess.run([sys.executable, '-B', str(record), '--root', str(repo), '--mapping', 'mapping.json'],
                                     cwd=work, env=dict(os.environ, PYTHONPATH=str(work)), capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertFalse(marker.exists(), 'missing sibling must never import a project module')
