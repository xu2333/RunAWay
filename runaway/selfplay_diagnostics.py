"""Non-mutating diagnostics for saved local synthetic scores; no model calls."""
import argparse
from collections import Counter
import json
from pathlib import Path


def diagnose(plan, rows):
    cases={c['public']['id']:c for c in plan['world']['test']}
    index={}
    for row in rows:
        key=(row['persona'],row['condition'],row['case_id'])
        if key in index or row['choice'] not in ('A','B','U') or row['case_id'] not in cases:
            raise ValueError('Duplicate or invalid score row')
        index[key]=row
    expected={(p['id'],condition,cid) for p in plan['world']['personas'] for condition in plan['conditions']
              if plan['memories'][p['id']][condition] is not None for cid in cases}
    if set(index)!=expected:raise ValueError('Incomplete local scores; no decoder verdict')
    controls={}
    for condition in plan['conditions']:
        selected=[r for r in rows if r['condition']==condition];swaps=[];unknown=[]
        for row in selected:
            case=cases[row['case_id']]
            if case['kind']=='order_swap':
                other=index[(row['persona'],condition,case['original_id'])]
                swaps.append(row['choice'] in ('A','B') and other['choice'] in ('A','B') and
                             case['actions'][row['choice']]==cases[case['original_id']]['actions'][other['choice']])
            elif case['kind']=='unobserved':unknown.append(row['choice']=='U')
        counts=Counter(r['choice'] for r in selected)
        controls[condition]={'choice_counts':dict(counts),'constant_answer':len(counts)==1 if selected else None,
                             'order_consistency':sum(swaps)/len(swaps) if swaps else None,
                             'unknown_abstention':sum(unknown)/len(unknown) if unknown else None}
    oracle=controls.get('oracle',{})
    degenerate=oracle.get('constant_answer') is True and oracle.get('order_consistency')==0
    return {'origin':'fully_synthetic','diagnostic_version':1,'posthoc_diagnostic':True,'controls':controls,
            'degenerate_oracle_decoder':degenerate,
            'rig_should_be_treated_as_decoder_diagnostic':degenerate,
            'true_person_fidelity_verified':False,
            'note':'A constant oracle response with zero order consistency fails basic decoding controls. Passing these checks would not by itself establish fidelity. This diagnostic was added after inspecting the first run; it does not change any frozen probability or score.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');args=p.parse_args()
    root=Path(args.directory);load=lambda name:json.loads((root/name).read_text())
    result=diagnose(load('plan.local.json'),load('rows.synthetic.json'))
    (root/'decoder-diagnostic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'degenerate_oracle_decoder':result['degenerate_oracle_decoder'],'diagnostic':str(root/'decoder-diagnostic.json')}))
if __name__=='__main__':main()
