"""Replay sealed owned-condition evidence with no service or new inference."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


shared = load('owned_archive_helpers', ROOT / 'scripts/replay_compression_stability.py')
engine = load('owned_archive_controller', ROOT / 'benchmarks/owned-conditions-v1/engine.py')
DEFAULT = ROOT / 'benchmarks/owned-conditions-v1/measured.synthetic.json'
INPUT_MANIFEST = '5f367a8265be4fb4cbbcabf61e0247c7b69c4de724e7e16c68df2a425e96f587'
KIND = 'actual_owned_conditions42'
require = shared.require


def replay(data):
    original = engine.plan.inputs()
    require(data['legacy_reference_rows'] == original['legacy_rows'], 'Legacy references differ')
    require(data['disputed_reference_rows'] == original['disputed_rows'], 'Prospective dispute mask differs')
    require(data['disputed_reference_accepted'] is False, 'Unsupported reference acceptance')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=engine.plan.METHODS, axis_name='method', record_fields=('method',))
    # This consumed development comparison adds no cells to the original inventory.
    result.update(original_inventory_measured=232, original_inventory_remaining=0,
                  primary_cases=79, disputed_cases_unscored=1, legacy_cases=80,
                  new_original_inventory_coverage=0, disputed_reference_accepted=False,
                  annotation_semantics_independently_verified=False)
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
