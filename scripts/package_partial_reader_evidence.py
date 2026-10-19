"""Seal D-0031 synthetic evidence once. Approval, intent and private runtime stay local."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def package(run,proposal,tokenizer):
    run,proposal=Path(run),Path(proposal);p=json.loads((proposal/'proposal.json').read_text())
    aliases={'jobs.json':'jobs.json','gold.private.json':'gold.synthetic.json','design.original.json':'design.original.synthetic.json',
        'world.private.json':'world.synthetic.json','deliveries.private.json':'deliveries.synthetic.json'}
    files={alias:proposal/name for name,alias in aliases.items()}
    files.update({'raw-report.synthetic.json':run/'service/report.json','answers.synthetic.json':run/'service/answers.json'})
    for path in (run/'service/calls').glob('*.json'):
        if path.name.endswith(('.request.json','.response.json','.attempt.json','.failure.json')):files['calls/'+path.name]=path
    for name in p['source_hashes']:files['frozen-source/'+name]=proposal/'frozen-source'/name
    aux='examples/temporal-partial-context/world.synthetic.json';files['frozen-source/'+aux]=proposal/'world.private.json'
    keys=('id','calls_max','stage_caps','models','timeout_seconds','cleanup_waits_seconds','character_budget','token_budget','reasoning','original_design_id',
        'source_hashes','old_archives','forbidden_request_ids','matrix','selection','data_scope','isolation','gates','reporting','cost_boundary','limitations','baseline_program_not_model_quality')
    contract={k:p[k] for k in keys};contract.update(input_aliases=aliases,input_hashes={n:p['input_hashes'][n] for n in aliases},
        withheld_private_input_hashes={'executor-acceptance.json':p['input_hashes']['executor-acceptance.json']},
        withheld_input_reason='Offline acceptance includes local Python/runtime paths; original hash retained, bytes withheld. Private preflight verified all6inputs before execution. Public replay verifies5synthetic inputs; does not claim to authenticate human approval or reconstruct withheld private bytes.',
        auxiliary_input_aliases={aux:'world.private.json'},original_proposal_sha256=hashlib.sha256((proposal/'proposal.json').read_bytes()).hexdigest(),
        tokenizer_sha256=p['tokenizer']['model_sha256'])
    with tempfile.TemporaryDirectory() as temporary:
        base=Path(temporary)
        for name,source in files.items():
            if source.is_symlink() or not source.resolve().is_relative_to(ROOT):raise ValueError('Escaping evidence source')
            target=base/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        (base/'contract.synthetic.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
        result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/replay_partial_reader_evidence.py'),'--base',str(base),'--tokenizer',str(tokenizer)],capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError('Frozen replay failed: '+result.stderr[-3000:])
        data=(json.dumps(json.loads(result.stdout),ensure_ascii=False,indent=2)+'\n').encode();(base/'report.synthetic.json').write_bytes(data)
        manifest={}
        for path in sorted(base.rglob('*')):
            if not path.is_file():continue
            name=str(path.relative_to(base));raw=path.read_bytes()
            if not name.startswith('frozen-source/') and any(x in raw.decode() for x in ('/Users/','human_source','access_token','refresh_token')):raise ValueError('Private metadata in evidence')
            manifest[name]=hashlib.sha256(raw).hexdigest()
        archive=ROOT/'examples/partial-reader-evidence.synthetic.zip'
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
            for name in manifest:z.writestr('d0031/'+name,(base/name).read_bytes())
            z.writestr('d0031/manifest.json',json.dumps(manifest,indent=2)+'\n')
        (ROOT/'examples/partial-reader-results.synthetic.json').write_bytes(data);(run/'audit-summary.json').write_bytes(data)
    return {'files':len(manifest),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'external_model_calls_by_packager':0,
        'private_approval_intent_and_runtime_bytes_exported':False,'original_private_input_hash_retained':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--proposal',required=True);p.add_argument('--tokenizer',required=True);a=p.parse_args()
    print(json.dumps(package(a.run,a.proposal,a.tokenizer)))
