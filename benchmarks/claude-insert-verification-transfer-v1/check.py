"""Verify the reader-only comparison, answer bytes and the fixed /2 counts."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYS = ('optional', 'inspection', 'branches', 'progress')
def recount():
    data = (ROOT/'protocol.json').read_bytes()
    assert sha256(data).hexdigest() == '934de2716cf011d1c2232fe7f29d69d52b9489572313b1e118925ac9c5cfa8c6'
    plan = json.loads(data)
    source = (ROOT.parent/'claude-unknown-verification-v1/protocol.json').read_bytes()
    assert sha256(source).hexdigest() == plan['prior_sha256']
    prior = json.loads(source)
    earlier = next(c for c in prior['cases'] if c['id'] == 'foldout')
    for arm, item in plan['inputs'].items():
        assert item['rule'].count(plan['card']) == 1
        assert item['rule'].replace(plan['card'], earlier['card']) == prior['inputs']['foldout-'+arm]['rule']
        assert item['task'] == plan['task']
    scores = {'old':Counter(), 'new':Counter()}
    answers = json.loads((ROOT/'observations.json').read_bytes())
    assert len(answers) == len(plan['slots']) == 4
    closed = False
    for slot, r in zip(plan['slots'], answers):
        assert all(r[k] == v for k,v in slot.items())
        if closed:
            assert r['state'] == 'unattempted'
            continue
        if r['state'] == 'failure':
            closed = True
            continue
        assert r['state'] == 'answer'
        assert sha256(r['answer'].encode()).hexdigest() == r['answer_sha256']
        yes = {}
        for key in KEYS:
            mark = r['marks'][key]
            assert mark['grade'] in ('pass','fail','ambiguous','omitted')
            assert mark['quotes'] and all(q and q in r['answer'] for q in mark['quotes'])
            yes[key] = mark['grade'] == 'pass'
        checks = scores[slot['arm']]
        checks.update(k for k in KEYS if yes[k])
        checks['joint'] += yes['optional'] and yes['inspection']
        checks['whole'] += all(yes.values()) and not r['other_loss']
    return scores

if __name__=='__main__':
    for arm,row in recount().items():
        print(arm, ', '.join(f'{k}={row[k]}/2' for k in (*KEYS, 'joint','whole')))
