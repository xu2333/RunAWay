"""Replay closed fixed-parent name-marker reads;no service or fresh producer."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


shared=load('named_read_archive_shared',ROOT/'scripts/replay_compression_stability.py')
engine=load('named_read_archive_engine',ROOT/'benchmarks/named-target-diagnostic-v1/engine.py')
INPUT_MANIFEST='dac3794c98c70ad5dea841797f7cc677c725c5f5b250eb392b641fd9e87f21b3'
KIND='actual_named_target_readonly8'
DEFAULT=ROOT/'benchmarks/named-target-diagnostic-v1/measured.synthetic.json'


def replay(data):
    shared.require(data['fixed_views']==engine.plan.views(),'Fixed view/parent differs')
    shared.require(data['upstream46_snapshot_sha256']==engine.plan.sha(engine.plan.fresh.DEFAULT),'Derivation differs')
    shared.require(data['post_hoc_case_informed_developer_annotation'] is True,'Annotation disclosure differs')
    for key in ('fresh_generation_stability_test','semantic_equivalence_independently_accepted',
                'automatic_encoder_fixed','validates_all_fresh48','uniquely_proves_formal_name_cause'):
        shared.require(data[key] is False,'Unsupported claim: '+key)
    shared.require(data['legacy_rows']==engine.plan.inputs()['legacy_rows'],'Legacy rows differ')
    shared.require(data['disputed_rows']==engine.plan.inputs()['disputed_rows'],'Disputed mask differs')
    result=shared.replay(data,controller=engine,kind=KIND,input_manifest=INPUT_MANIFEST,
        axes=(),axis_name='method',record_fields=('method','view_sha256'))
    shared.require(data['answers_per_primary_case']==4 and type(data['answers_per_primary_case']) is int,'Four-answer endpoint differs')
    shared.require(data['inherited_parents']==1 and type(data['inherited_parents']) is int,'One-parent endpoint differs')
    shared.require(data['neutral_equal_character_control'] is True,'Neutral matched wording control differs')
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
        fresh_generation_stability_test=False,post_hoc_case_informed_developer_annotation=True,
        semantic_equivalence_independently_accepted=False,automatic_encoder_fixed=False,validates_all_fresh48=False,
        uniquely_proves_formal_name_cause=False,neutral_equal_character_control=True)

    return result


def check(path=DEFAULT):
    path=Path(path)
    shared.require(engine.plan.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT);args=parser.parse_args()
    print(json.dumps(check(args.input),ensure_ascii=False,indent=2))
