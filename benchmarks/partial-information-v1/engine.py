"""Finite injected fixed-view controller;no generation,transport or service grant."""
import importlib.util
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('partial_information_plan', HERE / 'plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)
shared = plan.load('partial_information_shared', plan.ROOT / 'benchmarks/single-pass-repeat-v1/engine.py')
usage, write_new, score = shared.usage, shared.write_new, shared.score
from runaway.constraint_extract import check, parse_answer


def summarize(rows, responses):
    def pooled(selected, generations=(0, 1)):
        totals = {view: {k: Counter() for k in score.counts([], [{}])} for view in plan.VIEWS}
        for pid in plan.PROFILES:
            own = [r for r in selected if r['person'] == pid]
            for view in plan.VIEWS:
                answers = [responses.get((pid, g, view, repeat), {}) for g in generations for repeat in (0, 1)]
                for key, count in score.counts(own, answers).items():
                    totals[view][key].update(count)
        return {view: {key: dict(count) for key, count in metrics.items()} for view, metrics in totals.items()}
    cells = []
    for row in rows:
        views = {}
        for view in plan.VIEWS:
            values = [responses.get((row['person'], g, view, repeat), {}).get(q)
                      for g in (0, 1) for repeat in (0, 1) for q in row['query_ids']]
            views[view] = {'correct': all(v == row['gold'] for v in values), 'missing': any(v is None for v in values)}
        cells.append({'person': row['person'], 'case': row['case'], 'primary': row['primary'],
                      'known': row['gold'] != 'U', 'cohort': row['cohort'], **views})
    return {'joint': pooled(rows), 'primary': pooled([r for r in rows if r['primary']]),
            'anchors': pooled([r for r in rows if not r['primary']]),
            'per_parent_generation': {str(g): pooled(rows, (g,)) for g in (0, 1)},
            'cohorts': {name: pooled([r for r in rows if r['cohort'] == name]) for name in sorted({r['cohort'] for r in rows})},
            'transitions': cells, 'planned_all_person_cases_per_view': 64,
            'planned_primary_partial_cases_per_view': 48, 'planned_complete_anchors_per_view': 16,
            'answers_per_joint_case': 8, 'new_extractions': 0, 'fixed_posthoc_parents': True,
            'independent_holdout': False, 'real_person_fidelity_verified': False,
            'new_initial_generation_stability_verified': False, 'production_default_changed': False}


def run(root, destination, invoke, before, *, simulated):
    plan.verify(root)
    destination = Path(destination)
    destination.mkdir(exist_ok=False)
    rows = plan.inputs()['rows']
    records, responses, controls = [], {}, {}
    none, stop = None, None
    for slot in plan.slots():
        if slot['kind'] == 'read' and not (len(controls) == 4 and all(c['qualified'] for c in controls.values())):
            stop = 'controls_not_qualified'
            break
        try:
            plan.verify(root)
            guard = before(slot)
            if not simulated and not guard.get('owned_active'):
                raise PermissionError('Owned temporary guard required')
            req = plan.request(slot)
        except Exception as exc:
            stop = 'pre_call_failure:' + type(exc).__name__
            break
        if len(records) >= plan.CAP:
            stop = 'attempt_cap'
            break
        folder = destination / ('attempt-%02d' % slot['slot'])
        folder.mkdir()
        rec = {**slot, 'request_sha256': plan.digest(req), 'state': 'invocation_intent',
               'usage': None, 'simulated': simulated}
        write_new(folder / 'request.json', req)
        write_new(folder / 'intent.json', {**rec, 'guard': guard})
        records.append(rec)
        try:
            raw, provenance = invoke(req, folder, slot)
            write_new(folder / 'raw-response.json', {'raw': raw, 'provenance': provenance})
            rec['raw_response_sha256'] = plan.sha(folder / 'raw-response.json')
            rec['usage'] = usage(provenance)
            if provenance.get('model_requested') != plan.MODEL or (not simulated and provenance.get('backend') != 'codex'):
                raise ValueError('Backend/model differs')
            if type(raw) is not str or len(raw.encode()) > 256000:
                raise ValueError('Raw response type/size differs')
            answer = parse_answer(raw)
            check(answer, req['schema'])
            plan.choice_reader.decode_response(plan.inputs()['queries']['all'], answer, answer_format='text', reader_mode='standard')
            write_new(folder / 'answer.json', answer)
            if slot['kind'] == 'none':
                none = answer
            elif slot['kind'] == 'full':
                own = [r for r in rows if r['person'] == slot['profile']]
                primary = [r for r in own if r['primary']]
                f, n = score.counts(own, [answer]), score.counts(primary, [none])
                pf = score.counts(primary, [answer])
                controls[slot['profile']] = {'qualified': f['joint']['correct'] == 16 and not f['joint']['missing']
                                            and pf['personal_known']['correct'] > n['personal_known']['correct'],
                                            'full_all': f, 'full_primary': pf, 'none_primary': n}
                write_new(folder / 'control-gate.json', controls[slot['profile']])
                if not controls[slot['profile']]['qualified']:
                    stop = 'full_control_not_qualified'
            else:
                responses[slot['profile'], slot['generation_repeat'], slot['view'], slot['read_repeat']] = answer
            rec['state'] = 'completed'
        except Exception as exc:
            rec.update(state='failed', error_type=type(exc).__name__, error=str(exc))
            stop = 'transport_wire_decode_usage_or_model_failure'
            provenance = getattr(exc, 'provenance', None)
            if provenance:
                write_new(folder / 'failure-provenance.json', provenance)
                try:
                    rec['usage'] = usage(provenance)
                except ValueError:
                    pass
        write_new(folder / 'result.json', rec)
        if stop:
            break
    total = Counter()
    for rec in records:
        if rec['usage'] is not None:
            total.update(rec['usage'])
    state = {'status': 'stopped' if stop else 'complete', 'stop': stop, 'records': records,
             'control_gate': controls, 'attempt_reservations': len(records),
             'local_cli_child_intents': len(list(destination.glob('attempt-*/backend-child-intent.json'))),
             'known_usage': dict(total), 'missing_usage': sum(r['usage'] is None for r in records),
             'unused_slots_expire': plan.CAP - len(records), 'scope_closed': True,
             'simulated': simulated, 'new_service_authority': False, 'scores': summarize(rows, responses),
             'new_extractions': 0, 'old_scopes_reopened': False, 'production_default_changed': False}
    write_new(destination / 'result.json', state)
    return state
