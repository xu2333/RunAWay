"""Offline execution accounting: a request fingerprint is not an execution ID.

Historical identities are explicitly derived from immutable response records,
not asserted to be service IDs. New attempts persist a local UUID before calls.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

from .card import canonical, digest
from .pipeline import write_once

FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
          'output_tokens', 'reasoning_output_tokens')


def start_attempt(path, request_id):
    if path.exists():
        raise ValueError('Unresolved prior attempt; inspect evidence before any retry')
    value = {'schema_version': 1, 'execution_id': 'local-attempt:' + uuid.uuid4().hex,
             'request_id': request_id, 'identity_basis': 'local_uuid_persisted_before_invocation',
             'recorded_at': datetime.now(timezone.utc).isoformat(),
             'state': 'invocation_intent',
             'interpretation': 'Local invocation intent, not proof the service ran or a service response ID.'}
    value['sha256'] = digest(canonical(value))
    write_once(path, value)
    return value


def checked(path):
    if path.is_symlink():
        raise ValueError('Refusing symlink evidence')
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('sha256') != digest(canonical({k: v for k, v in value.items() if k != 'sha256'})):
        raise ValueError('Evidence checkpoint hash mismatch: ' + path.name)
    return value


def validate_attempt(path, execution_id, request_id):
    value = checked(path)
    if not re.fullmatch(r'local-attempt:[0-9a-f]{32}', str(execution_id)):
        raise ValueError('Invalid local attempt ID')
    if value.get('execution_id') != execution_id or value.get('request_id') != request_id:
        raise ValueError('Attempt/result identity mismatch')
    if value.get('identity_basis') != 'local_uuid_persisted_before_invocation':
        raise ValueError('Unknown attempt identity basis')
    return value


def usage(provenance):
    rows = provenance.get('usage')
    if not isinstance(rows, list) or not rows:
        return None
    total = Counter()
    for row in rows:
        if not isinstance(row, dict):
            return None
        if any(type(row.get(k)) is not int or row[k] < 0 for k in ('input_tokens', 'output_tokens')):
            return None
        for k in FIELDS:
            value = row.get(k, 0)
            if type(value) is not int or value < 0:
                return None
            total[k] += value
    result = {k: total[k] for k in FIELDS}
    result['total_tokens'] = result['input_tokens'] + result['output_tokens']
    return result


def collect(root):
    """Validate original checkpoints and group copies without rewriting them.

    Identical historical result records are conservatively deduplicated. Two
    truly separate, byte-identical historical executions cannot be distinguished
    without a pre-existing attempt ID. This is stated rather than guessed.
    """
    root = Path(root).resolve()
    records = {}
    paths = sorted(p for p in root.rglob('*.json')
                   if p.parent.name == 'calls' and p.name.endswith(('.response.json', '.failure.json', '.attempt.json')))
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Evidence escapes root')
        if path.name.endswith('.attempt.json'):
            key = path.name.removesuffix('.attempt.json')
            if any((path.parent / (key + suffix)).exists() for suffix in ('.response.json', '.failure.json')):
                continue
            result = checked(path)
            validate_attempt(path, result['execution_id'], key)
            provenance = {}
            outcome = 'unresolved_invocation_intent'
        else:
            result = checked(path)
            key = result['request_id']
            outcome = 'completed' if path.name.endswith('.response.json') else 'failed'
            provenance = result.get('provenance', {})
        request_path = path.parent / (key + '.request.json')
        if request_path.is_symlink():
            raise ValueError('Refusing symlink request')
        request = json.loads(request_path.read_text(encoding='utf-8'))
        if digest(canonical(request)) != key or not path.name.startswith(key + '.'):
            raise ValueError('Request fingerprint mismatch')
        execution_id = result.get('execution_id')
        if execution_id:
            attempt = validate_attempt(path.parent / (key + '.attempt.json'), execution_id, key)
            basis = attempt['identity_basis']
            recorded_at = attempt['recorded_at']
        else:
            execution_id = 'legacy-response-sha256:' + result['sha256']
            basis = 'retrospective_full_checkpoint_fingerprint_not_service_id'
            recorded_at = None  # Never fabricate historical execution time from mtime.
        artifact = {'path': str(path.relative_to(root)),
                    'bytes_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        body = {'schema_version': 1, 'execution_id': execution_id,
                'identity_basis': basis, 'request_id': key,
                'outcome': outcome, 'recorded_at': recorded_at,
                'result_checkpoint_sha256': result['sha256'],
                'provenance': provenance, 'usage': usage(provenance)}
        if result.get('backend_invoked') is False:
            body['backend_invoked']=False
            body['outcome']='locally_blocked_before_backend'
        prior = records.get(execution_id)
        if prior:
            if {k: v for k, v in prior.items() if k != 'artifacts'} != body:
                raise ValueError('Conflicting records for one execution ID')
            prior['artifacts'].append(artifact)
        else:
            records[execution_id] = {**body, 'artifacts': [artifact]}
    return sorted(records.values(), key=lambda x: x['execution_id'])


def summarize(records):
    by_id = {}
    duplicate_records = 0
    for row in records:
        key = row['execution_id']
        if key in by_id:
            if {k: v for k, v in by_id[key].items() if k != 'artifacts'} != {k: v for k, v in row.items() if k != 'artifacts'}:
                raise ValueError('Conflicting execution accounting records')
            duplicate_records += 1
            continue
        by_id[key] = row
    rows = list(by_id.values())
    total = Counter()
    billable_candidates=[row for row in rows if row.get('backend_invoked') is not False]
    for row in billable_candidates:
        if row['usage'] is not None:
            total.update(row['usage'])
    return {'execution_records': len(rows), 'unique_request_fingerprints': len({r['request_id'] for r in rows}),
            'copied_artifacts_excluded': sum(len(r['artifacts']) - 1 for r in rows) + duplicate_records,
            'locally_blocked_before_backend':len(rows)-len(billable_candidates),
            'executions_with_usage': sum(r['usage'] is not None for r in billable_candidates),
            'executions_missing_usage': sum(r['usage'] is None for r in billable_candidates),
            'outcomes': dict(Counter(r['outcome'] for r in rows)),
            'known_usage': {k: total[k] for k in (*FIELDS, 'total_tokens')},
            'interpretation': 'Known local records, not an invoice. Cache is within input; reasoning is within output. Unresolved attempts and missing usage are not zero. Identical legacy executions may be indistinguishable from copies.'}


def build(root, destination):
    records = collect(root)
    report = summarize(records)
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'records').mkdir()
    for row in records:
        write_once(out / 'records' / (digest(row['execution_id']) + '.execution.json'), row)
    report['records_manifest'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((out / 'records').glob('*.execution.json'))}
    write_once(out / 'summary.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--out', required=True, help='New ledger directory, never the source evidence')
    a = p.parse_args()
    print(json.dumps(build(a.root, a.out), ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
