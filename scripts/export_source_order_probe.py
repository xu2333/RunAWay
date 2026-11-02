"""Export reviewed fictional source-order22 evidence without local grant data."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


shared = load('source_order_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('source_order_export_replay', ROOT / 'scripts/replay_source_order_probe.py')


def export(root):
    inputs = replay.engine.plan.inputs()
    extra = {k: inputs[k] for k in ('legacy_rows', 'disputed_rows', 'auxiliary_rows', 'erased_auxiliary_expectation_rows')}
    extra.update(answers_per_primary_case=8, fresh_generations_planned=4,
        independent_reference_acceptance=False, independent_generalization=False,
        validates_h93_or_development=False, semantic_erasure_proven=False, developer_bindings_sent=False,
        source_only_model_generated_annotation=True, primary_auxiliary_packets_separate=True,
        post_hoc_consumed_development_design=True, erased_label_is_card_information_not_source_preference=True)
    return shared.export(Path(root), replay_fn=replay.replay, kind=replay.KIND,
                         record_fields=('method', 'task', 'variant'), extra=extra)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT); args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream: stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream: stream.write(replay.engine.plan.sha(args.out)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
