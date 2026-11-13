"""Reconstruct actual domain and condition-revision14 evidence from portable archived values, with zero services."""
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LOCATOR = HERE / 'domain-revision-locator.private.json'
ROOT = Path(json.loads(LOCATOR.read_text())['repository_root']) if LOCATOR.exists() else HERE.parent
spec = importlib.util.spec_from_file_location('repeat_evidence_engine', ROOT / 'benchmarks/domain-revision-probe-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
from runaway.constraint_extract import parse_answer
e.parse_answer = parse_answer
KIND = 'actual_domain_revision14'
SOURCE = 'fee9768ae871b813ac88aef09ca4cc92c008b89f'
INPUT = '4677ada9bb329e01f4489c7e0781c2ccb6ae990ea48e2df690950397066b4d2b'
DEFAULT = ROOT / 'benchmarks/domain-revision-probe-v1/measured.synthetic.json'
FALSE_CLAIMS = ('new_service_authority', 'old_scopes_reopened', 'old_scores_replaced',
                'production_default_changed', 'independent_holdout',
                'population_generation_stability_verified', 'real_person_fidelity_verified',
                'source_reference_semantics_verified', 'cross_provider_verified',
                'token_matched_tail', 'optimal_tail_selection', 'generation_stability_verified')
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
    for key in ('attempt_reservations','local_cli_child_intents','unused_slots_expire'):
        if type(data['status'][key]) is not int:
            raise ValueError('Integer attempt/child counters required')
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
            # Archive-only injected core: no human grants are published or invented.
            # The native audit separately verified the actual outer authorization gate.
            rebuilt = e.base.original_run(tmp / 'inputs', tmp / 'replay', archived, before,
                                          plan=p, score=e.score, simulated=False)
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


def transition(before,after):
    if before['missing']or after['missing']:
        return 'both_missing'if before['missing']and after['missing']else'baseline_missing'if before['missing']else'candidate_missing'
    if before['correct']:return 'kept'if after['correct']else'new_observed_loss'
    return 'recovered'if after['correct']else'both_observed_fail'


def parent_diagnostics(data):
    from collections import Counter
    result=[]
    for rec in data['records']:
        if rec['kind']!='extract':continue
        row=dict(slot=rec['slot'],method=rec['method'],generation=rec['generation'],original_product_valid=rec['artifact']is not None,
            original_characters=rec['artifact']['characters']if rec['artifact']else None,semantic_edit_correctness_verified=False)
        if rec['raw_present']and rec['state']=='completed':
            try:
                answer=e.parse_answer(rec['raw']);nodes=answer['nodes']
                row.update(raw_node_count=len(nodes),node_kinds=dict(Counter(x['kind']for x in nodes)))
                files=p.encoder(rec['method']).bind(answer,p.inputs()['sources']['rivet'],16000)
                value=p.old.candidate.dense.parse(p.old.candidate.restore(files['prompt.md']))
                row.update(private_diagnostic_ceiling=16000,diagnostic_characters=len(files['prompt.md']),
                    diagnostic_active_rows=sum(len(g['rules'])for g in value['groups']),
                    literal_integer_domain_in_prompt='整数'in files['prompt.md'],
                    private_diagnostic_not_reader_memory=True)
                if rec['method']=='condition_revision':
                    history=files['condition-revision.private.json']
                    edits=[dict(node=n['id'],parent=n['parent_id'],before=x['parent_condition'],after=x['replacement']['text']if x['replacement']else None)for n in history['resolved']['nodes']if n['kind']=='condition_revision'for x in n['edits']]
                    row.update(retired_node_count=len(history['retired_node_ids']),active_node_count=len(history['active_node_ids']),revisions=history['revisions'],literal_condition_edits=edits,
                        removed_predicates=sum(x['after']is None for x in edits),replaced_predicates=sum(x['after']is not None for x in edits))
            except(ValueError,KeyError,TypeError)as exc:
                row['diagnostic_failure']=dict(error_type=type(exc).__name__,detail=str(exc))
        if rec['artifact']is not None:
            try:
                layout=domain_layout_probe(data,rec['slot'])
                row['domain_layout_diagnostic']={k:v for k,v in layout.items()if k!='prompt'}
                row['domain_layout_diagnostic']['fits768']=True
            except(ValueError,KeyError,TypeError)as exc:
                row['domain_layout_diagnostic']=dict(fits768=False,error_type=type(exc).__name__,detail=str(exc),model_reader_fidelity_verified=False,new_model_calls=0)
        result.append(row)
    return result


def domain_layout_probe(data,slot):
    rec=next((x for x in data['records']if x['slot']==slot and x['kind']=='extract'and x['artifact']),None)
    if rec is None:raise ValueError('Original valid extraction card required')
    spec=importlib.util.spec_from_file_location('domain_readonly_layout_codec',ROOT/'benchmarks/domain-template-v2/codec.py')
    codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    value=p.old.candidate.dense.parse(p.old.candidate.restore(rec['artifact']['prompt']))
    result=codec.render(value)
    return dict(original_slot=slot,original_characters=rec['artifact']['characters'],**result,
        original_observation_replaced=False,posthoc_fixed_graph_diagnostic=True,
        source_completeness_not_established_by_roundtrip=True)


def analyze(data,state):
    from collections import Counter
    cells=[]
    for original in state['scores']['all_case_transitions']:
        c=dict(original)
        for m in p.METHODS:c[m]=dict(c[m],loss_kind=loss_kind(c['gold'],c[m]['answers']))
        c['observed_transition']=transition(c['current'],c['condition_revision']);cells.append(c)
    groups={}
    for cohort in sorted({c['cohort']for c in cells}):
        selected=[c for c in cells if c['cohort']==cohort]
        groups[cohort]=dict(planned=len(selected),transitions=dict(Counter(c['observed_transition']for c in selected)),
            methods={m:dict(correct=sum(c[m]['correct']for c in selected),missing=sum(c[m]['missing']for c in selected),losses=dict(Counter(c[m]['loss_kind']for c in selected)))for m in p.METHODS})
    def segment(selected):
        return dict(planned=len(selected),methods={m:dict(correct=sum(c[m]['correct']for c in selected),missing=sum(c[m]['missing']for c in selected))for m in p.METHODS},
            transitions=dict(Counter(c['observed_transition']for c in selected)))
    return dict(status=state['status'],stop=state['stop'],actual_local_attempts=len(data['records']),
        local_cli_children=state['local_cli_child_intents'],unused_slots_expire=state['unused_slots_expire'],
        known_usage=state['known_usage'],missing_usage=state['missing_usage'],control_gates=state['control_gates'],
        methods=state['scores']['methods'],fixed_cases_per_method=94,known=36,unknown=58,answers_per_case=8,
        old82anchors=segment([c for c in cells if c['family']!='declared_numeric_domain']),
        new12domaincases=segment([c for c in cells if c['family']=='declared_numeric_domain']),
        observed_transitions=dict(Counter(c['observed_transition']for c in cells)),by_cohort=groups,
        all_case_transitions=cells,parent_diagnostics=parent_diagnostics(data),
        new_service_calls_from_replay=0,source_only_generations_per_method=2,
        population_generation_stability_verified=False,independent_semantic_gold=False,
        new_source_only768_generation_tested=False,independent_people=1,production_default_changed=False,
        provenance_limits=PROVENANCE_LIMITS)


def check(path=DEFAULT):
    path=Path(path)
    if path.is_symlink()or path.with_suffix('.sha256').is_symlink()or p.sha(path)!=path.with_suffix('.sha256').read_text().strip():
        raise ValueError('Portable archive checksum differs')
    return replay(p.read(path))


if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('archive',nargs='?',type=Path,default=DEFAULT)
    report=check(a.parse_args().archive)
    print(json.dumps({k:v for k,v in report.items()if k not in('all_case_transitions','by_cohort','parent_diagnostics')},ensure_ascii=False,indent=2))
