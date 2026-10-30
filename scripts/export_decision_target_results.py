"""Export the sealed fictional comparison; never invoke a model backend."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runaway.card import canonical


def read(path):
    if path.is_symlink():
        raise ValueError('Symlink evidence refused')
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(run):
    for name in ('manifest.json', 'observation-manifest.json'):
        for rel, expected in read(run / name)['files'].items():
            if sha(run / rel) != expected:
                raise ValueError('Sealed evidence differs: ' + rel)
    state = read(run / 'execution/result.json')
    if state['simulated'] or state['status'] not in ('complete', 'completed_with_invalid_products'):
        raise ValueError('Exporter requires a closed completed comparison')
    fields = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens')
    records = []
    for rec in state['records']:
        folder = run / 'execution' / rec['execution_id']
        request, envelope = read(folder / 'request.json'), read(folder / 'raw-response.json')
        if (hashlib.sha256(canonical(request).encode()).hexdigest() != rec['request_sha256']
                or sha(folder / 'raw-response.json') != rec['raw_response_sha256']
                or not (folder / 'backend-child-intent.json').exists()):
            raise ValueError('Original request/response/child binding differs')
        public = {key: rec[key] for key in ('slot', 'kind', 'profile', 'method', 'repeat', 'key',
                    'execution_id', 'state', 'request_sha256', 'usage')}
        prov = envelope['provenance']
        public.update(request=request, raw=envelope['raw'],
                      raw_text_sha256=hashlib.sha256(envelope['raw'].encode()).hexdigest(),
                      usage_rows=[{k: row[k] for k in fields if k in row} for row in prov['usage']],
                      requested_model=prov['model_requested'], backend=prov['backend'],
                      original_response_envelope_sha256=rec['raw_response_sha256'])
        if rec.get('product_invalid'):
            public['product_invalid'] = True
        if (folder / 'artifact.json').exists():
            if sha(folder / 'artifact.json') != rec['artifact_sha256']:
                raise ValueError('Artifact file binding differs')
            public['card'] = read(folder / 'artifact.json')
        records.append(public)
    data = {'kind': 'actual_decision_target21_consumed_development',
            'all_sources_fictional': True, 'independent_holdout': False,
            'real_person_fidelity_verified': False, 'production_default_changed': False,
            'new_service_authority': False, 'project_goal_complete': False,
            'sources': read(run / 'sources.json'), 'queries': read(run / 'queries.public.json'),
            'reference_rows': read(run / 'reference.consumed-development.private.json')['rows'],
            'cached_v1': read(run / 'cached-v1-cards.json'), 'slots': read(run / 'slots.json'),
            'implementation_sha256': read(run / 'implementation-sha256.json'),
            'source_input_manifest_sha256': sha(run / 'manifest.json'),
            'source_observation_manifest_sha256': sha(run / 'observation-manifest.json'),
            'records': records, 'status': {key: state[key] for key in (
                'status', 'stop', 'scope_closed', 'simulated', 'missing_usage', 'attempt_reservations',
                'local_cli_child_intents', 'unused_slots_expire', 'known_usage', 'skipped',
                'invalid_products', 'control_gates')},
            'provenance_limits': 'Exact requests/raw response text and safe counters retained. Private approval records, machine paths and transport envelopes omitted. Original envelope hashes are provenance only, not public byte reconstructions. Internal RPC retries, served model identity and cancellation are unobservable.'}
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if re.search(r'/Users/|Documents/ChatGPT|Bearer\s+[A-Za-z0-9]|sk-[A-Za-z0-9]{24}|direct-human-', text):
        raise ValueError('Local/private metadata in public export')
    return data, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'benchmarks/decision-targets-v1')
    args = parser.parse_args()
    data, text = export(args.run.resolve())
    spec = importlib.util.spec_from_file_location('export_target_replay', ROOT / 'benchmarks/decision-targets-v1/measured.py')
    measured = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measured)
    result = measured.replay(data)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / 'measured.synthetic.json'
    path.write_text(text, encoding='utf-8')
    (args.out / 'measured.synthetic.sha256').write_text(sha(path) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
