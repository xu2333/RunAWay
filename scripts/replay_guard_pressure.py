"""Reconstruct actual heterogeneous guard pressure16 evidence from portable archived values, with zero services."""
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LOCATOR = HERE / 'guard-pressure-locator.private.json'
ROOT = Path(json.loads(LOCATOR.read_text())['repository_root']) if LOCATOR.exists() else HERE.parent
spec = importlib.util.spec_from_file_location('repeat_evidence_engine', ROOT / 'benchmarks/heterogeneous-guard-pressure-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
from runaway.constraint_extract import parse_answer
e.parse_answer = parse_answer
KIND = 'actual_guard_pressure16'
SOURCE = 'cefee72e75e979b66a302756c5303ffd22646253'
INPUT = '7f0ba33fe5b129a2f12b34eafcaee351f8b7fb581cf8e8f714a5746d7ac582da'
DEFAULT = ROOT / 'benchmarks/heterogeneous-guard-pressure-v1/measured.synthetic.json'
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


def subset_counts(cells, method):
    result = {kind: dict(planned=0, correct=0, missing=0) for kind in ('joint', 'known', 'unknown')}
    for cell in cells:
        for kind in ('joint', 'unknown' if cell['gold'] == 'U' else 'known'):
            result[kind]['planned'] += 1
            result[kind]['correct'] += int(cell[method]['correct'])
            result[kind]['missing'] += int(cell[method]['missing'])
    return result


TRIAGE = {
    'new_boundary': 'inclusive current threshold and full action label',
    'old_boundary': 'condition-only threshold amendment rather than stale cutoff',
    'below_boundary': 'second ordinary choice and current numeric partition',
    'narrow': 'local priority exception and retained current guard',
    'guard_false_narrow': 'narrow release versus necessary guard',
    'guard_missing_narrow': 'narrow release versus unknown prerequisite',
    'guard_false_ordinary': 'local exception must not broaden ordinary branches',
    'gate_missing': 'necessary premise not assumed true',
    'old_alias': 'alias identity and current amended policy',
    'copy': 'distinct copy must not inherit original choice',
    'status': 'actual implementation versus preference or tool-template claim',
    'missing_amount_same': 'exhaustive completions agree;over-abstention',
    'missing_reviewer': 'different compatible choices must remain unknown',
    'guard_missing_ordinary': 'missing ordinary prerequisite',
    'old_guard_only': 'old guard removed and replacement guard still necessary',
}


def layout_scheme(prompt):
    unpacked = p.candidate.dense.decode(prompt)
    prefix = p.candidate.dense.prefix(p.candidate.dense.metadata(unpacked))
    return 'common_then_dense' if unpacked[len(prefix):].startswith(p.candidate.factor.LABEL) else 'dense'


def budget_transition(low, high):
    if low['missing'] and high['missing']: return 'both_missing'
    if low['missing']: return 'only768missing'
    if high['missing']: return 'only1536missing'
    if low['correct'] and high['correct']: return 'both_retained'
    if high['correct']: return 'only1536retained'
    if low['correct']: return 'only768retained'
    return 'both_observed_fail'


def literal_action_diagnostic(value):
    """Navigation only: short labels can identify options without full wording."""
    full_names = {a for spec in p.corpus.SPECS for a in spec[9:11]}
    actions = {row['choose'] for group in value['groups'] for row in group['rules']}
    return dict(complete_source_action_names=sorted(full_names), actual_public_action_fields=sorted(actions),
        full_names_not_exact_action_fields=sorted(full_names - actions),
        exact_literal_difference_is_semantic_loss=False,
        option_matching_does_not_prove_unprompted_full_action_reconstruction=True)


def analyze(data, rebuilt):
    records = data['records']
    decoded = {(r['profile'], r['method'], r['budget'], r['read_repeat']): e.parse_answer(r['raw'])
        for r in records if r['kind'] == 'read' and r['state'] == 'completed'}
    cells, losses, differences = [], [], []
    for original in rebuilt['scores']['all_case_transitions']:
        cell = json.loads(json.dumps(original))
        own = next(r for r in p.inputs()['rows'] if (r['person'], r['case']) == (cell['person'], cell['case']))
        navigation = next(x for x in data['prepared_files']['author-evidence.private.json']
            if (x['person'], x['case']) == (cell['person'], cell['case']))
        cell['source_ids_for_review'] = navigation['complete_episode_source_ids']
        for method in p.METHODS:
            budget = p.METHOD_BUDGET[method]
            values = [decoded.get((cell['person'], method, budget, repeat), {}).get(q)
                for repeat in (0, 1) for q in own['query_ids']]
            assert values == cell[method]['answers']
            cell[method]['budget'] = budget
            cell[method]['loss_kind'] = loss_kind(cell['gold'], values)
            if values[:2] != values[2:]:
                differences.append(dict(person=cell['person'], case=cell['case'], method=method,
                    budget=budget, answers_by_read=[values[:2], values[2:]]))
            if not cell[method]['correct']:
                losses.append(dict(person=cell['person'], case=cell['case'], method=method,
                    gold=cell['gold'], cohort=cell['cohort'], **cell[method],
                    source_ids_for_review=cell['source_ids_for_review'],
                    source_linked_hypothesis_not_proven_cause=TRIAGE[cell['cohort']]))
        cells.append(cell)
        assert cell['transition'] == budget_transition(cell[p.METHODS[0]], cell[p.METHODS[1]])
    cards, stages = [], {}
    for record in records:
        stage = record['kind'] + (':' + record['method'] if record['method'] else '')
        totals = stages.setdefault(stage, dict(attempts=0, reported_total_tokens=0, missing_usage=0))
        totals['attempts'] += 1; totals['missing_usage'] += record['usage'] is None
        if record['usage'] is not None: totals['reported_total_tokens'] += record['usage']['total_tokens']
        if record['kind'] != 'extract': continue
        prompt = record['artifact']['prompt'] if record['artifact'] else None
        raw = e.parse_answer(record['raw']) if record['raw_present'] and record['state'] == 'completed' else None
        card = dict(person=record['profile'], method=record['method'], budget=record['budget'],
                    valid=prompt is not None, characters=len(prompt) if prompt else None,
                    nodes=len(raw['nodes']) if raw else None, objects=len(raw['objects']) if raw else None,
                    product_diagnostic=None)
        if raw is not None:
            try:
                p.bind(p.slots()[record['slot'] - 1], raw)
            except (ValueError, KeyError, TypeError) as exc:
                card['product_diagnostic'] = dict(error_type=type(exc).__name__,
                    error=str(exc), budget_rejection=str(exc) == 'Neither complete reversible layout fits whole budget; no truncation')
        if prompt is not None:
            value = p.candidate.dense.parse(p.candidate.restore(prompt))
            card.update(active_public_rows=sum(len(g['rules']) for g in value['groups']),
                        public_rule_fields=value, layout_not_fidelity=layout_scheme(prompt),
                        action_literal_navigation_not_semantic_verdict=literal_action_diagnostic(value))
        cards.append(card)
    controls = []
    for person in p.PROFILES:
        rec = next((r for r in records if r['kind'] == 'full' and r['profile'] == person), None)
        answer = e.parse_answer(rec['raw']) if rec and rec['state'] == 'completed' else {}
        for row in p.inputs()['rows']:
            if row['person'] != person: continue
            values = [answer.get(q) for q in row['query_ids']]
            if any(v != row['gold'] for v in values):
                controls.append(dict(person=person, case=row['case'], cohort=row['cohort'], gold=row['gold'],
                    answers=values, missing=any(v is None for v in values), record_state=rec['state'] if rec else 'not_attempted'))
    return dict(kind=KIND, status=rebuilt['status'], stop=rebuilt['stop'],
        actual_attempts=len(records), actual_children=data['status']['local_cli_child_intents'],
        unused_slots_expire=rebuilt['unused_slots_expire'], original_scope_closed=True,
        summary=rebuilt['scores'], invalid_products=safe_invalid(rebuilt['invalid_products']), skipped=rebuilt['skipped'],
        known_usage=rebuilt['known_usage'], missing_usage=rebuilt['missing_usage'], cards=cards, usage_by_stage=stages,
        all_case_transitions=cells, paired_budget_transitions=rebuilt['scores']['paired_transitions'],
        failed_or_missing_cases=losses, within_parent_reader_differences=differences,
        full_control_failed_or_missing_cases=controls,
        controls_qualified=len(rebuilt['control_gates']) == 2 and all(v['qualified'] for v in rebuilt['control_gates'].values()),
        literal_presence_is_semantic_coverage=False, new_service_calls_from_replay=0,
        generation_stability_verified=False, independent_holdout=False,
        real_person_fidelity_verified=False, production_default_changed=False)


def check(path=DEFAULT):
    path = Path(path)
    if p.sha(path) != path.with_suffix('.sha256').read_text().strip():
        raise ValueError('Portable evidence checksum differs')
    return replay(p.read(path))


TEMPLATE_GUIDE = ('列：范围|常规另须|界(带单位)|例外|甲|乙。范围必需；余量≥界且常规另须选甲，'
    '余量<界且常规另须选乙；余量<界且例外成立优先选甲，不需常规另须。常规另须空即无额外条件。'
    '缺前提/未覆盖未知，缺细节仅所有可能同选才选。@项，?未知；\\转义符号或n/r/t。\n')


def _template_render(value):
    """Literal substitution for one declared row shape;no semantic inference."""
    d = p.candidate.dense
    if not value['groups']: raise ValueError('Template requires a group')
    question = value['groups'][0]['rules'][0]['question']
    text = d.base.grouped.HEADER + json.dumps(value['name'], ensure_ascii=False) + '｜' + json.dumps(value['tagline'], ensure_ascii=False) + '\n' + TEMPLATE_GUIDE
    text += '目标=' + d.escape(question) + '\n'
    for group in value['groups']:
        if len(group['rules']) != 3: raise ValueError('Template requires exactly three ordered rules per group')
        high, low, narrow = group['rules']
        if any(row['question'] != question for row in group['rules']): raise ValueError('Template questions differ')
        if [row['priority'] for row in group['rules']] != [0, 0, 1]: raise ValueError('Template priorities differ')
        if not high['requires'] or not high['requires'][-1].startswith('余量≥'): raise ValueError('Foreign threshold syntax')
        threshold, extra = high['requires'][-1][3:], high['requires'][:-1]
        if not threshold or len(extra) > 1 or low['requires'] != extra + ['余量<' + threshold]: raise ValueError('Template ordinary conditions differ')
        if len(narrow['requires']) != 2 or narrow['requires'][0] != '余量<' + threshold or narrow['choose'] != high['choose']:
            raise ValueError('Template narrow conditions or action differ')
        fields = (group['scope'], extra[0] if extra else '', threshold, narrow['requires'][1], high['choose'], low['choose'])
        text += '@' + '|'.join(d.escape(s) for s in fields) + '\n'
    return text + ''.join('?' + d.escape(t) + '\n' for t in value['unknowns'])


def template_restore(text):
    """Program round trip only;LLM comprehension of this new guide is untested."""
    d = p.candidate.dense; header = d.base.grouped.HEADER
    if not isinstance(text, str) or not text.startswith(header) or not text.endswith('\n'): raise ValueError('Incomplete template')
    line = text[len(header):].split('\n', 1)[0]; decoder = json.JSONDecoder()
    name, end = decoder.raw_decode(line)
    if line[end:end + 1] != '｜': raise ValueError('Missing template tagline')
    tagline, tail = decoder.raw_decode(line[end + 1:])
    if end + 1 + tail != len(line): raise ValueError('Trailing metadata')
    prefix = header + json.dumps(name, ensure_ascii=False) + '｜' + json.dumps(tagline, ensure_ascii=False) + '\n' + TEMPLATE_GUIDE
    if not text.startswith(prefix): raise ValueError('Counted template guide differs')
    lines = text[len(prefix):].split('\n')[:-1]
    if not lines or not lines[0].startswith('目标='): raise ValueError('Missing template decision target')
    question = d.unescape(lines[0][3:])
    value = dict(name=name, tagline=tagline, groups=[], unknowns=[])
    unknown = False
    for line in lines[1:]:
        if line.startswith('?'):
            unknown = True; value['unknowns'].append(d.unescape(line[1:])); continue
        if unknown or not line.startswith('@'): raise ValueError('Unexpected template line')
        fields = [d.unescape(s) for s in d.split(line[1:], '|')]
        if len(fields) != 6 or any(not s for i, s in enumerate(fields) if i != 1): raise ValueError('Invalid template fields')
        scope, extra, threshold, reviewer, a, b = fields
        base = [extra] if extra else []
        value['groups'].append(dict(scope=scope, rules=[
            dict(question=question, requires=base + ['余量≥' + threshold], choose=a, priority=0),
            dict(question=question, requires=base + ['余量<' + threshold], choose=b, priority=0),
            dict(question=question, requires=['余量<' + threshold, reviewer], choose=a, priority=1)]))
    value = d.parse(d._render(value))
    if _template_render(value) != text: raise ValueError('Noncanonical template syntax')
    return value


def template_render(value, budget=768):
    p.candidate.base.b.grouped.budget_check(budget)
    d = p.candidate.dense
    if p.digest(d.parse(d._render(value))) != p.digest(value): raise ValueError('Invalid original projection')
    text = _template_render(value)
    if p.digest(template_restore(text)) != p.digest(value): raise ValueError('Template changed an ordered field')
    if len(text) > budget: raise ValueError('Complete template exceeds budget;no truncation')
    return dict(prompt=text, characters=len(text), budget=budget, ordered_fields_roundtrip_exact=True,
                model_reader_fidelity_verified=False, authorized16uses_this_layout=False)


def template_capacity_probe():
    rows = []
    for person in p.PROFILES:
        files = p.candidate.base.bind(p.corpus.graph(person), p.inputs()['sources'][person], 16000)
        value = p.candidate.dense.parse(p.candidate.restore(files['prompt.md']))
        rendered = template_render(value)
        rows.append(dict(person=person, original_projection_characters=len(files['prompt.md']), **rendered))
    return dict(new_model_calls=0, new_service_authority=False, author_fixture_only=True,
        preserves_declared_public_fields_not_proven_source_completeness=True,
        not_model_extraction_or_reader_fidelity=True, rows=rows)


def template_slot_probe(data, slot, budget=768):
    replay(data)  # Verify original observations;never invent or repair a graph.
    if type(slot) is not int: raise ValueError('Integer extraction slot required')
    record = next((r for r in data['records'] if r['slot'] == slot), None)
    if not record or record['kind'] != 'extract' or record['state'] != 'completed':
        raise ValueError('A completed original extraction is required')
    answer = e.parse_answer(record['raw'])
    files = p.candidate.base.bind(answer, data['prepared_files']['sources.json'][record['profile']], 16000)
    value = p.candidate.dense.parse(p.candidate.restore(files['prompt.md']))
    rendered = template_render(value, budget)
    return dict(original_slot=slot, profile=record['profile'], diagnostic_flat_characters=len(files['prompt.md']),
        **rendered, new_model_calls=0, reader_tested=False, posthoc_development_layout=True,
        original_observation_replaced=False, preserves_declared_fields_not_proven_source_completeness=True)


if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    action = cli.add_mutually_exclusive_group()
    action.add_argument('--template-probe', action='store_true')
    action.add_argument('--template-slot', type=int)
    args = cli.parse_args()
    result = template_capacity_probe() if args.template_probe else template_slot_probe(p.read(DEFAULT), args.template_slot) if args.template_slot is not None else check()
    print(json.dumps(result, ensure_ascii=False, indent=2))


