"""Freeze14read-only layout comparisons; no generation, backend or service."""
import argparse
import copy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway.card import canonical


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


derived = load('dense_read_derivation', HERE.parent / 'owned-dense-v1/evidence.py')
old = derived.upstream.engine.plan
read, sha, digest = old.read, old.sha, old.digest
choice_reader, grouped_support = old.choice_reader, old.grouped_support
PROFILES, METHODS = ('h93',), ('baseline', 'expanded', 'dense')
MODEL, AS_OF, CAP, BUDGET = old.MODEL, old.AS_OF, 14, 1536
COMMON = '仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'


def inputs():
    data = old.inputs()
    return {k: data[k] for k in ('sources', 'queries', 'rows', 'legacy_rows', 'disputed_rows')}


@lru_cache(maxsize=1)
def _views():
    derived.check()
    data = read(derived.DEFAULT)
    views = []
    for card in data['baseline_cards']:
        views.append({'profile': 'h93', 'method': 'baseline', 'generation': card['generation'],
            'prompt': card['prompt'], 'characters': len(card['prompt']), 'memory_ceiling': BUDGET,
            'view_class': 'previous_valid_baseline', 'source_sha256': card['source_sha256'],
            'parent_answer_sha256': card['answer_sha256'], 'semantic_projection_sha256': None})
    for parent in data['parents']:
        for method in ('expanded', 'dense'):
            prompt = parent[method+'_prompt']
            views.append({'profile': 'h93', 'method': method, 'generation': parent['generation'],
                'prompt': prompt, 'characters': len(prompt), 'memory_ceiling': None if method == 'expanded' else BUDGET,
                'view_class': 'uncapped_literal_projection_diagnostic' if method == 'expanded' else 'lossless_dense_candidate',
                'source_sha256': parent['source_sha256'], 'parent_answer_sha256': parent['ledger_sha256'],
                'semantic_projection_sha256': digest(parent['semantic_projection'])})
    if len(views) != 6 or any(v['memory_ceiling'] is not None and v['characters'] > v['memory_ceiling'] for v in views):
        raise ValueError('Fixed layout inventory differs')
    return views


def views():
    return copy.deepcopy(_views())


def parent(slot):
    return slot['profile'], slot['method'], slot['generation']


def view(slot):
    return next(v for v in views() if (v['profile'], v['method'], v['generation']) == parent(slot))


def bank(pid):
    if pid not in ('h93', 'shared_h'):
        raise ValueError('Foreign source')
    return 'h'


def slots():
    cells = [('baseline', 0), ('expanded', 0), ('dense', 0), ('dense', 1), ('expanded', 1), ('baseline', 1)]
    jobs = [('none', 'shared_h', None, None, None), ('full', 'h93', None, None, None)]
    for repeat in (0, 1):
        jobs += [('read', 'h93', m, g, repeat) for m, g in (cells if repeat == 0 else reversed(cells))]
    return [{'slot': i+1, 'kind': k, 'profile': p, 'method': m, 'generation': g, 'read_repeat': r,
        'budget': BUDGET if m in ('baseline', 'dense') else None,
        'key': ':'.join(map(str, (k, p, m, g, r)))} for i, (k, p, m, g, r) in enumerate(jobs)]


def request(slot, parents=None):
    if slot not in slots() or parents:
        raise ValueError('Only frozen fixed views allowed')
    data = inputs()
    material = '' if slot['kind'] == 'none' else canonical(data['sources']['h93']) if slot['kind'] == 'full' else view(slot)['prompt']
    req = choice_reader.make_request(material, data['queries']['h'], as_of=AS_OF, answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped_support.SYSTEM, **req, 'prompt': COMMON + req['prompt']}


def implementation():
    result = old.implementation()
    paths = list(HERE.glob('*.py')) + list((HERE.parent / 'owned-dense-v1').glob('*.py'))
    paths += [derived.DEFAULT, derived.DEFAULT.with_suffix('.sha256'), derived.upstream.DEFAULT,
              derived.upstream.DEFAULT.with_suffix('.sha256'), ROOT / 'scripts/replay_budgeted_table_probe.py',
              ROOT / 'scripts/replay_compression_stability.py']
    result.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    return dict(sorted(result.items()))


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    data = inputs()
    proposal = {'kind': 'unapproved_dense_layout_readonly14', 'requested_model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'stages': {'controls': 2, 'fixed_view_reads': 12, 'new_extractions': 0},
        'source_messages': 48, 'public_question_forms': 80, 'primary_cases': 40,
        'methods': list(METHODS), 'primary_candidate': 'dense', 'primary_memory_ceiling': BUDGET,
        'expanded_view_is_uncapped_diagnostic_not_memory_candidate': True,
        'inherited_producer_generations': 2, 'new_reads_per_fixed_view': 2,
        'primary': 'Dense40fixed cases,each requires both inherited ledger parents*both new reads*both orders correct. Baseline40secondary at1536;expanded40uncapped semantic control,not a compression pass. Keep all missing if scope stops.',
        'control': 'New full source immediately40cases,bothorders,no missing,personal-known>none;failure closes before read3.',
        'lineage': 'Both chronological budgeted14candidate outputs reused unchanged;expanded/dense share exact literal semantic projection. Previous baseline cards fixed too. No new generation or repair/replacement of old closed experiment products.',
        'aggregate_token_cap': None, 'money_cap': None, 'timeout_per_local_child_seconds': 180,
        'max_nominal_timeout_sum_seconds': 2520, 'not_a_spend_or_total_duration_cap': True,
        'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
        'fatal': 'Control,transport,wire,decode,unknownusage,model,runtime,inputhash,viewhash or ownedguard failure closes remainder;intent counts;unused expire. All views prevalidated;no per-product regeneration or invalid skips.',
        'references_scores_prior_reader_responses_sent': False, 'old_generated_public_views_sent': True,
        'independent_holdout': False, 'fresh_generation_stability_test': False,
        'new_original_inventory_coverage': 0, 'validates_j16_or_development': False,
        'approved': False, 'new_service_authority': False, 'production_default_changed': False}
    values = {'proposal.json': proposal, 'slots.json': slots(), 'sources.json': data['sources'], 'queries.public.json': data['queries'],
        'reference.consumed-development.private.json': {k: data[k] for k in ('rows', 'legacy_rows', 'disputed_rows')},
        'views.public.json': views(), 'static-requests.json': {s['key']: request(s) for s in slots()},
        'dynamic-rules.json': {'slots': [], 'reason': 'All14requests frozen;no new generation or dynamic card binding'},
        'implementation-sha256.json': implementation()}
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2)+'\n')
    return proposal


def verify(root, *, reconstruct=True):
    for rel, expected in read(root / 'manifest.json')['files'].items():
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts or (root / p).is_symlink() or sha(root / p) != expected:
            raise ValueError('Frozen input/view drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Frozen implementation/ancestor drift')
    if reconstruct:
        data = inputs()
        pairs = [('sources.json', data['sources']), ('queries.public.json', data['queries']), ('slots.json', slots()),
            ('views.public.json', views()), ('static-requests.json', {s['key']: request(s) for s in slots()}),
            ('reference.consumed-development.private.json', {k: data[k] for k in ('rows', 'legacy_rows', 'disputed_rows')})]
        if any(read(root / n) != expected for n, expected in pairs):
            raise ValueError('Reconstructed fixed views differ')
    return True


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
