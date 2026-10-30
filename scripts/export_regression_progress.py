"""Export only fictional, portable evidence from the five closed local studies.

No backend, approval receipt or private transport envelope is published. This
command reads sealed local runs; CI replays the exported snapshot without them.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runaway.card import canonical


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def verify_sealed(root):
    for name in ('manifest.json', 'observation-manifest.json'):
        manifest = read(root / name)
        for rel, expected in manifest['files'].items():
            path = root / rel
            if path.is_symlink() or sha(path) != expected:
                raise ValueError('Sealed evidence drift: ' + rel)


def export_records(root):
    state = read(root / 'execution/result.json')
    if state['simulated'] or state['status'] not in ('complete',):
        raise ValueError('This snapshot exports only the five completed scopes')
    if state.get('skipped') or state.get('invalid_products') or state['missing_usage']:
        raise ValueError('Unexpected missing/product-failure scope')
    records = []
    usage_fields = ('input_tokens', 'output_tokens', 'cached_input_tokens',
                    'cache_write_input_tokens', 'reasoning_output_tokens')
    for rec in state['records']:
        if rec['state'] != 'completed' or rec['simulated']:
            raise ValueError('Unexpected incomplete observation')
        folder = root / 'execution' / rec['execution_id']
        req = read(folder / 'request.json')
        original = read(folder / 'raw-response.json')
        if digest(req) != rec['request_sha256'] or sha(folder / 'raw-response.json') != rec['raw_response_sha256']:
            raise ValueError('Original request/response binding differs')
        prov = original['provenance']
        if prov['backend'] != 'codex' or prov['model_requested'] != 'gpt-6.1-sol':
            raise ValueError('Unexpected backend/model')
        public = {
            'slot': rec['slot'], 'execution_id': rec['execution_id'],
            'group': rec.get('group', rec.get('kind')),
            'person': rec.get('person', rec.get('profile')),
            'state': rec['state'], 'request': req, 'request_sha256': rec['request_sha256'],
            'raw': original['raw'],
            'raw_text_sha256': hashlib.sha256(original['raw'].encode()).hexdigest(),
            'usage_rows': [{k: row[k] for k in usage_fields if k in row} for row in prov['usage']],
            'usage': rec['usage'],
            'requested_model': prov['model_requested'], 'backend': prov['backend'],
            'original_response_envelope_sha256': rec['raw_response_sha256'],
        }
        if public['person'] is None and public['group'] == 'none':
            public['person'] = 'shared'
        if (folder / 'artifact.json').exists():
            artifact = read(folder / 'artifact.json')
            public['card'] = {k: artifact[k] for k in ('prompt', 'characters', 'source_sha256')}
        records.append(public)
    return records, {'status': state['status'], 'stop': state.get('stop'),
                     'scope_closed': state.get('scope_closed', True),
                     'unused_slots_expire': state.get('unused_slots_expire', 0),
                     'known_usage': state['known_usage'], 'missing_usage': state['missing_usage']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', required=True, type=Path)
    parser.add_argument('--out', type=Path, default=ROOT / 'benchmarks/regression-progress-v1')
    args = parser.parse_args()
    runs, out = args.runs_root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    study_paths = {
        'forward': runs / 'forward-reader-v1',
        'new_worlds': runs / 'unseen-worlds-v1',
        'repair': runs / 'policy-scope-repair-v1',
        'h17': runs / 'next-evidence-decision-v1/development/regression-pilot-proposal',
        'remaining_h': runs / 'next-evidence-decision-v1/development/remaining-h-regression-proposal',
    }
    studies = {}
    source_worlds = {}
    for name, root in study_paths.items():
        verify_sealed(root)
        records, status = export_records(root)
        if name in ('forward', 'new_worlds'):
            people = read(root / 'sources/index.json')['people']
            sources = {pid: read(root / 'sources' / (pid + '.json')) for pid in people}
            queries = read(root / 'evaluation/queries.public.json')
            rows = read(root / 'evaluation/gold.private.json')['rows']
            initial = read(root / 'cards/fixed.json')['cards'] if name == 'forward' else {}
            as_of = read(root / 'configuration.json')['as_of']
            kind = name
            source_worlds.update(sources)
        elif name == 'repair':
            people = ['j39']
            sources = {'j39': source_worlds['j39']}
            queries = read(root / 'evaluation/queries.public.json')
            rows = read(root / 'evaluation/gold.private.json')['rows']
            initial = {'j39': {k: read(root / 'baseline/card.json')[k] for k in ('prompt', 'characters', 'source_sha256')}}
            as_of, kind = '2026-10-25', 'single_repair'
        elif name == 'h17':
            people, sources = ['h17'], {'h17': read(root / 'source.json')}
            queries = read(root / 'queries.public.json')
            rows = read(root / 'gold.consumed-development.private.json')['rows']
            initial = {'h17': read(root / 'baseline-card.json')}
            as_of, kind = '2026-10-28', 'single_repair'
        else:
            people = ['h42', 'h68', 'h93']
            sources = read(root / 'sources.json')
            queries = read(root / 'queries.public.json')
            rows = read(root / 'gold.consumed-development.private.json')['rows']
            initial = read(root / 'baseline-cards.json')
            as_of, kind = '2026-10-29', 'remaining_h'
        studies[name] = {
            'kind': kind, 'people': people, 'sources': sources, 'queries': queries,
            'reference_rows': rows, 'initial_cards': initial, 'records': records,
            'reference_sha256': digest(rows), 'sources_sha256': digest(sources),
            'queries_sha256': digest(queries), 'initial_cards_sha256': digest(initial),
            'as_of': as_of, 'requested_model': 'gpt-6.1-sol', 'whole_card_cap': 1536,
            'status': status, 'new_service_authority': False,
            'source_input_manifest_sha256': sha(root / 'manifest.json'),
            'source_observation_manifest_sha256': sha(root / 'observation-manifest.json'),
        }
    # The fixed role-spoof payload is synthetic quoted content, never executed.
    # Take the actual full-attack material suffix, retaining every byte while
    # proving the un-attacked prefix is exactly this person's source JSON.
    attack_rec = next(r for r in studies['new_worlds']['records'] if r['group'] == 'full_attack')
    body = json.loads(attack_rec['request']['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
    prefix = canonical(studies['new_worlds']['sources'][attack_rec['person']])
    if not body['material'].startswith(prefix):
        raise ValueError('Attack source prefix differs')
    studies['new_worlds']['attack_attachment'] = body['material'][len(prefix):]
    # Separate two actual opinions from semantic acceptance. Preserve the first
    # controller failure instead of promoting its posthoc audit into success.
    first = runs / 'w14-firstpass-review-v1'
    second = runs / 'w14-citation-controller-v2-offline'
    verify_sealed(first)
    for rel, expected in read(second / 'manifest.json')['files'].items():
        if sha(second / rel) != expected:
            raise ValueError('Neutral input drift')
    for rel, expected in read(second / 'single-review-observation-manifest.json')['files'].items():
        if sha(second / rel) != expected:
            raise ValueError('Neutral observation drift')
    neutral = read(first / 'review/neutral-input.json')
    semantics = {
        'question': neutral['original_question'], 'episodes': neutral['episodes'],
        'opinions': [
            {'report': read(first / 'firstpass-report.unaccepted.json')['original_report'],
             'original_controller_state': 'failed', 'failure': 'question citation ID omitted by old validator',
             'posthoc_literal_citations_verified': True,
             'usage': read(first / 'execution/result.json')['known_usage']},
            {'report': read(second / 'service-execution/report.json'),
             'original_controller_state': 'completed', 'failure': None,
             'usage': read(second / 'service-execution/result.json')['usage']},
        ],
        'same_requested_model': True, 'independent_semantic_acceptance': False,
        'original_w14_labels_or_93of96_changed': False,
    }
    modules = ['card', 'choice_reader', 'choice_contract', 'constraint_extract', 'portable', 'profile',
               'prompt_codec', 'scope_rows', 'grouped_support', 'support_extract', 'text_integrity']
    data = {
        'kind': 'consumed_actual_regression_progress', 'studies': studies,
        'all_sources_fictional': True, 'developer_visible': True, 'independent_holdout': False,
        'real_person_or_cross_vendor_fidelity_verified': False,
        'production_default_changed': False, 'new_service_authority': False,
        'transport_metadata_policy': 'Exact request objects and raw JSON response text retained. Private transport envelopes, credentials, local paths and approval records omitted; original envelope hashes are provenance only,not publicly reconstructed bytes.',
        'runtime_sha256': {'runaway/' + module + '.py': sha(ROOT / 'runaway' / (module + '.py')) for module in modules},
    }
    for filename, value in [('observed.synthetic.json', data), ('semantic-dispute.synthetic.json', semantics)]:
        text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if re.search(r'/Users/|Documents/ChatGPT|Bearer\s+[A-Za-z0-9]|sk-[A-Za-z0-9]{24}|direct-human-', text):
            raise ValueError('Private local/authorization data in public export')
        (out / filename).write_text(text, encoding='utf-8')
        (out / filename.replace('.json', '.sha256')).write_text(sha(out / filename) + '\n')
    cards = out / 'cards'
    cards.mkdir(exist_ok=True)
    for name, study in studies.items():
        for rec in study['records']:
            if 'card' in rec:
                (cards / (name + '-' + rec['person'] + '.txt')).write_text(rec['card']['prompt'], encoding='utf-8')
    print(json.dumps({'studies': len(studies), 'actual_choice_calls': sum(len(s['records']) for s in studies.values()),
                      'neutral_opinions': 2, 'new_model_calls': 0,
                      'public_bytes': (out / 'observed.synthetic.json').stat().st_size}))


if __name__ == '__main__':
    main()
