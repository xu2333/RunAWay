"""Replay closed fixed-parent order-target reads;no service or fresh producer."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


shared=load('order_read_archive_shared',ROOT/'scripts/replay_compression_stability.py')
engine=load('order_read_archive_engine',ROOT/'benchmarks/order-target-read-v1/engine.py')
INPUT_MANIFEST='26a655718cdc1a2dfa974062831f22a1f20a42ee33a98a626fe707f6e42b1038'
KIND='actual_order_target_readonly10'
DEFAULT=ROOT/'benchmarks/order-target-read-v1/measured.synthetic.json'


def replay(data):
    shared.require(data['fixed_views']==engine.plan.views(),'Fixed view/parent differs')
    shared.require(data['source_derivation_sha256']==engine.plan.sha(engine.plan.derived.DEFAULT),'Derivation differs')
    shared.require(data['post_hoc_case_informed_developer_annotation'] is True,'Annotation disclosure differs')
    for key in ('fresh_generation_stability_test','semantic_decomposition_independently_accepted',
                'old_semantic_equivalence_verified','validates_h93_or_development'):
        shared.require(data[key] is False,'Unsupported claim: '+key)
    shared.require(data['legacy_rows']==engine.plan.inputs()['legacy_rows'],'Legacy rows differ')
    shared.require(data['disputed_rows']==engine.plan.inputs()['disputed_rows'],'Disputed mask differs')
    result=shared.replay(data,controller=engine,kind=KIND,input_manifest=INPUT_MANIFEST,
        axes=engine.plan.METHODS,axis_name='method',record_fields=('method','view_sha256'))
    result.update(original_inventory_measured=232,original_inventory_remaining=0,new_original_inventory_coverage=0,
        primary_cases_per_method=23,new_extractions=0,inherited_parent_generations=2,
        fresh_generation_stability_test=False,post_hoc_case_informed_developer_annotation=True,
        semantic_decomposition_independently_accepted=False,old_semantic_equivalence_verified=False,
        validates_h93_or_development=False)
    return result


def check(path=DEFAULT):
    path=Path(path)
    shared.require(engine.plan.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT);args=parser.parse_args()
    print(json.dumps(check(args.input),ensure_ascii=False,indent=2))
