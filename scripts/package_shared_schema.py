"""Seal one immutable schema-variant proof, including source v1 dependency."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from replay_shared_schema import replay

ROOT=Path(__file__).resolve().parents[1]


def main():
    data=ROOT/'examples/shared-schema';run=ROOT/'runs/shared-schema-v1';read=lambda p:json.loads(p.read_text())
    design=read(run/'design-frozen.json');report=read(data/'report.synthetic.json')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in design['archive_hashes_before'].items())
    shutil.copyfile(run/'design-frozen.json',data/'design.synthetic.json')
    with tempfile.TemporaryDirectory() as temporary:
        base=Path(temporary)/'shared-schema';source=base/'frozen-source'
        paths=list(sorted((ROOT/'runaway').glob('*.py')))+[ROOT/'tests/test_shared_schema.py',ROOT/'examples/structural-dual-evidence.synthetic.zip']+list(sorted(data.glob('*.json')))
        for path in paths:
            target=source/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        manifest={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.rglob('*')) if p.is_file()}
        for p in base.rglob('*.json'):
            assert not any(secret in p.read_text() for secret in ('/Users/','human_source','access_token','refresh_token'))
        (base/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        replayed=replay(base)
        archive=ROOT/'examples/shared-schema-evidence.synthetic.zip'
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(base.rglob('*')):
                if p.is_file():z.write(p,'shared-schema/'+str(p.relative_to(base)))
    summary={k:report[k] for k in ('totals','savings','request_count','source_archive_sha256','backend_compatibility','model_output_equivalence','token_scope','native_development_usage')}
    summary.update(kind='offline_shared_schema_request_variant',proof_count=16,corpus_cases=590,
        wire_accepted=sum(c['old_accepted'] for c in report['audit']['cases']),score_rejected=sum(c['score']['status']=='rejected' for c in report['audit']['cases']),
        stages={stage:{side:{u:sum(x[side][u] for x in report['whole_request_lengths'] if x['stage']==stage) for u in report['totals'][side]} for side in ('before','after')} for stage in ('development_jobs','wrong_person_jobs','holdout_jobs')},
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),replay=replayed,source_files=len(list((ROOT/'runaway').glob('*.py')))+1,
        unchanged_prior_archives=16,actual_initial_request_recounts=32,subsequent_actual_recounts=0,
        request_file_sha256=hashlib.sha256((data/'requests.synthetic.json').read_bytes()).hexdigest(),review_scope_id=read(data/'review-scope.synthetic.json')['id'],
        review_status='data_and_protocol_review_only; dedicated executor binding/fake acceptance and direct human approval still required',
        prospective_calls_max=16,prospective_approval=False,new_external_model_calls=0,experimental_service_tokens=0)
    raw=json.dumps(summary,ensure_ascii=False,indent=2)+'\n';(ROOT/'examples/shared-schema-results.synthetic.json').write_text(raw);(run/'summary.json').write_text(raw)
    print(json.dumps(dict(archive_sha256=summary['archive_sha256'],files=len(manifest),replay=replayed)))


if __name__=='__main__':main()
