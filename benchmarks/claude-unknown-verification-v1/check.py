"""Offline input integrity and within-case comparison with the retained reader."""
import hashlib
import json
from collections import Counter
from pathlib import Path

def verify(path, previous):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '288e145d72a22c536bf30cebe1aa491331f47b03b953faec1073a1f781790766'
    plan = json.loads(raw)
    assert hashlib.sha256(previous).hexdigest() == plan['source_sha256']
    control = json.loads(previous)
    assert plan['cases'] == control['cases']
    assert plan['stop'] == control['stop']
    slots = plan['slots']
    assert len({slot['slot'] for slot in slots}) == len(slots) == plan['max_cli_attempts'] == 12
    assert Counter(slot['input'] for slot in slots) == {key: 2 for key in plan['inputs']}
    for case in plan['cases']:
        original = control['inputs'][case['id']+'-old']
        for arm in ('old', 'new'):
            item = plan['inputs'][case['id']+'-'+arm]
            assert item['task'] == case['task'] == original['task']
            assert item['rule_path'] == original['rule_path']
            extra = '\n'+plan['candidate_append']+'\n' if arm == 'new' else ''
            assert item['rule'] == original['rule']+extra
            assert item['rule_sha256'] == hashlib.sha256(item['rule'].encode()).hexdigest()

if __name__ == '__main__':
    import sys
    verify(Path(sys.argv[1]), Path(sys.argv[2]).read_bytes())
    print('Matched all six inputs to the existing cards, tasks and retained reader.')
