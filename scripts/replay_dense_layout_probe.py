"""Replay closed fixed-parent layout reading with no new service invocation."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


shared = load('dense_read_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('dense_read_archive_engine', ROOT / 'benchmarks/dense-layout-probe-v1/engine.py')
INPUT_MANIFEST = '0f4112ea1edf98f09595187916bad0422170ec2ded864a64a8153255505a5da9'
KIND = 'actual_dense_layout_readonly14'
DEFAULT = ROOT / 'benchmarks/dense-layout-probe-v1/measured.synthetic.json'
require = shared.require


def replay(data):
    require(data['fixed_views'] == engine.plan.views(), 'Fixed view or parent differs')
    require(data['source_derivation_sha256'] == engine.plan.sha(engine.plan.derived.DEFAULT), 'Source derivation differs')
    require(data['expanded_is_uncapped_diagnostic_not_memory_candidate'] is True, 'Diagnostic budget classification differs')
    require(data['fresh_generation_stability_test'] is False, 'Unsupported fresh generation claim')
    require(data['independent_reference_acceptance'] is False, 'Unsupported reference acceptance')
    require(data['validates_j16_or_development'] is False, 'Unsupported cross-source claim')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
        axes=engine.plan.METHODS, axis_name='method', record_fields=('method', 'view_sha256'))
    usage = {m: [] for m in engine.plan.METHODS}
    for r in data['records']:
        if r['kind'] == 'read':
            usage[r['method']].append({'generation': r['generation'], 'repeat': r['read_repeat'], 'usage': r['usage']})
    answers = {engine.plan.parent(r)+(r['read_repeat'],): shared.parse_answer(r['raw'])
               for r in data['records'] if r['kind'] == 'read' and r['state'] == 'completed'}
    agreement = {'planned_paired_question_responses': 320, 'matching': 0, 'differing': 0, 'missing': 0}
    for g in (0, 1):
        for repeat in (0, 1):
            a = answers.get(('h93', 'expanded', g, repeat), {})
            b = answers.get(('h93', 'dense', g, repeat), {})
            for q in engine.plan.inputs()['queries']['h']:
                x, y = a.get(q['id']), b.get(q['id'])
                agreement['missing' if x is None or y is None else 'matching' if x == y else 'differing'] += 1
    result.update(original_inventory_measured=232, original_inventory_remaining=0,
        new_original_inventory_coverage=0, primary_dense_cases=40, new_extractions=0,
        inherited_parent_generations=2, fresh_generation_stability_test=False,
        expanded_is_uncapped_diagnostic_not_memory_candidate=True,
        validates_j16_or_development=False, independent_reference_acceptance=False,
        per_view_reported_usage_not_a_bill=usage, expanded_dense_observed_response_agreement=agreement)
    return result


def check(path=DEFAULT):
    path = Path(path)
    require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
