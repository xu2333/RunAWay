"""Offline counterfactual layouts from both closed budgeted14producer outputs."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


codec = load('dense_derivation_codec', HERE / 'codec.py')
upstream = load('dense_derivation_upstream', ROOT / 'scripts/replay_budgeted_table_probe.py')
DEFAULT = HERE / 'derived.synthetic.json'
p = upstream.engine.plan


def derive():
    upstream.check()
    data = p.read(upstream.DEFAULT)
    sources = data['sources']['h93']
    records = data['records']
    parents = []
    for generation in (0, 1):
        record = next(r for r in records if r['kind'] == 'extract' and r['method'] == 'budgeted-table-v1' and r['generation'] == generation)
        answer = upstream.shared.parse_answer(record['raw'])
        ledger = p.candidate.expand(answer)
        dense = codec.bind(ledger, sources, 1536)
        projected, _ = codec.base.project(ledger, sources)
        expected = codec.base.grouped.projection(projected)
        expanded = codec.base.grouped.render_public(expected)
        assert codec.grouped_projection(codec.parse(dense['prompt.md'])) == expected
        failure = next(v for v in data['status']['invalid_products'] if v['slot'] == record['slot'])
        parents.append({'generation': generation, 'extraction_key': record['key'],
            'raw_value_sha256': record['raw_value_sha256'], 'ledger_sha256': p.digest(ledger),
            'source_sha256': p.digest(sources), 'semantic_projection': expected,
            'original_failure': failure, 'expanded_prompt': expanded,
            'expanded_characters': len(expanded), 'expanded_is_uncapped_diagnostic': True,
            'dense_prompt': dense['prompt.md'], 'dense_characters': len(dense['prompt.md']),
            'dense_encoding': dense['encoding.private.json'],
            'literal_projection_roundtrip_exact': True})
    baselines = [r['card'] for r in records if r['kind'] == 'extract' and r['method'] == 'scope-v1']
    return {'kind': 'offline_owned_dense_derivation_v1', 'all_sources_fictional': True,
        'upstream_snapshot_sha256': p.sha(upstream.DEFAULT),
        'upstream_input_manifest_sha256': data['source_input_manifest_sha256'],
        'upstream_observation_manifest_sha256': data['source_observation_manifest_sha256'],
        'baseline_cards': baselines, 'parents': parents, 'whole_character_ceiling': 1536,
        'actual_new_model_calls': 0, 'replaces_closed_products': False,
        'behavioral_fidelity_verified': False, 'new_service_authority': False,
        'production_default_changed': False}


def replay(data):
    if data != derive():
        raise ValueError('Dense derivation or unsupported claim differs')
    return {'new_model_calls': 0, 'dense_characters': [x['dense_characters'] for x in data['parents']],
        'all_literal_projections_equal': True, 'all_fit1536': True,
        'replaces_closed_products': False, 'behavioral_fidelity_verified': False,
        'independent_semantic_acceptance': False, 'production_default_changed': False}


def check(path=DEFAULT):
    path = Path(path)
    if p.sha(path) != path.with_suffix('.sha256').read_text().strip():
        raise ValueError('Dense derivation checksum differs')
    return replay(p.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        value = derive()
        with DEFAULT.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
        with DEFAULT.with_suffix('.sha256').open('x') as stream:
            stream.write(p.sha(DEFAULT)+'\n')
    print(json.dumps(check(), ensure_ascii=False, indent=2))
