"""Export reviewed synthetic new-source card/tail contrast evidence,excluding local grants."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


shared = load('fresh_contrast_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('fresh_contrast_export_replay', ROOT / 'scripts/replay_fresh_source_contrast.py')


def export(root):
    inputs = replay.engine.plan.inputs()
    return shared.export(Path(root),replay_fn=replay.replay,kind=replay.KIND,record_fields=('method','view'),
        extra={'answers_per_primary_case':8,'fresh_generations_planned':8,'design':inputs['design'],
          'disputed_rows':inputs['disputed_rows'],'legacy_rows':inputs['legacy_rows'],
          'independent_reference_acceptance':False,'independent_generalization':False,
          'encoder_changed_for_new_sources':False,'pair_rescoring_independent':False,
          'token_matched_tail':False,'optimal_tail_selection':False,
          'source_only_model_generated_annotation':True,'development_informed':True,'template_paired_families':True})



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT); args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream: stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream: stream.write(replay.engine.plan.sha(args.out)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
