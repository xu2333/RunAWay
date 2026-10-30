"""Export sealed fictional41scope evidence, excluding private transport data."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stability_export_replay', ROOT / 'scripts/replay_compression_stability.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
p = replay.engine.plan


def export(root):
    for name in ('manifest.json', 'observation-manifest.json'):
        for rel, expected in p.read(root / name)['files'].items():
            path = root / rel
            if path.is_symlink() or p.sha(path) != expected:
                raise ValueError('Sealed evidence differs: ' + rel)
    state = p.read(root / 'execution/result.json')
    if not state['scope_closed'] or state['simulated']:
        raise ValueError('Actual closed scope required')
    fields = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens')
    records = []
    for rec in state['records']:
        folder = root / 'execution' / rec['execution_id']
        req = p.read(folder / 'request.json')
        if p.digest(req) != rec['request_sha256']:
            raise ValueError('Original request differs')
        out = {k: rec[k] for k in ('slot', 'kind', 'profile', 'budget', 'generation', 'read_repeat', 'key',
                'execution_id', 'state', 'request_sha256', 'usage')}
        out.update(request=req, local_cli_child_intent=(folder / 'backend-child-intent.json').exists())
        prov, raw = {}, folder / 'raw-response.json'
        out['raw_present'] = raw.exists()
        if raw.exists():
            if p.sha(raw) != rec['raw_response_sha256']:
                raise ValueError('Original response envelope differs')
            envelope = p.read(raw)
            prov = envelope['provenance']
            out.update(raw=envelope['raw'], raw_value_sha256=p.digest(envelope['raw']),
                       original_response_envelope_sha256=rec['raw_response_sha256'])
        elif (folder / 'failure-provenance.json').exists():
            prov = p.read(folder / 'failure-provenance.json')
        out.update(backend=prov.get('backend'), requested_model=prov.get('model_requested'),
                   usage_rows=[{k: row[k] for k in fields if k in row} for row in prov['usage']]
                   if isinstance(prov.get('usage'), list) else None)
        for key in ('error_type', 'product_invalid', 'artifact_sha256'):
            if key in rec:
                out[key] = rec[key]
        artifact = folder / 'artifact.json'
        if artifact.exists():
            if p.sha(artifact) != rec['artifact_sha256']:
                raise ValueError('Original artifact differs')
            out['card'] = p.read(artifact)
        records.append(out)
    keys = ('status', 'stop', 'invalid_products', 'skipped', 'control_gates', 'attempt_reservations',
            'local_cli_child_intents', 'known_usage', 'missing_usage', 'simulated', 'scope_closed',
            'unused_slots_expire', 'scores')
    data = {'kind': 'actual_scope_v1_compression_stability41', 'all_sources_fictional': True,
            'new_service_authority': False, 'production_default_changed': False,
            'independent_holdout': False, 'real_person_fidelity_verified': False,
            'sources': p.read(root / 'sources.json'), 'queries': p.read(root / 'queries.public.json'),
            'reference_rows': p.read(root / 'reference.consumed-development.private.json')['rows'],
            'slots': p.read(root / 'slots.json'), 'implementation_sha256': p.read(root / 'implementation-sha256.json'),
            'source_input_manifest_sha256': p.sha(root / 'manifest.json'),
            'source_observation_manifest_sha256': p.sha(root / 'observation-manifest.json'),
            'records': records, 'status': {k: state[k] for k in keys},
            'provenance_limits': 'Exact requests/raw values, artifacts and safe counters retained. Private approval records, machine paths, error messages and transport envelopes omitted. Envelope hashes are provenance, not reconstructed bytes. Replay reuses the frozen controller and references; it is not independent semantics, a new service invocation or a bill.'}
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if re.search(r'/Users/|Documents/ChatGPT|Bearer\s+[A-Za-z0-9]|sk-[A-Za-z0-9]{24}|direct-human-', text):
        raise ValueError('Local/private metadata in export')
    result = replay.replay(data)
    return text, result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT)
    args = parser.parse_args()
    text, result = export(args.run.resolve())
    args.out.write_text(text, encoding='utf-8')
    args.out.with_suffix('.sha256').write_text(p.sha(args.out) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
