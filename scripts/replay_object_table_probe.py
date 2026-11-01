"""Replay the sealed single-source object-table probe without a model service."""
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


shared = load('table_probe_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('table_probe_archive_engine', ROOT / 'benchmarks/object-table-probe-v1/engine.py')
INPUT_MANIFEST = 'df77544e0b338e10c3b5c2dd31999b2cddf8d8d8ac9afc5c9a31b56acd266154'
KIND = 'actual_object_table_h93_probe14'
DEFAULT = ROOT / 'benchmarks/object-table-probe-v1/measured.synthetic.json'
require = shared.require


def replay(data):
    original = engine.plan.inputs()
    require(data['legacy_reference_rows'] == original['legacy_rows'], 'Legacy references differ')
    require(data['disputed_reference_rows'] == [], 'Unexpected reference mask')
    require(data['independent_reference_acceptance'] is False, 'Unsupported reference acceptance')
    require(data['validates_j16_or_development'] is False, 'Unsupported cross-source claim')
    require(data['can_combine_with_older39_into_new79_result'] is False, 'Unsupported combined endpoint')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=engine.plan.METHODS, axis_name='method', record_fields=('method',))
    result.update(original_inventory_measured=232, original_inventory_remaining=0,
        new_original_inventory_coverage=0, primary_cases=40, legacy_cases=40, disputed_cases=0,
        independent_reference_acceptance=False, annotation_semantics_independently_verified=False,
        validates_j16_or_development=False, can_combine_with_older39_into_new79_result=False)
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
