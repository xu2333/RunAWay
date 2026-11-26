"""Verify both historical readers, the shared new task and the four frozen slots."""
from pathlib import Path
from hashlib import sha256
import json

def verify(protocol, parent):
    data=protocol.read_bytes()
    assert sha256(data).hexdigest()=='b99f79e07aec5b1f1b163b5dc59c3d0a9c382dfd55df70b5f037fab3306345af'
    plan=json.loads(data)
    archive=parent.read_bytes()
    assert sha256(archive).hexdigest()==plan['prior_sha256']
    base=json.loads(archive)
    for key in ('client','model','deadline_seconds','max_cli_attempts','stop','candidate_append'):
        assert plan[key]==base[key]
    assert [(s['arm'],s['repeat']) for s in plan['slots']]==[('old',1),('new',1),('new',2),('old',2)]
    assert len({s['slot'] for s in plan['slots']})==4
    for arm,item in plan['inputs'].items():
        assert item['rule'].count(plan['card'])==1
        assert item['rule'].replace(plan['card'],base['card'])==base['inputs'][arm]['rule']
        assert item['rule_sha256']==sha256(item['rule'].encode()).hexdigest()
        assert item['task']==plan['task']
        assert item['task_sha256']==sha256(plan['task'].encode()).hexdigest()
    return plan

if __name__=='__main__':
    import sys
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print('Verified frozen input bytes, both readers and four independent slots.')
