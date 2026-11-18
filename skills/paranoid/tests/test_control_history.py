import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from control_history import (HistoryError, PublicationError, capture_inputs, definitions,
                             history_report, load_history, load_model, make_bundle, publish)


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('threat-model/\n__pycache__/\n')
        (self.root / 'app.py').write_text('value = 1\n')
        self.model = json.loads((Path(__file__).resolve().parents[1] / 'assets/example.json').read_text())
        self.path = self.root / 'threat-model/model.json'
        self.path.parent.mkdir()
        self.path.write_text(json.dumps(self.model))

    def record(self, outcome='pass', parent=None, model=None):
        model = model or self.model
        source = capture_inputs(self.root, model)
        obs = {'CHK1': {'outcome': outcome, 'reason': 'tests_passed' if outcome == 'pass' else 'test_failure',
                       'counts': {'run': 1, 'passed': int(outcome == 'pass'), 'failed': int(outcome == 'fail'), 'errors': 0, 'skipped': 0},
                       'test_ids': ['a' * 64]}}
        bundle = make_bundle(model, source, obs, parent=parent, adapter='unittest', exit_code=int(outcome != 'pass'))
        publish(self.root, bundle, self.path)
        return bundle

    def test_real_history_and_live_source_freshness_without_writes(self):
        self.assertEqual(load_model(self.path), self.model)
        self.assertIsNone(load_history(self.root))
        first = self.record()
        before = {p: p.read_bytes() for p in self.path.parent.rglob('*') if p.is_file()}
        report = history_report(self.root, self.path, compare='previous')
        self.assertEqual(report['controls'][0]['checks'][0]['freshness'], 'matching')
        self.assertEqual(report['comparison']['state'], 'no_baseline')
        self.assertEqual(before, {p: p.read_bytes() for p in self.path.parent.rglob('*') if p.is_file()})
        (self.root / 'app.py').write_text('value = 2\n')
        self.assertEqual(history_report(self.root, self.path)['controls'][0]['checks'][0]['freshness'], 'stale')
        self.assertEqual(load_history(self.root)['run_id'], first['run_id'])

    def test_latest_failed_attempt_supersedes_pass_and_retains_definitions(self):
        first = self.record()
        second = self.record('fail', first)
        self.assertEqual(history_report(self.root, self.path, compare='previous')['comparison']['outcome_changes'][0]['after'], 'fail')
        self.assertEqual(load_history(self.root, first['run_id'])['latest']['CHK1']['outcome'], 'pass')
        self.assertEqual(load_history(self.root)['latest']['CHK1']['outcome'], 'fail')
        changed = copy.deepcopy(self.model)
        changed['controls'][0]['requirement'] += ' and recheck ownership'
        self.assertNotEqual(definitions(changed)['checks']['CHK1']['revision'], definitions(self.model)['checks']['CHK1']['revision'])
        self.assertNotEqual(first['run_id'], second['run_id'])

    def test_unselected_check_keeps_its_original_observation(self):
        model = copy.deepcopy(self.model)
        model['checks'].append({**model['checks'][0], 'id': 'CHK2'})
        model['controls'][0]['check_ids'].append('CHK2')
        self.path.write_text(json.dumps(model))
        source = capture_inputs(self.root, model)
        obs = {'CHK1': {'outcome': 'pass', 'reason': 'tests_passed', 'counts': {'run': 1, 'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0}, 'test_ids': ['a' * 64]}}
        first = make_bundle(model, source, obs, adapter='unittest', exit_code=0)
        publish(self.root, first, self.path)
        obs = {'CHK2': obs['CHK1']}
        second = make_bundle(model, source, obs, parent=first, adapter='unittest', exit_code=0)
        publish(self.root, second, self.path)
        self.assertEqual(second['latest']['CHK1']['run_id'], first['run_id'])
        self.assertEqual(second['latest']['CHK2']['run_id'], second['run_id'])
        self.assertEqual(len(history_report(self.root, self.path)['controls'][0]['checks']), 2)
        changed = history_report(self.root, self.path, compare='previous')['comparison']['outcome_changes']
        self.assertIn({'check_id': 'CHK2', 'before': 'not_run', 'after': 'pass'}, changed)

    def test_conflict_corruption_path_escape_and_unknown_control_are_errors(self):
        first = self.record()
        with self.assertRaises(PublicationError) as error:
            self.record()
        self.assertEqual(error.exception.state, 'not_committed')
        self.assertEqual(load_history(self.root)['run_id'], first['run_id'])
        with self.assertRaises(HistoryError):
            load_history(self.root, '../model')
        with self.assertRaises(HistoryError):
            history_report(self.root, self.path, control='missing')
        (self.root / 'threat-model/history/HEAD.json').write_text('{}')
        with self.assertRaises(HistoryError):
            load_history(self.root)

    def test_input_scope_detects_untracked_delete_and_rejects_symlinks(self):
        initial = capture_inputs(self.root, self.model)
        (self.root / 'new.txt').write_text('new')
        self.assertNotEqual(initial['digest'], capture_inputs(self.root, self.model)['digest'])
        (self.root / 'new.txt').unlink()
        self.assertEqual(initial['digest'], capture_inputs(self.root, self.model)['digest'])
        (self.root / 'escape').symlink_to('/etc/passwd')
        with self.assertRaises(HistoryError):
            capture_inputs(self.root, self.model)

    def test_failures_on_each_side_of_head_switch_preserve_prior_bundles(self):
        first = self.record()
        source = capture_inputs(self.root, self.model)
        second = make_bundle(self.model, source, {}, parent=first, adapter='unittest', exit_code=1)
        with patch('control_history.os.replace', side_effect=OSError('synthetic')):
            with self.assertRaises(PublicationError) as error:
                publish(self.root, second, self.path)
        self.assertEqual(error.exception.state, 'not_committed')
        self.assertEqual(load_history(self.root)['run_id'], first['run_id'])
        third = make_bundle(self.model, source, {}, parent=first, adapter='unittest', exit_code=1)
        from control_history import sync_directory
        def fail_after_head(path):
            if Path(path).name == 'history':
                raise OSError('synthetic')
            return sync_directory(path)
        with patch('control_history.sync_directory', side_effect=fail_after_head):
            with self.assertRaises(PublicationError) as error:
                publish(self.root, third, self.path)
        self.assertEqual(error.exception.state, 'unknown')
        self.assertEqual(load_history(self.root)['run_id'], third['run_id'])
        self.assertEqual(load_history(self.root, first['run_id'])['latest']['CHK1']['outcome'], 'pass')

    def test_invalid_model_and_unknown_read_identity_never_claim_matching(self):
        self.record()
        with patch('control_history.capture_inputs', side_effect=HistoryError('input_unavailable')):
            report = history_report(self.root, self.path)
        self.assertEqual(report['controls'][0]['checks'][0]['freshness'], 'unknown')
        self.path.write_text('{"bad": true}')
        with self.assertRaises(HistoryError):
            load_model(self.path)

    def test_deleted_tracked_file_is_a_distinct_recordable_snapshot(self):
        subprocess.run(['git', '-C', str(self.root), 'add', 'app.py'], check=True)
        original = capture_inputs(self.root, self.model)
        (self.root / 'app.py').unlink()
        changed = capture_inputs(self.root, self.model)
        self.assertNotEqual(original['digest'], changed['digest'])
        self.assertNotIn('app.py', changed['files'])
        with self.assertRaises(HistoryError):
            capture_inputs(self.root, self.model, includes=['app.py'])

    def test_active_lock_is_not_stolen_and_corrupted_input_digest_is_denied(self):
        first = self.record()
        lock = self.root / 'threat-model/history/.publish.lock'
        lock.mkdir()
        (lock / 'owner.json').write_text('{"pid":1}')
        candidate = make_bundle(self.model, capture_inputs(self.root, self.model), {}, parent=first)
        with self.assertRaises(PublicationError):
            publish(self.root, candidate, self.path, lock_wait=0)
        self.assertTrue(lock.is_dir())
        self.assertEqual(load_history(self.root)['run_id'], first['run_id'])
        candidate['inputs']['files']['forged.py'] = 'b' * 64
        from control_history import validate_bundle
        with self.assertRaisesRegex(HistoryError, 'input_digest'):
            validate_bundle(candidate)

    def test_cleanup_failure_after_head_switch_is_reported_as_unknown(self):
        first = self.record()
        candidate = make_bundle(self.model, capture_inputs(self.root, self.model), {}, parent=first)
        original = Path.unlink
        def fail_owned_stage(path, *args, **kwargs):
            if path.name == '.' + candidate['run_id'] + '.tmp':
                raise PermissionError('synthetic')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'unlink', fail_owned_stage):
            with self.assertRaises(PublicationError) as error:
                publish(self.root, candidate, self.path)
        self.assertEqual(error.exception.state, 'unknown')
        self.assertEqual(load_history(self.root)['run_id'], candidate['run_id'])
        self.assertFalse((self.root / 'threat-model/history/.publish.lock').exists())

    def test_git_revision_is_informational_and_not_an_execution_claim(self):
        source = capture_inputs(self.root, self.model)
        self.assertIsNone(source['git']['head'])
        self.assertTrue(source['git']['dirty'])
        self.assertEqual(source['model_digest'], __import__('control_history').digest(self.model))

    def test_corrupt_parent_after_preparation_blocks_publication(self):
        first = self.record()
        candidate = make_bundle(self.model, capture_inputs(self.root, self.model), {}, parent=first)
        head_path = self.root / 'threat-model/history/HEAD.json'
        head = json.loads(head_path.read_text())
        head['sha256'] = 'f' * 64
        head_path.write_text(json.dumps(head))
        before = head_path.read_bytes()
        with self.assertRaises(PublicationError) as error:
            publish(self.root, candidate, self.path)
        self.assertEqual(error.exception.state, 'not_committed')
        self.assertEqual(head_path.read_bytes(), before)
        self.assertFalse((self.root / ('threat-model/history/runs/' + candidate['run_id'] + '.json')).exists())

    def test_read_detects_source_change_during_input_capture(self):
        self.record()
        original = capture_inputs
        calls = []
        def change_after_capture(*args, **kwargs):
            value = original(*args, **kwargs)
            if not calls:
                (self.root / 'app.py').write_text('value = 99\n')
            calls.append(True)
            return value
        with patch('control_history.capture_inputs', side_effect=change_after_capture):
            report = history_report(self.root, self.path)
        self.assertNotEqual(report['controls'][0]['checks'][0]['freshness'], 'matching')

    def test_failed_confirmation_capture_never_claims_matching(self):
        self.record()
        source = capture_inputs(self.root, self.model)
        with patch('control_history.capture_inputs', side_effect=[source, HistoryError('input_unavailable')]):
            report = history_report(self.root, self.path)
        self.assertEqual(report['controls'][0]['checks'][0]['freshness'], 'unknown')
        self.assertIsNone(report['scope_digest'])
        self.assertEqual(report['source_error'], 'input_unavailable')

    @unittest.skipUnless(__import__('os').name == 'posix', 'local POSIX process groups')
    def test_completed_leader_does_not_leave_owned_descendant_alive(self):
        import os
        import select
        from control_history import run_process
        request, response, ready = (self.root / p for p in ('request', 'response', 'ready'))
        os.mkfifo(request)
        os.mkfifo(response)
        read_fd = os.open(response, os.O_RDONLY | os.O_NONBLOCK)
        write_fd = os.open(request, os.O_RDWR | os.O_NONBLOCK)
        child = ('import os; from pathlib import Path; '
                 'out=os.open(' + repr(str(response)) + ',os.O_WRONLY); '
                 'inp=os.open(' + repr(str(request)) + ',os.O_RDONLY); '
                 'os.write(out,b"R"); Path(' + repr(str(ready)) + ').touch(); '
                 'data=os.read(inp,1); os.write(out,b"A") if data else None')
        leader = ('import subprocess,sys,time; from pathlib import Path; '
                  'subprocess.Popen([sys.executable,"-c",' + repr(child) + '], '
                  'stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
                  'p=Path(' + repr(str(ready)) + ')\nwhile not p.exists(): time.sleep(0.01)\n')
        try:
            result = run_process([sys.executable, '-c', leader], self.root, timeout=3)
            self.assertEqual(result['termination'], 'completed')
            self.assertEqual(os.read(read_fd, 1), b'R')
            os.write(write_fd, b'G')
            self.assertTrue(select.select([read_fd], [], [], 3)[0])
            self.assertNotEqual(os.read(read_fd, 1), b'A')
        finally:
            os.write(write_fd, b'G')
            os.close(write_fd)
            os.close(read_fd)

    def test_two_independent_writers_cannot_lose_an_observation(self):
        import time
        from control_history import encoded
        source = capture_inputs(self.root, self.model)
        candidates = [make_bundle(self.model, source, {}, adapter='unittest') for _ in range(2)]
        paths = []
        for i, bundle in enumerate(candidates):
            path = self.path.parent / ('candidate' + str(i) + '.json')
            path.write_bytes(encoded(bundle))
            paths.append(path)
        code = """import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from control_history import publish,read_json,PublicationError
root=Path(sys.argv[2]); candidate=Path(sys.argv[3])
candidate.with_suffix('.ready').touch()
while not (root/'threat-model/start').exists(): time.sleep(0.01)
try:
 publish(root,read_json(candidate),root/'threat-model/model.json')
 print('committed')
except PublicationError as exc:
 print(exc.state)
"""
        processes = [subprocess.Popen([sys.executable, '-B', '-c', code,
                                       str(Path(__file__).resolve().parents[1] / 'scripts'),
                                       str(self.root), str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for path in paths]
        try:
            deadline = time.monotonic() + 5
            while not all(path.with_suffix('.ready').exists() for path in paths):
                if time.monotonic() > deadline:
                    self.fail('writers did not reach ready barrier')
                time.sleep(0.01)
            (self.path.parent / 'start').touch()
            outputs = [p.communicate(timeout=5) for p in processes]
            self.assertEqual(sorted(stdout.strip() for stdout, _ in outputs), [b'committed', b'not_committed'])
            self.assertTrue(all(p.returncode == 0 for p in processes), outputs)
            self.assertEqual(len(list((self.path.parent / 'history/runs').glob('*.json'))), 1)
            self.assertIn(load_history(self.root)['run_id'], [b['run_id'] for b in candidates])
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                process.communicate()
