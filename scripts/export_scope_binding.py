"""Export only sealed fictional scope-binding51 values;never export grants,runtime or host paths."""
import argparse
import importlib.util
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('single_repeat_export_replay', HERE / 'replay_scope_binding.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
p = r.p


def export(observations, out):
    root, out = Path(observations), Path(out)
    if root.is_symlink() or out.is_symlink() or out.exists() or out.with_suffix('.sha256').exists():
        raise ValueError('Existing or symlink export path refused')
    observation = p.read(root / 'observation-manifest.json')
    if observation['scope_closed'] is not True or observation['new_service_authority'] is not False:
        raise ValueError('Original scope not closed')
    for name, expected in observation['files'].items():
        rel = Path(name)
        file = root / rel
        if rel.is_absolute() or '..' in rel.parts or file.is_symlink() or p.sha(file) != expected:
            raise ValueError('Sealed original observation drift')
    audit = p.read(root / 'execution-audit.json')
    if not (audit['archive_replay_exact'] is True and audit['whole_scientific_source_unchanged'] is True
            and audit['original_intake_unchanged'] is True and audit['new_service_calls_from_audit'] == 0):
        raise ValueError('Original audit not verified')
    p.verify(root / 'inputs')
    if p.sha(root / 'inputs/manifest.json') != r.INPUT:
        raise ValueError('Original scope differs')
    prepared = {name: p.read(root / 'inputs' / name) for name in p.values()}
    state = p.read(root / 'execution/result.json')
    if audit['actual_attempts'] != len(state['records']) or audit['actual_local_cli_children'] != state['local_cli_child_intents']:
        raise ValueError('Original audit counters differ')
    records = []
    for rec in state['records']:
        folder = root / 'execution' / ('attempt-%02d' % rec['slot'])
        assert rec == p.read(folder / 'result.json')
        raw_present = (folder / 'raw-response.json').exists()
        failure_present = (folder / 'failure-provenance.json').exists()
        envelope = p.read(folder / 'raw-response.json') if raw_present else {}
        if raw_present and p.sha(folder / 'raw-response.json') != rec['raw_response_sha256']:
            raise ValueError('Original provider envelope fingerprint differs')
        prov = envelope.get('provenance', p.read(folder / 'failure-provenance.json') if failure_present else {})
        usage_rows = None
        if rec['usage'] is not None:
            fields = ('input_tokens', 'output_tokens', 'cached_input_tokens',
                      'cache_write_input_tokens', 'reasoning_output_tokens')
            usage_rows = [{key: row.get(key, 0) for key in fields} for row in prov['usage']]
            assert r.e.usage({'usage': usage_rows}) == rec['usage']
        artifact = p.read(folder / 'artifact.json') if (folder / 'artifact.json').exists() else None
        records.append({**{key: rec[key] for key in r.SLOT_KEYS},
                        'state': rec['state'], 'error_type': rec.get('error_type'),
                        'request': p.read(folder / 'request.json'),
                        'request_sha256': rec['request_sha256'],
                        'raw_present': raw_present, 'raw': envelope.get('raw'),
                        'raw_value_sha256': p.digest(envelope['raw']) if raw_present else None,
                        'original_response_envelope_sha256': rec.get('raw_response_sha256'),
                        'failure_provenance_present': failure_present,
                        'backend': prov.get('backend', 'codex'),
                        'requested_model': prov.get('model_requested', p.MODEL),
                        'usage': rec['usage'], 'usage_rows': usage_rows,
                        'local_cli_child_intent': (folder / 'backend-child-intent.json').exists(),
                        'artifact': artifact, 'execution_record': r.safe_record(rec)})
    data = {key: False for key in r.FALSE_CLAIMS}
    data.update(kind=r.KIND, scientific_source_ref=r.SOURCE, input_manifest_sha256=r.INPUT,
                source_observation_manifest_sha256=p.sha(root / 'observation-manifest.json'),
                all_sources_fictional=True, prepared_files=prepared, records=records,
                status=r.status(state),
                provenance_limits=r.PROVENANCE_LIMITS)
    report = r.replay(data)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    for pattern in (r'/Users/', r'/private/tmp', r'Documents/ChatGPT', r'Bearer\s+[A-Za-z0-9]',
                    r'sk-[A-Za-z0-9]{20,}', r'call_[A-Za-z0-9]{16,}'):
        if re.search(pattern, text):
            raise ValueError('Private host or grant material in export')
    out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'w') as file:
        file.write(text)
    with out.with_suffix('.sha256').open('x') as file:
        file.write(p.sha(out) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.observations, args.out), ensure_ascii=False, indent=2))
