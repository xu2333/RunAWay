"""Finite injected controller; no CLI transport, credential access or service grant."""
import importlib.util
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('single_repeat_plan', HERE / 'plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)
shared = plan.seed.load('single_repeat_shared_io', plan.ROOT / 'benchmarks/source-id-enum-repeat-v1/engine.py')
usage, write_new, score = shared.usage, shared.write_new, shared.score
from runaway.constraint_extract import check, parse_answer


def summarize(rows, responses):
    def pooled(selected, generations):
        totals = {view: {k: Counter() for k in score.counts([], [{}])} for view in plan.VIEWS}
        for pid in plan.PROFILES:
            own = [r for r in selected if r['person'] == pid]
            for view in plan.VIEWS:
                answers = [responses.get((pid, g, view, r), {}) for g in generations for r in (0, 1)]
                for key, count in score.counts(own, answers).items():
                    totals[view][key].update(count)
        return {view: {key: dict(count) for key, count in metrics.items()}
                for view, metrics in totals.items()}

    cells = []
    for row in rows:
        endpoints = {}
        for view in plan.VIEWS:
            values = [responses.get((row['person'], g, view, r), {}).get(q)
                      for g in (0, 1) for r in (0, 1) for q in row['query_ids']]
            endpoints[view] = {'correct': all(v == row['gold'] for v in values),
                               'missing': any(v is None for v in values)}
        cells.append({'person': row['person'], 'case': row['case'],
                      'known': row['gold'] != 'U', 'derived_known': row['derived_known'],
                      'cohort': row['cohort'], **endpoints})
    slices = {
        'known': lambda r: r['gold'] != 'U', 'unknown': lambda r: r['gold'] == 'U',
        'derived_known': lambda r: r['derived_known'],
        'withdrawal_unseen': lambda r: r['cohort'] == 'withdrawal_unseen',
        'execution': lambda r: r['stratum'] == 'execution'}
    return {'joint': pooled(rows, (0, 1)),
            'per_generation': {str(g): pooled(rows, (g,)) for g in (0, 1)},
            'slices': {name: pooled([r for r in rows if predicate(r)], (0, 1))
                       for name, predicate in slices.items()}, 'transitions': cells,
            'planned_unique_person_cases_per_view': 64, 'fictional_people': 4,
            'joint_answers_per_case': 8, 'independent_holdout': False,
            'population_generation_stability_verified': False,
            'production_default_changed': False}


def run(root, destination, invoke, before, *, simulated):
    plan.verify(root)
    destination = Path(destination)
    # Claiming execution belongs in before(), after successful directory creation.
    destination.mkdir(exist_ok=False)
    data = plan.inputs()
    graphs, responses, controls = {}, {}, {}
    records, invalid, skipped = [], [], []
    none, stop = None, None
    for slot in plan.slots():
        pid, kind = slot['profile'], slot['kind']
        key = (pid, slot['generation_repeat'])
        qualified = len(controls) == 4 and all(x['qualified'] for x in controls.values())
        if kind in ('extract', 'read') and not qualified:
            stop = 'controls_not_qualified'
            break
        if kind == 'read' and key not in graphs:
            skipped.append({**slot, 'reason': 'own_generation_product_invalid'})
            continue
        try:
            plan.verify(root)
            guard = before(slot)
            if not simulated and not guard.get('owned_active'):
                raise PermissionError('Owned temporary guard required')
            req = plan.request(slot, graphs)
            if req is None:
                raise ValueError('Missing planned material')
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
            if provenance.get('model_requested') != plan.MODEL or (
                    not simulated and provenance.get('backend') != 'codex'):
                raise ValueError('Backend/model differs')
            if type(raw) is not str or len(raw.encode()) > 256000:
                raise ValueError('Raw response type/size differs')
            answer = parse_answer(raw)
            check(answer, req['schema'])
            write_new(folder / 'answer.json', answer)
            if kind == 'extract':
                try:
                    prompt = plan.bind(pid, answer)['prompt.md']
                    if not 0 < len(prompt) <= plan.BUDGET:
                        raise ValueError('Whole-public budget differs')
                except (ValueError, KeyError, TypeError) as exc:
                    rec['product_invalid'] = True
                    invalid.append({**slot, 'error_type': type(exc).__name__, 'error': str(exc)})
                else:
                    artifact = {'profile': pid, 'generation_repeat': slot['generation_repeat'],
                                'prompt': prompt, 'characters': len(prompt),
                                'answer_sha256': plan.digest(answer),
                                'source_sha256': plan.digest(data['sources'][pid])}
                    write_new(folder / 'artifact.json', artifact)
                    rec['artifact_sha256'] = plan.sha(folder / 'artifact.json')
                    graphs[key] = answer
            else:
                plan.choice_reader.decode_response(data['queries']['all'], answer,
                                                   answer_format='text', reader_mode='standard')
                if kind == 'none':
                    none = answer
                elif kind == 'full':
                    own = [r for r in data['rows'] if r['person'] == pid]
                    f, n = score.counts(own, [answer]), score.counts(own, [none])
                    controls[pid] = {'qualified': f['joint']['correct'] == 16 and
                                     not f['joint']['missing'] and
                                     f['personal_known']['correct'] > n['personal_known']['correct'],
                                     'full': f, 'none': n}
                    write_new(folder / 'control-gate.json', controls[pid])
                    if not controls[pid]['qualified']:
                        stop = 'full_control_not_qualified'
                else:
                    responses[pid, slot['generation_repeat'], slot['view'], slot['read_repeat']] = answer
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
    state = {'status': 'stopped' if stop else 'complete', 'stop': stop,
             'records': records, 'control_gate': controls, 'invalid_products': invalid,
             'skipped': skipped, 'attempt_reservations': len(records),
             'local_cli_child_intents': len(list(destination.glob('attempt-*/backend-child-intent.json'))),
             'known_usage': dict(total), 'missing_usage': sum(r['usage'] is None for r in records),
             'unused_slots_expire': plan.CAP - len(records), 'scope_closed': True,
             'simulated': simulated, 'new_service_authority': False,
             'scores': summarize(data['rows'], responses), 'old_scopes_reopened': False,
             'production_default_changed': False}
    write_new(destination / 'result.json', state)
    return state
