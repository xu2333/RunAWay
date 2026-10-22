"""Offline consumed-output parity, not another measurement of model accuracy."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runaway import constraint_extract as ce
from runaway.portable import render_expression


def check():
    here = Path(__file__).resolve().parent
    raw = (here / 'observed.synthetic.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (here / 'observed.sha256').read_text().strip():
        raise ValueError('Recorded regression bytes changed')
    observed = json.loads(raw)
    if observed['fresh_holdout'] is not False or len(observed['records']) != 6:
        raise ValueError('Consumed regression boundary changed')
    lengths = []
    for row in observed['records']:
        request = row['request']
        body = json.loads(request['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
        if set(body) != {'sources', 'budget_characters'} or body['sources'] != row['sources']:
            raise ValueError('Source-only request boundary changed')
        budget = body['budget_characters']
        actual = dict(ce.make_request(row['sources'], budget), model=observed['requested_model'])
        if actual != request:
            raise ValueError('Measured request/schema differs: ' + row['person'])
        answer = ce.parse_answer(row['raw'])
        if ce.compile_answer(answer, row['sources'], budget) != row['expected']:
            raise ValueError('Measured compilation/render differs: ' + row['person'])
        bundle = ce.bind(answer, row['sources'], budget)
        if render_expression(bundle['portable.json']) != row['expected']['prompt']:
            raise ValueError('Product wrapper changed the public card')
        lengths.append(bundle['summary.private.json']['characters'])
    return {'status': 'consumed_parity_pass', 'source_only_requests': 6,
            'exact_compilations': 6, 'whole_characters': lengths,
            'new_model_calls': 0, 'fresh_holdout': False, 'human_fidelity_verified': False}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False))
