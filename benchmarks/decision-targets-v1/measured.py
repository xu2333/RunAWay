"""Replay the closed decision-target comparison without a model service."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway.constraint_extract import parse_answer, check as schema_check
spec = importlib.util.spec_from_file_location('measured_target_experiment', HERE / 'experiment.py')
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)
spec = importlib.util.spec_from_file_location('measured_target_old', ROOT / 'benchmarks/regression-progress-v1/check.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
IMPLEMENTATION_DIGEST = '7823c827f6ce4c9f1acd703d39d4043fc4a272f6f7079173290cb319bfc4cb6c'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counts(rows, first, second=None):
    """A case passes only when every planned order/read matches its reference."""
    result = {k: {'planned': 0, 'correct': 0, 'missing': 0}
              for k in ('joint', 'known', 'unknown', 'personal_known', 'preference', 'execution')}
    for row in rows:
        values = [first.get(q) for q in row['query_ids']]
        if second is not None:
            values += [second.get(q) for q in row['query_ids']]
        missing = any(v is None for v in values)
        correct = not missing and all(v == row['gold'] for v in values)
        keys = ['joint', 'unknown' if row['gold'] == 'U' else 'known', row.get('stratum', 'preference')]
        if row['personal_known']:
            keys.append('personal_known')
        for key in keys:
            result[key]['planned'] += 1
            result[key]['correct'] += int(correct)
            result[key]['missing'] += int(missing)
    return result


def replay(data):
    require(data['kind'] == 'actual_decision_target21_consumed_development', 'Wrong evidence kind')
    for key in ('independent_holdout', 'real_person_fidelity_verified', 'production_default_changed',
                'new_service_authority', 'project_goal_complete'):
        require(data[key] is False, 'Unsupported claim: ' + key)
    require(data['all_sources_fictional'] is True, 'Fictional boundary differs')
    require(exp.digest(data['implementation_sha256']) == IMPLEMENTATION_DIGEST, 'Frozen implementation manifest differs')
    for rel, expected in data['implementation_sha256'].items():
        path = Path(rel)
        require(not path.is_absolute() and '..' not in path.parts and not (ROOT / path).is_symlink(), 'Unsafe implementation path')
        require(sha(ROOT / path) == expected, 'Frozen implementation differs: ' + rel)
    inputs = exp.inputs()
    require(data['sources'] == inputs['sources'] and data['queries'] == inputs['queries']
            and data['reference_rows'] == inputs['rows'] and data['cached_v1'] == inputs['cached_v1'], 'Frozen data differs')
    require(data['slots'] == exp.slots(), 'Planned slots differ')
    status, records = data['status'], data['records']
    require(status['scope_closed'] is True and status['simulated'] is False, 'Scope not actually closed')
    require(status['status'] in ('complete', 'completed_with_invalid_products'), 'Unexpected closed state')
    require(status['stop'] is None and not status['missing_usage'], 'Incomplete scope')
    require(status['attempt_reservations'] == status['local_cli_child_intents'] == len(records), 'Attempt ledger differs')
    require(status['unused_slots_expire'] == 21-len(records), 'Unused count differs')
    ids, parents, answers, cards, gates, none = set(), {}, {}, {}, {}, {}
    invalid, skipped, totals = [], [], Counter()
    it = iter(records)
    for slot in exp.slots():
        pid, method, kind = slot['profile'], slot['method'], slot['kind']
        key = (pid, method)
        if slot['slot'] >= 6:
            require(len(gates) == 3 and all(v['qualified'] for v in gates.values()), 'Failed controls were bypassed')
        if kind == 'read' and key not in parents:
            skipped.append({**slot, 'reason': 'own_profile_method_product_invalid'})
            continue
        rec = next(it, None)
        require(rec is not None and all(rec[k] == v for k, v in slot.items()), 'Missing/reordered slot')
        require(rec['state'] == 'completed' and rec['execution_id'] not in ids, 'Failed or duplicate execution')
        ids.add(rec['execution_id'])
        request = exp.request(slot, parents)
        require(request == rec['request'] and exp.digest(request) == rec['request_sha256'], 'Request/card parent differs')
        require(rec['backend'] == 'codex' and rec['requested_model'] == exp.MODEL, 'Requested backend/model differs')
        require(hashlib.sha256(rec['raw'].encode()).hexdigest() == rec['raw_text_sha256'], 'Raw response drift')
        usage = old.usage(rec['usage_rows'])
        require(usage == rec['usage'], 'Usage counters differ')
        totals.update(usage)
        answer = parse_answer(rec['raw'])
        schema_check(answer, request['schema'])
        if kind == 'extract':
            try:
                prompt = exp.checks.candidate.bind(answer, inputs['sources'][pid], exp.BUDGET)['prompt.md']
                require(0 < len(prompt) <= exp.BUDGET, 'Whole card over budget')
            except (ValueError, KeyError, TypeError) as exc:
                require(rec.get('product_invalid') is True and 'card' not in rec, 'Invalid product hidden')
                invalid.append({**slot, 'error_type': type(exc).__name__, 'error': str(exc)})
                continue
            artifact = {'profile': pid, 'method': method, 'prompt': prompt, 'characters': len(prompt),
                        'source_sha256': exp.digest(inputs['sources'][pid]), 'answer_sha256': exp.digest(answer)}
            require(rec.get('card') == artifact and not rec.get('product_invalid'), 'Extraction artifact differs')
            cards[key], parents[key] = artifact, answer
        else:
            bank = 'dev' if pid in ('dev', 'shared_dev') else 'h'
            exp.choice_reader.decode_response(inputs['queries'][bank], answer, answer_format='text', reader_mode='standard')
            if kind == 'none':
                none[bank] = answer
            elif kind == 'full':
                rows = [r for r in inputs['rows'] if r['person'] == pid]
                f, n = counts(rows, answer), counts(rows, none[bank])
                signal = 'known' if pid == 'dev' else 'personal_known'
                gates[pid] = {'qualified': f['joint']['correct'] == len(rows) and not f['joint']['missing']
                              and f[signal]['correct'] > n[signal]['correct'], 'full': f, 'none': n}
            else:
                answers[pid, method, slot['repeat']] = answer
    require(next(it, None) is None, 'Extra unplanned attempts')
    require(status['skipped'] == skipped and status['invalid_products'] == invalid, 'Product failure/skip ledger differs')
    require(status['control_gates'] == gates and status['known_usage'] == dict(totals), 'Gate/usage ledger differs')
    require(status['status'] == ('completed_with_invalid_products' if invalid else 'complete'), 'Product state differs')
    profiles, totals_by_method, losses = {}, {}, []
    for pid in ('h68', 'h93', 'dev'):
        rows = [r for r in inputs['rows'] if r['person'] == pid]
        profiles[pid] = {}
        for method in ('v1', 'v2'):
            a, b = [answers.get((pid, method, repeat), {}) for repeat in (0, 1)]
            card = inputs['cached_v1'][pid] if method == 'v1' and pid != 'dev' else cards.get((pid, method))
            profiles[pid][method] = {'characters': card['characters'] if card else None,
                                    'first': counts(rows, a), 'second': counts(rows, b), 'strict': counts(rows, a, b),
                                    'disagreeing_cases': sum([a.get(q) for q in r['query_ids']] != [b.get(q) for q in r['query_ids']] for r in rows)}
            for row in rows:
                values = [[ans.get(q) for q in row['query_ids']] for ans in (a, b)]
                if any(v != row['gold'] for pair in values for v in pair):
                    losses.append({'person': pid, 'method': method, 'case': row['case'], 'gold': row['gold'], 'reads': values})
    for method in ('v1', 'v2'):
        total = {k: Counter() for k in profiles['dev'][method]['strict']}
        for pid in profiles:
            for key, count in profiles[pid][method]['strict'].items():
                total[key].update(count)
        totals_by_method[method] = {k: dict(v) for k, v in total.items()}
    return {'actual_calls': len(records), 'known_usage': dict(totals), 'profiles': profiles,
            'strict_totals': totals_by_method, 'losses': losses, 'control_gates': gates,
            'new_model_calls': 0, 'new_unique_old_inventory_coverage': 0,
            'old_inventory_measured': 160, 'old_inventory_remaining': 72,
            'independent_holdout': False, 'production_default_changed': False, 'project_goal_complete': False}


def check():
    path = HERE / 'measured.synthetic.json'
    require(sha(path) == (HERE / 'measured.synthetic.sha256').read_text().strip(), 'Public snapshot checksum differs')
    return replay(json.loads(path.read_text(encoding='utf-8')))


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
