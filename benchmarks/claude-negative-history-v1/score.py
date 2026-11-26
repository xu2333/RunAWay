"""Verify the registered inputs and recount per-answer evidence on a fixed /2."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from check import verify

ROOT = Path(__file__).resolve().parent
GRADES = {
    'chuan_history': {'explicit_unknown', 'unstated', 'unsupported', 'ambiguous'},
    'ting_history': {'explicit_unknown', 'unstated', 'unsupported', 'ambiguous'},
    'chuan': {'named_operator', 'unknown', 'omitted', 'wrong', 'conflict'},
    'ting': {'explicit_unknown', 'omitted', 'speculation', 'wrong', 'conflict'},
    'records': {'pass', 'omitted', 'wrong', 'ambiguous'},
    'state': {'pass', 'omitted', 'wrong', 'ambiguous'},
    'handoff': {'pass', 'omitted', 'wrong', 'ambiguous'},
}

def recount():
    plan = verify(ROOT/'protocol.json', ROOT.parent/'claude-matched-attribution-v1/protocol.json')
    rows = json.loads((ROOT/'observations.json').read_bytes())
    assert len(rows) == len(plan['slots']) == 4
    totals = {'old':Counter(), 'new':Counter()}
    stopped = False
    for row, slot in zip(rows, plan['slots']):
        assert all(row[k]==v for k,v in slot.items())
        if stopped:
            assert row['state']=='unattempted'
            continue
        if row['state']=='failure':
            stopped=True
            continue
        assert row['state']=='answer'
        assert sha256(row['answer'].encode()).hexdigest()==row['answer_sha256']
        marks=row['marks']
        assert set(marks)==set(row['quotes'])==set(GRADES)
        counts=totals[row['arm']]
        for key, allowed in GRADES.items():
            assert marks[key] in allowed
            assert row['quotes'][key] and all(q and q in row['answer'] for q in row['quotes'][key])
            counts[(key,marks[key])]+=1
        joint=marks['chuan']=='named_operator' and marks['ting']=='explicit_unknown'
        counts['joint']+=joint
        histories=[marks[k] for k in ('chuan_history','ting_history')]
        explicit=all(v=='explicit_unknown' for v in histories)
        clean=all(v in ('explicit_unknown','unstated') for v in histories)
        counts['explicit_history']+=explicit
        counts['clean_history']+=clean
        counts['primary']+=explicit and joint and marks['handoff']=='pass'
        counts['omission_allowed']+=clean and joint and marks['handoff']=='pass'
        counts['whole']+=clean and joint and all(marks[k]=='pass' for k in ('records','state','handoff')) and not row['other_loss']
    return totals

if __name__ == '__main__':
    for arm, values in recount().items():
        print(arm, dict(values))
