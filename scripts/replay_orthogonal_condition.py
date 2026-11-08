"""Reconstruct actual orthogonal-condition24 evidence from portable archived values, with zero services."""
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LOCATOR = HERE / 'orthogonal-condition-locator.private.json'
ROOT = Path(json.loads(LOCATOR.read_text())['repository_root']) if LOCATOR.exists() else HERE.parent
spec = importlib.util.spec_from_file_location('repeat_evidence_engine', ROOT / 'benchmarks/orthogonal-condition-diagnostic-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
from runaway.constraint_extract import parse_answer
e.parse_answer = parse_answer
KIND = 'actual_orthogonal_condition24'
SOURCE = 'fcd2f71458b430f64afc9e9d617d88ffb33f0618'
INPUT = '78aafe00af4e0a2046e93aa0be28bf8168c22ed2cf7b4f996ec35f91189a0aba'
DEFAULT = ROOT / 'benchmarks/orthogonal-condition-diagnostic-v1/measured.synthetic.json'
FALSE_CLAIMS = ('new_service_authority', 'old_scopes_reopened', 'old_scores_replaced',
                'production_default_changed', 'independent_holdout',
                'population_generation_stability_verified', 'real_person_fidelity_verified',
                'source_reference_semantics_verified', 'cross_provider_verified',
                'token_matched_tail', 'optimal_tail_selection')
PROVENANCE_LIMITS = ('Checksums and archive replay verify content consistency,not independent service '
                     'attestation,model identity or source-reference semantics.')
SLOT_KEYS = ('slot', 'kind', 'profile', 'method', 'generation', 'budget', 'read_repeat', 'key')
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
        if rec.get('artifact') is not None:
            raise ValueError('Fixed-read study cannot create an artifact')
        if set(rec) != RECORD_KEYS:
            raise ValueError('Unreviewed portable record field')
        if type(rec['slot']) is not int or not 1 <= rec['slot'] <= p.CAP:
            raise ValueError('Invalid recorded slot')
        if any(type(rec[k]) is not bool for k in ('raw_present', 'failure_provenance_present', 'local_cli_child_intent')):
            raise ValueError('Invalid presence/child flags')
        for key in SLOT_KEYS + ('state', 'usage', 'request_sha256'):
            if p.digest(rec[key]) != p.digest(rec['execution_record'][key]):
                raise ValueError('Portable record metadata differs')
    if type(data['status']['local_cli_child_intents']) is not int:
        raise ValueError('Child counter must be an integer')
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


def transition(before, after):
    """Keep missing products separate from observed behavioral regressions."""
    if before['missing'] and after['missing']:
        return 'both_missing'
    if before['missing']:
        return 'baseline_missing'
    if after['missing']:
        return 'candidate_missing'
    if before['correct']:
        return 'kept' if after['correct'] else 'new_observed_loss'
    return 'recovered' if after['correct'] else 'both_observed_fail'


def generation_transition(cell, generation):
    states = []
    for method in p.METHODS:
        values = cell[method]['answers_by_generation'][generation]
        states.append({'correct': all(v == cell['gold'] for v in values),
                       'missing': any(v is None for v in values)})
    return transition(*states)


def subset_counts(cells, method):
    result = {kind: dict(planned=0, correct=0, missing=0) for kind in ('joint', 'known', 'unknown')}
    for cell in cells:
        for kind in ('joint', 'unknown' if cell['gold'] == 'U' else 'known'):
            result[kind]['planned'] += 1
            result[kind]['correct'] += int(cell[method]['correct'])
            result[kind]['missing'] += int(cell[method]['missing'])
    return result


TRIAGE = {
    'base_current': ('ordinary choice or scope binding',),
    'exception_current': ('local exception or prerequisite',),
    'revised_current': ('latest local revision and inherited conditions',),
    'base_old_alias': ('old/current project binding',),
    'revised_old_alias': ('project binding,latest revision and inherited conditions',),
    'scope_not_established': ('necessary prerequisite or unsupported extrapolation',),
    'linked_name': ('intermediate chain or qualified old-name binding and choice',),
    'denied_name': ('denied identity retention,lookalike overmerge or role contamination',),
    'ambiguity': ('divergent possible projects or branches and false certainty',),
    'same_choice_contexts': ('all possible paired contexts agree;over-abstention or wrong rule binding',),
    'execution_fact': ('preference/permission/actual-fact separation or role contamination',),
}


def source_ids_for(row):
    inputs=p.old.inputs()
    if row['cohort']!='crossed_time_material':
        return next(x['source_ids']for x in inputs['author_evidence']if x['person']==row['person']and x['case']==row['case'])
    pi=p.old.corpus.PROFILES.index(row['person']);index=int(row['case'].split('_',1)[0])
    owner=next(i for i in range(4)if p.old.corpus.old_current(pi,i)==index)
    return [s['id']for s in inputs['sources'][row['person']]['sources']if s['episode_id']=='journal%d'%owner and s['role']=='user']


def analyze(data, rebuilt):
    records=data['records'];inputs=p.inputs()
    decoded={(r['profile'],r['method'],r['generation'],r['read_repeat']):e.parse_answer(r['raw'])
             for r in records if r['kind']=='read'and r['state']=='completed'}
    def cell_for(row,methods,generations):
        cell={k:row[k]for k in('person','case','gold','cohort')}
        cell['source_ids_for_review']=source_ids_for(row)
        for method in methods:
            answers=[[decoded.get((row['person'],method,g,repeat),{}).get(q)
                      for repeat in(0,1)for q in row['query_ids']]for g in generations]
            values=[v for a in answers for v in a]
            cell[method]=dict(correct=all(v==row['gold']for v in values),missing=any(v is None for v in values),
                              answers_by_generation=answers,loss_kind=loss_kind(row['gold'],values))
        return cell
    cells=[];losses=[];diagnostic=[];repeats=[]
    labels=('kept','recovered','new_observed_loss','both_observed_fail','baseline_missing','candidate_missing','both_missing')
    for row in inputs['rows']:
        cell=cell_for(row,p.METHODS,(0,1));cell['transition']=transition(*(cell[m]for m in p.METHODS))
        cell['transitions_by_generation']={str(g):generation_transition(cell,g)for g in(0,1)}
        for m in p.METHODS:
            if not cell[m]['correct']:losses.append(dict(person=cell['person'],case=cell['case'],cohort=cell['cohort'],gold=cell['gold'],method=m,**cell[m]))
            for g,values in enumerate(cell[m]['answers_by_generation']):
                if values[:2]!=values[2:]:repeats.append(dict(person=row['person'],case=row['case'],method=m,generation=g,answers_by_read=[values[:2],values[2:]]))
        cells.append(cell)
        if row['person']=='otter':
            d=cell_for(row,p.DIAGNOSTICS,(0,));d['transition']=transition(*(d[m]for m in p.DIAGNOSTICS));diagnostic.append(d)
    controls=[]
    for rec in records:
        if rec['kind']!='full'or rec['state']!='completed':continue
        a=e.parse_answer(rec['raw'])
        for row in inputs['rows']:
            if row['person']!=rec['profile']:continue
            values=[a.get(q)for q in row['query_ids']]
            if any(v!=row['gold']for v in values):controls.append(dict(person=row['person'],case=row['case'],cohort=row['cohort'],gold=row['gold'],answers=values))
    stages={}
    for record in records:
        key=record['kind']+(':'+record['method']if record['method']else'')
        v=stages.setdefault(key,dict(attempts=0,reported_total_tokens=0,missing_usage=0))
        v['attempts']+=1;v['missing_usage']+=record['usage']is None
        if record['usage']is not None:v['reported_total_tokens']+=record['usage']['total_tokens']
    return dict(kind=KIND,status=rebuilt['status'],stop=rebuilt['stop'],actual_attempts=len(records),
        actual_children=data['status']['local_cli_child_intents'],unused_slots_expire=rebuilt['unused_slots_expire'],
        original_scope_closed=True,summary=rebuilt['scores'],known_usage=rebuilt['known_usage'],missing_usage=rebuilt['missing_usage'],
        usage_by_stage=stages,all_case_transitions=cells,paired_transitions={label:sum(c['transition']==label for c in cells)for label in labels},
        failed_or_missing_cases=losses,within_parent_reader_differences=repeats,
        paired_transitions_by_generation={str(g):{label:sum(c['transitions_by_generation'][str(g)]==label for c in cells)for label in labels}for g in(0,1)},
        constructed_diagnostic_cases=diagnostic,constructed_diagnostic_transitions={label:sum(c['transition']==label for c in diagnostic)for label in labels},
        full_control_failed_or_missing_cases=controls,
        controls_qualified=len(rebuilt['control_gates'])==2 and all(g['qualified']for g in rebuilt['control_gates'].values()),
        symbolic_diagnostic_is_model_measurement=False,new_service_calls_from_replay=0,
        independent_holdout=False,real_person_fidelity_verified=False,production_default_changed=False)


def check(path=DEFAULT):
    path = Path(path)
    if p.sha(path) != path.with_suffix('.sha256').read_text().strip():
        raise ValueError('Portable evidence checksum differs')
    return replay(p.read(path))


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
