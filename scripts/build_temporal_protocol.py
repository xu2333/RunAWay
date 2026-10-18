"""Build browser protocol constants from the Python product; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
from runaway import temporal as t

ROOT = Path(__file__).resolve().parents[1]


def protocol():
    sources = {'schema_version': 1, 'sources': [{'id': 'protocol', 'episode_id': 'local', 'role': 'user', 'text': 'Protocol fixture.'}]}
    span = t.spans(sources)[0]
    artifact = t.bind({'scope': 'Protocol fixture.', 'events': [], 'unmodeled': [{'span_id': span['id'], 'reason': 'No preference.'}]}, sources)
    return {'version': 1, 'schema': t.SCHEMA, 'instruction_prefix': t.make_request(sources).split('INPUT_JSON:\n', 1)[0],
            'header': t.HEADER, 'validation': artifact['validation'],
            'interpretation': t.render(artifact, 10000)['interpretation'],
            'python_source_sha256': hashlib.sha256((ROOT / 'runaway/temporal.py').read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    path = ROOT / 'web/dist/temporal-protocol.json'
    encoded = json.dumps(protocol(), ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if path.read_text() != encoded:
            raise SystemExit('Browser temporal protocol is stale')
        print('Shared temporal protocol matches Python product')
    else:
        path.write_text(encoded)
