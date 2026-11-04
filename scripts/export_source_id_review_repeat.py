"""Export a sealed seven-slot fixed-card study without private host/grant data."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixed_card_export_replay', ROOT / 'scripts/replay_source_id_review_repeat.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
p = replay.p


def export(root):
    for name in ('manifest.json', 'observation-manifest.json'):
        for rel, expected in p.read(root / name)['files'].items():
            path = Path(rel)
            if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or p.sha(root / path) != expected:
                raise ValueError('Sealed evidence differs')
    state = p.read(root / 'execution/result.json')
    if not state['scope_closed'] or state['simulated']:
        raise ValueError('Closed actual scope required')
    records = []
    fields = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens')
    for rec in state['records']:
        folder = root / 'execution' / ('attempt-%02d' % rec['slot'])
        req = p.read(folder / 'request.json')
        if p.digest(req) != rec['request_sha256']:
            raise ValueError('Original request differs')
        out = {k: rec[k] for k in ('slot', 'kind', 'profile', 'parent', 'review_repeat', 'view', 'read_repeat', 'state', 'usage', 'request_sha256')}
        out.update(request=req, local_cli_child_intent=(folder / 'backend-child-intent.json').exists(),
                   raw_present=(folder / 'raw-response.json').exists())
        provenance = {}
        if out['raw_present']:
            raw = folder / 'raw-response.json'
            if p.sha(raw) != rec['raw_response_sha256']:
                raise ValueError('Original envelope differs')
            envelope = p.read(raw)
            provenance = envelope['provenance']
            out.update(raw=envelope['raw'], raw_value_sha256=p.digest(envelope['raw']),
                       original_response_envelope_sha256=rec['raw_response_sha256'])
        elif (folder / 'failure-provenance.json').exists():
            provenance = p.read(folder / 'failure-provenance.json')
        out.update(backend=provenance.get('backend'), requested_model=provenance.get('model_requested'),
            usage_rows=[{k: row[k] for k in fields if k in row} for row in provenance['usage']]
            if isinstance(provenance.get('usage'), list) else None)
        for field in ('error_type','product_invalid','artifact_sha256'):
            if field in rec:out[field]=rec[field]
        if (folder/'artifact.json').exists():
            if p.sha(folder/'artifact.json')!=rec['artifact_sha256']:raise ValueError('Original artifact differs')
            out['card']=p.read(folder/'artifact.json')
        records.append(out)
    data = {'kind': replay.KIND, 'all_sources_fictional': True, 'posthoc_consumed_fixed_parents': True,
        'source_input_manifest_sha256': p.sha(root / 'manifest.json'),
        'source_observation_manifest_sha256': p.sha(root / 'observation-manifest.json'),
        'intake_protocol': p.read(root / 'proposal.json'), 'slots': p.read(root / 'slots.json'),
        'sources': p.inputs()['sources'], 'queries': p.inputs()['queries'],
        'reference_rows': p.read(root / 'reference.private.json'),
        'parents': p.read(root / 'parents.public.json'),
        'implementation_sha256': p.read(root / 'implementation-sha256.json'),
        'records': records, 'status': {k: v for k, v in state.items() if k != 'records'},
        'provenance_limits': 'Portable input bytes, exact requests/raw values, material, references and safe counters retained. Private grants, machine paths, process IDs, runtime/activation files and transport envelopes omitted. Observation/envelope hashes are provenance, not reconstruction of omitted bytes. Replay is offline, not an independent semantic acceptance, new inference or bill.'}
    for name in ('new_service_authority', 'production_default_changed', 'independent_holdout', 'independent_semantic_acceptance',
                 'generation_stability_verified', 'real_person_fidelity_verified', 'old_scopes_reopened',
                 'old_scores_replaced', 'external_reader_decoder', 'token_matched_tail', 'optimal_tail_selection'):
        data[name] = False
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if re.search(r'/Users/|/private/tmp|Documents/ChatGPT|Bearer\s+[A-Za-z0-9]|sk-[A-Za-z0-9]{24}|direct-human-', text):
        raise ValueError('Private metadata in export')
    return text, replay.replay(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT)
    args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream:
        stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream:
        stream.write(p.sha(args.out) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
