"""Explicitly run approved tests and retain private, revision-bound observations."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

CORE = Path(__file__).resolve().parents[2] / 'paranoid' / 'scripts'
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(CORE))
try:
    if not all(p.is_file() for p in (CORE / 'control_history.py', CORE / 'validate_model.py',
                                     Path(__file__).with_name('result_adapters.py'))):
        raise ImportError('installed_component_unavailable')
    from control_history import (HISTORY, MAX_BYTES, HistoryError, PublicationError,
                                 capture_inputs, contained, digest, encoded, load_history,
                                 load_model, make_bundle, publish, read_json, run_process)
    from result_adapters import check_results, parse_junit, read_native, test_id
except ImportError:
    print(json.dumps({'error': 'installed_component_or_tooling_unavailable', 'publication_state': 'not_committed'}))
    sys.exit(2)


class PrivateParser(argparse.ArgumentParser):
    def error(self, message):
        raise HistoryError('invalid_arguments')


def read_bytes(path):
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise HistoryError('invalid_result_file')
        data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HistoryError('result_size_limit')
    return data


def parse_reports(directory):
    if directory.is_symlink():
        raise HistoryError('result_symlink')
    cases = {}
    size = 0
    count = 0
    for root, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            if (Path(root) / name).is_symlink():
                raise HistoryError('result_symlink')
        for name in sorted(files):
            count += 1
            if count > 10000:
                raise HistoryError('result_file_limit')
            if Path(name).suffix.lower() != '.xml':
                continue
            data = read_bytes(Path(root) / name)
            size += len(data)
            if size > MAX_BYTES:
                raise HistoryError('result_size_limit')
            parsed = parse_junit(data)
            if set(parsed) & set(cases):
                raise HistoryError('duplicate_test_identity')
            cases.update(parsed)
    return encoded({'format_version': 1, 'cases': [{'test_id': k, 'outcome': v} for k, v in sorted(cases.items())]})


def mapping_for(value, model, adapter):
    checks = {c['id'] for c in model['checks']}
    if not isinstance(value, dict) or not value or len(value) > 10000:
        raise HistoryError('invalid_mapping')
    mapping = {}
    selectors = set()
    for check_id, identities in value.items():
        if check_id not in checks or not isinstance(identities, list) or not identities or len(identities) > 100000:
            raise HistoryError('invalid_mapping')
        wanted = []
        for identity in identities:
            if adapter == 'unittest':
                if not isinstance(identity, str):
                    raise HistoryError('invalid_mapping')
                wanted.append(test_id('unittest', identity))
                selectors.add(identity)
            else:
                if not isinstance(identity, list) or len(identity) != 3:
                    raise HistoryError('invalid_mapping')
                wanted.append(test_id('junit', *identity))
        if len(set(wanted)) != len(wanted):
            raise HistoryError('duplicate_mapping')
        mapping[check_id] = wanted
    return mapping, sorted(selectors)


def main():
    parser = PrivateParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Local Git repository root')
    parser.add_argument('--model', default='threat-model/model.json')
    parser.add_argument('--mapping', required=True, help='JSON check IDs to exact test identity lists')
    parser.add_argument('--adapter', choices=('unittest', 'junit'), default='unittest')
    parser.add_argument('--include', action='append', default=[], help='Additional ignored input file, relative to root')
    parser.add_argument('--exclude', action='append', default=[], help='Generated output path, relative to root')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('command', nargs=argparse.REMAINDER, help='JUnit only: explicit argv after --, with {report_dir}')
    try:
        args = parser.parse_args()
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if os.name != 'posix' or not 0 < args.timeout <= 300:
            raise HistoryError('unsupported_process_capability')
        if (args.adapter == 'unittest' and command) or (args.adapter == 'junit' and not command):
            raise HistoryError('explicit_adapter_command_required')
        root = args.root.resolve()
        model_path = contained(root, args.model)
        model = load_model(model_path)
        mapping, selectors = mapping_for(read_json(contained(root, args.mapping)), model, args.adapter)
        parent = load_history(root)
        source = capture_inputs(root, model, args.include, args.exclude)
        directory = contained(root, HISTORY.as_posix())
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        cases = {}
        with tempfile.TemporaryDirectory(prefix='.run-', dir=directory) as temporary:
            temporary = Path(temporary)
            reports = temporary / 'reports'
            reports.mkdir(mode=0o700)
            native = temporary / 'native.json'
            if args.adapter == 'unittest':
                if not Path(__file__).with_name('unittest_runner.py').is_file():
                    raise HistoryError('installed_runner_unavailable')
                command = [sys.executable, '-B', str(Path(__file__).with_name('unittest_runner.py')),
                           '--result', str(native), *selectors]
            else:
                if not any('{report_dir}' in arg for arg in command):
                    raise HistoryError('fresh_report_destination_required')
                command = [arg.replace('{report_dir}', str(reports)) for arg in command]
            try:
                run = run_process(command, root, timeout=args.timeout,
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            except OSError:
                run = {'exit_code': None, 'termination': 'launch_failed', 'duration': 0}
            result_error = None
            try:
                if args.adapter == 'unittest':
                    cases = read_native(read_bytes(native))
                else:
                    parsed = run_process([sys.executable, '-B', str(Path(__file__).resolve()),
                                          '--parse-junit', str(reports)], root, timeout=10, capture=True)
                    if parsed['exit_code'] or parsed['termination'] != 'completed':
                        raise HistoryError('invalid_junit_result')
                    cases = read_native(parsed['stdout'])
            except (OSError, ValueError, UnicodeError):
                result_error = 'invalid_result'
        matching = False
        try:
            matching = source['digest'] == capture_inputs(root, load_model(model_path), args.include, args.exclude)['digest']
        except HistoryError:
            pass
        observations = check_results(mapping, cases, run['exit_code'],
                                     result_error if result_error and run['termination'] == 'completed' else run['termination'])
        bundle = make_bundle(model, source, observations, parent=parent, adapter=args.adapter,
                             exit_code=run['exit_code'], termination=run['termination'],
                             source_matching=matching, duration=run['duration'])
        publish(root, bundle, model_path)
        print(json.dumps({'run_id': bundle['run_id'], 'publication_state': 'committed',
                          'checks': observations, 'freshness': 'matching' if matching else 'unknown',
                          'termination': run['termination'], 'security_effectiveness': 'not_assessed'}))
        return 0 if matching and all(v['outcome'] == 'pass' for v in observations.values()) else 1
    except PublicationError as exc:
        print(json.dumps({'error': str(exc), 'publication_state': exc.state, 'run_id': exc.run_id}))
        return 2
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        error = str(exc) if isinstance(exc, HistoryError) else 'recording_unavailable'
        print(json.dumps({'error': error, 'publication_state': 'not_committed'}))
        return 2


if __name__ == '__main__':
    if sys.argv[1:2] == ['--parse-junit']:
        try:
            if len(sys.argv) != 3:
                raise HistoryError('invalid_parser_arguments')
            data = parse_reports(Path(sys.argv[2]))
            if len(data) > MAX_BYTES:
                raise HistoryError('normalized_result_limit')
            sys.stdout.buffer.write(data)
        except (OSError, ValueError, UnicodeError, RecursionError):
            sys.exit(2)
    else:
        sys.exit(main())
