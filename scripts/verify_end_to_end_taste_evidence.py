"""Archive-local verifier, copied as verify.py; no model, network or inference."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'frozen' / 'frozen-source'))

from runaway import end_to_end_taste as et
from runaway.card import canonical, digest
from runaway.execution_ledger import checked, collect, summarize
from runaway.selfplay import browser
from runaway.shared_schema_executor import records_checked


def main():
    if sys.flags.optimize:
        raise ValueError('Optimized Python unsupported')
    frozen, service = ROOT / 'frozen', ROOT / 'service'
    p = et.read(frozen / 'proposal.json')
    et.require(p['id'] == digest(canonical({k: v for k, v in p.items() if k != 'id'})), 'Proposal binding changed')
    for name, sha in p['source_hashes'].items():
        et.require(et.sha(frozen / 'frozen-source' / name) == sha, 'Frozen source changed')
    for name, sha in p['input_hashes'].items():
        et.require(et.sha(frozen / 'frozen-source' / et.BASE / name) == sha, 'Frozen input changed')
    f = et.read(frozen / 'fixtures.synthetic.json')
    et.require(et.sha(frozen / 'fixtures.synthetic.json') == p['fixture_sha256'] and f == et.fixtures(), 'Independent fixture/gold changed')
    acceptance = checked(frozen / 'offline-acceptance.json')
    et.require(acceptance['proposal_id'] == p['id'] and acceptance['all_checks_passed'] is True,
               'Offline acceptance mismatch')
    et.require(et.sha(frozen / 'corruption-controls.synthetic.json') == acceptance['corruption_control_sha256'], 'Controls changed')
    static = et.read(frozen / 'static-requests.synthetic.json')
    et.require(et.sha(frozen / 'static-requests.synthetic.json') == p['static_requests_sha256'], 'Static request binding changed')
    records = records_checked(service)
    et.require(len(records) == 10 and all(r['outcome'] == 'completed' and r['usage'] is not None for r in records),
               'Expected ten completed calls with known usage')
    et.require(len({r['execution_id'] for r in records}) == len({r['request_id'] for r in records}) == 10, 'Duplicate executions/requests')
    rows, memories, products, seen = {}, {}, {}, set()
    saved_products = et.read(service / 'products.synthetic.json')
    saved_memories = et.read(service / 'memories.synthetic.json')
    for stage in p['stage_order']:
        for i, pid in enumerate(et.PEOPLE):
            if stage == 'full_history':
                request = et.reader_request(f, pid, et.full_history(f, pid))
            elif stage == 'none':
                request = et.reader_request(f, pid, '')
            elif stage == 'shared_extraction':
                request = et.generation_request(f, pid)
            else:
                donor = pid if stage == 'own' else et.PEOPLE[1-i]
                request = et.reader_request(f, pid, memories[donor]['text'])
            if stage in static:
                et.require(static[stage][pid] == request, 'Static request reconstruction changed')
            key = digest(canonical(request))
            et.require(key not in seen, 'Reused request')
            seen.add(key)
            et.require(et.read(service / 'calls' / (key + '.request.json')) == request, 'Exact request changed')
            response = checked(service / 'calls' / (key + '.response.json'))
            answer = response['answer']
            if stage == 'shared_extraction':
                bundle = browser('validate', et.person(f, pid)['sources'], et.BUDGET, answer)
                text = bundle['portable']['text']
                et.require(len(text) <= et.BUDGET, 'Complete export exceeds frozen budget')
                et.require(saved_products[pid] == {'answer': answer, 'bundle': bundle}, 'Product/bundle reconstruction changed')
                memory = saved_memories[pid]
                h = et.full_history(f, pid)
                et.require(memory == {'text': text, 'complete_characters': len(text), 'complete_utf8_bytes': len(text.encode()),
                                      'history_characters': len(h), 'history_utf8_bytes': len(h.encode()),
                                      'character_ratio_to_role_labelled_history': len(text)/len(h),
                                      'utf8_byte_ratio_to_role_labelled_history': len(text.encode())/len(h.encode()),
                                      'meaning': 'Actual browser export includes HEADER and newline; no name/tagline/claims/evidence sent to readers.'}, 'Memory/length changed')
                memories[pid] = memory
            else:
                rows.setdefault(stage, {})[pid] = et.validate_answers(f, pid, answer)
    et.require(seen == {r['request_id'] for r in records}, 'Unplanned/missing call')
    et.require(rows == et.read(service / 'answers.synthetic.json'), 'Answers changed')
    report = et.read(service / 'report.json')
    recomputed = et.report(f, rows)
    for key, value in recomputed.items():
        et.require(report[key] == value, 'Score/report mismatch: ' + key)
    ledger = summarize(records)
    et.require(report['calls'] == ledger and report['memories'] == memories and report['status'] == 'complete', 'Ledger/status mismatch')
    et.require(report['stage_attempts'] == et.CAPS and report['external_model_calls'] == 10 and
               report['backend_kind'] == 'actual_codex_service' and report['proposal_id'] == p['id'], 'Scope/provenance mismatch')
    # An internally rehashed changed choice still changes the frozen published
    # result; score calculation has no path back into the model responses.
    from copy import deepcopy
    corrupted = deepcopy(rows)
    pid = et.PEOPLE[0]
    qid = next(iter(corrupted['own'][pid]))
    corrupted['own'][pid][qid] = 'B' if corrupted['own'][pid][qid] == 'A' else 'A'
    et.require(et.report(f, corrupted) != recomputed, 'Choice corruption not detected')
    print(json.dumps({'status': 'verified', 'original_service_calls': 10, 'new_model_calls': 0,
                      'new_tokenization_calls': 0, 'prediction_denominator': 192,
                      'correct': {k: v['correct'] for k, v in recomputed['scores'].items()},
                      'complete_characters': {k: v['complete_characters'] for k, v in memories.items()},
                      'normalized_retention': recomputed['normalized_retention'],
                      'known_service_usage': ledger['known_usage'], 'choice_corruption_detected': True}))


if __name__ == '__main__':
    main()
