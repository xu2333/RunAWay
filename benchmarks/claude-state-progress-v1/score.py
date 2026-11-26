"""Recount stated uncertainty separately from leaving the field unmentioned."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from check import verify

here = Path(__file__).resolve().parent
def recount():
    plan = verify(here/'protocol.json', here.parent/'claude-insert-verification-transfer-v1/protocol.json')
    rows = json.loads((here/'observations.json').read_bytes())
    assert len(rows) == len(plan['slots']) == 4
    counts = {'old':Counter(), 'new':Counter()}
    stopped = False
    for row, slot in zip(rows, plan['slots']):
        assert all(row[k] == v for k,v in slot.items())
        tally = counts[row['arm']]
        if stopped:
            assert row['state'] == 'unattempted'
            continue
        if row['state'] == 'failure':
            stopped = True
            continue
        assert row['state'] == 'answer'
        assert sha256(row['answer'].encode()).hexdigest() == row['answer_sha256']
        location = row['location']
        assert location in ('explicit_unknown','unstated','unsupported','ambiguous')
        tally[location] += 1
        safe = location in ('explicit_unknown','unstated')
        tally['no_inference'] += safe
        success = True
        for k in ('optional','inspection','present','empty','progress'):
            mark = row['marks'][k]
            assert mark in ('pass','fail','ambiguous','omitted')
            tally[k] += mark == 'pass'
            success = success and mark == 'pass'
        for key in ('location', *row['marks']):
            quotes = row['quotes'][key]
            assert quotes and all(q and q in row['answer'] for q in quotes)
        tally['whole'] += safe and success and not row['other_loss']
    return counts

if __name__=='__main__':
    for arm,t in recount().items():
        print(arm, dict(t))
