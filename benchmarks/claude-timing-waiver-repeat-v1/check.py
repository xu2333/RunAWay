"""Check the exact installed inputs against the previous round, offline."""
from collections import Counter
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
def load(path):
    return json.loads(path.read_bytes())
def digest(data):
    return hashlib.sha256(data).hexdigest()
def verify():
    prior = here.parent/'timing-versus-waiver-cross-harness-v1'
    archive = load(prior/'protocol.json')
    reference = {row['slot']:row for row in load(prior/'rule-receipts.json')}
    spec = load(here/'protocol.json')
    assert digest((here/'protocol.json').read_bytes())=='c98c9a2173518ca444fee8e9f2ac50afd28432b445f339312d643ef80aef034f'
    assert spec['cases']==[next(c for c in archive['cases'] if c['id']==case) for case in ('thread','foldout','listening')]
    expected = {(c['id'],arm) for c in spec['cases'] for arm in ('old','new')}
    assert Counter((c['case'],c['arm']) for c in spec['slots'])=={key:2 for key in expected}
    assert len({c['slot'] for c in spec['slots']})==spec['max_cli_attempts']==12
    for case in spec['cases']:
        for arm in ('old','new'):
            item=spec['inputs'][case['id']+'-'+arm]
            ref=reference['claude-code-'+case['id']+'-'+arm]
            assert digest(item['rule'].encode())==item['rule_sha256']==ref['rule_sha256']
            assert item['rule_path']==ref['rule']
            assert item['task']==case['task']
            assert item['rule'].count(case['card'])==1
            assert item['rule'].endswith(archive['reader'][arm]+'\n')
    return spec

if __name__=='__main__':
    verify()
    print('Verified six original task/rule pairs and twelve fresh-session slots.')
