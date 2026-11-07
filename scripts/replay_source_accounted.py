"""Reconstruct actual source-accounted27 evidence from portable archived values, with zero services."""
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LOCATOR = HERE / 'source-accounted-locator.private.json'
ROOT = Path(json.loads(LOCATOR.read_text())['repository_root']) if LOCATOR.exists() else HERE.parent
spec = importlib.util.spec_from_file_location('repeat_evidence_engine', ROOT / 'benchmarks/source-accounted-encoding-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
from runaway.constraint_extract import parse_answer
e.parse_answer = parse_answer
KIND = 'actual_source_accounted27'
SOURCE = '1938b59845e3b33b28a17aab5fffeff8cbb1dfdf'
INPUT = '5520c69ffd50c386e5c23e62a611ebcba31752c400ce8b0098c899a892485227'
DEFAULT = ROOT / 'benchmarks/source-accounted-encoding-v1/measured.synthetic.json'
FALSE_CLAIMS = ('new_service_authority', 'old_scopes_reopened', 'old_scores_replaced',
                'production_default_changed', 'independent_holdout',
                'population_generation_stability_verified', 'real_person_fidelity_verified',
                'source_reference_semantics_verified', 'cross_provider_verified',
                'token_matched_tail', 'optimal_tail_selection')
PROVENANCE_LIMITS = ('Checksums and archive replay verify content consistency,not independent service '
                     'attestation,model identity or source-reference semantics.')
SLOT_KEYS = ('slot', 'kind', 'profile', 'method', 'generation', 'budget', 'read_repeat', 'view', 'key')
ROOT_KEYS = set(FALSE_CLAIMS) | {'kind', 'scientific_source_ref', 'input_manifest_sha256',
                                'source_observation_manifest_sha256', 'all_sources_fictional',
                                'prepared_files', 'records', 'status', 'provenance_limits'}
RECORD_KEYS = set(SLOT_KEYS) | {'state', 'error_type', 'request', 'request_sha256',
                              'raw_present', 'raw', 'raw_value_sha256',
                              'original_response_envelope_sha256', 'failure_provenance_present',
                              'backend', 'requested_model', 'usage', 'usage_rows',
                              'local_cli_child_intent', 'artifact', 'execution_record'}
STATUS_KEYS = ('status', 'stop', 'control_gates', 'invalid_products', 'skipped', 'attempt_reservations',
               'local_cli_child_intents', 'known_usage', 'missing_usage', 'unused_slots_expire',
               'scope_closed', 'simulated', 'new_service_authority', 'scores',
               'usage_is_fixture_not_billable', 'no_retry_repair_resume_or_replenishment')


def safe_invalid(rows):
    return [{k: v for k, v in row.items() if k != 'error'} for row in rows]


def safe_record(rec):
    return {k: v for k, v in rec.items() if k not in ('raw_response_sha256', 'error')}


def status(state):
    result = {k: state[k] for k in STATUS_KEYS}
    result['invalid_products'] = safe_invalid(result['invalid_products'])
    return result


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
    if p.digest(data['prepared_files']) != p.digest(p.values()):
        raise ValueError('Exact source,question,reference or implementation differs')
    records = data['records']
    by_slot = {rec['slot']: rec for rec in records}
    if len(by_slot) != len(records) or not 0 <= len(records) <= p.CAP:
        raise ValueError('Repeated or excessive original attempts')
    for rec in records:
        if set(rec) != RECORD_KEYS:
            raise ValueError('Unreviewed portable record field')
        if type(rec['slot']) is not int or not 1 <= rec['slot'] <= p.CAP:
            raise ValueError('Invalid recorded slot')
        if any(type(rec[k]) is not bool for k in ('raw_present', 'failure_provenance_present', 'local_cli_child_intent')):
            raise ValueError('Invalid presence/child flags')
        for key in SLOT_KEYS + ('state', 'usage', 'request_sha256'):
            if p.digest(rec[key]) != p.digest(rec['execution_record'][key]):
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
        if p.digest({k: rec[k] for k in SLOT_KEYS}) != p.digest(slot):
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
            if p.digest(safe_record(rec)) != p.digest(observed['execution_record']):
                raise ValueError('Original execution record differs')
            folder = tmp / 'replay' / ('attempt-%02d' % rec['slot'])
            artifact = p.read(folder / 'artifact.json') if (folder / 'artifact.json').exists() else None
            if p.digest(artifact) != p.digest(observed['artifact']):
                raise ValueError('Original public card differs')
            if artifact is not None and p.sha(folder / 'artifact.json') != rec['artifact_sha256']:
                raise ValueError('Original artifact bytes differ')
        rebuilt['local_cli_child_intents'] = data['status']['local_cli_child_intents']
        if p.digest(status(rebuilt)) != p.digest(data['status']):
            raise ValueError('Control,score,denominator,counter or usage differs')
    if not 0 <= data['status']['local_cli_child_intents'] <= len(records):
        raise ValueError('Original child count differs')
    expected_children = sum(r['local_cli_child_intent'] is True for r in records)
    if expected_children != data['status']['local_cli_child_intents']:
        raise ValueError('Original child ledger differs')
    return analyze(data, rebuilt)


def historical_losses():
    """Derive the seven original losses from sealed responses,not new gold."""
    targets = []
    for archive, slot_id in (('remaining-source-repeat-v1', 49), ('ambiguous-source-repeat-v1', 19)):
        path = ROOT / 'benchmarks' / archive / 'measured.synthetic.json'
        if p.sha(path) != path.with_suffix('.sha256').read_text().strip():
            raise ValueError('Historical loss archive changed')
        old = p.read(path)
        parent = next(r for r in old['records'] if r['slot'] == slot_id)
        pid, method, generation = parent['profile'], parent['method'], parent['generation']
        reads = sorted((r for r in old['records'] if r['kind'] == 'read' and r['profile'] == pid
                        and r['method'] == method and r['generation'] == generation and r['view'] == 'card'),
                       key=lambda r: r['read_repeat'])
        if len(reads) != 2 or any(r['state'] != 'completed' for r in reads):
            raise ValueError('Historical failed-parent readers missing')
        for row in old['reference_rows']:
            if row['person'] != pid or row['gold'] == 'U':
                continue
            answers = [e.parse_answer(r['raw']).get(q) for r in reads for q in row['query_ids']]
            if any(v != row['gold'] for v in answers):
                targets.append({'person': pid, 'case': row['case'], 'gold': row['gold'],
                                'historical_bad_parent_slot': slot_id, 'historical_bad_parent_characters': parent['card']['characters'],
                                'historical_archive': archive, 'historical_archive_sha256': p.sha(path),
                                'historical_four_answers': answers})
    if len(targets) != 7:
        raise ValueError('Original seven-loss target set differs')
    return targets


def analyze(data, rebuilt):
    records, rows = data['records'], p.inputs()['rows']
    decoded = {(r['profile'], r['method'], r['generation'], r['read_repeat']): e.parse_answer(r['raw'])
               for r in records if r['kind'] == 'read' and r['state'] == 'completed'}
    cases, losses = [], []
    for row in rows:
        cell = {key: row[key] for key in ('person', 'case', 'gold', 'derived_known', 'guarantee_withdrawal_sensitive')}
        for method in p.METHODS:
            answers = [[decoded.get((row['person'], method, g, r), {}).get(q)
                        for r in (0, 1) for q in row['query_ids']] for g in (0, 1)]
            values = [v for group in answers for v in group]
            cell[method] = {'correct': all(v == row['gold'] for v in values),
                            'missing': any(v is None for v in values),
                            'answers_by_generation': answers, 'loss_kind': loss_kind(row['gold'], values)}
            if not cell[method]['correct']:
                losses.append({'person': row['person'], 'case': row['case'], 'method': method,
                               'gold': row['gold'], **cell[method]})
        before, after = (cell[m]['correct'] for m in p.METHODS)
        cell['transition'] = 'kept' if before and after else 'new_loss' if before else 'recovered' if after else 'both_fail'
        cases.append(cell)
    historical = []
    for old in historical_losses():
        cell = next(c for c in cases if c['person'] == old['person'] and c['case'] == old['case'])
        if cell['gold'] != old['gold']:
            raise ValueError('Historical/new reference mismatch')
        historical.append({**old, 'transition_in_new_round': cell['transition'],
                           **{method: cell[method] for method in p.METHODS}})
    cards, usage = [], {}
    for record in records:
        stage = record['kind'] + (':' + record['method'] if record['method'] is not None else '')
        counted = usage.setdefault(stage, {'attempts': 0, 'reported_total_tokens': 0, 'missing_usage': 0})
        counted['attempts'] += 1
        counted['missing_usage'] += record['usage'] is None
        if record['usage'] is not None:
            counted['reported_total_tokens'] += record['usage']['total_tokens']
        if record['kind'] == 'extract':
            raw = e.parse_answer(record['raw']) if record['raw_present'] and record['state'] == 'completed' else None
            card = {'person': record['profile'], 'method': record['method'], 'generation': record['generation'],
                    'valid': record['artifact'] is not None, 'characters': record['artifact']['characters'] if record['artifact'] else None,
                    'objects': len(raw['objects']) if raw else None, 'nodes': len(raw['nodes']) if raw else None}
            if raw and 'source_accounting' in raw:
                accounting = raw['source_accounting']
                card['declared_source_kinds'] = {k: sum(v['kind'] == k for v in accounting.values())
                                                 for k in ('direct_choice', 'contextual_choice', 'no_choice')}
                card['derived_node_count'] = len(raw['derived_node_ids'])
            cards.append(card)
    strata = {}
    by_case = {(c['person'], c['case']): c for c in cases}
    for label in ('derived_known', 'guarantee_withdrawal_sensitive', 'personal_known', 'structural_known'):
        selected = [by_case[row['person'], row['case']] for row in rows if row[label]]
        strata[label] = {method: {'planned': len(selected),
                                 'correct': sum(c[method]['correct'] for c in selected),
                                 'missing': sum(c[method]['missing'] for c in selected)}
                          for method in p.METHODS}
    return {'kind': KIND, 'status': rebuilt['status'], 'stop': rebuilt['stop'],
            'actual_attempts': len(records), 'actual_children': data['status']['local_cli_child_intents'],
            'unused_slots_expire': rebuilt['unused_slots_expire'], 'original_scope_closed': True,
            'summary': rebuilt['scores'], 'invalid_products': safe_invalid(rebuilt['invalid_products']),
            'skipped': rebuilt['skipped'], 'known_usage': rebuilt['known_usage'], 'missing_usage': rebuilt['missing_usage'],
            'usage_by_stage': usage, 'cards': cards, 'all_case_transitions': cases,
            'reference_strata': strata,
            'transition_counts': {name: sum(c['transition'] == name for c in cases)
                                  for name in ('kept', 'recovered', 'new_loss', 'both_fail')},
            'historical_seven_loss_targets': historical, 'failed_or_missing_cases': losses,
            'controls_qualified': len(rebuilt['control_gates']) == 2 and all(v['qualified'] for v in rebuilt['control_gates'].values()),
            'new_service_calls_from_replay': 0, 'source_accounting_is_behavioral_endpoint': False,
            'independent_holdout': False, 'real_person_fidelity_verified': False,
            'production_default_changed': False}


def check(path=DEFAULT):
    path = Path(path)
    if p.sha(path) != path.with_suffix('.sha256').read_text().strip():
        raise ValueError('Portable evidence checksum differs')
    return replay(p.read(path))


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
