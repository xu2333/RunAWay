"""Publish only development calibration; never export the future cohort or approvals."""
import argparse
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def package(run):
    run=Path(run);world=json.loads((run/'development-final/fixtures.synthetic.json').read_text())
    report=json.loads((run/'development-final/calibration.synthetic.json').read_text())
    if world['purpose']!='development' or world['origin']!='fully_synthetic' or report['external_model_calls']!=0:
        raise ValueError('Only explicitly synthetic development calibration is publishable')
    rows=[]
    for name,tasks in report['controls'].items():
        c=tasks['current_choice'];h=tasks['historical_reconstruction'];j=tasks['joint']
        rows.append({'condition':name,'current_correct':c['correct'],'current_planned':c['planned'],
            'collapsed_correct':c['current_scenarios_option_orders_collapsed']['correct'],
            'collapsed_planned':c['current_scenarios_option_orders_collapsed']['planned'],
            'historical_correct':h['correct'],'historical_planned':h['planned'],
            'joint_correct':j['correct'],'joint_planned':j['planned'],
            'matched_correct':c['matched_domain_contrasts']['correct'],'matched_planned':c['matched_domain_contrasts']['planned'],
            'hard_violations':c['hard_constraints']['observed_violations']})
    proposal_path=run/'proposed-comparison/proposal.json';p=json.loads(proposal_path.read_text())
    summary={'origin':'fully_synthetic','kind':report['kind'],'external_model_calls':0,'experiment_service_tokens':0,
             'native_chat_usage':'Tracked separately by the host/central ledger; final turn total not available here, never assumed zero.',
             'people':len(world['people']),'paired_clusters':report['independent_cluster_count'],'domains':6,
             'rows':rows,'model_quality_measured':False,'real_person_fidelity_verified':False,
             'future_proposal':{'status':'not_approved_not_executed','id':p['id'],'calls_max':p['calls_max'],
                'people':p['data_scope']['synthetic_people'],'paired_clusters':2,'budgets':p['budgets'],
                'history_characters':p['data_scope']['history_characters'],'timeout_seconds':180,
                'source_path':str(proposal_path.relative_to(ROOT)) if proposal_path.is_relative_to(ROOT) else 'operator-local proposal',
                'scope':'16control reads +8shared extractions +8additional compressions +16memory reads; stop at failed controls, no retry/repair. Current224 +historical76 remain in every method/budget denominator. Two paired clusters only; no population significance claim.'},
             'limits':report['limitations']}
    dest=ROOT/'examples/fidelity-stress';dest.mkdir(exist_ok=True)
    for name in ('fixtures.synthetic.json','calibration.synthetic.json'):
        shutil.copyfile(run/'development-final'/name,dest/name)
    (dest/'summary.synthetic.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    path=ROOT/'runs/real-adapters-offline-v1/readiness.json';ready=json.loads(path.read_text());ready['fidelity_stress']=summary
    path.write_text(json.dumps(ready,ensure_ascii=False,indent=2)+'\n')
    path=ROOT/'examples/metric-view/metric-data.synthetic.json';data=json.loads(path.read_text());data['actual_adapters']['fidelity_stress']=summary
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    js=(ROOT/'dashboard/dist/metric.mjs').read_text().replace("fetch('/api/metric'","fetch('./metric-data.synthetic.json'")
    js=js[:js.index('const events=new EventSource')]+"$('live').textContent='离线快照';\n"
    (ROOT/'examples/metric-view/metric.mjs').write_text(js)
    return {'files':3,'future_histories_or_truth_published':False,'external_model_calls':0,'proposal_id':p['id']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args()
    print(json.dumps(package(Path(a.run).resolve())))
