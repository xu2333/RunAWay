"""Reconstruct actual repeat45 evidence from portable archived values, with zero services."""
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LOCATOR = HERE / 'fresh-decision-locator.private.json'
ROOT = Path(json.loads(LOCATOR.read_text())['repository_root']) if LOCATOR.exists() else HERE.parent
spec = importlib.util.spec_from_file_location('repeat_evidence_engine', ROOT / 'benchmarks/fresh-decision-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
e.parse_answer, e.score, e.usage = e.shared.parse_answer, e.shared.score, e.shared.usage
KIND = 'actual_fresh_decision45'
SOURCE = '02ce4d581d72dc2c4d89bb8d23bf02626682e81a'
INPUT = '0b6935d0853254ae966e050e340be6c38e86a31cfef72f64a68987e0f9b3a0be'
DEFAULT = ROOT / 'benchmarks/fresh-decision-v1/measured.synthetic.json'
FALSE_CLAIMS = ('new_service_authority', 'old_scopes_reopened', 'old_scores_replaced',
                'production_default_changed', 'independent_holdout',
                'population_generation_stability_verified', 'real_person_fidelity_verified',
                'source_reference_semantics_verified', 'cross_provider_verified',
                'token_matched_tail', 'optimal_tail_selection')
PROVENANCE_LIMITS = ('Checksums and archive replay verify content consistency,not independent service '
                     'attestation,model identity or source-reference semantics.')
SLOT_KEYS = ('slot', 'kind', 'profile', 'generation_repeat', 'view', 'read_repeat')
ROOT_KEYS = set(FALSE_CLAIMS) | {'kind', 'scientific_source_ref', 'input_manifest_sha256',
                                'source_observation_manifest_sha256', 'all_sources_fictional',
                                'prepared_files', 'records', 'status', 'provenance_limits'}
RECORD_KEYS = set(SLOT_KEYS) | {'state', 'error_type', 'request', 'request_sha256',
                              'raw_present', 'raw', 'raw_value_sha256',
                              'original_response_envelope_sha256', 'failure_provenance_present',
                              'backend', 'requested_model', 'usage', 'usage_rows',
                              'local_cli_child_intent', 'artifact', 'execution_record'}
STATUS_KEYS = ('status', 'stop', 'control_gate', 'skipped', 'attempt_reservations',
               'local_cli_child_intents', 'known_usage', 'missing_usage',
               'unused_slots_expire', 'scope_closed', 'simulated',
               'new_service_authority', 'scores', 'old_scopes_reopened', 'production_default_changed')


def safe_invalid(rows):
    return [{k: v for k, v in row.items() if k != 'error'} for row in rows]


def safe_record(rec):
    return {k: v for k, v in rec.items() if k not in ('raw_response_sha256', 'error')}


def status(state):
    return {**{k: state[k] for k in STATUS_KEYS}, 'invalid_products': safe_invalid(state['invalid_products'])}


def loss_kind(gold, values):
    """Classify archived answer relationships;never replace a missing answer by U."""
    if not values:
        raise ValueError('No planned answers supplied')
    if any(value is None for value in values):
        return 'missing'
    if gold == 'U':
        return 'choice_when_reference_unknown' if any(value != 'U' for value in values) else 'retained'
    wrong = any(value not in (gold, 'U') for value in values)
    unknown = any(value == 'U' for value in values)
    if all(value == 'U' for value in values):
        return 'all_unknown_from_known'
    if wrong and unknown:
        return 'mixed_unknown_and_different_choice'
    if unknown:
        return 'intermittent_unknown_from_known'
    return 'different_choice_from_known' if wrong else 'retained'


def replay(data):
    if set(data) != ROOT_KEYS or data['provenance_limits'] != PROVENANCE_LIMITS:
        raise ValueError('Unreviewed portable fields or claims')
    observation_hash = data['source_observation_manifest_sha256']
    if type(observation_hash) is not str or len(observation_hash) != 64 or any(c not in '0123456789abcdef' for c in observation_hash):
        raise ValueError('Original observation fingerprint differs')
    if data['kind'] != KIND or data['scientific_source_ref'] != SOURCE:
        raise ValueError('Foreign study or source')
    if data['input_manifest_sha256'] != INPUT or data['all_sources_fictional'] is not True:
        raise ValueError('Foreign input or source type')
    if any(data[k] is not False for k in FALSE_CLAIMS):
        raise ValueError('Unsupported claim')
    if data['prepared_files'] != p.values():
        raise ValueError('Exact source,question,reference or implementation differs')
    records = data['records']
    by_slot = {rec['slot']: rec for rec in records}
    if len(by_slot) != len(records) or not 0 <= len(records) <= p.CAP:
        raise ValueError('Repeated or excessive original attempts')
    for rec in records:
        if set(rec) != RECORD_KEYS:
            raise ValueError('Unreviewed portable record field')
        for key in SLOT_KEYS + ('state', 'usage', 'request_sha256'):
            if rec[key] != rec['execution_record'][key]:
                raise ValueError('Portable record metadata differs')
    if data['status']['simulated'] is not False or data['status']['scope_closed'] is not True:
        raise ValueError('Only closed real observations may be measured')
    consumed = []

    def before(slot):
        stop = data['status']['stop']
        if slot['slot'] not in by_slot and stop and stop.startswith('pre_call_failure:'):
            raise type(stop.split(':', 1)[1], (Exception,), {})('Archived pre-call failure')
        return {'owned_active': True}

    def archived(req, folder, slot):
        rec = by_slot[slot['slot']]
        if {k: rec[k] for k in SLOT_KEYS} != slot:
            raise ValueError('Original person,generation,view or repeat differs')
        if req != rec['request'] or p.digest(req) != rec['request_sha256']:
            raise ValueError('Original request differs')
        consumed.append(slot['slot'])
        if rec['raw_present']:
            if p.digest(rec['raw']) != rec['raw_value_sha256']:
                raise ValueError('Original raw value differs')
            return rec['raw'], {'backend': rec['backend'], 'model_requested': rec['requested_model'],
                                'usage': rec['usage_rows']}
        if rec['state'] != 'failed' or rec['raw'] is not None or rec['raw_value_sha256'] is not None:
            raise ValueError('Missing raw response differs')
        exc = type(rec['error_type'], (Exception,), {})('Archived failed invocation')
        if rec['failure_provenance_present']:
            exc.provenance = {'backend': rec['backend'], 'model_requested': rec['requested_model'],
                              'usage': rec['usage_rows']}
        raise exc

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        p.prepare(tmp / 'inputs')
        if p.sha(tmp / 'inputs/manifest.json') != INPUT:
            raise ValueError('Prepared input fingerprint differs')
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('Replay cannot call service')) as backend:
            rebuilt = e.run(tmp / 'inputs', tmp / 'replay', archived, before, simulated=False)
        backend.assert_not_called()
        if consumed != [r['slot'] for r in records]:
            raise ValueError('Original attempt sequence differs')
        for rec, observed in zip(rebuilt['records'], records):
            if safe_record(rec) != observed['execution_record']:
                raise ValueError('Original execution record differs')
            folder = tmp / 'replay' / ('attempt-%02d' % rec['slot'])
            artifact = p.read(folder / 'artifact.json') if (folder / 'artifact.json').exists() else None
            if artifact != observed['artifact']:
                raise ValueError('Original public card differs')
            if artifact is not None and p.sha(folder / 'artifact.json') != rec['artifact_sha256']:
                raise ValueError('Original artifact bytes differ')
        rebuilt['local_cli_child_intents'] = data['status']['local_cli_child_intents']
        if status(rebuilt) != data['status']:
            raise ValueError('Control,score,denominator,counter or usage differs')
    if not 0 <= data['status']['local_cli_child_intents'] <= len(records):
        raise ValueError('Original child count differs')
    expected_children = sum(r['local_cli_child_intent'] is True for r in records)
    if expected_children != data['status']['local_cli_child_intents']:
        raise ValueError('Original child ledger differs')
    stages, cards = {}, []
    for rec in records:
        stage = rec['kind'] if rec['kind'] != 'read' else rec['view'] + '_read'
        row = stages.setdefault(stage, {'actual_calls': 0, 'known_total_tokens': 0, 'missing_usage': 0})
        row['actual_calls'] += 1
        if rec['usage'] is None:
            row['missing_usage'] += 1
        else:
            row['known_total_tokens'] += rec['usage']['total_tokens']
        if rec['artifact'] is not None:
            cards.append(rec['artifact'])
    losses, generation_differences = [], []
    source_rows = p.inputs()['rows']
    for cell in rebuilt['scores']['transitions']:
        reference = next(r for r in source_rows if r['person'] == cell['person'] and r['case'] == cell['case'])
        for view in p.VIEWS:
            answers = []
            for generation in (0, 1):
                values = []
                for repeat in (0, 1):
                    rec = next((x for x in records if x['kind'] == 'read' and x['profile'] == cell['person']
                                and x['generation_repeat'] == generation and x['view'] == view
                                and x['read_repeat'] == repeat and x['state'] == 'completed'), None)
                    decoded = e.parse_answer(rec['raw']) if rec is not None else {}
                    values.extend(decoded.get(q) for q in reference['query_ids'])
                answers.append(values)
            if answers[0] != answers[1]:
                generation_differences.append({
                    'person': cell['person'], 'case': cell['case'], 'view': view,
                    'gold': reference['gold'], 'answers_by_generation': answers,
                    'correct_by_generation': [all(v == reference['gold'] for v in row) for row in answers],
                    'missing_by_generation': [any(v is None for v in row) for row in answers]})
            if not cell[view]['correct']:
                losses.append({'person': cell['person'], 'case': cell['case'], 'view': view,
                               'gold': reference['gold'], 'known': cell['known'],
                               'derived_known': cell['derived_known'], 'cohort': cell['cohort'],
                               'missing': cell[view]['missing'], 'answers_by_generation': answers,
                               'failure_kind': loss_kind(reference['gold'], [v for row in answers for v in row])})
    loss_counts = {}
    for loss in losses:
        key = loss['view'] + ':' + loss['cohort'] + ':' + loss['failure_kind']
        loss_counts[key] = loss_counts.get(key, 0) + 1
    card_results = []
    for pid in p.PROFILES:
        own = [row for row in source_rows if row['person'] == pid]
        for generation in (0, 1):
            original = next((rec for rec in records if rec['kind'] == 'extract' and
                             rec['profile'] == pid and rec['generation_repeat'] == generation), None)
            artifact = original['artifact'] if original is not None else None
            views = {}
            for view in p.VIEWS:
                decoded = []
                for repeat in (0, 1):
                    rec = next((x for x in records if x['kind'] == 'read' and x['profile'] == pid
                                and x['generation_repeat'] == generation and x['view'] == view
                                and x['read_repeat'] == repeat and x['state'] == 'completed'), None)
                    decoded.append(e.parse_answer(rec['raw']) if rec is not None else {})
                views[view] = e.score.counts(own, decoded)
            card_results.append({'person': pid, 'generation_repeat': generation,
                                 'card_available': artifact is not None,
                                 'characters': artifact['characters'] if artifact is not None else None,
                                 'views': views})
    return {'kind': KIND, 'actual_original_attempts': len(records),
            'actual_original_children': expected_children,
            'controls_qualified': len(rebuilt['control_gate']) == 4 and
            all(v['qualified'] for v in rebuilt['control_gate'].values()),
            'summary': rebuilt['scores'], 'cards': cards, 'per_person_generation': card_results,
            'failed_or_missing_cases': losses, 'generation_differences': generation_differences,
            'usage_by_stage': stages, 'loss_counts_by_view_cohort_reason': loss_counts,
            'known_original_usage': rebuilt['known_usage'], 'missing_original_usage': rebuilt['missing_usage'],
            'invalid_products': safe_invalid(rebuilt['invalid_products']), 'skipped': rebuilt['skipped'],
            'unused_slots_expire': rebuilt['unused_slots_expire'], 'original_scope_closed': True,
            'new_model_calls_from_replay': 0, 'production_default_changed': False}


def check(path=DEFAULT):
    path = Path(path)
    if p.sha(path) != path.with_suffix('.sha256').read_text().strip():
        raise ValueError('Portable evidence checksum differs')
    return replay(p.read(path))


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
