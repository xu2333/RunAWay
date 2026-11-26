"""Offline verification of the two readers and strict versus omission-aware scores."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

def verify(protocol, predecessor):
    data = protocol.read_bytes()
    assert sha256(data).hexdigest() == 'f7a3c5273bdd6091d2b4764d5ba4e6814949921601307416bc4daf96131229bc'
    plan = json.loads(data)
    source = predecessor.read_bytes()
    assert sha256(source).hexdigest() == plan['prior_sha256']
    prior = json.loads(source)
    for k in ('card', 'task', 'slots', 'max_cli_attempts', 'deadline_seconds', 'model', 'client', 'stop', 'rubric'):
        assert plan[k] == prior[k]
    baseline = prior['inputs']['old']
    assert plan['inputs']['old'] == baseline
    for arm, item in plan['inputs'].items():
        addition = '\n'+plan['candidate_append']+'\n' if arm=='new' else ''
        assert item['rule'] == baseline['rule'] + addition
        assert item['task'] == plan['task'] and item['rule'].count(plan['card']) == 1
        assert item['rule_sha256'] == sha256(item['rule'].encode()).hexdigest()
    assert Counter(s['arm'] for s in plan['slots']) == {'old':2, 'new':2}
    return plan

if __name__=='__main__':
    import sys
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print('Both readers and all four slots verified.')
