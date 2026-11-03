"""Export one sealed synthetic extraction, omitting private host and grant data."""
import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readiness_export_replay', ROOT / 'scripts/replay_extraction_readiness.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
p = replay.p


def export(root):
    for name in ('manifest.json', 'observation-manifest.json'):
        for rel, expected in p.read(root / name)['files'].items():
            path = Path(rel)
            if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or p.sha(root / path) != expected:
                raise ValueError('Sealed evidence drift')
    state = p.read(root / 'execution/result.json')
    if not state['scope_closed'] or state['simulated']:
        raise ValueError('Closed actual scope required')
    rec, folder = state['record'], root / 'execution/attempt-01'
    request = p.read(folder / 'request.json')
    if p.digest(request) != rec['request_sha256']:
        raise ValueError('Request drift')
    child = p.read(folder / 'backend-child-intent.json')
    out = {k: rec[k] for k in ('slot', 'kind', 'profile', 'request_sha256', 'state', 'usage', 'simulated', 'product_invalid')}
    out.update(request=request, local_cli_child_intent=True, timeout_seconds=child['timeout_seconds'],
               prompt_sha256=child['prompt_sha256'], raw_present=(folder / 'raw-response.json').exists())
    provenance, answer, artifact = {}, None, None
    if out['raw_present']:
        raw = folder / 'raw-response.json'
        if p.sha(raw) != rec['raw_response_sha256']:
            raise ValueError('Original response envelope differs')
        envelope = p.read(raw)
        provenance = envelope['provenance']
        out.update(raw=envelope['raw'], raw_value_sha256=p.digest(envelope['raw']),
                   original_response_envelope_sha256=rec['raw_response_sha256'])
        if (folder / 'answer.json').exists():
            answer = p.read(folder / 'answer.json')
    elif (folder / 'failure-provenance.json').exists():
        provenance = p.read(folder / 'failure-provenance.json')
    fields = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens')
    out.update(backend=provenance.get('backend'), requested_model=provenance.get('model_requested'),
        usage_rows=[{k: r[k] for k in fields if k in r} for r in provenance['usage']]
        if isinstance(provenance.get('usage'), list) else None)
    for name in ('error_type', 'product_error_type'):
        if name in rec:
            out[name] = rec[name]
    if (folder / 'artifact.json').exists():
        artifact = p.read(folder / 'artifact.json')
        if p.sha(folder / 'artifact.json') != rec['artifact_sha256']:
            raise ValueError('Artifact differs')
        out.update(card=artifact, artifact_sha256=rec['artifact_sha256'])
    data = {'kind': replay.KIND, 'all_sources_fictional': True,
        'source_input_manifest_sha256': p.sha(root / 'manifest.json'),
        'source_observation_manifest_sha256': p.sha(root / 'observation-manifest.json'),
        'intake_protocol': p.read(root / 'proposal.json'),
        'implementation_sha256': p.read(root / 'implementation-sha256.json'),
        'sources': {'a8r': p.inputs()['sources']['a8r']}, 'record': out,
        'status': {k: v for k, v in state.items() if k != 'record'},
        'literal_audit': replay.literal_audit(answer, artifact),
        'provenance_limits': 'Exact fictional source, request, raw value, safe counters and card retained. Private grants, machine paths, process IDs, runtime policy and transport envelopes omitted. Original input/observation/envelope hashes are provenance, not reconstructed omitted bytes. Replay verifies public request/schema/binding/usage, not independent semantics, a bill or model behavior.'}
    for name in ('new_service_authority', 'production_default_changed', 'fidelity_verified',
                 'stability_verified', 'timeout_cause_verified', 'independent_semantic_acceptance',
                 'old_scope_reopened', 'old49_scores_replaced', 'real_person_fidelity_verified'):
        data[name] = False
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if re.search(r'/Users/|/private/tmp|Documents/ChatGPT|Bearer\s+[A-Za-z0-9]|sk-[A-Za-z0-9]{24}|direct-human-', text):
        raise ValueError('Private metadata in public export')
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
