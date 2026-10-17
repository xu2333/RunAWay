"""Export only the development contract and consumed synthetic audit, no future cohort."""
import argparse
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run)
    world=json.loads((run/'contract-v1/fixtures.synthetic.json').read_text())
    audit=json.loads((run/'D0015-trace-audit.synthetic.json').read_text())
    if world['purpose']!='representative_development_fixtures_only' or audit['external_model_calls']!=0:raise ValueError('Only offline development evidence is publishable')
    dest=ROOT/'examples/taste-contract';dest.mkdir(exist_ok=True)
    for name in ('contract.json','fixtures.synthetic.json','calibration.synthetic.json','reader-job-templates.jsonl'):
        shutil.copyfile(run/'contract-v1'/name,dest/name)
    shutil.copyfile(run/'D0015-trace-audit.synthetic.json',dest/'D0015-trace-audit.synthetic.json')
    view=ROOT/'examples/metric-view';data_path=view/'metric-data.synthetic.json';dashboard=ROOT/'dashboard/dist'
    if data_path.is_file() and dashboard.is_dir():
        summary=json.loads((run/'summary.json').read_text())
        if summary['external_model_calls']!=0:raise ValueError('Offline audit must not claim model calls')
        data=json.loads(data_path.read_text());data['actual_adapters']['task_contract_audit']=summary
        data_path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
        html=(dashboard/'metric.html').read_text().replace('href="/metric.css"','href="./metric.css"').replace('src="/metric.mjs"','src="./metric.mjs"').replace('href="/"','href="https://github.com/xu2333/RunAWay"').replace('href="/metric"','href="./index.html"')
        (view/'index.html').write_text(html)
        js=(dashboard/'metric.mjs').read_text().replace("fetch('/api/metric'","fetch('./metric-data.synthetic.json'")
        js=js[:js.index('const events=new EventSource')]+"$('live').textContent='离线快照';\n"
        (view/'metric.mjs').write_text(js);shutil.copyfile(dashboard/'metric.css',view/'metric.css')
    print(json.dumps({'files':5,'future_comparison_inputs_published':False,'external_model_calls':0}))


if __name__=='__main__':main()
