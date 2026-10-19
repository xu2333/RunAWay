"""Single-use tiny end-to-end reader. No calls in prepare or preflight mode.

Uses the existing isolated 180s Codex transport and durable execution ledger;
the public browser's actual request/validation/export are used without edits.
An approval receipt records independently verified human authorization, it does
not authenticate it. Injected backends are plumbing tests, never model evidence.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from unittest.mock import patch
import zipfile

from . import end_to_end_taste as et, generation
from .card import canonical, digest
from .execution_ledger import checked, collect, summarize
from .fidelity_runner import DirectCalls
from .pipeline import write_once
from .selfplay import browser
from .shared_schema import parse_wire
from .shared_schema_executor import records_checked, runtime_metadata
from .taste_executor import atomic


def forbidden_ids(archives):
    ids = set()
    for name in archives:
        with zipfile.ZipFile(et.ROOT / name) as z:
            ids.update(Path(n).name.removesuffix('.request.json') for n in z.namelist() if n.endswith('.request.json'))
    return ids


class StrictCalls(DirectCalls):
    def __init__(self, out, config, backend, guard):
        self.guard = guard
        def strict_backend(*args, **kwargs):
            raw, provenance = backend(*args, **kwargs)
            try:
                answer = parse_wire(raw.encode('utf-8'))
            except Exception as exc:
                error = ValueError('Invalid JSON wire; no repair')
                error.provenance = dict(provenance, rejected_wire_sha256=digest(raw))
                raise error from exc
            return canonical(answer), provenance
        super().__init__(out, config, strict_backend)

    def call(self, stage, request):
        self.guard()
        key = digest(canonical(request))
        et.require(not any(r['request_id'] == key for r in collect(self.out)), 'No repeated or reused calls')
        answer = super().call(stage, request)
        counts = records_checked(self.out)
        et.require(all(r['usage'] is not None for r in counts), 'Unknown/contradictory usage; stop globally')
        return answer


def execute(root, out, backend=None, approval=None, runtime=None):
    root, out = Path(root).resolve(), Path(out).resolve()
    p, f, static = et.preflight(root)
    real = backend is None
    if real:
        et.require(approval is not None and approval.get('proposal_id') == p['id'] and
                   approval.get('calls_max') == 10 and approval.get('human_source') and
                   approval.get('status') == 'approved', 'Independently verified human authorization required')
        acceptance = checked(root / 'offline-acceptance.json')
        et.require(acceptance['proposal_id'] == p['id'] and acceptance['all_checks_passed'] is True and
                   acceptance['external_model_calls'] == 0, 'Offline acceptance required')
        expected = checked(root / 'runtime.json')['runtime']
        et.require((runtime or runtime_metadata)() == expected, 'Runtime drift')
    et.require(not (root / 'execution-intent.json').exists(), 'Single-use proposal already claimed')
    out.mkdir(parents=True, exist_ok=False)
    if real:
        # Exclusive creation precedes the first possible backend entry. A crashed
        # or partial run cannot be resumed or replenished from another directory.
        with (root / 'execution-intent.json').open('x') as stream:
            json.dump({'proposal_id': p['id'], 'out': str(out), 'human_source': approval['human_source'],
                       'at': datetime.now(timezone.utc).isoformat()}, stream)
        backend = generation.codex_generate
    config = dict(p, forbidden_request_ids=sorted(forbidden_ids(p['archives'])))
    def guard():
        et.preflight(root)
        if real:
            et.require((runtime or runtime_metadata)() == expected, 'Runtime drift')
    calls = StrictCalls(out, config, backend, guard)
    rows, memories, products = {}, {}, {}
    complete = False
    try:
        with patch.object(generation, 'run_bounded', calls.observed_runner):
            for stage in p['stage_order']:
                for index, pid in enumerate(et.PEOPLE):
                    if stage in static:
                        request = static[stage][pid]
                    else:
                        donor = pid if stage == 'own' else et.PEOPLE[1 - index]
                        request = et.reader_request(f, pid, memories[donor]['text'])
                    answer = calls.call(stage, request)
                    if stage == 'shared_extraction':
                        bundle = browser('validate', et.person(f, pid)['sources'], et.BUDGET, answer)
                        text = bundle['portable']['text']
                        et.require(len(text) <= et.BUDGET, 'Complete prompt exceeded budget; no truncation')
                        history = et.full_history(f, pid)
                        memories[pid] = {'text': text, 'complete_characters': len(text),
                                         'complete_utf8_bytes': len(text.encode()),
                                         'history_characters': len(history), 'history_utf8_bytes': len(history.encode()),
                                         'character_ratio_to_role_labelled_history': len(text) / len(history),
                                         'utf8_byte_ratio_to_role_labelled_history': len(text.encode()) / len(history.encode()),
                                         'meaning': 'Actual browser export includes HEADER and newline; no name/tagline/claims/evidence sent to readers.'}
                        products[pid] = {'answer': answer, 'bundle': bundle}
                        atomic(out / 'products.synthetic.json', products)
                        atomic(out / 'memories.synthetic.json', memories)
                    else:
                        rows.setdefault(stage, {})[pid] = et.validate_answers(f, pid, answer)
                        atomic(out / 'answers.synthetic.json', rows)
                    atomic(out / 'progress-report.json', et.report(f, rows))
            complete = True
    except Exception as exc:
        calls.stop('end_to_end_validation_or_transport_failure', error_type=type(exc).__name__, error=str(exc))
    # Summarize accepted usage only; contradictory provenance remains in raw
    # checkpoints but cannot masquerade as known costs.
    try:
        ledger = summarize(records_checked(out))
    except Exception:
        ledger = {'integrity_uncertain': True, 'known_usage': None}
        complete = False
    result = {**et.report(f, rows), 'status': 'complete' if complete and not calls.stopped else 'stopped',
              'proposal_id': p['id'], 'backend_kind': 'actual_codex_service' if real else 'injected_fake_not_model_evidence',
              'external_model_calls': sum(calls.counts.values()) if real else 0,
              'calls_max': 10, 'stage_attempts': dict(calls.counts), 'calls': ledger,
              'stop_reason': calls.reason, 'memories': memories,
              'quality_result': 'Diagnostic; no claim of population accuracy or human fidelity.',
              'resolved_model': None, 'model_requested': et.MODEL,
              'new_model_tokenization_calls': 0, 'gpu_required': False}
    write_once(out / 'report.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal', required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--out')
    parser.add_argument('--approval')
    args = parser.parse_args()
    if args.prepare:
        et.require(not args.run, 'Choose prepare or run')
        result = et.prepare(args.proposal)
        print(json.dumps({'proposal_id': result['id'], 'calls_max': 10, 'external_model_calls': 0}))
    elif args.run:
        et.require(args.out and args.approval, 'Run requires output and verified approval receipt')
        result = execute(args.proposal, args.out, approval=et.read(args.approval))
        print(json.dumps({'status': result['status'], 'calls': result['external_model_calls']}))
    else:
        print(json.dumps({'proposal_id': et.preflight(args.proposal)[0]['id'], 'external_model_calls': 0}))


if __name__ == '__main__':
    main()
