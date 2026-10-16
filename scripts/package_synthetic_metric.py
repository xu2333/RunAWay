"""Package an explicitly synthetic calibration and a standalone read-only viewer."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run)
    report=json.loads((run/'report.json').read_text());world=json.loads((run/'world.private.json').read_text())
    if report['origin']!='fully_synthetic' or world['origin']!='fully_synthetic':raise ValueError('Only synthetic calibration can be published')
    examples=ROOT/'examples';examples.mkdir(exist_ok=True)
    shutil.copyfile(run/'report.json',examples/'synthetic-metric-results.synthetic.json')
    target=examples/'synthetic-metric-evidence.synthetic.zip';manifest={}
    snapshot=json.loads((run/'snapshot.json').read_text())
    names=['snapshot.json','world.private.json','histories.public.json','protocol.public.json','compressor-jobs.jsonl','report.json','memories.json','predictions.json','decoder-jobs.jsonl','costs.json']
    names+=['frozen-source/'+name for name in snapshot['code_hashes']]
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            path=run/name
            if path.is_symlink() or not path.resolve().is_relative_to(run.resolve()):raise ValueError('Refusing escaping or symlink evidence')
            name=str(path.relative_to(run));manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest();archive.write(path,'synthetic-metric/'+name)
        archive.writestr('synthetic-metric/manifest.json',json.dumps(manifest,indent=2)+'\n')
    view=examples/'metric-view';view.mkdir(exist_ok=True);dashboard=ROOT/'dashboard/dist'
    if (dashboard/'metric.html').is_file():
        html=(dashboard/'metric.html').read_text().replace('href="/metric.css"','href="./metric.css"').replace('src="/metric.mjs"','src="./metric.mjs"').replace('href="/"','href="https://github.com/xu2333/RunAWay"').replace('href="/metric"','href="./index.html"')
        (view/'index.html').write_text(html)
        js=(dashboard/'metric.mjs').read_text().replace("fetch('/api/metric'","fetch('./metric-data.synthetic.json'")
        js=js[:js.index('const events=new EventSource')] + "$('live').textContent='离线快照';\n"
        (view/'metric.mjs').write_text(js);shutil.copyfile(dashboard/'metric.css',view/'metric.css')
    if not (view/'index.html').is_file():raise ValueError('Missing standalone viewer template')
    data={'available':True,'report':report,'snapshot':json.loads((run/'snapshot.json').read_text()),'people':[{k:person[k] for k in ('id','twin','split','history','queries')} for person in world['people']],
          'memories':json.loads((run/'memories.json').read_text()),'predictions':json.loads((run/'predictions.json').read_text()),'costs':json.loads((run/'costs.json').read_text()),'source':'frozen-synthetic-metric-calibration',
          'warning':'Read-only audit view reveals synthetic answers; never use it as compressor input.'}
    (view/'metric-data.synthetic.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'evidence_files':len(manifest),'evidence_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'viewer':'examples/metric-view/index.html','external_model_calls':0}))


if __name__=='__main__':main()
