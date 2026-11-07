"""Experimental condition-aware memory:one explicit call,or offline prepare/import/demo."""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runaway import generation
from runaway.cli import save_private_bundle
from runaway.constraint_extract import parse_answer
from runaway.profile import validate_sources


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


producer = load('trial_coverage_encoder', ROOT / 'benchmarks/object-coverage-guidance-v1/candidate.py')
capture = load('trial_safe_completion', ROOT / 'scripts/capture_codex_failure.py')
source_input = load('trial_source_input', ROOT / 'scripts/source_input.py')
PROTOCOL = 'condition-memory-trial-v1'
COMPILER_FILES = (
    'benchmarks/object-coverage-guidance-v1/candidate.py',
    'benchmarks/source-order-v3/candidate.py',
    'benchmarks/action-policy-v2/candidate.py',
    'benchmarks/action-revision-graph-v1/candidate.py',
    'benchmarks/owned-conditions-v1/candidate.py',
    'benchmarks/owned-dense-v1/codec.py',
    'benchmarks/order-targets-v1/prototype.py',
    'runaway/card.py', 'runaway/profile.py', 'runaway/constraint_extract.py',
    'runaway/constraint_memory.py', 'runaway/grouped_support.py',
    'runaway/support_extract.py', 'runaway/portable.py', 'runaway/prompt_codec.py',
    'runaway/scope_rows.py', 'runaway/text_integrity.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def read_text(path, limit=256000):
    with Path(path).open('rb') as file:
        raw = file.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Selected file exceeds byte limit')
    return raw.decode('utf8')


def read_json(path, limit=256000):
    try:
        return parse_answer(read_text(path, limit))
    except RecursionError:
        raise ValueError('JSON nesting exceeds supported depth') from None


def sources_file(path, input_format='auto'):
    return source_input.normalize(read_text(path, 64000), input_format,
                                  json_filename=Path(path).suffix.lower() == '.json')


def compiler_hashes():
    return {name: sha(ROOT / name) for name in COMPILER_FILES}


def request(sources, budget=1536):
    return {'system': producer.base.b.grouped.SYSTEM,
            **producer.make_request(sources, budget)}


def manual_request(req):
    return (req['system'] + '\n\n' + req['prompt'] + '\n\nOUTPUT_SCHEMA_JSON:\n' +
            json.dumps(req['schema'], ensure_ascii=False, indent=2) + '\n')


def write_new(path, value):
    path = Path(path)
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf8') as file:
        file.write(text)


def prepare(sources, budget, out):
    sources = source_input.selected_sources(sources)
    req = request(sources, budget)
    markdown = manual_request(req)
    manifest = {'protocol': PROTOCOL, 'budget_characters': budget,
                'source_sha256': digest(sources), 'request_sha256': digest(req),
                'manual_request_sha256': hashlib.sha256(markdown.encode()).hexdigest(),
                'compiler_sha256': compiler_hashes(), 'experimental': True}
    files = {'sources.private.json': sources, 'request.private.json': req,
             'request.private.md': markdown, 'manifest.private.json': manifest}
    for value in files.values():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if len(text.encode()) > 256000:
            raise ValueError('Prepared packet exceeds local import limit')
    directory = save_private_bundle(out, files)
    return {'status': 'request_prepared', 'directory': directory,
            'backend_calls_attempted': 0, 'contains_selected_source': True,
            'source_role_counts': source_input.role_counts(sources), 'speaker_labels_verified': False,
            'request_file': 'request.private.json', 'manual_request_file': 'request.private.md'}


def prepared(directory):
    directory = Path(directory)
    names = ('sources.private.json', 'request.private.json', 'request.private.md', 'manifest.private.json')
    if directory.is_symlink() or any((directory / n).is_symlink() for n in names):
        raise ValueError('Prepared symlinks refused')
    sources = source_input.selected_sources(read_json(directory / names[0], 256000))
    req, manifest = read_json(directory / names[1]), read_json(directory / names[3])
    keys = {'protocol', 'budget_characters', 'source_sha256', 'request_sha256',
            'manual_request_sha256', 'compiler_sha256', 'experimental'}
    if set(manifest) != keys or manifest['protocol'] != PROTOCOL or manifest['experimental'] is not True:
        raise ValueError('Unsupported prepared packet')
    if manifest['compiler_sha256'] != compiler_hashes() or digest(sources) != manifest['source_sha256']:
        raise ValueError('Source or compiler changed')
    if req != request(sources, manifest['budget_characters']) or digest(req) != manifest['request_sha256']:
        raise ValueError('Prepared request changed')
    text = read_text(directory / names[2])
    if text != manual_request(req) or hashlib.sha256(text.encode()).hexdigest() != manifest['manual_request_sha256']:
        raise ValueError('Prepared manual request changed')
    return sources, req, manifest


def import_answer(directory, answer, out):
    sources, req, manifest = prepared(directory)
    files = producer.bind(answer, sources, manifest['budget_characters'])
    summary = {'status': 'candidate_unvalidated', 'protocol': PROTOCOL,
               'characters': len(files['prompt.md']), 'budget_characters': manifest['budget_characters'],
               'source_sha256': digest(sources), 'request_sha256': digest(req),
               'behavioral_fidelity_verified': False, 'semantic_support_verified': False,
               'backend_calls_attempted': 0, 'shareable_files': ['prompt.md', 'portable.json']}
    files['import.private.json'] = summary
    return {**summary, 'directory': save_private_bundle(out, files)}


class TrialFailure(ValueError):
    def __init__(self, summary):
        super().__init__('Generation failed;inspect private run files;no automatic retry')
        self.summary = summary


def generate(sources, budget, model, out):
    if not isinstance(model, str) or not model.strip():
        raise ValueError('An explicit available model is required')
    prepare(sources, budget, out)
    out = Path(out)
    _, req, _ = prepared(out)
    if generation.shutil.which('codex') is None:
        raise TrialFailure({'status': 'backend_unavailable', 'directory': str(out.resolve()),
                            'backend_calls_attempted': 0, 'local_cli_children': 0,
                            'message': 'Codex CLI was not found. Use request.private.md with your chosen LLM,then import its answer.'})
    write_new(out / 'backend-call-intent.private.json', {
        'backend': 'codex', 'model_requested': model, 'request_sha256': digest(req),
        'timeout_seconds': 180, 'max_local_children': 1, 'automatic_retry': False})
    children = 0
    original = generation.run_bounded

    def bounded(argv, prompt, timeout):
        nonlocal children
        if children or prompt != req['prompt'] or timeout != 180:
            raise ValueError('Unexpected additional backend child')
        write_new(out / 'backend-child-intent.private.json', {
            'argv_sha256': digest(argv), 'prompt_sha256': digest(prompt), 'timeout_seconds': timeout})
        children += 1
        return original(argv, prompt, timeout)

    returned_provenance = None
    try:
        with patch.object(generation, 'run_bounded', bounded):
            raw, returned_provenance = capture.capture_once(lambda: generation.codex_generate(
                req['prompt'], model, timeout=180, schema=req['schema'], system=req['system']), model=model)
        if children != 1:
            raise ValueError('Backend child count differs')
        write_new(out / 'answer.private.txt', raw)
        write_new(out / 'provenance.private.json', returned_provenance)
        answer = parse_answer(raw)
        result = import_answer(out, answer, out / 'candidate')
        result.update(backend_calls_attempted=1, local_cli_children=children, automatic_retry=False)
        write_new(out / 'result.private.json', result)
        return result
    except Exception as exc:
        provenance = getattr(exc, 'provenance', None) or returned_provenance
        record_failed = False
        if provenance is not None and not (out / 'provenance.private.json').exists():
            try:
                write_new(out / 'provenance.private.json', provenance)
            except (OSError, ValueError, TypeError):
                record_failed = True
        result = {'status': 'failed', 'directory': str(out.resolve()),
                  'backend_calls_attempted': 1, 'local_cli_children': children,
                  'error_type': type(exc).__name__, 'automatic_retry': False,
                  'candidate_created': (out / 'candidate/portable.json').exists(),
                  'usage_status': 'inspect_private_provenance' if (out / 'provenance.private.json').exists() else 'unknown',
                  'message': 'Inspect private run files and CLI login/version. No automatic retry was made.'}
        try:
            write_new(out / 'result.private.json', result)
        except (OSError, ValueError, TypeError):
            record_failed = True
        if record_failed:
            result['private_record_write_failed'] = True
        raise TrialFailure(result) from None


def demo(out):
    replay = load('trial_archived_repeat', ROOT / 'scripts/replay_single_pass_repeat.py')
    data = read_json(replay.DEFAULT, 4000000)
    replay.check()
    rec = next(r for r in data['records'] if r['kind'] == 'extract' and
               r['profile'] == 'pavo' and r['generation_repeat'] == 0)
    sources = data['prepared_files']['sources.json']['pavo']
    req = dict(rec['request'])
    req.pop('model')
    if request(sources) != req:
        raise ValueError('Archived request differs')
    prepare(sources, 1536, out)
    write_new(Path(out) / 'answer.private.txt', rec['raw'])
    result = import_answer(out, parse_answer(rec['raw']), Path(out) / 'candidate')
    result.update(synthetic_archive_replay=True, new_inference=False, backend_calls_attempted=0)
    write_new(Path(out) / 'result.private.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'generate'):
        action = actions.add_parser(name)
        action.add_argument('--input', type=Path, required=True)
        action.add_argument('--input-format', choices=source_input.FORMATS, default='auto')
        action.add_argument('--budget-chars', type=int, default=1536)
        action.add_argument('--out', type=Path, required=True)
        if name == 'generate':
            action.add_argument('--backend', choices=['codex'], required=True)
            action.add_argument('--model', required=True)
    action = actions.add_parser('import')
    action.add_argument('--prepared', type=Path, required=True)
    action.add_argument('--answer', type=Path, required=True)
    action.add_argument('--out', type=Path, required=True)
    action = actions.add_parser('demo')
    action.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'generate':
            result = generate(sources_file(args.input, args.input_format), args.budget_chars, args.model, args.out)
        elif args.command == 'prepare':
            result = prepare(sources_file(args.input, args.input_format), args.budget_chars, args.out)
        elif args.command == 'import':
            result = import_answer(args.prepared, read_json(args.answer), args.out)
        else:
            result = demo(args.out)
    except TrialFailure as exc:
        print(json.dumps(exc.summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    except source_input.SourceInputError as exc:
        print(json.dumps({'status': 'input_rejected', 'error_code': exc.code,
                          'message': str(exc), 'backend_calls_attempted': 0}), file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError, OSError, StopIteration) as exc:
        print(json.dumps({'status': 'input_rejected', 'error_type': type(exc).__name__,
                          'backend_calls_attempted': 0,
                          'message': 'Inspect the selected local files;no backend call was made.'}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
