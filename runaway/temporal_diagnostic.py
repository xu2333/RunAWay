"""A six-call, single-use DEVELOPMENT diagnostic. Preparation is entirely offline."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import zipfile

from . import temporal as t, generation
from .card import canonical, digest
from .fidelity_plan import CODE as BASE_CODE
from .fidelity_runner import DirectCalls
from .pipeline import write_once
from .selfplay import SYSTEM
from .taste_executor import ORIGINAL_RUN_BOUNDED, answers_checked, runtime_check, atomic
from .taste_plan import reader_job
from .fidelity_stress import READER

ROOT = Path(__file__).resolve().parents[1]
STAGES = {'full_history': 2, 'shared_extraction': 2, 'actual_memory_reader': 2}
CODE = tuple(dict.fromkeys((*BASE_CODE, 'runaway/temporal.py', 'runaway/temporal_diagnostic.py',
                           'runaway/cli.py', 'tests/test_temporal.py', 'tests/test_temporal_diagnostic.py')))


def read(path):
    return json.loads(Path(path).read_text())


def development_people():
    """Source-only annotations of consumed D18 excerpts; not a production parser."""
    with zipfile.ZipFile(ROOT / 'examples/stress-service-evidence.synthetic.zip') as archive:
        histories = [p['history'] for p in json.loads(archive.read('d0018/fixtures.synthetic.json'))['people'][:2]]
    people = []
    for i, history in enumerate(histories):
        records = {m[1]: line for line in history.splitlines() if (m := re.match(r'记录(r1[1-8])（', line))}
        order = ('r11', 'r12', 'r13', 'r15', 'r16', 'r17', 'r18')
        source = '\n'.join(history.splitlines()[:3] + [records[key] for key in order])
        sources = {'schema_version': 1, 'sources': [{'id': 'history', 'episode_id': 'consumed-development', 'role': 'user', 'text': source}]}
        spans = t.spans(sources)
        chosen = lambda key: re.findall('「([^」]+)」', records[key])[-1]
        def event(key, kind, action='', strength=0, when=(), target=''):
            return {'id': key, 'kind': kind, 'domain': '' if kind == 'retract' else '产品验证',
                    'action': action, 'strength': strength, 'when_all': [{'predicate': p, 'equals': True} for p in when],
                    'target': target, 'span_ids': [spans[3 + order.index(key)]['id']]}
        annotation = {'scope': '合成开发记录，仅产品验证。', 'events': [
            event('r11', 'regular', chosen('r11'), 3), event('r12', 'regular', chosen('r12'), 1),
            event('r13', 'replace', chosen('r13'), 2),
            event('r15', 'exception', chosen('r15'), when=['方向尚未验证']),
            event('r16', 'constraint', chosen('r16'), when=['方向尚未验证', '改动不可撤销']),
            event('r17', 'retract', target='r16'), event('r18', 'retract', target='r17')],
            'unmodeled': [{'span_id': s['id'], 'reason': '该段解释来源契约，不是个人选择事件。'} for s in spans[:3]]}
        t.bind(annotation, sources)
        cases = []
        for scenario, (a, b) in enumerate(((False, False), (True, False), (False, True), (True, True))):
            action = chosen('r16') if a and b else chosen('r15') if a else chosen('r13')
            for option_order in (0, 1):
                actions = ['先做小实验', '先完成整体设计'][::(-1 if option_order else 1)]
                cases.append({'public': {'id': f'dev-{i}-c{scenario}-{option_order}', 'task': 'current_choice',
                    'question': f'当前产品验证：方向尚未验证={a}；改动不可撤销={b}。A={actions[0]}；B={actions[1]}。',
                    'answer_options': ['A', 'B', 'U']}, 'gold': 'AB'[actions.index(action)],
                    'context': {'方向尚未验证': a, '改动不可撤销': b}, 'action': action,
                    'option_actions': dict(zip(('A', 'B', 'U'), (*actions, None)))})
        for day, key in ((6, 'r16'), (7, 'r15')):
            actions = ['先做小实验', '先完成整体设计']
            cases.append({'public': {'id': f'dev-{i}-h{day}', 'task': 'historical_reconstruction',
                'question': f'第{day}天当时，方向尚未验证且改动不可撤销。A=先做小实验；B=先完成整体设计。',
                'answer_options': ['A', 'B', 'U']}, 'gold': 'AB'[actions.index(chosen(key))]})
        people.append({'id': 'development-' + str(i), 'sources': sources, 'annotation': annotation, 'cases': cases})
    return people


def prepare(out, runtime_template, runtime_expected=None):
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    people = development_people()
    write_once(out / 'development.private.json', people)
    jobs = []
    for p in people:
        public = [c['public'] for c in p['cases']]
        full = reader_job('full_history', p['id'], p['sources']['sources'][0]['text'], public, READER, 12)
        jobs.append({'stage': 'full_history', 'person_id': p['id'], 'request': full['request']})
        jobs.append({'stage': 'shared_extraction', 'person_id': p['id'], 'request': {
            'prompt': t.make_request(p['sources']), 'schema': t.SCHEMA, 'model': 'gpt-6-luna', 'system': SYSTEM}})
    write_once(out / 'jobs.json', jobs)
    runtime = read(runtime_template)
    body = {'status': 'offline_not_approved_not_executed', 'runner': 'runaway.temporal_diagnostic.execute',
        'proposal_directory': str(out.resolve()), 'models': {'generator': 'gpt-6-luna', 'reader': 'gpt-6.1-sol'},
        'python_executable': runtime['python_executable'], 'tokenizer': runtime['tokenizer'], 'tokenizer_path': runtime['tokenizer_path'],
        'runtime_expected': runtime_expected,
        'calls_max': 6, 'stage_caps': STAGES, 'timeout_seconds': 180, 'cleanup_waits_seconds': [2, 2],
        'character_budget': 768, 'token_budget': 384, 'retries': 0,
        'scope': 'Two source-only product-validation excerpts of consumed D18 synthetic people, one paired DEVELOPMENT unit. Not fresh holdout evidence or a population comparison. No legacy method rerun. 16 current +4 historical planned per reader condition. Portable output intentionally covers current state only; historical loss remains visible.',
        'data_scope': {'history_characters': sum(len(p['sources']['sources'][0]['text']) for p in people),
            'included': 'Only the two listed synthetic source excerpts, derived event graphs/current memories, public queries and necessary system/schema/CLI metadata.',
            'excluded': 'Real data, workspace/central messages, archived profiles/answers, private annotation/gold/context mappings and credentials in payload.'},
        'stopping': 'Full-source reader must score16/16 current and4/4 historical before extraction. Every extraction must pass span/graph validation, model all7 event-bearing spans, preserve the r18→r17→r16 retraction edges with arbitrary event IDs, and pass all4 current context checks. Otherwise stop the whole remaining batch. Complete prompt must fit768 characters and384 actual tokenizer tokens; failure stops. Any timeout, format/transport error, unknown usage/state or frozen drift stops. Zero retry/repair/resampling/balance reuse. Preserve all denominators.',
        'cost_boundary': 'At most6 experiment generations, not a hard aggregate HTTP/token/money/time ceiling. Existing official Codex login/service, no purchases. CLI default reasoning, empty isolated workspace/tools disabled via unchanged existing observer.',
        'source_hashes': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in CODE},
        'input_hashes': {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in ('development.private.json', 'jobs.json')},
        'sealed_prior_archives': {n: hashlib.sha256((ROOT / 'examples' / n).read_bytes()).hexdigest() for n in ('pilot-evidence.synthetic.zip', 'comparison-evidence.synthetic.zip', 'stress-service-evidence.synthetic.zip')},
        'forbidden_request_ids': sorted({Path(n).name.removesuffix('.request.json') for filename in ('pilot-evidence.synthetic.zip', 'comparison-evidence.synthetic.zip', 'stress-service-evidence.synthetic.zip') for n in zipfile.ZipFile(ROOT / 'examples' / filename).namelist() if n.endswith('.request.json')})}
    proposal = {**body, 'id': digest(canonical(body))}
    write_once(out / 'proposal.json', proposal)
    for name in CODE:
        target = out / 'frozen-source' / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / name, target)
    return proposal


def preflight(root):
    root = Path(root); p = read(root / 'proposal.json')
    if p['id'] != digest(canonical({k: v for k, v in p.items() if k != 'id'})) or p['proposal_directory'] != str(root.resolve()):
        raise ValueError('Frozen proposal changed/moved')
    if p['calls_max'] != 6 or p['stage_caps'] != STAGES or p['character_budget'] != 768 or p['token_budget'] != 384:
        raise ValueError('Diagnostic limits changed')
    for name, sha in p['source_hashes'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha or hashlib.sha256((root / 'frozen-source' / name).read_bytes()).hexdigest() != sha:
            raise ValueError('Frozen source changed: ' + name)
    for name, sha in p['input_hashes'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != sha:
            raise ValueError('Frozen input changed')
    for name, sha in p['sealed_prior_archives'].items():
        if hashlib.sha256((ROOT / 'examples' / name).read_bytes()).hexdigest() != sha:
            raise ValueError('Sealed evidence changed')
    return p


def score(people, predictions):
    result = {}
    for task in ('current_choice', 'historical_reconstruction', 'joint'):
        rows = [(p, c) for p in people for c in p['cases'] if task == 'joint' or c['public']['task'] == task]
        result[task] = {'correct': sum(predictions.get(p['id'], {}).get(c['public']['id']) == c['gold'] for p, c in rows),
                        'missing': sum(c['public']['id'] not in predictions.get(p['id'], {}) for p, c in rows),
                        'unknown_answers': sum(predictions.get(p['id'], {}).get(c['public']['id']) == 'U' for p, c in rows), 'planned': len(rows)}
    right = lambda p, c: predictions.get(p['id'], {}).get(c['public']['id']) == c['gold']
    result['collapsed_current'] = {'correct': sum(all(right(p, c) for c in p['cases'][i:i + 2]) for p in people for i in range(0, 8, 2)), 'planned': 8}
    result['matched_condition_contrasts'] = {'correct': sum(all(right(p, c) for p in people for c in p['cases'][i:i + 2]) for i in (2, 6)), 'planned': 2}
    return result


def graph_checks(person, artifact):
    expected = {e['id']: e['span_ids'][0] for e in person['annotation']['events']}
    events = artifact['extraction']['events']
    modeled = {sid for event in events for sid in event['span_ids']}
    matches = {key: [e for e in events if e['kind'] == kind and expected[key] in e['span_ids']]
               for key, kind in (('r16', 'constraint'), ('r17', 'retract'), ('r18', 'retract'))}
    edges = all(len(x) == 1 for x in matches.values())
    if edges:
        edges = matches['r18'][0]['target'] == matches['r17'][0]['id'] and matches['r17'][0]['target'] == matches['r16'][0]['id']
    return {'all7_event_spans_modeled': set(expected.values()) <= modeled, 'nested_retraction_edges_preserved': edges}


def execute(root, out, approval=None, backend=None, count=None):
    root, out = Path(root), Path(out); p = preflight(root); real = backend is None
    if real:
        if not approval or approval.get('status') != 'approved' or approval.get('proposal_id') != p['id'] or not approval.get('human_source'):
            raise ValueError('Separate direct human approval for this exact new batch is required')
        if not p['runtime_expected'] or runtime_check(p) != p['runtime_expected']:
            raise ValueError('Frozen runtime changed')
        fd = os.open(root / 'execution-intent.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump({'proposal_id': p['id'], 'human_source': approval['human_source'], 'at': datetime.now(timezone.utc).isoformat()}, stream)
        backend = generation.codex_generate
    out.mkdir(parents=True, exist_ok=False)
    people = read(root / 'development.private.json'); jobs = read(root / 'jobs.json')
    calls = DirectCalls(out, p, backend); predictions = {'full_history': {}, 'temporal': {}}
    artifacts, memories, parser_checks, source_graph_checks, gate = {}, {}, {}, {}, None
    generation.run_bounded = calls.observed_runner
    tokenizer = None
    try:
        for job in [j for j in jobs if j['stage'] == 'full_history']:
            person = next(x for x in people if x['id'] == job['person_id'])
            predictions['full_history'][person['id']] = answers_checked(calls.call('full_history', job['request']), [c['public'] for c in person['cases']])
        gate = score(people, predictions['full_history'])
        if any(x['correct'] != x['planned'] for x in gate.values()):
            calls.stop('full_source_reader_gate_failed'); raise ValueError('Full-source reader gate failed')
        if count is None:
            import llama_cpp
            tokenizer = llama_cpp.Llama(model_path=p['tokenizer_path'], vocab_only=True, n_gpu_layers=0, verbose=False)
            count = lambda text: len(tokenizer.tokenize(text.encode(), add_bos=False, special=False))
        for job in [j for j in jobs if j['stage'] == 'shared_extraction']:
            person = next(x for x in people if x['id'] == job['person_id']); pid = person['id']
            artifact = t.bind(calls.call('shared_extraction', job['request']), person['sources']); artifacts[pid] = artifact
            source_graph_checks[pid] = graph_checks(person, artifact)
            cases = person['cases'][:8:2]
            parser_checks[pid] = [t.resolve(artifact, '产品验证', c['context'])['action'] == c['action'] for c in cases]
            if not all(parser_checks[pid]) or not all(source_graph_checks[pid].values()):
                calls.stop('source_to_event_semantics_failed', person_id=pid); raise ValueError('Source-to-event context checks failed')
            memory = t.render(artifact, 768, count=count, budget_tokens=384); memories[pid] = memory
            if memory['status'] == 'budget_blocked':
                calls.stop('whole_prompt_budget_failed', person_id=pid); raise ValueError('Whole prompt budget failed')
        for person in people:
            pid = person['id']; public = [c['public'] for c in person['cases']]
            job = reader_job('temporal', pid, memories[pid]['text'], public, READER, 12)
            predictions['temporal'][pid] = answers_checked(calls.call('actual_memory_reader', job['request']), public)
    except Exception as exc:
        if not calls.stopped:
            calls.stop('local_or_format_failure', error_type=type(exc).__name__, error=str(exc))
    finally:
        generation.run_bounded = ORIGINAL_RUN_BOUNDED
        if tokenizer is not None:
            tokenizer.close()
    try:
        calls.update()
    except Exception:
        calls.stop('uncertain_checkpoint_state')
    report = {'status': 'stopped' if calls.stopped else 'complete', 'proposal_id': p['id'],
        'calls': calls.ledger, 'stage_attempts': dict(calls.counts), 'stop_reason': calls.reason,
        'full_source_gate': gate, 'source_to_event_checks': parser_checks, 'source_to_event_planned': 8,
        'source_graph_checks': source_graph_checks,
        'scores': {k: score(people, v) for k, v in predictions.items()}, 'artifacts': artifacts, 'memories': memories,
        'origin': 'consumed_synthetic_development_only', 'paired_statistical_units': 1,
        'external_model_calls': calls.ledger['execution_records'] if real else 0,
        'backend_kind': 'actual_service' if real else 'injected_fake_not_quality',
        'real_person_fidelity_verified': False, 'historical_prompt_fidelity_improvement_claimed': False}
    write_once(out / 'answers.json', predictions); write_once(out / 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal', required=True)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--out'); parser.add_argument('--approval')
    args = parser.parse_args()
    if args.run:
        if not args.out or not args.approval:
            parser.error('--run requires --out and separately verified --approval')
        result = execute(args.proposal, args.out, read(args.approval))
        print(json.dumps({'status': result['status'], 'calls': result['calls']['execution_records']}))
    else:
        print(json.dumps({'proposal_id': preflight(args.proposal)['id'], 'external_model_calls': 0}))
