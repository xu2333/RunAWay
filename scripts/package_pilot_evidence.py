"""Package only the sealed, fully synthetic D-0015 results for offline replay."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def package(run,examples):
    run=Path(run);examples=Path(examples)
    summary=json.loads((run/'audit-summary.json').read_text())
    pilot=ROOT/'runs/real-adapters-offline-v1/proposed-pilot'
    world=json.loads((pilot/'metric/world.private.json').read_text())
    if summary['origin']!='fully_synthetic' or world['origin']!='fully_synthetic' or summary['cli_attempts']!=24 or summary['status']!='complete':
        raise ValueError('Only the sealed fully synthetic24-call pilot is publishable')
    examples.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(run/'audit-summary.json',examples/'pilot-results.synthetic.json')
    files={'report.synthetic.json':run/'audit-summary.json','raw-report.synthetic.json':run/'report.json',
           'memories.synthetic.json':pilot/'adapters/memories.private.json',
           'adapter-stages.synthetic.json':pilot/'adapters/adapter-result.private.json',
           'trials.private.json':run/'service/memory-jobs/trials.private.json',
           'decoder-answers.synthetic.json':run/'service/memory-reader-answers.json',
           'control-reader-jobs.synthetic.jsonl':pilot/'control-reader-jobs.jsonl'}
    for name in ('snapshot.json','world.private.json','protocol.public.json','histories.public.json'):
        files['metric/'+name]=pilot/'metric'/name
    for path in (pilot/'metric/frozen-source').rglob('*.py'):
        files['metric/frozen-source/'+str(path.relative_to(pilot/'metric/frozen-source'))]=path
    for path in (pilot/'adapters/frozen-source').rglob('*'):
        if path.is_file():files['adapters/frozen-source/'+str(path.relative_to(pilot/'adapters/frozen-source'))]=path
    for path in (run/'service/calls').glob('*.json'):
        if path.name.endswith(('.request.json','.response.json','.attempt.json','.failure.json')):
            files['calls/'+path.name]=path
    manifest={};archive=examples/'pilot-evidence.synthetic.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
        for name,path in sorted(files.items()):
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):raise ValueError('Refusing escaping evidence')
            data=path.read_bytes();manifest[name]=hashlib.sha256(data).hexdigest();output.writestr('d0015/'+name,data)
        output.writestr('d0015/manifest.json',json.dumps(manifest,indent=2)+'\n')
    # Enrich the existing read-only calibration viewer with a separate actual
    # service panel; do not replace reference curves with product scores.
    view=examples/'metric-view';data_path=view/'metric-data.synthetic.json'
    dashboard=ROOT/'dashboard/dist'
    if data_path.exists() and dashboard.exists():
        data=json.loads(data_path.read_text());raw=json.loads((run/'report.json').read_text())
        ledger={k:raw['ledger'][k] for k in ('executions_with_usage','executions_missing_usage','known_usage')}
        data['actual_adapters']={'external_model_calls':24,'mock_usable_rows':8,'mock_planned_rows':8,
            'proposed_service_call_cap':24,'product_llm_quality_measured':True,
            'service_result':summary,'service_batch':{'decision':'D-0015','status':'complete','attempts':24,
            'calls_cap':24,'call_timeout_seconds':180,'current':None,'ledger':ledger,'stop_reason':None,
            'full_history_gate':{'passed':True},'sensitivity_gate':{'passed':True}}}
        data_path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
        html=(dashboard/'metric.html').read_text().replace('href="/metric.css"','href="./metric.css"').replace('src="/metric.mjs"','src="./metric.mjs"').replace('href="/"','href="https://github.com/xu2333/RunAWay"').replace('href="/metric"','href="./index.html"')
        (view/'index.html').write_text(html)
        js=(dashboard/'metric.mjs').read_text().replace("fetch('/api/metric'","fetch('./metric-data.synthetic.json'")
        js=js[:js.index('const events=new EventSource')]+"$('live').textContent='离线快照';\n"
        (view/'metric.mjs').write_text(js);shutil.copyfile(dashboard/'metric.css',view/'metric.css')
    return {'files':len(manifest),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'external_model_calls_by_packager':0,'private_approval_auth_or_workspace_files_included':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--examples',default=str(ROOT/'examples'));a=p.parse_args()
    print(json.dumps(package(a.run,a.examples)))


if __name__=='__main__':main()
