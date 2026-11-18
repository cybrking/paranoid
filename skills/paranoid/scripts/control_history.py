"""Versioned local check history; recorded observations are not security assurance."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import time
import uuid

from jsonschema import Draft202012Validator
from validate_model import validate

MAX_BYTES = 2 * 1024 * 1024
MAX_FILES = 10000
MAX_INPUT_BYTES = 1024 * 1024 * 1024
ID = re.compile(r'^[0-9a-f]{32}$')
HASH = re.compile(r'^[0-9a-f]{64}$')
HISTORY = Path('threat-model/history')


class HistoryError(ValueError):
    pass


class PublicationError(HistoryError):
    def __init__(self, code, state='not_committed', run_id=None):
        super().__init__(code)
        self.state = state
        self.run_id = run_id


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise HistoryError('duplicate_json_key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise HistoryError('invalid_json_number')


def read_json(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as f:
            info = os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise HistoryError('input_limit_or_type')
            data = f.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HistoryError('input_limit')
        return json.loads(data, object_pairs_hook=_object, parse_constant=_invalid_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise HistoryError('input_unavailable_or_invalid') from exc


def load_model(path):
    model = read_json(path)
    if validate(model):
        raise HistoryError('invalid_model')
    return model


def run_process(argv, cwd, timeout=300, capture=False, env=None):
    """Drain bounded output and cancel only the explicitly launched process group."""
    if os.name != 'posix' or not 0 < timeout <= 300:
        raise HistoryError('unsupported_process_capability')
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, env=env, stdin=subprocess.DEVNULL)
    output = bytearray()
    size = 0
    termination = 'completed'
    start = time.monotonic()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ)
            selector.register(proc.stderr, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() - start > timeout:
                    termination = 'timeout'
                    break
                for key, _ in selector.select(min(0.1, timeout)):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(chunk)
                    if size > MAX_BYTES:
                        termination = 'output_limit'
                        break
                    if capture and key.fileobj is proc.stdout:
                        output.extend(chunk)
                if termination != 'completed':
                    break
        if termination == 'completed':
            try:
                proc.wait(timeout=max(0.01, timeout - (time.monotonic() - start)))
            except subprocess.TimeoutExpired:
                termination = 'timeout'
    except KeyboardInterrupt:
        termination = 'interrupted'
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        proc.stdout.close()
        proc.stderr.close()
    return {'exit_code': proc.returncode, 'termination': termination,
            'stdout': bytes(output) if capture else b'', 'duration': time.monotonic() - start}


def _relative(value):
    if not isinstance(value, str) or not value:
        raise HistoryError('invalid_scoped_path')
    p = Path(value)
    if p.is_absolute() or '..' in p.parts or p == Path('.'):
        raise HistoryError('invalid_scoped_path')
    return p.as_posix()


def contained(root, relative):
    relative = _relative(relative)
    current = Path(root)
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise HistoryError('input_symlink')
    return current


def capture_inputs(root, model, includes=(), excludes=()):
    root = Path(root).resolve()
    includes = sorted({_relative(p) for p in includes})
    excludes = sorted({_relative(p) for p in excludes} | {HISTORY.as_posix()})
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    command = ['git', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
               '-c', 'core.hooksPath=/dev/null', '-C', str(root)]
    try:
        top = run_process(command + ['rev-parse', '--show-toplevel'], root, timeout=10, capture=True, env=env)
        if top['termination'] != 'completed' or top['exit_code'] or Path(os.fsdecode(top['stdout']).strip()).resolve() != root:
            raise HistoryError('repository_root_required')
        result = run_process(command + ['ls-files', '-co', '--exclude-standard', '-z'], root,
                             timeout=10, capture=True, env=env)
    except OSError as exc:
        raise HistoryError('git_unavailable') from exc
    if result['exit_code'] or result['termination'] != 'completed':
        raise HistoryError('input_inventory_unavailable')
    names = {os.fsdecode(p) for p in result['stdout'].split(b'\0') if p} | set(includes)
    if len(names) > MAX_FILES:
        raise HistoryError('input_file_limit')
    files = {}
    total = 0
    for name in sorted(names):
        name = _relative(name)
        if any(name == ex or name.startswith(ex + '/') for ex in excludes):
            continue
        path = contained(root, name)
        try:
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as f:
                info = os.fstat(f.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise HistoryError('unsupported_input_type')
                total += info.st_size
                if total > MAX_INPUT_BYTES:
                    raise HistoryError('input_byte_limit')
                sha = hashlib.sha256()
                remaining = info.st_size
                while True:
                    data = f.read(min(65536, remaining + 1))
                    if not data:
                        break
                    remaining -= len(data)
                    if remaining < 0:
                        raise HistoryError('input_changed')
                    sha.update(data)
                if remaining:
                    raise HistoryError('input_changed')
                files[name] = sha.hexdigest()
        except FileNotFoundError as exc:
            if name in includes:
                raise HistoryError('input_unavailable') from exc
        except OSError as exc:
            raise HistoryError('input_unavailable') from exc
    scope = {'includes': includes, 'excludes': excludes}
    value = {'model_digest': digest(model), 'scope': scope, 'files': files}
    head = run_process(command + ['rev-parse', '--verify', 'HEAD'], root, timeout=10, capture=True, env=env)
    status = run_process(command + ['status', '--porcelain', '-z'], root, timeout=10, capture=True, env=env)
    if 'interrupted' in (head['termination'], status['termination']):
        raise HistoryError('interrupted')
    revision = head['stdout'].decode('ascii', errors='replace').strip() if head['exit_code'] == 0 else None
    if revision is not None and not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', revision):
        raise HistoryError('invalid_git_revision')
    git = {'head': revision, 'dirty': bool(status['stdout']) if status['exit_code'] == 0 and status['termination'] == 'completed' else None}
    return {**value, 'digest': digest(value), 'git': git}


def definitions(model):
    controls, checks = {}, {}
    by_check = {c['id']: c for c in model['checks']}
    for c in model['controls']:
        revision = digest({'requirement': c['requirement'], 'checks': [by_check[k] for k in c['check_ids']]})
        controls[c['id']] = {'id': c['id'], 'requirement': c['requirement'], 'status': c['status'],
                             'check_ids': c['check_ids'], 'revision': revision}
    for c in model['checks']:
        checks[c['id']] = {'id': c['id'], 'control_id': c['control_id'], 'procedure': c['procedure'],
                           'expected': c['expected'], 'revision': digest({
                               'control_revision': controls[c['control_id']]['revision'],
                               'procedure': c['procedure'], 'expected': c['expected']})}
    return {'model_id': model['model_id'], 'snapshot': model['scope']['snapshot'],
            'controls': controls, 'checks': checks}


def validate_bundle(bundle):
    schema = json.loads((Path(__file__).resolve().parents[1] / 'references/run.schema.json').read_text())
    if len(encoded(bundle)) > MAX_BYTES or not Draft202012Validator(schema).is_valid(bundle):
        raise HistoryError('invalid_history_bundle')
    inputs = bundle['inputs']
    if (inputs['model_digest'] != bundle['model_digest'] or inputs['digest'] != digest({
            k: inputs[k] for k in ('model_digest', 'scope', 'files')})):
        raise HistoryError('history_input_digest_mismatch')
    defs = bundle['definitions']
    if defs['model_id'] != bundle['model_id']:
        raise HistoryError('history_model_mismatch')
    for key, c in defs['controls'].items():
        if c['id'] != key or any(k not in defs['checks'] or defs['checks'][k]['control_id'] != key for k in c['check_ids']):
            raise HistoryError('history_control_link')
    for key, c in defs['checks'].items():
        if c['id'] != key or c['control_id'] not in defs['controls'] or key not in defs['controls'][c['control_id']]['check_ids']:
            raise HistoryError('history_check_link')
    for key, observation in bundle['latest'].items():
        if key not in defs['checks'] or observation['counts']['run'] != sum(observation['counts'][k] for k in ('passed', 'failed', 'errors', 'skipped')):
            raise HistoryError('history_observation_link')
        if observation['outcome'] == 'pass' and (observation['counts']['passed'] == 0 or observation['counts']['passed'] != observation['counts']['run'] or not observation['test_ids']):
            raise HistoryError('history_pass_without_tests')
    if any(k not in defs['checks'] for k in bundle['attempt']['check_ids']):
        raise HistoryError('history_attempt_link')
    return bundle


def _directory(root):
    return contained(Path(root).resolve(), HISTORY.as_posix())


def _head(root):
    directory = _directory(root)
    path = directory / 'HEAD.json'
    if not path.exists() and not path.is_symlink():
        return None
    value = read_json(path)
    if (not isinstance(value, dict) or set(value) != {'run_id', 'sha256', 'lineage'} or
            not ID.fullmatch(str(value['run_id'])) or not ID.fullmatch(str(value['lineage'])) or
            not HASH.fullmatch(str(value['sha256']))):
        raise HistoryError('invalid_history_head')
    return value


def load_history(root, run_id=None):
    head = _head(root)
    if run_id is None:
        if head is None:
            return None
        run_id = head['run_id']
    if not isinstance(run_id, str) or not ID.fullmatch(run_id):
        raise HistoryError('invalid_run_id')
    path = contained(Path(root).resolve(), (HISTORY / 'runs' / (run_id + '.json')).as_posix())
    bundle = validate_bundle(read_json(path))
    if bundle['run_id'] != run_id or (head and bundle['lineage'] != head['lineage']):
        raise HistoryError('history_lineage_mismatch')
    if head and run_id == head['run_id'] and digest(bundle) != head['sha256']:
        raise HistoryError('history_digest_mismatch')
    return bundle


def make_bundle(model, source, observations, parent=None, adapter='unittest', exit_code=0,
                termination='completed', source_matching=True, duration=0):
    defs = definitions(model)
    if parent and parent['model_id'] != model['model_id']:
        raise HistoryError('history_model_mismatch')
    run_id = uuid.uuid4().hex
    latest = {k: v for k, v in (parent['latest'].items() if parent else []) if k in defs['checks']}
    for check_id, value in observations.items():
        if check_id not in defs['checks']:
            raise HistoryError('unknown_check')
        latest[check_id] = {**value, 'run_id': run_id, 'observed_at': now(),
                            'check_revision': defs['checks'][check_id]['revision'],
                            'model_digest': source['model_digest'],
                            'input_digest': source['digest'] if source_matching else None}
    bundle = {'format_version': 1, 'run_id': run_id, 'lineage': parent['lineage'] if parent else uuid.uuid4().hex,
              'parent': parent['run_id'] if parent else None, 'recorded_at': now(),
              'parent_digest': digest(parent) if parent else None,
              'model_id': model['model_id'], 'model_digest': source['model_digest'],
              'inputs': source, 'definitions': defs, 'latest': latest,
              'attempt': {'adapter': adapter, 'exit_code': exit_code, 'termination': termination,
                          'duration': duration, 'check_ids': sorted(observations)}}
    return validate_bundle(bundle)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_new(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as f:
        f.write(encoded(value))
        f.flush()
        os.fsync(f.fileno())


def publish(root, bundle, model_path, lock_wait=5):
    validate_bundle(bundle)
    directory = _directory(root)
    switched = False
    locked = False
    stage = None
    problem = None
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        runs = contained(Path(root).resolve(), (HISTORY / 'runs').as_posix())
        runs.mkdir(exist_ok=True, mode=0o700)
        stage = directory / ('.' + bundle['run_id'] + '.tmp')
        _write_new(stage, bundle)
        head_tmp = directory / ('.' + bundle['run_id'] + '.head')
        lock = directory / '.publish.lock'
        start = time.monotonic()
        while True:
            try:
                lock.mkdir(mode=0o700)
                locked = True
                _write_new(lock / 'owner.json', {'pid': os.getpid(), 'run_id': bundle['run_id']})
                break
            except FileExistsError:
                if time.monotonic() - start >= lock_wait:
                    raise HistoryError('history_busy')
                time.sleep(0.02)
        head = _head(root)
        if (head['run_id'] if head else None) != bundle['parent'] or (head and head['lineage'] != bundle['lineage']):
            raise HistoryError('history_conflict')
        if head:
            previous = read_json(contained(Path(root).resolve(), (HISTORY / 'runs' / (head['run_id'] + '.json')).as_posix()))
            if head['sha256'] != bundle['parent_digest'] or digest(previous) != bundle['parent_digest']:
                raise HistoryError('history_parent_corrupt')
        if digest(read_json(model_path)) != bundle['model_digest']:
            raise HistoryError('model_changed')
        os.link(stage, runs / (bundle['run_id'] + '.json'), follow_symlinks=False)
        sync_directory(runs)
        _write_new(head_tmp, {'run_id': bundle['run_id'], 'sha256': digest(bundle), 'lineage': bundle['lineage']})
        os.replace(head_tmp, directory / 'HEAD.json')
        switched = True
        sync_directory(directory)
    except (OSError, HistoryError) as exc:
        code = str(exc) if isinstance(exc, HistoryError) else 'history_write_failed'
        problem = PublicationError(code, 'unknown' if switched else 'not_committed', bundle['run_id'])
    finally:
        cleanup = []
        if stage:
            cleanup.extend((stage, stage.with_suffix('.head')))
        if locked:
            cleanup.extend((directory / '.publish.lock/owner.json', directory / '.publish.lock'))
        for path in cleanup:
            try:
                if path == directory / '.publish.lock':
                    path.rmdir()
                else:
                    path.unlink(missing_ok=True)
            except OSError:
                if problem is None:
                    problem = PublicationError('history_cleanup_failed', 'unknown' if switched else 'not_committed', bundle['run_id'])
    if problem:
        raise problem
    return bundle['run_id']


def _rows(defs, latest, source):
    rows = []
    for control in defs['controls'].values():
        checks = []
        for check_id in control['check_ids']:
            c = defs['checks'][check_id]
            observation = latest.get(check_id)
            freshness = 'not_run'
            if observation:
                if source is None or observation['input_digest'] is None:
                    freshness = 'unknown'
                elif (observation['input_digest'] != source['digest'] or observation['model_digest'] != source['model_digest'] or
                      observation['check_revision'] != c['revision']):
                    freshness = 'stale'
                else:
                    freshness = 'matching'
            checks.append({**c, 'observation': observation, 'outcome': observation['outcome'] if observation else 'not_run',
                           'freshness': freshness, 'rerun_reason': None if freshness == 'matching' else freshness})
        rows.append({**control, 'checks': checks})
    return rows


def history_report(root, model_path, compare=None, control=None):
    model = load_model(model_path)
    defs = definitions(model)
    bundle = load_history(root)
    if bundle and bundle['model_id'] != model['model_id']:
        raise HistoryError('history_model_mismatch')
    latest = bundle['latest'] if bundle else {}
    source = None
    source_error = None
    try:
        scope = bundle['inputs']['scope'] if bundle else {}
        source = capture_inputs(root, model, scope.get('includes', ()), scope.get('excludes', ()))
        second = capture_inputs(root, load_model(model_path), scope.get('includes', ()), scope.get('excludes', ()))
        if source['digest'] != second['digest']:
            source = None
            source_error = 'inputs_changed_during_read'
    except HistoryError as exc:
        source = None
        source_error = str(exc)
    rows = _rows(defs, latest, source)
    report = {'model_id': model['model_id'], 'snapshot': model['scope']['snapshot'],
              'identified_controls': len(rows),
              'run_id': bundle['run_id'] if bundle else None, 'state': 'recorded_history' if bundle else 'no_history',
              'freshness_as_of': now(), 'scope_digest': source['digest'] if source else None,
              'source_error': source_error, 'controls': rows, 'security_effectiveness': 'not_assessed'}
    baseline = None
    if compare:
        wanted = bundle['parent'] if bundle and compare == 'previous' else compare if compare != 'previous' else None
        baseline = load_history(root, wanted) if wanted else None
        if baseline and baseline['model_id'] != model['model_id']:
            raise HistoryError('baseline_lineage_mismatch')
        if baseline and bundle and wanted == bundle['parent'] and digest(baseline) != bundle['parent_digest']:
            raise HistoryError('baseline_digest_mismatch')
        previous = baseline['definitions']['controls'] if baseline else {}
        current = defs['controls']
        changes = []
        if baseline:
            for key, value in latest.items():
                old = baseline['latest'].get(key)
                before = old['outcome'] if old else 'not_run'
                if before != value['outcome']:
                    changes.append({'check_id': key, 'before': before, 'after': value['outcome']})
        report['comparison'] = {'state': 'compared' if baseline else 'no_baseline',
                                'run_id': baseline['run_id'] if baseline else None,
                                'added': sorted(set(current) - set(previous)) if baseline else [],
                                'retired': sorted(set(previous) - set(current)) if baseline else [],
                                'changed': sorted(k for k in set(current) & set(previous) if current[k]['revision'] != previous[k]['revision']),
                                'outcome_changes': changes,
                                'needs_rerun': [c['id'] for row in rows for c in row['checks'] if c['freshness'] != 'matching']}
    if control:
        selected = next((row for row in rows if row['id'] == control), None)
        if selected is None and baseline and control in baseline['definitions']['controls']:
            selected = {'state': 'retired', **baseline['definitions']['controls'][control]}
        if selected is None:
            raise HistoryError('unknown_control')
        report['control'] = selected
    return report
