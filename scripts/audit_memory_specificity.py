"""Post-hoc donor-response rescoring of sealed fiction; no model calls or new trials."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIES = {
    'fresh': ('fresh-decision-v1', 'replay_fresh_decision.py',
              'c54bd485cdb7002dafc825679116fb64fd5aa5741aef1975e52891c940007781'),
    'partial': ('partial-information-v1', 'replay_partial_information.py',
                '8a8514f9da14a427ccf898dd608195edd741c8e588569e7412e4cfa9c0ff86aa'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def common_contract(records, queries, parents):
    """Only the material may vary; never assume a recipient-specific prompt matches."""
    fingerprints = set()
    for record in records:
        request = copy.deepcopy(record['request'])
        prefix, marker, raw = request['prompt'].rpartition('\nREADER_INPUT_JSON:\n')
        if not marker:
            raise ValueError('Reader payload marker missing')
        payload = json.loads(raw)
        if (set(payload) != {'material', 'queries'} or payload['queries'] != queries or
                payload['material'] != parents[record['profile'], record['generation_repeat']]):
            raise ValueError('Queries, material or public parent differ')
        payload['material'] = ''
        request['prompt'] = prefix + marker + json.dumps(payload, ensure_ascii=False,
                                                        sort_keys=True, separators=(',', ':'))
        fingerprints.add(digest(request))
    if len(fingerprints) != 1:
        raise ValueError('Reader requests differ beyond the supplied material')
    return next(iter(fingerprints))


def count(cells):
    return {'total': len(cells), 'correct': sum(c['correct'] for c in cells),
            'missing': sum(c['missing'] for c in cells)}


def matrix(rows, responses, profiles):
    """Keep all planned eight-answer cells; missing is never converted to U."""
    if not profiles or len(set(profiles)) != len(profiles) or not rows:
        raise ValueError('Nonempty unique profiles and references required')
    by_person = {person: {} for person in profiles}
    for row in rows:
        if row['person'] not in by_person or row['case'] in by_person[row['person']]:
            raise ValueError('Foreign or duplicate reference case')
        if (type(row['gold']) is not str or not row['gold'] or
                len(row['query_ids']) != 2 or len(set(row['query_ids'])) != 2):
            raise ValueError('Each reference needs a choice/U and two query IDs')
        by_person[row['person']][row['case']] = row
    first = by_person[profiles[0]]
    for own in by_person.values():
        if set(own) != set(first) or any(own[case]['query_ids'] != first[case]['query_ids'] for case in first):
            raise ValueError('Recipients do not share the same public case contract')
    cells = []
    for recipient in profiles:
        for donor in profiles:
            for case, row in by_person[recipient].items():
                answers = [[responses.get((donor, generation, repeat), {}).get(q)
                            for repeat in (0, 1) for q in row['query_ids']]
                           for generation in (0, 1)]
                values = [v for group in answers for v in group]
                gold, donor_gold = row['gold'], by_person[donor][case]['gold']
                cells.append({'recipient': recipient, 'donor': donor, 'case': case,
                              'gold': gold, 'donor_gold': donor_gold,
                              'correct': all(v == gold for v in values),
                              'missing': any(v is None for v in values),
                              'known': gold != 'U',
                              'contrast_known': gold != 'U' and donor_gold != 'U' and gold != donor_gold,
                              'answers_by_parent': answers})

    def slices(selected):
        return {'all': count(selected),
                'known': count([c for c in selected if c['known']]),
                'unknown': count([c for c in selected if not c['known']]),
                'contrast_known': count([c for c in selected if c['contrast_known']])}

    own = [c for c in cells if c['recipient'] == c['donor']]
    other = [c for c in cells if c['recipient'] != c['donor']]
    contrast = [c for c in other if c['contrast_known']]
    unique_contrast = {(c['recipient'], c['case']) for c in contrast}
    return {'own': slices(own), 'other_card_rescore': slices(other),
            'matrix': [{'recipient': recipient, 'donor': donor,
                        **slices([c for c in cells if c['recipient'] == recipient and c['donor'] == donor])}
                       for recipient in profiles for donor in profiles],
            'contrast_unique_recipient_cases': len(unique_contrast),
            'own_on_unique_contrast': count([c for c in own if (c['recipient'], c['case']) in unique_contrast]),
            'ordered_mismatched_pairs': len(profiles) * (len(profiles) - 1),
            'cells': cells}


def audit(name):
    folder, script, expected = STUDIES[name]
    path = ROOT / 'benchmarks' / folder / 'measured.synthetic.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Pinned original evidence changed')
    spec = importlib.util.spec_from_file_location('specificity_' + name, ROOT / 'scripts' / script)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    data = json.loads(path.read_text())
    # Reconstruct original requests, controls, raw responses, scores and usage
    # through the existing offline validator before any post-hoc rescoring.
    verified = replay.replay(data)
    if not verified['controls_qualified'] or not verified['original_scope_closed']:
        raise ValueError('Original control gate or closed scope missing')
    records = [r for r in data['records'] if r['kind'] == 'read' and r['view'] == 'card']
    parents = {}
    if name == 'fresh':
        for record in data['records']:
            if record['kind'] == 'extract' and record['artifact'] is not None:
                parents[record['profile'], record['generation_repeat']] = record['artifact']['prompt']
    else:
        parents = {(v['profile'], v['parent_generation']): v['prompt']
                   for v in data['prepared_files']['parents.public.json'].values()}
    queries = data['prepared_files']['queries.public.json']['all']
    contract = common_contract(records, queries, parents)
    profiles = tuple(replay.p.PROFILES)
    responses = {}
    for record in records:
        key = record['profile'], record['generation_repeat'], record['read_repeat']
        if key in responses or record['state'] != 'completed':
            raise ValueError('Duplicate or incomplete original card reader')
        responses[key] = replay.e.parse_answer(record['raw'])
    if set(responses) != {(p, g, r) for p in profiles for g in (0, 1) for r in (0, 1)}:
        raise ValueError('All original card readers required')
    rows = data['prepared_files']['reference.private.json']
    subsets = {'all': rows}
    if name == 'partial':
        subsets.update(primary=[r for r in rows if r['primary']],
                       anchors=[r for r in rows if not r['primary']])
    return {'study': name, 'original_evidence_sha256': expected,
            'original_replay_verified': True, 'material_only_contract_sha256': contract,
            'reused_card_reader_records': len(records), 'profiles': list(profiles),
            'answers_per_pair_case': 8, 'new_model_calls': 0, 'new_extractions': 0,
            'posthoc_rescoring': True, 'new_independent_trials': False,
            'recipient_identity_routing_verified': False, 'real_person_fidelity_verified': False,
            'production_default_changed': False, 'RIG_computed': False,
            'subsets': {key: matrix(selected, responses, profiles) for key, selected in subsets.items()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', choices=tuple(STUDIES) + ('all',), default='all')
    parser.add_argument('--details', action='store_true', help='Include every donor/recipient case and all eight answers')
    args = parser.parse_args(argv)
    result = [audit(name) for name in STUDIES if args.study in ('all', name)]
    if not args.details:
        for study in result:
            for subset in study['subsets'].values():
                subset.pop('cells')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
