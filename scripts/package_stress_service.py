"""Seal and replay D-0018 synthetic service evidence. Never invokes a model."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from runaway import fidelity_stress as fs, fidelity_plan as fp, bound_memory
from runaway.card import canonical, digest
from runaway.execution_ledger import collect, summarize, checked
from runaway.selfplay import browser, SYSTEM
from runaway.taste_plan import reader_job
from runaway.taste_executor import answers_checked

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('full_history', 'wrong_person_history', 'current_policy_oracle', 'none')


def read(path):
    return json.loads(Path(path).read_text())


def equal(actual, expected):
    # Only the display mean may vary by a few ULPs between Python versions.
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError('Replay keys differ')
        for key in actual:
            if key == 'macro_cluster_accuracy':
                if abs(actual[key] - expected[key]) > 1e-12:
                    raise ValueError('Replay cluster mean differs')
            else:
                equal(actual[key], expected[key])
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError('Replay list length differs')
        for a, b in zip(actual, expected):
            equal(a, b)
    elif actual != expected:
        raise ValueError('Replay value differs: ' + repr((actual, expected)))


def replay(base, count=None):
    """Reconstruct predictions, products, gates and accounting from raw records."""
    base = Path(base)
    world = read(base / 'fixtures.synthetic.json')
    contract = read(base / 'contract.json')
    report = read(base / 'raw-report.synthetic.json')
    saved_answers = read(base / 'answers.synthetic.json')
    if world['origin'] != 'fully_synthetic' or report['backend_kind'] != 'actual_service':
        raise ValueError('Expected explicitly synthetic, actual-service evidence')
    if report['status'] not in ('complete', 'stopped'):
        raise ValueError('Batch is not sealed')
    records = collect(base)
    equal(summarize(records), report['calls'])
    if len(records) > 48 or len(records) != report['external_model_calls']:
        raise ValueError('Call cap/count mismatch')
    responses = {}
    for record in records:
        if record['outcome'] == 'completed':
            responses[record['request_id']] = checked(base / 'calls' / (record['request_id'] + '.response.json'))
    requests, labels, rebuilt = {}, {}, {}
    dependencies = defaultdict(list)

    def register(request, stage, label):
        key = digest(canonical(request))
        if key in labels and labels[key] != stage:
            raise ValueError('Same request assigned different stages')
        requests[key], labels[key] = request, stage
        dependencies[key].append(label)
        return key

    def reader(request, stage, condition, pid, queries):
        key = register(request, stage, {'condition': condition, 'person_id': pid})
        if key in responses:
            rebuilt.setdefault(condition, {})[pid] = answers_checked(responses[key]['answer'], queries)

    for line in (base / 'reader-jobs.synthetic.jsonl').read_text().splitlines():
        job = json.loads(line)
        query = json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n', 1)[1])['queries']
        reader(job['request'], job['id'], job['id'], job['persona_id'], query)
    people = {p['id']: p for p in world['people']}
    products = {}
    for line in (base / 'generation-jobs.synthetic.jsonl').read_text().splitlines():
        job = json.loads(line)
        pid, budget, limit = job['persona_id'], job['budget'], job['character_limit']
        label = {'person_id': pid, 'budget': budget}
        key = register(job['request'], 'shared_extraction', label)
        if key not in responses:
            continue
        try:
            bundle = browser('validate', fp.history_sources(people[pid]), limit, responses[key]['answer'])
        except ValueError:
            continue
        products[(pid, 'current_browser', budget)] = bundle['portable']['text']
        request = {'prompt': bound_memory.make_request(bundle['profile'], limit),
                   'schema': bound_memory.SCHEMA, 'model': 'gpt-6-luna', 'system': SYSTEM}
        newkey = register(request, 'new_compression', label)
        if newkey in responses:
            try:
                text, _ = bound_memory.bind(responses[newkey]['answer'], bundle['profile'], limit)
                products[(pid, 'new_bound', budget)] = text
            except ValueError:
                pass
    memory_checks = []
    for memory in report['memories']:
        pid, condition, budget = memory['persona_id'], memory['condition'], memory['budget']
        equal(products[(pid, condition, budget)], memory['text'])
        if memory['units'] > budget:
            raise ValueError('Retained memory exceeds its budget')
        if count is not None and count(memory['text']) != memory['units']:
            raise ValueError('Actual tokenizer count differs')
        public = [c['public'] for c in people[pid]['cases']]
        job = reader_job('actual_memory', pid, memory['text'], public, fs.READER, 12, 'actual_memory')
        reader(job['request'], 'actual_memory_reader', condition + ':' + str(budget), pid, public)
        memory_checks.append({'person_id': pid, 'condition': condition, 'budget': budget,
                              'units': memory['units'], 'characters': len(memory['text']),
                              'text_sha256': digest(memory['text'])})
    equal(rebuilt, saved_answers)
    computed = {name: {task: fs.score(world, rebuilt.get(name, {}), task)
                      for task in ('current_choice', 'historical_reconstruction', 'joint')}
                for name in (*CONDITIONS, *(name + ':' + str(b) for b in fp.BUDGETS
                                            for name in ('current_browser', 'new_bound')))}
    equal(computed, report['scores'])
    for name, gate in report['gates'].items():
        equal(fp.gates(name, computed[name], computed['full_history']), gate)
    stages = Counter()
    cost = defaultdict(list)
    order = []
    for record in sorted(records, key=lambda x: x['recorded_at']):
        key = record['request_id']
        if key not in requests:
            raise ValueError('Execution not part of reconstructed requests')
        equal(read(base / 'calls' / (key + '.request.json')), requests[key])
        stage = labels[key]
        stages[stage] += 1
        cost[stage].append(record)
        order.append({'execution_id': record['execution_id'], 'request_id': key,
                      'stage': stage, 'outcome': record['outcome'],
                      'usage': record['usage'], 'dependencies': dependencies[key]})
    equal(dict(stages), report['stage_attempts'])
    if any(stages[k] > contract['stage_caps'][k] for k in stages):
        raise ValueError('Stage cap exceeded')
    failed = [k for k, v in report['gates'].items() if not v['passed']]
    if failed and (order[-1]['stage'] != failed[0] or report['status'] != 'stopped'):
        raise ValueError('Calls continued after failed gate')
    for reuse in report['identical_requests_reused_offline']:
        if responses[reuse['request_id']]['execution_id'] != reuse['execution_id']:
            raise ValueError('Reuse did not reference the same completed execution')
    pipeline_costs = {}
    for budget in fp.BUDGETS:
        for condition in ('current_browser', 'new_bound'):
            generation_ids, reader_ids = set(), set()
            for key, links in dependencies.items():
                if labels[key] in ('shared_extraction', 'new_compression'):
                    if labels[key] == 'new_compression' and condition == 'current_browser':
                        continue
                    if any(x['budget'] == budget for x in links):
                        generation_ids.add(key)
                elif labels[key] == 'actual_memory_reader':
                    if any(x['condition'] == condition + ':' + str(budget) for x in links):
                        reader_ids.add(key)
            pipeline_costs[condition + ':' + str(budget)] = {
                'generation_including_shared_extraction': summarize([r for r in records if r['request_id'] in generation_ids]),
                'memory_reading': summarize([r for r in records if r['request_id'] in reader_ids]),
                'meaning': 'Standalone dependency costs, including unsuccessful products. Shared/reused executions overlap across rows; do not sum these rows as batch cost.'}
    return {'origin': 'fully_synthetic', 'decision': 'D-0018',
            'status': report['status'], 'proposal_id': report['proposal_id'],
            'publication_redactions': read(base / 'publication-redactions.json'),
            'checks': {'raw_predictions_rebuilt': True, 'all_score_fields_replayed': True,
                       'gates_replayed': True, 'products_rebuilt': True,
                       'all_executions_mapped': True, 'ledger_replayed': True,
                       'actual_tokenizer_recounted': count is not None},
            'calls': report['calls'], 'stage_attempts': dict(stages),
            'stage_costs': {k: summarize(v) for k, v in cost.items()},
            'pipeline_dependency_costs': pipeline_costs,
            'execution_order': order, 'memories': memory_checks,
            'gates': report['gates'], 'scores': computed,
            'stop_reason': report['stop_reason'],
            'local_validation_failures': report['local_validation_failures'],
            'reused_requests': report['identical_requests_reused_offline'],
            'independent_paired_clusters': 2, 'people': 4,
            'real_person_fidelity_verified': False,
            'interpretation': 'Small synthetic pilot; no population, real-person, cross-provider or likelihood-information-gain claim. Shared extraction is charged once in the batch; standalone new-method cost includes extraction plus compression. Missing predictions stay in planned denominators.'}


def package(run, proposal, examples, count=None):
    run, proposal, examples = map(Path, (run, proposal, examples))
    # Explicit allowlist. No approval, human messages, auth, execution intent or local paths.
    files = {'raw-report.synthetic.json': run / 'service/report.json',
             'answers.synthetic.json': run / 'service/answers.json',
             'fixtures.synthetic.json': proposal / 'fixtures.private.json',
             'contract.json': proposal / 'contract.json',
             'reader-jobs.synthetic.jsonl': proposal / 'reader-jobs.jsonl',
             'generation-jobs.synthetic.jsonl': proposal / 'generation-jobs.jsonl'}
    for path in (run / 'service/calls').glob('*.json'):
        if path.name.endswith(('.request.json', '.response.json', '.attempt.json', '.failure.json')):
            files['calls/' + path.name] = path
    for path in (proposal / 'frozen-source').rglob('*'):
        if path.is_file():
            files['frozen-source/' + str(path.relative_to(proposal / 'frozen-source'))] = path
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        for name, path in files.items():
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError('Escaping evidence path')
            destination = base / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes()
            # Local product-validator stacks may contain an absolute workspace path.
            # This is the only report transformation; checkpoint bytes stay exact.
            if name == 'raw-report.synthetic.json':
                data = data.replace(str(ROOT).encode(), b'<workspace>')
            destination.write_bytes(data)
        (base / 'publication-redactions.json').write_text(json.dumps({
            'raw_report_original_sha256': hashlib.sha256((run / 'service/report.json').read_bytes()).hexdigest(),
            'transformation': 'Replace the absolute workspace prefix with <workspace> in report-local validator errors only. Raw request/response/attempt checkpoints are unchanged.',
            'original_private_report_published': False}, indent=2) + '\n')
        summary = replay(base, count)
        encoded = (json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode()
        examples.mkdir(parents=True, exist_ok=True)
        archive = examples / 'stress-service-evidence.synthetic.zip'
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
            manifest = {}
            for path in sorted(base.rglob('*')):
                if path.is_file():
                    name = str(path.relative_to(base))
                    manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
                    output.writestr('d0018/' + name, path.read_bytes())
            manifest['report.synthetic.json'] = hashlib.sha256(encoded).hexdigest()
            output.writestr('d0018/report.synthetic.json', encoded)
            output.writestr('d0018/manifest.json', json.dumps(manifest, indent=2) + '\n')
        (examples / 'stress-service-results.synthetic.json').write_bytes(encoded)
        (run / 'audit-summary.json').write_bytes(encoded)
    return {'files': len(manifest), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'external_model_calls_by_packager': 0, 'private_approval_auth_included': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--proposal', required=True)
    parser.add_argument('--examples', default=str(ROOT / 'examples'))
    parser.add_argument('--tokenizer', required=True)
    args = parser.parse_args()
    import llama_cpp
    tokenizer = llama_cpp.Llama(model_path=args.tokenizer, vocab_only=True, n_gpu_layers=0, verbose=False)
    try:
        print(json.dumps(package(args.run, args.proposal, args.examples,
              lambda text: len(tokenizer.tokenize(text.encode(), add_bos=False, special=False)))))
    finally:
        tokenizer.close()
