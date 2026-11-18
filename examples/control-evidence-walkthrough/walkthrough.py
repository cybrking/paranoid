#!/usr/bin/env python3
"""Observe fail -> pass -> stale in a disposable fictional repository."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
RECORDER = ROOT / 'skills/paranoid-record/scripts/record_check.py'
INVENTORY = ROOT / 'skills/paranoid-gain/scripts/control_inventory.py'
SELECTOR = 'test_app.AuthorizationTests.test_denies_other_tenant'
INSECURE = '''def export_records(authenticated_tenant, requested_tenant):
    return ['fictional record']
'''
SECURE = '''def export_records(authenticated_tenant, requested_tenant):
    if requested_tenant != authenticated_tenant:
        raise PermissionError('tenant mismatch')
    return ['fictional record']
'''
TEST = '''import unittest
from app import export_records


class AuthorizationTests(unittest.TestCase):
    def test_denies_other_tenant(self):
        self.assertEqual(export_records('tenant-a', 'tenant-a'), ['fictional record'])
        with self.assertRaises(PermissionError):
            export_records('tenant-a', 'tenant-b')
'''


def invoke(script, root, arguments, expected_code=0):
    done = subprocess.run([sys.executable, '-B', str(script), *arguments], cwd=root,
                          env=dict(os.environ, TMPDIR=str(root / 'threat-model')),
                          capture_output=True, text=True, timeout=30)
    if done.returncode != expected_code:
        raise RuntimeError(f'{script.name}: exit {done.returncode}\n{done.stdout}{done.stderr}')
    return json.loads(done.stdout)


def main():
    steps = []
    with tempfile.TemporaryDirectory(prefix='paranoid-walkthrough-') as directory:
        root = Path(directory)
        (root / 'threat-model').mkdir()
        subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True,
                       env=dict(os.environ, TMPDIR=str(root / 'threat-model')))
        (root / '.gitignore').write_text('threat-model/\n__pycache__/\n', encoding='utf-8')
        model = json.loads((ROOT / 'skills/paranoid/assets/example.json').read_text(encoding='utf-8'))
        model['controls'][0]['requirement'] = 'Deny cross-tenant exports with PermissionError before returning records.'
        model['checks'][0]['procedure'] = f'Run {SELECTOR} in this isolated fictional repository.'
        (root / 'threat-model/model.json').write_text(json.dumps(model), encoding='utf-8')
        (root / 'mapping.json').write_text(json.dumps({'CHK1': [SELECTOR]}), encoding='utf-8')
        (root / 'test_app.py').write_text(TEST, encoding='utf-8')
        app = root / 'app.py'
        record_args = ['--root', str(root), '--mapping', 'mapping.json', '--timeout', '10']
        for label, source, exit_code in [('fail', INSECURE, 1), ('pass', SECURE, 0)]:
            app.write_text(source, encoding='utf-8')
            recorded = invoke(RECORDER, root, record_args, exit_code)
            check = recorded['checks']['CHK1']
            assert recorded['publication_state'] == 'committed', recorded
            assert check['outcome'] == label and recorded['freshness'] == 'matching', recorded
            steps.append({'label': label, 'run_id': recorded['run_id'],
                          'outcome': check['outcome'], 'counts': check['counts'],
                          'freshness': recorded['freshness']})

        read_args = [str(root / 'threat-model/model.json'), '--history', '--root', str(root),
                     '--compare', '--control', 'CTRL1']
        matching = invoke(INVENTORY, root, read_args)
        assert matching['control']['checks'][0]['freshness'] == 'matching', matching
        app.write_text(SECURE + '\n# Source changed after the recorded pass.\n', encoding='utf-8')
        report = invoke(INVENTORY, root, read_args)
        check = report['control']['checks'][0]
        assert check['freshness'] == 'stale' and check['outcome'] == 'pass', report
        assert report['run_id'] == steps[-1]['run_id'], report
        history_runs = len(list((root / 'threat-model/history/runs').glob('*.json')))
        assert history_runs == 2, history_runs
        steps.append({'label': 'stale', 'run_id': report['run_id'],
                      'outcome': check['outcome'], 'freshness': check['freshness']})
        summary = {'workspace': str(root), 'steps': steps, 'history_runs': history_runs,
                   'comparison': report['comparison'],
                   'security_effectiveness': report['security_effectiveness']}
    summary['cleaned_up'] = not root.exists()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
