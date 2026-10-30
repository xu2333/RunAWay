"""Offline replay of the closed41scope using its frozen finite controller."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('archive_stability_engine', ROOT / 'benchmarks/compression-stability-v1/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
INPUT_MANIFEST = '658f1178c144dd8a238fcf50b84854446d1e2d071edd616f1e57ba33de2dcee2'
DEFAULT = ROOT / 'benchmarks/compression-stability-v1/measured.synthetic.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def archived_error(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,80}', name), 'Invalid failure type')
    return type(name, (Exception,), {})('Archived failure category; private error text omitted')


def replay(data):
    require(data['kind'] == 'actual_scope_v1_compression_stability41', 'Wrong scope')
    for key in ('new_service_authority', 'production_default_changed', 'independent_holdout', 'real_person_fidelity_verified'):
        require(data[key] is False, 'Unsupported claim: ' + key)
    require(data['all_sources_fictional'] is True, 'Fiction boundary differs')
    inputs = engine.plan.inputs()
    require(data['sources'] == inputs['sources'] and data['queries'] == inputs['queries']
            and data['reference_rows'] == inputs['rows'], 'Source/query/reference differs')
    require(data['implementation_sha256'] == engine.plan.implementation(), 'Frozen implementation differs')
    require(data['slots'] == engine.plan.slots(), 'Planned schedule differs')
    require(data['source_input_manifest_sha256'] == INPUT_MANIFEST, 'Input manifest differs')
    state, records = data['status'], data['records']
    require(state['scope_closed'] is True and state['simulated'] is False, 'Not a closed actual scope')
    require(state['attempt_reservations'] == len(records) <= 41, 'Attempt ledger differs')
    require(state['unused_slots_expire'] == 41-len(records), 'Unused count differs')
    require(len({r['execution_id'] for r in records}) == len(records), 'Duplicate execution')
    require(state['local_cli_child_intents'] == sum(r['local_cli_child_intent'] is True for r in records), 'Child ledger differs')
    position = 0
    validation_errors = []
    def before(slot):
        if position == len(records) and state['stop'] and state['stop'].startswith('pre_call_failure:'):
            raise archived_error(state['stop'].split(':', 1)[1])
        return {'offline_archive_fixture': True}
    def invoke(request, folder, slot):
        nonlocal position
        if position >= len(records):
            validation_errors.append('Replay tried an unrecorded call')
            raise ValueError(validation_errors[-1])
        rec = records[position]
        position += 1
        try:
            require(all(rec[k] == v for k, v in slot.items()), 'Reordered or foreign slot')
            require(rec['execution_id'] == folder.name, 'Execution binding differs')
            require(request == rec['request'] and engine.plan.digest(request) == rec['request_sha256'], 'Request/own artifact differs')
            if rec['raw_present']:
                require(engine.plan.digest(rec['raw']) == rec['raw_value_sha256'], 'Raw response differs')
                require(rec['backend'] == 'codex', 'Unexpected original backend')
            else:
                require(rec['state'] == 'failed', 'Completed record without raw response')
        except (ValueError, KeyError) as exc:
            validation_errors.append(str(exc))
            raise
        prov = {'backend': rec['backend'], 'model_requested': rec['requested_model'], 'usage': rec['usage_rows']}
        if rec['raw_present']:
            return rec['raw'], prov
        exc = archived_error(rec['error_type'])
        if rec['usage_rows'] is not None:
            exc.provenance = prov
        raise exc
    with tempfile.TemporaryDirectory() as temp:
        frozen = Path(temp) / 'inputs'
        engine.plan.prepare(frozen)
        require(engine.plan.sha(frozen / 'manifest.json') == INPUT_MANIFEST, 'Reconstructed frozen package differs')
        destination = Path(temp) / 'archive-replay'
        # The injected archive has no service capability. Usage is copied evidence,
        # while this replay invocation itself is simulated and incurs no model cost.
        result = engine.run(frozen, destination, invoke, before, simulated=True)
        require(not validation_errors, 'Archive validation failed: ' + repr(validation_errors))
        require(position == len(records), 'Original records not all replayed')
        for key in ('status', 'stop', 'invalid_products', 'skipped', 'control_gates', 'attempt_reservations',
                    'known_usage', 'missing_usage', 'scope_closed', 'unused_slots_expire', 'scores'):
            require(result[key] == state[key], 'Controller/scorer ledger differs: ' + key)
        require(len(result['records']) == len(records), 'Replayed attempt count differs')
        keys = ('slot', 'kind', 'profile', 'budget', 'generation', 'read_repeat', 'key', 'execution_id',
                'state', 'request_sha256', 'usage')
        for original, restored in zip(records, result['records']):
            require(all(original[k] == restored[k] for k in keys), 'Restored record differs')
            require(original.get('error_type') == restored.get('error_type'), 'Failure category differs')
            require(bool(original.get('product_invalid')) == bool(restored.get('product_invalid')), 'Invalid product differs')
            artifact = destination / restored['execution_id'] / 'artifact.json'
            if artifact.exists():
                require(original.get('card') == engine.plan.read(artifact), 'Bound artifact differs')
                require(original['artifact_sha256'] == engine.plan.sha(artifact), 'Original artifact bytes differ')
            else:
                require('card' not in original and 'artifact_sha256' not in original, 'Unbound card inserted')
    decoded = {engine.plan.parent(r)+(r['read_repeat'],): engine.parse_answer(r['raw']) for r in records
               if r['kind'] == 'read' and r['state'] == 'completed'}
    losses = []
    for budget in engine.plan.BUDGETS:
        for row in inputs['rows']:
            pid = row['person']
            values = [[[decoded.get((pid, budget, g, repeat), {}).get(q) for q in row['query_ids']]
                       for repeat in (0, 1)] for g in (0, 1)]
            flat = [v for generation in values for reading in generation for v in reading]
            if any(v != row['gold'] for v in flat):
                losses.append({'profile': pid, 'budget': budget, 'case': row['case'], 'gold': row['gold'],
                               'missing': any(v is None for v in flat), 'generations_reads_orders': values})
    return {'actual_original_attempts': len(records), 'actual_original_children': state['local_cli_child_intents'],
            'original_status': state['status'], 'original_stop': state['stop'], 'known_original_usage': state['known_usage'],
            'missing_original_usage': state['missing_usage'], 'invalid_products': state['invalid_products'],
            'skipped_readers': len(state['skipped']), 'scores': result['scores'], 'failed_or_missing_cases': losses,
            'new_model_calls': 0, 'replay_is_simulated_not_a_new_billable_run': True,
            'independent_semantic_validation': False, 'production_default_changed': False,
            'original_inventory_measured': 160, 'original_inventory_remaining': 72}


def check(path=DEFAULT):
    path = Path(path)
    require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
