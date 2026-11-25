"""Recount the fixed /2 and /6 denominators using the quoted human-readable grades."""
from collections import Counter
import hashlib
import json
from check import here, verify

FACETS = {
    'thread': {'assignment_time','action_scope'},
    'foldout': {'optional_photo','book_conditions'},
    'listening': {'page_form','real_release'},
}

def recount():
    spec = verify()
    rows=json.loads((here/'observations.json').read_bytes())
    assert len(rows)==len(spec['slots'])
    stopped=False
    for r,slot in zip(rows,spec['slots']):
        assert all(r[k]==v for k,v in slot.items())
        state=r['state']
        assert state in ('answer','failure','unattempted')
        if stopped:
            assert state=='unattempted'
        elif state=='failure':
            stopped=True
        else:
            assert state=='answer'
        if state!='answer':
            assert 'answer' not in r and not r['focus_pass'] and not r['whole_pass']
            continue
        answer=r['answer']
        assert hashlib.sha256(answer.encode()).hexdigest()==r['answer_sha256']
        clauses=r['clauses']
        assert len(clauses)==3
        assert set(r['facets'])==FACETS[r['case']]
        for mark in [*clauses,*r['facets'].values()]:
            assert mark['grade'] in ('pass','fail','ambiguous','omitted')
            assert mark['quotes'] and all(q and q in answer for q in mark['quotes'])
        assert r['focus_pass']==all(v['grade']=='pass' for v in r['facets'].values())
        assert r['whole_pass']==(r['focus_pass'] and all(x['grade']=='pass' for x in clauses) and not r['other_loss'])
    out={}
    for arm in ('old','new'):
        values=[r for r in rows if r['arm']==arm]
        out[arm]={'cases':{},'whole':sum(r['whole_pass'] for r in values),
                  'states':dict(Counter(r['state'] for r in values))}
        for c in FACETS:
            these=[r for r in values if r['case']==c]
            out[arm]['cases'][c]={'focus':sum(r['focus_pass'] for r in these),
                'whole':sum(r['whole_pass'] for r in these)}
            if c=='listening':
                out[arm]['cases'][c]['lenient']=sum(r['state']=='answer' and r['facets']['page_form']['grade'] in ('pass','ambiguous') and r['facets']['real_release']['grade']=='pass' for r in these)
    transitions=Counter()
    for c in FACETS:
        for repeat in (1,2):
            a,b=(next(r for r in rows if r['case']==c and r['repeat']==repeat and r['arm']==arm) for arm in ('old','new'))
            key='missing' if any(r['state']!='answer' for r in (a,b)) else f"{int(a['whole_pass'])}→{int(b['whole_pass'])}"
            transitions[key]+=1
    out['whole_pairs']=dict(transitions)
    return out

if __name__=='__main__':
    print(json.dumps(recount(),ensure_ascii=False,indent=2))
