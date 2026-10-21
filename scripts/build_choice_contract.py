"""Generate the browser reader prefix from the Python contract; no model calls."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runaway.choice_reader import make_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    queries = [{'id': 'q1', 'scenario': 'placeholder', 'options': {'A': 'first', 'B': 'second'}}]
    prefixes = {reader: {mode: make_request('', queries, answer_format=mode, reader_mode=reader)['prompt'].split('\nANSWER_SCHEMA_JSON:\n', 1)[0] for mode in ['label', 'text']} for reader in ['standard', 'coverage']}
    value = {'schema_version': 1, 'prefixes': prefixes['standard'], 'reader_modes': prefixes, 'default_reader_mode': 'standard'}
    target = ROOT / 'web/dist/choice-contract.json'
    content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not target.exists() or target.read_text() != content:
            raise SystemExit('Browser choice contract differs; run scripts/build_choice_contract.py')
        print('Browser choice contract matches Python')
    else:
        target.write_text(content)


if __name__ == '__main__':
    main()
