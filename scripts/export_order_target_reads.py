"""Export reviewed synthetic fixed-view evidence,excluding local grants/envelopes."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


shared=load('order_read_export_shared',ROOT/'scripts/export_compression_stability.py')
replay=load('order_read_export_replay',ROOT/'scripts/replay_order_target_reads.py')


def export(root):
    p=replay.engine.plan;inputs=p.inputs()
    return shared.export(Path(root),replay_fn=replay.replay,kind=replay.KIND,record_fields=('method','view_sha256'),
        extra={'fixed_views':p.views(),'source_derivation_sha256':p.sha(p.derived.DEFAULT),
            'post_hoc_case_informed_developer_annotation':True,'fresh_generation_stability_test':False,
            'semantic_decomposition_independently_accepted':False,'old_semantic_equivalence_verified':False,
            'validates_h93_or_development':False,'legacy_rows':inputs['legacy_rows'],'disputed_rows':inputs['disputed_rows']})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=replay.DEFAULT);args=parser.parse_args()
    text,result=export(args.run.resolve())
    with args.out.open('x',encoding='utf-8') as f:f.write(text)
    with args.out.with_suffix('.sha256').open('x') as f:f.write(replay.engine.plan.sha(args.out)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
