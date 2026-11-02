"""Replay closed fixed-memory question-contract reads;no service or fresh producer."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


shared=load('question_contract_archive_shared',ROOT/'scripts/replay_compression_stability.py')
engine=load('question_contract_archive_engine',ROOT/'benchmarks/question-contract-diagnostic-v1/engine.py')
INPUT_MANIFEST='1151d353e2ca3cda9c7d66a37b9093d9266c8fc6e4fc0e0a58151295768909f2'
KIND='actual_question_contract_readonly8'
DEFAULT=ROOT/'benchmarks/question-contract-diagnostic-v1/measured.synthetic.json'


def replay(data):
    shared.require(data['fixed_views']==engine.plan.views(),'Fixed view/parent differs')
    shared.require(data['upstream_named8_snapshot_sha256']==engine.plan.sha(engine.plan.upstream.DEFAULT),'Derivation differs')
    shared.require(data['posthoc_task_clarification'] is True,'Annotation disclosure differs')
    for key in ('fresh_generation_stability_test','semantic_equivalence_independently_accepted',
                'automatic_encoder_fixed','validates_all_fresh48','uniquely_proves_question_wording_cause'):
        shared.require(data[key] is False,'Unsupported claim: '+key)
    shared.require(data['legacy_rows']==engine.plan.inputs()['legacy_rows'],'Legacy rows differ')
    shared.require(data['disputed_rows']==engine.plan.inputs()['disputed_rows'],'Disputed mask differs')
    result=shared.replay(data,controller=engine,kind=KIND,input_manifest=INPUT_MANIFEST,
        axes=(),axis_name='method',record_fields=('method','view_sha256'))
    shared.require(data['answers_per_primary_case']==4 and type(data['answers_per_primary_case']) is int,'Four-answer endpoint differs')
    shared.require(data['inherited_parents']==1 and type(data['inherited_parents']) is int,'One-parent endpoint differs')
    shared.require(data['same_memory_across_conditions'] is True,'Unchanged memory differs')
    shared.require(data['packets_isolated_calls'] is True,'Question packet isolation differs')
    shared.require(data['old_question_gold_replaced'] is False,'Old question/gold replacement claimed')
    shared.require(data['semantic_paraphrase_equivalence_accepted'] is False,'Unsupported semantic equivalence')
    decoded={engine.plan.parent(r)+(r['read_repeat'],):shared.parse_answer(r['raw']) for r in data['records'] if r['kind']=='read' and r['state']=='completed'}
    losses=[]
    for method in engine.plan.METHODS:
        for row in engine.plan.inputs()['rows']:
            values=[[decoded.get(('e0',method,0,r),{}).get(q) for q in row['query_ids']] for r in (0,1)]
            flat=[v for reading in values for v in reading]
            if any(v!=row['gold'] for v in flat):losses.append({'profile':'e0','method':method,'case':row['case'],'gold':row['gold'],
                'missing':any(v is None for v in flat),'reads_orders':values})
    result.update(failed_or_missing_cases=losses,original_inventory_measured=232,original_inventory_remaining=0,new_original_inventory_coverage=0,
        primary_cases_per_method=12,new_extractions=0,inherited_parent_generations=1,answers_per_primary_case=4,
        fresh_generation_stability_test=False,posthoc_task_clarification=True,
        semantic_equivalence_independently_accepted=False,automatic_encoder_fixed=False,validates_all_fresh48=False,
        uniquely_proves_question_wording_cause=False,same_memory_across_conditions=True,
        packets_isolated_calls=True,old_question_gold_replaced=False,semantic_paraphrase_equivalence_accepted=False)
    # Post-hoc application-request audit;not a service-context or semantic proof.
    comparisons=[]
    for kind,repeat in (('none',None),('full',None),('read',0),('read',1)):
        a=next((r for r in data['records'] if r['kind']==kind and r['method']=='original' and r['read_repeat']==repeat),None)
        b=next((r for r in data['records'] if r['kind']==kind and r['method']=='explicit' and r['read_repeat']==repeat),None)
        if a is None or b is None:continue
        x,y=a['request'],b['request']
        comparisons.append({'kind':kind,'repeat':repeat,
            'other_request_fields_equal':{k:v for k,v in x.items() if k!='prompt'}=={k:v for k,v in y.items() if k!='prompt'},
            'prompt_exact_task_substitution_equal':y['prompt'].replace(engine.plan.NEW_TARGET,engine.plan.OLD_TARGET)==x['prompt']})
    previous=engine.plan.read(engine.plan.upstream.DEFAULT)
    historical={r['request_sha256'] for r in previous['records'] if r['kind']=='read' and r['method']=='original'}
    current=[r['request_sha256'] for r in data['records'] if r['kind']=='read' and r['method']=='original']
    result['application_request_audit']={'posthoc_not_semantic_acceptance':True,'packet_comparisons':comparisons,
        'original_read_requests':len(current),'previous_original_digests_match':all(h in historical for h in current) if current else None,
        'served_identity_and_internal_harness_context_verified':False}

    return result


def check(path=DEFAULT):
    path=Path(path)
    shared.require(engine.plan.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT);args=parser.parse_args()
    print(json.dumps(check(args.input),ensure_ascii=False,indent=2))
