"""Run explicitly selected offline historical checks in their original source tree.

Recorded hashes are never translated or regenerated. A temporary source copy
contains the original, hash-verified executor bytes; every other source and all
evidence come from the working tree and remain subject to the existing checks.
This is not an execution/resume path for approved model experiments.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path('benchmarks/frozen-history-v1')
EXECUTOR = 'runaway/taste_executor.py'
ORIGINAL_SHA256 = '57b7165a596cc731547a804b7b81f2a2c22feaa14b44182f478f222acdebb041'
SOURCE_DIRS = ('runaway', 'benchmarks', 'scripts', 'tests', 'examples', 'web',
               'catalog', 'data', 'dashboard', 'docs', '.github')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root=ROOT):
    root = Path(root)
    value = json.loads((root / ARCHIVE / 'manifest.json').read_text())
    expected = {EXECUTOR: {'blob': 'taste_executor.py.txt', 'sha256': ORIGINAL_SHA256}}
    if value['schema_version'] != 1 or value['source_overrides'] != expected:
        raise ValueError('Unexpected historical source override')
    if sha(root / ARCHIVE / 'taste_executor.py.txt') != ORIGINAL_SHA256:
        raise ValueError('Historical executor snapshot differs')
    return value


def partition(root=ROOT):
    """Every test module is assigned once; new modules default to current code."""
    root = Path(root)
    all_modules = set()
    test_root = root / 'tests'
    for directory, subdirs, files in os.walk(test_root):
        directory = Path(directory)
        if directory != test_root and not (directory / '__init__.py').is_file():
            subdirs[:] = []
            continue
        for name in files:
            path = Path(name)
            if name.startswith('test') and path.suffix == '.py' and path.stem.isidentifier():
                relative = (directory / path.stem).relative_to(test_root)
                all_modules.add('.'.join(relative.parts))
    historical = manifest(root)['test_modules']
    if len(historical) != len(set(historical)) or not set(historical) <= all_modules:
        raise ValueError('Duplicate or missing historical test module')
    # The bug regression and the snapshot guard must always test live code.
    if {'test_taste_executor', 'test_frozen_history'} & set(historical):
        raise ValueError('Current executor regressions cannot use historical code')
    return sorted(all_modules - set(historical)), sorted(historical)


@contextmanager
def snapshot(root=ROOT):
    root = Path(root).resolve()
    manifest(root)
    with tempfile.TemporaryDirectory(prefix='runaway-frozen-history-') as temp:
        destination = Path(temp) / 'source'
        destination.mkdir()
        ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '.venv', 'node_modules')
        for name in SOURCE_DIRS:
            source = root / name
            if source.exists():
                shutil.copytree(source, destination / name, ignore=ignore, symlinks=True)
        for source in root.iterdir():
            if source.is_file() and (source.suffix in ('.py', '.md', '.toml', '.in')
                                     or source.name in ('LICENSE', '.gitignore')):
                shutil.copy2(source, destination / source.name)
        target = destination / EXECUTOR
        # Do not follow a working-tree symlink while installing original bytes.
        if target.is_symlink():
            target.unlink()
        target.write_bytes((root / ARCHIVE / 'taste_executor.py.txt').read_bytes())
        if sha(target) != ORIGINAL_SHA256:
            raise ValueError('Historical source copy differs')
        yield destination


# An isolated interpreter prevents already-imported live modules from leaking
# into the historical run. The explicit service guards are additional to each
# replay's existing injected archive/fixture backend.
BOOTSTRAP = r'''
import json, os, pathlib, runpy, sys, unittest
root = pathlib.Path(sys.argv[1]).resolve()
mode, payload = sys.argv[2], json.loads(sys.argv[3])
os.chdir(root)
sys.path[:0] = [str(root), str(root / 'tests'), str(root / 'scripts')]
if mode.startswith('historical'):
    from runaway import generation
    def no_service(*args, **kwargs):
        raise RuntimeError('Historical replay cannot invoke a model service')
    generation.codex_generate = no_service
    def audit(event, args):
        if event == 'subprocess.Popen':
            command = args[1]
            executable = command[0] if isinstance(command, (list, tuple)) else args[0]
            if pathlib.Path(str(executable)).name in ('codex', 'codex.exe'):
                no_service()
    sys.addaudithook(audit)
if mode.endswith('tests'):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in payload['modules'])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    pathlib.Path(payload['result']).write_text(json.dumps({
        'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped)}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
sys.argv = [str(root / payload['script']), *payload['args']]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


def child(root, mode, payload):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    return subprocess.run([sys.executable, '-I', '-c', BOOTSTRAP, str(root), mode,
                           json.dumps(payload)], cwd=root, env=env).returncode


def suite_result(code, path, *, require_tests):
    """An exit code cannot substitute for a complete interpreter report."""
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {'exit_code': code, 'report_valid': False,
                'error': 'Test interpreter report is missing or unreadable'}
    fields = {'tests', 'failures', 'errors', 'skipped'}
    if (type(value) is not dict or set(value) != fields
            or any(type(v) is not int or v < 0 for v in value.values())
            or (require_tests and value['tests'] == 0)):
        return {'exit_code': code, 'report_valid': False,
                'error': 'Test interpreter report has invalid or empty counts'}
    return {**value, 'exit_code': code, 'report_valid': True}


def check_tests(root=ROOT):
    root = Path(root).resolve()
    current, historical = partition(root)
    print('Current-source modules: %d; historical-source modules: %d; none omitted.'
          % (len(current), len(historical)), flush=True)
    summary = {}
    with tempfile.TemporaryDirectory(prefix='runaway-test-results-') as temp:
        for mode, modules in (('current-tests', current), ('historical-tests', historical)):
            result = Path(temp) / (mode + '.json')
            payload = {'modules': modules, 'result': str(result)}
            print('\n=== %s ===' % mode, flush=True)
            if mode == 'historical-tests':
                with snapshot(root) as source:
                    code = child(source, mode, payload)
            else:
                code = child(root, mode, payload)
            summary[mode] = suite_result(code, result, require_tests=bool(modules))
    print(json.dumps({'offline_test_suites': summary}, sort_keys=True), flush=True)
    return 0 if all(row['report_valid'] and row['exit_code'] == 0
                    and row['failures'] == 0 and row['errors'] == 0
                    for row in summary.values()) else 1


def replay(script, args, root=ROOT):
    root = Path(root).resolve()
    path = Path(script)
    if (path.is_absolute() or '..' in path.parts or script not in manifest(root)['offline_scripts']
            or any(value == '--run' or value.startswith('--run=') for value in args)):
        raise ValueError('Only listed offline replay scripts are supported')
    # Inputs and outputs belong to the caller, not the disposable source copy.
    converted = list(args)
    path_flags = {'--out', '--input', '--prepared', '--original-prepared',
                  '--draft-answer', '--answer', '--card', '--questions'}
    for index, value in enumerate(args[:-1]):
        if value in path_flags:
            converted[index + 1] = str(Path(args[index + 1]).resolve())
    for index, value in enumerate(args):
        flag, separator, argument = value.partition('=')
        if separator and flag in path_flags:
            converted[index] = flag + '=' + str(Path(argument).resolve())
    with snapshot(root) as source:
        return child(source, 'historical-script', {'script': script, 'args': converted})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('tests')
    command = commands.add_parser('run')
    command.add_argument('script')
    command.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    return check_tests() if args.command == 'tests' else replay(args.script, args.args)


if __name__ == '__main__':
    raise SystemExit(main())
