"""Prepare an unapproved balanced40call breadth/frontier study, no service."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway import choice_reader, grouped_support
from runaway.card import canonical
from runaway.constraint_extract import check
spec = importlib.util.spec_from_file_location('remaining_world_policy', ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
PROFILES, BUDGETS = ('j16', 'j62', 'j85'), (1024, 1536)
MODEL, AS_OF, CAP = 'gpt-6.1-sol', '2026-10-30', 40
COMMON = '仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def inputs():
    old = read(ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json')['studies']['new_worlds']
    rows = [r for r in old['reference_rows'] if r['person'] in PROFILES]
    return {'sources': {pid: old['sources'][pid] for pid in PROFILES}, 'queries': {'j': old['queries']},
            'rows': [r for r in rows if r['case'] != 'w14'],
            'disputed_rows': [r for r in rows if r['case'] == 'w14'], 'legacy_rows': rows}


def cells():
    result = []
    for generation in (0, 1):
        for index, budget in enumerate(BUDGETS if generation == 0 else reversed(BUDGETS)):
            people = list(PROFILES[index:] + PROFILES[:index])
            if generation:
                people.reverse()
            result += [(pid, budget, generation) for pid in people]
    return result


def slots():
    jobs = [('none', 'shared_j', None, None, None)]
    jobs += [('full', pid, None, None, None) for pid in PROFILES]
    jobs += [('extract', pid, budget, generation, None) for pid, budget, generation in cells()]
    for repeat in (0, 1):
        order = cells() if repeat == 0 else list(reversed(cells()))
        jobs += [('read', pid, budget, generation, repeat) for pid, budget, generation in order]
    return [{'slot': i+1, 'kind': kind, 'profile': pid, 'budget': budget, 'generation': generation,
             'read_repeat': repeat, 'key': ':'.join(str(v) for v in (kind, pid, budget, generation, repeat))}
            for i, (kind, pid, budget, generation, repeat) in enumerate(jobs)]


def parent(slot):
    return slot['profile'], slot['budget'], slot['generation']


def bank(pid):
    if pid not in PROFILES + ('shared_j',):
        raise ValueError('Foreign source')
    return 'j'


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen40slot schedule')
    data, pid, kind = inputs(), slot['profile'], slot['kind']
    if kind == 'extract':
        return {'model': MODEL, 'system': grouped_support.SYSTEM,
                **policy.make_request(data['sources'][pid], slot['budget'])}
    if kind == 'none':
        material = ''
    elif kind == 'full':
        material = canonical(data['sources'][pid])
    else:
        key = parent(slot)
        if parents is None or key not in parents:
            return None
        extraction = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == key)
        check(parents[key], request(extraction)['schema'])
        material = policy.bind(parents[key], data['sources'][pid], slot['budget'])['prompt.md']
        if not 0 < len(material) <= slot['budget']:
            raise ValueError('Whole-card cap exceeded')
    req = choice_reader.make_request(material, data['queries'][bank(pid)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped_support.SYSTEM, **req, 'prompt': COMMON + req['prompt']}


def implementation():
    files = list(HERE.glob('*.py')) + list((ROOT / 'runaway').rglob('*.py'))
    files += list((ROOT / 'benchmarks/compression-stability-v1').glob('*.py'))
    files += [ROOT / 'benchmarks/decision-targets-v1/experiment.py', ROOT / 'benchmarks/decision-targets-v1/check.py',
              ROOT / 'benchmarks/decision-targets-v1/oracle.py', ROOT / 'benchmarks/decision-targets-v1/prototype/decision_targets.py',
              ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py',
              ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json']
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    data = inputs()
    proposal = {'kind': 'unapproved_remaining_world_frontier40_consumed_fiction', 'requested_model': MODEL,
                'as_of': AS_OF, 'max_new_local_cli_attempts': CAP,
                'stages': {'controls': 4, 'source_only_extractions': 12, 'bound_reads': 24},
                'whole_character_budgets': list(BUDGETS), 'generations_per_source_budget': 2, 'reads_per_card': 2,
                'source_messages': 102, 'distinct_public_question_forms': 48, 'legacy_cases': 72,
                'primary_unflagged_author_cases': 69, 'unscored_disputed_cases': 3,
                'disputed_policy': 'Freeze the3preexisting w14 flags before new outputs. Keep all72legacy rows and48questions unchanged;send no reference/flag to a model. Score/gate69unflagged rows;report3flagged response vectors without acceptance or pass/fail. Do not retroactively change old72/96results or labels.',
                'controls': 'Each full immediately:all23primary cases,bothorders,no missing,personal-known>sharednone. All3mustpass before extraction. Flaggedw14is not a control-failure or pass criterion.',
                'primary': 'At each budget,69fixed cases require bothgenerations*bothreads*bothorders correct. Always report missing,known,unknown,personal-known and untyped strata;no best-of. Invalid exactcell skips only its2readers.',
                'method': 'Source-policyv1unchanged;no target-v2 or when-wire candidate,cachedcards,oldresponses or feedback. All12extractions before any read.',
                'aggregate_token_cap': None, 'money_cap': None, 'timeout_per_local_child_seconds': 180,
                'max_nominal_timeout_sum_seconds': 7200, 'not_a_spend_or_total_duration_cap': True,
                'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
                'fatal': 'Transport/wire/decode/unknownusage/requestedmodel/runtime/inputhash/ownedguard failure closes remainder. Intent counts even if upstream receipt unknown;unused expire.',
                'new_original_inventory_coverage_before_actual_binding_audit': 0,
                'original_inventory_current_measured': 160, 'original_inventory_current_remaining': 72,
                'preparation_or1024alone_does_not_fill1536_locked_inventory': True,
                'independent_holdout': False, 'real_person_fidelity_verified': False,
                'approved': False, 'new_service_authority': False, 'production_default_changed': False}
    values = {'proposal.json': proposal, 'slots.json': slots(), 'sources.json': data['sources'],
              'queries.public.json': data['queries'],
              'reference.consumed-development.private.json': {'primary_rows': data['rows'], 'disputed_rows': data['disputed_rows'], 'legacy_rows': data['legacy_rows']},
              'static-requests.json': {s['key']: request(s) for s in slots() if s['kind'] != 'read'},
              'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                'builder': 'benchmarks/remaining-world-frontier-v1/plan.py:request',
                'parent': 'Only exactprofile+budget+generation;unchanged source binder;two identical readers'},
              'implementation-sha256.json': implementation()}
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {name: sha(out / name) for name in sorted(values)},
                                                'new_model_calls': 0}, indent=2) + '\n')
    return proposal


def verify(root, *, reconstruct=True):
    for rel, expected in read(root / 'manifest.json')['files'].items():
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or sha(root / path) != expected:
            raise ValueError('Frozen input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Frozen implementation drift')
    if reconstruct:
        data = inputs()
        if read(root / 'sources.json') != data['sources'] or read(root / 'queries.public.json') != data['queries']:
            raise ValueError('Source/query drift')
        if read(root / 'slots.json') != slots() or read(root / 'static-requests.json') != {s['key']: request(s) for s in slots() if s['kind'] != 'read'}:
            raise ValueError('Schedule/request drift')
        if read(root / 'reference.consumed-development.private.json') != {'primary_rows': data['rows'], 'disputed_rows': data['disputed_rows'], 'legacy_rows': data['legacy_rows']}:
            raise ValueError('Reference/mask drift')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
