"""New8fixed-view name-marker controller. No backend, approval issuer or executable CLI."""
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = module('named_target_read_plan', HERE / 'plan.py')
score = module('named_target_read_score', HERE / 'score.py')
from runaway.constraint_extract import parse_answer, check


def write_new(path, value):
    if path.is_symlink():
        raise ValueError('Symlink output refused')
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def usage(prov):
    rows = prov.get('usage')
    if type(rows) is not list or not rows:
        raise ValueError('Unknown usage')
    fields = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens')
    total = Counter()
    for row in rows:
        if type(row) is not dict or any(type(row.get(k)) is not int or row[k] < 0 for k in fields[:2]):
            raise ValueError('Unknown mandatory usage')
        if any(type(row.get(k, 0)) is not int or row.get(k, 0) < 0 for k in fields):
            raise ValueError('Invalid usage')
        if row.get('cached_input_tokens', 0) > row['input_tokens'] or row.get('reasoning_output_tokens', 0) > row['output_tokens']:
            raise ValueError('Usage subset exceeds total')
        total.update({k: row.get(k, 0) for k in fields})
    value = dict(total)
    value['total_tokens'] = value['input_tokens'] + value['output_tokens']
    return value


def run(root, destination, invoke, before, *, simulated):
    root, destination = Path(root), Path(destination)
    plan.verify(root)
    destination.mkdir(parents=False, exist_ok=False)
    data, responses, records, gates = plan.inputs(), {}, [], {}
    none, stop = None, None
    for slot in plan.slots():
        if slot['kind'] == 'read' and not gates.get('e0', {}).get('qualified'):
            stop = 'controls_not_qualified'; break
        try:
            plan.verify(root, reconstruct=False)
            req = plan.request(slot)
            guard = before(slot)
            if not simulated and not guard.get('owned_active'):
                raise PermissionError('Owned temporary guard required')
        except Exception as exc:
            stop = 'pre_call_failure:' + type(exc).__name__; break
        if len(records) >= plan.CAP:
            stop = 'attempt_cap'; break
        folder = destination / ('attempt-%02d' % slot['slot']); folder.mkdir()
        rec = {**slot, 'execution_id': folder.name, 'state': 'invocation_intent', 'request_sha256': plan.digest(req),
               'view_sha256': plan.digest(plan.view(slot)) if slot['kind'] == 'read' else None,
               'usage': None, 'simulated': simulated}
        write_new(folder / 'request.json', req)
        write_new(folder / 'intent.json', {**rec, 'guard': guard}); records.append(rec)
        try:
            raw, prov = invoke(req, folder, slot)
            write_new(folder / 'raw-response.json', {'raw': raw, 'provenance': prov})
            rec['raw_response_sha256'] = plan.sha(folder / 'raw-response.json')
            rec['usage'] = usage(prov)
            if prov.get('model_requested') != plan.MODEL or (not simulated and prov.get('backend') != 'codex'):
                raise ValueError('Requested model/backend differs')
            if type(raw) is not str or len(raw.encode()) > 256000:
                raise ValueError('Raw response type/size differs')
            answer = parse_answer(raw); check(answer, req['schema'])
            plan.choice_reader.decode_response(data['queries']['editing'], answer, answer_format='text', reader_mode='standard')
            write_new(folder / 'answer.json', answer)
            if slot['kind'] == 'none':
                none = answer
            elif slot['kind'] == 'full':
                f, n = score.counts(data['rows'], [answer]), score.counts(data['rows'], [none])
                gate = {'qualified': f['joint']['correct'] == len(data['rows']) and not f['joint']['missing'] and f['personal_known']['correct'] > n['personal_known']['correct'], 'full': f, 'none': n}
                gates['e0'] = gate; write_new(destination / 'control-gate-e0.json', gate)
                if not gate['qualified']: stop = 'full_control_not_qualified:e0'
            else:
                responses[plan.parent(slot)+(slot['read_repeat'],)] = answer
            rec['state'] = 'completed'
        except Exception as exc:
            rec.update(state='failed', error_type=type(exc).__name__, error=str(exc))
            stop = 'transport_wire_decode_usage_or_model_failure'
            extra = getattr(exc, 'provenance', None)
            if extra:
                write_new(folder / 'failure-provenance.json', extra)
                try: rec['usage'] = usage(extra)
                except ValueError: pass
        write_new(folder / 'result.json', rec)
        if stop: break
    totals = Counter()
    for rec in records:
        if rec['usage'] is not None: totals.update(rec['usage'])
    result = {'status': 'stopped' if stop else 'complete', 'stop': stop, 'records': records,
        'invalid_products': [], 'skipped': [], 'control_gates': gates,
        'attempt_reservations': len(records),
        'local_cli_child_intents': sum((destination / r['execution_id'] / 'backend-child-intent.json').exists() for r in records),
        'known_usage': dict(totals), 'missing_usage': sum(r['usage'] is None for r in records),
        'simulated': simulated, 'usage_is_fixture_not_billable': simulated, 'scope_closed': True,
        'unused_slots_expire': plan.CAP-len(records), 'new_service_authority': False,
        'no_retry_repair_resume_or_replenishment': True, 'scores': score.summarize(data['rows'], responses)}
    write_new(destination / 'result.json', result)
    return result
