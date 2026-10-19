"""One-time seal of the completed offline structural audit; no inference."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from replay_structural_dual import replay

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'runs/structural-dual-benchmark-v1'


def main():
    generated=BASE/'generated';read=lambda p:json.loads(p.read_text())
    plan=read(generated/'plan.synthetic.json');receipt=read(generated/'implementation-freeze.json')
    assert hashlib.sha256((BASE/'design-frozen.json').read_bytes()).hexdigest()==receipt['design_sha256']
    assert (BASE/'design-frozen.json').read_bytes()==(generated/'plan.synthetic.json').read_bytes()
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==sha for n,sha in receipt['implementation_hashes'].items())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==sha for n,sha in plan['sealed_archives'].items())
    splits={split:read(generated/(split+'-report.synthetic.json')) for split in ('development','holdout')}
    keys=('strict_choice','reported_rule_status','completion_choice','possible_outcomes')
    families={};costs={};states={}
    for split,r in splits.items():
        world=read(generated/(split+'-world.synthetic.json'));expected=read(generated/(split+'-expected.synthetic.json'))
        for fid,counts in r['families'].items():
            people=[p for p in world['people'] if p['family']==fid]
            rows=[expected[p['id']][c['public']['id']] for p in people for c in p['cases']]
            applicability={name:True for name in plan['controls']}
            applicability['conflict_reported_unobserved']=any(e['reported_status']=='conflict' or any(x['status']=='conflict' for x in e['possible_outcomes']) for e in rows)
            applicability['invariant_action_loses_unknown']=any(e['reported_status']=='context_unknown' and e['completion_action']!='U' for e in rows)
            applicability['drop_completion_branch']=any(len(e['possible_outcomes'])>1 for e in rows)
            families[fid]=dict(split=split,planned=len(rows),controls=counts,applicability={n:('applicable' if yes else 'not_applicable_no_target_structure') for n,yes in applicability.items()})
        jobs=r['reader_jobs'];costs[split]=dict(
            whole_memories={k:sum(j['whole_memory_lengths'][k] for j in jobs) for k in ('characters','utf8_bytes','actual_local_vocabulary_tokens')},
            canonical_requests={k:sum(j['canonical_request_lengths'][k] for j in jobs) for k in ('characters','utf8_bytes','actual_local_vocabulary_tokens')},
            program_outputs={name:{k:sum(v[k] for v in rows.values()) for k in ('characters','utf8_bytes','actual_local_vocabulary_tokens')} for name,rows in r['complete_program_output_lengths'].items()})
        states[split]=dict(planned=r['planned'],people=r['people'],family_pairs=r['family_pairs'],groups=r['groups'],checks=r['checks'],
            controls={name:{key:score[key]['joint']['correct'] for key in keys} for name,score in r['controls'].items()},
            changing_missing_sensitivity=r['changing_missing_sensitivity'])
    service=read(generated/'service-design.synthetic.json');jobs=service['development_jobs']+service['wrong_person_jobs']+service['holdout_jobs']
    prospective_costs={k:sum(j['canonical_request_lengths'][k] for j in jobs) for k in ('characters','utf8_bytes','actual_local_vocabulary_tokens')}
    annotation=dict(status='delivery_annotation_not_new_score_or_selection',per_family_applicability=families,
        costs=costs,prospective16canonical_request_lengths=prospective_costs,
        tokenizer_note='All memory,request and all10program-output lengths counted by actual frozen local GGUF during original lifecycle; no model inference or service usage. Length is not charged usage or price estimate.',
        statistics='7authored family-pair descriptive strata,not7independent human samples.3development and4structurally disjoint heldout families,now program-audited and consumed. No CI/significance,real-person,cross-provider or compression-win claim.')
    # Independent manipulated-policy gold for the two fixed prospective controls;
    # it remains evaluation-side, never inside a request.
    import sys
    sys.path.insert(0,str(ROOT))
    from runaway import structural_dual as b
    world=read(generated/'development-world.synthetic.json');policies=read(generated/'development-policies.synthetic.json');manipulated={}
    for p in world['people']:
        if p['family']!='overlap_exception_conflict':continue
        manipulated[p['id']]={}
        for c in p['cases']:
            e=b.expected_row(policies[p['twin']],c['public']['domain'],c['context'],c['public']['answer_options'])
            e['completion_action']=c['options'][e['completion_answer']];manipulated[p['id']][c['public']['id']]=e
    with tempfile.TemporaryDirectory() as temporary:
        base=Path(temporary)/'structural-dual';source=base/'frozen-source'
        for name,sha in receipt['implementation_hashes'].items():
            target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        for p in generated.glob('*.json'):
            target=source/'examples/structural-dual'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        (base/'delivery-annotation.synthetic.json').write_text(json.dumps(annotation,ensure_ascii=False,indent=2)+'\n')
        (base/'prospective-manipulated-expected.synthetic.json').write_text(json.dumps(manipulated,ensure_ascii=False,indent=2)+'\n')
        manifest={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.rglob('*')) if p.is_file()}
        for path in base.rglob('*.json'):
            text=path.read_text()
            assert not any(secret in text for secret in ('/Users/','human_source','access_token','refresh_token'))
        (base/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        replay_result=replay(base)
        archive=ROOT/'examples/structural-dual-evidence.synthetic.zip'
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(base.rglob('*')):
                if p.is_file():z.write(p,'structural-dual/'+str(p.relative_to(base)))
    summary=dict(kind='offline_structural_dual_audit_not_model_quality',splits=states,
        design_sha256=receipt['design_sha256'],structural_audit=read(generated/'structural-audit.synthetic.json'),
        family_annotation=families,complete_lengths=costs,prospective16canonical_request_lengths=prospective_costs,
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),replay=replay_result,
        prospective_calls_max=16,prospective_approval=False,holdout_status='consumed_program_audit_not_fresh_reusable_holdout',
        external_model_calls=0,experimental_service_tokens=0,native_development_usage='Separate host accounting,not0.',
        interpretation=annotation['statistics'])
    raw=json.dumps(summary,ensure_ascii=False,indent=2)+'\n';(ROOT/'examples/structural-dual-results.synthetic.json').write_text(raw);(BASE/'summary.json').write_text(raw)
    print(json.dumps(dict(archive_sha256=summary['archive_sha256'],files=len(manifest),replay=replay_result)))


if __name__=='__main__':main()
