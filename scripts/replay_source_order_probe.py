"""Replay the closed source-order22 probe, including separate task/variant keys."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


shared = load('source_order_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('source_order_archive_engine', ROOT / 'benchmarks/source-order-probe-v1/engine.py')
INPUT_MANIFEST = '216b49da2fc6300dbc0d3e1d496bd8dc8e273ed762c437b3dc10d0422245c830'
KIND = 'actual_source_order22_generation_probe'
DEFAULT = ROOT / 'benchmarks/source-order-probe-v1/measured.synthetic.json'


def replay(data):
    inputs = engine.plan.inputs()
    for key in ('independent_reference_acceptance', 'independent_generalization',
                'validates_h93_or_development', 'semantic_erasure_proven', 'developer_bindings_sent'):
        shared.require(data[key] is False, 'Unsupported claim: '+key)
    for key in ('source_only_model_generated_annotation', 'primary_auxiliary_packets_separate',
                'post_hoc_consumed_development_design', 'erased_label_is_card_information_not_source_preference'):
        shared.require(data[key] is True, 'Missing limitation/invariant: '+key)
    for key in ('legacy_rows', 'disputed_rows', 'auxiliary_rows', 'erased_auxiliary_expectation_rows'):
        shared.require(data[key] == inputs[key], 'Frozen endpoint differs: '+key)
    shared.require(type(data['answers_per_primary_case']) is int and data['answers_per_primary_case'] == 8,
                   'Primary eight-answer endpoint differs')
    shared.require(type(data['fresh_generations_planned']) is int and data['fresh_generations_planned'] == 4,
                   'Fresh producer count differs')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=(), record_fields=('method', 'task', 'variant'))
    # The shared archive driver replays the complete controller. Its old loss
    # display keys have no task/variant dimension, so derive this display here.
    decoded = {engine.plan.parent(r)+(r['task'], r['variant'], r['read_repeat']):
               shared.parse_answer(r['raw']) for r in data['records']
               if r['kind'] == 'read' and r['state'] == 'completed'}
    losses = []
    for method in engine.plan.METHODS:
        for row in inputs['rows']:
            values = [[[decoded.get((row['person'], method, g, 'primary', 'intact', r), {}).get(q)
                        for q in row['query_ids']] for r in (0, 1)] for g in (0, 1)]
            flat = [v for generation in values for reading in generation for v in reading]
            if any(v != row['gold'] for v in flat):
                losses.append({'profile': row['person'], 'method': method, 'case': row['case'],
                               'gold': row['gold'], 'missing': any(v is None for v in flat),
                               'generations_reads_orders': values})
    result.update(failed_or_missing_cases=losses, answers_per_primary_case=8, fresh_generations_planned=4,
        original_inventory_measured=232, original_inventory_remaining=0, new_original_inventory_coverage=0,
        primary_auxiliary_packets_separate=True, independent_reference_acceptance=False,
        independent_generalization=False, semantic_erasure_proven=False, validates_h93_or_development=False)
    return result


def check(path=DEFAULT):
    path = Path(path)
    shared.require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args(); print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
