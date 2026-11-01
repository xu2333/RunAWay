"""Injected finite method-study runner for new scopes; no service backend."""
from collections import Counter
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('finite_method_io', ROOT / 'benchmarks/owned-conditions-v1/engine.py')
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
write_new, usage = io.write_new, io.usage
from runaway.constraint_extract import parse_answer, check

def run(root, destination, invoke, before, *, plan, score, simulated):
    """Actual use requires a separate host's exact new human grant verification.

    invoke and before are mandatory injections; this module cannot contact a
    service by itself. Offline fixtures explicitly mark every record simulated.
    """
    root, destination = Path(root), Path(destination)
    plan.verify(root)
    destination.mkdir(parents=False, exist_ok=False)
    data = plan.inputs()
    parents, cards, responses, gates, none = {}, {}, {}, {}, {}
    records, invalid, skipped = [], [], []
    stop = None
    for slot in plan.slots():
        pid, kind, key = slot['profile'], slot['kind'], plan.parent(slot)
        if kind in ('extract', 'read') and not (len(gates) == len(plan.PROFILES) and all(g['qualified'] for g in gates.values())):
            stop = 'controls_not_qualified'
            break
        if kind == 'read' and key not in parents:
            skipped.append({**slot, 'reason': 'own_profile_method_generation_product_invalid'})
            continue
        try:
            plan.verify(root, reconstruct=False)
            req = plan.request(slot, parents)
            guard = before(slot)
            if not simulated and not guard.get('owned_active'):
                raise PermissionError('Owned temporary guard required')
        except Exception as exc:
            stop = 'pre_call_failure:' + type(exc).__name__
            break
        if len(records) >= plan.CAP:
            stop = 'attempt_cap'
            break
        folder = destination / ('attempt-%02d' % slot['slot'])
        folder.mkdir()
        rec = {**slot, 'execution_id': folder.name, 'state': 'invocation_intent',
               'request_sha256': plan.digest(req), 'usage': None, 'simulated': simulated}
        write_new(folder / 'request.json', req)
        write_new(folder / 'intent.json', {**rec, 'guard': guard})
        records.append(rec)
        try:
            raw, provenance = invoke(req, folder, slot)
            write_new(folder / 'raw-response.json', {'raw': raw, 'provenance': provenance})
            rec['raw_response_sha256'] = plan.sha(folder / 'raw-response.json')
            rec['usage'] = usage(provenance)
            if provenance.get('model_requested') != plan.MODEL or (not simulated and provenance.get('backend') != 'codex'):
                raise ValueError('Requested model/backend differs')
            if type(raw) is not str or len(raw.encode()) > 256000:
                raise ValueError('Raw response type/size differs')
            answer = parse_answer(raw)
            check(answer, req['schema'])
            write_new(folder / 'answer.json', answer)
            if kind == 'extract':
                try:
                    prompt = plan.bind(slot, answer)['prompt.md']
                    if not 0 < len(prompt) <= slot['budget']:
                        raise ValueError('Whole-card budget exceeded')
                    artifact = {'profile': pid, 'method': slot['method'], 'budget': slot['budget'], 'generation': slot['generation'],
                                'prompt': prompt, 'characters': len(prompt),
                                'source_sha256': plan.digest(data['sources'][pid]), 'answer_sha256': plan.digest(answer)}
                    write_new(folder / 'artifact.json', artifact)
                    rec['artifact_sha256'] = plan.sha(folder / 'artifact.json')
                    parents[key], cards[key] = answer, artifact
                except (ValueError, KeyError, TypeError) as exc:
                    rec['product_invalid'] = True
                    invalid.append({**slot, 'error_type': type(exc).__name__, 'error': str(exc)})
            else:
                plan.choice_reader.decode_response(data['queries'][plan.bank(pid)], answer,
                                                   answer_format='text', reader_mode='standard')
                if kind == 'none':
                    none[plan.bank(pid)] = answer
                elif kind == 'full':
                    own = [r for r in data['rows'] if r['person'] == pid]
                    f, n = score.counts(own, [answer]), score.counts(own, [none[plan.bank(pid)]])
                    signal = 'known' if pid == 'dev' else 'personal_known'
                    gates[pid] = {'qualified': f['joint']['correct'] == len(own) and not f['joint']['missing']
                                  and f[signal]['correct'] > n[signal]['correct'], 'full': f, 'none': n}
                    write_new(destination / ('control-gate-' + pid + '.json'), gates[pid])
                    if not gates[pid]['qualified']:
                        stop = 'full_control_not_qualified:' + pid
                else:
                    responses[key + (slot['read_repeat'],)] = answer
            rec['state'] = 'completed'
        except Exception as exc:
            rec.update(state='failed', error_type=type(exc).__name__, error=str(exc))
            stop = 'transport_wire_decode_usage_or_model_failure'
            extra = getattr(exc, 'provenance', None)
            if extra:
                write_new(folder / 'failure-provenance.json', extra)
                try:
                    rec['usage'] = usage(extra)
                except ValueError:
                    pass
        write_new(folder / 'result.json', rec)
        if stop:
            break
    totals = Counter()
    for rec in records:
        if rec['usage'] is not None:
            totals.update(rec['usage'])
    result = {'status': 'stopped' if stop else 'completed_with_invalid_products' if invalid else 'complete',
              'stop': stop, 'records': records, 'invalid_products': invalid, 'skipped': skipped,
              'control_gates': gates, 'attempt_reservations': len(records),
              'local_cli_child_intents': sum((destination / r['execution_id'] / 'backend-child-intent.json').exists() for r in records),
              'known_usage': dict(totals), 'missing_usage': sum(r['usage'] is None for r in records),
              'simulated': simulated, 'usage_is_fixture_not_billable': simulated, 'scope_closed': True,
              'unused_slots_expire': plan.CAP-len(records), 'new_service_authority': False,
              'no_retry_repair_resume_or_replenishment': True,
              'scores': score.summarize(data['rows'], responses, cards)}
    write_new(destination / 'result.json', result)
    return result
