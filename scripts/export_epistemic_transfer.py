"""Export sealed fictional source-licensed49 observations without private transport data."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
replay=load('epistemic_export_replay',ROOT/'scripts/replay_epistemic_transfer.py')
base=load('epistemic_safe_export_base',ROOT/'scripts/export_long_task_probe.py')
base.p=replay.engine.plan

def export(root):
 return base._export(Path(root),replay_fn=replay.replay,kind=replay.KIND,
  record_fields=('method','view'),extra={
   'answers_per_primary_case':4,'fresh_generations_planned':8,
   'design':replay.engine.plan.inputs()['design'],'independent_reference_acceptance':False,
   'independent_generalization':False,'generation_stability_verified':False,
   'new_scene_generalization_claim':False,'external_reader_decoder':False,
   'hidden_generating_truth_resolves_unknown':False,'token_matched_tail':False,
   'optimal_tail_selection':False,'encoder_changed_for_new_sources':False,
   'tail_has_json_metadata':False,'source_licensed_finite_inference':True,
   'source_only_model_generated_annotation':True,'full_and_tail_transcript_layout_identical':True})

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--run',type=Path,required=True)
 parser.add_argument('--out',type=Path,default=replay.DEFAULT)
 args=parser.parse_args()
 text,result=export(args.run.resolve())
 with args.out.open('x',encoding='utf8') as f:f.write(text)
 with args.out.with_suffix('.sha256').open('x') as f:f.write(base.p.sha(args.out)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
