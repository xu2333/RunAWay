"""Offline structural replay of one independent extraction; no behavioral reads."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


engine = load('readiness_public_original', ROOT / 'benchmarks/epistemic-transfer-v1/engine.py')
coverage = load('readiness_object_incidence', ROOT / 'scripts/audit_graph_object_coverage.py')
p = engine.plan
from runaway.constraint_extract import parse_answer, check as check_schema

HERE = ROOT / 'benchmarks/extraction-readiness-v1'
DEFAULT = HERE / 'measured.synthetic.json'
INPUT = '97ab522e0a35cc31f5c1c879eba7bca277ec2d3db163cdd1573d5374e1ef7d13'
REQUEST = 'c850abe00ea49dd98e75f378cb7a6090d185a110c781cfbbdc3bc59ff06dd899'
KIND = 'actual_independent_extraction_readiness1'
PROTOCOL_SHA = 'b08a6f342e8129326b843ee12a748054bfbed7d5bc8b89a2e1acb1d974a02a82'


def require(value, message):
    if not value:
        raise ValueError(message)


def literal_audit(answer, artifact):
    """Exact strings and graph incidence only; aliases and semantics unverified."""
    incidence = coverage.graph_incidence(answer or {'objects': [], 'nodes': []})
    objects = incidence['object_labels']
    used = incidence['referenced_object_indices']
    prompt = artifact['prompt'] if artifact else ''
    return {'kind': 'posthoc_literal_and_node_incidence_not_behavioral_fidelity',
        'object_labels': objects, 'node_count': len(answer['nodes']) if answer else 0,
        'referenced_object_indices': used,
        'unreferenced_object_indices': [i for i in range(len(objects)) if i not in used],
        'public_card_has_exact_domain_name': {d[1]: d[1] in prompt for d in p.corpus.DOMAINS},
        'general_semantic_coverage_verified': False, 'new_model_calls': 0}


def replay(data):
    require(data['kind'] == KIND and data['source_input_manifest_sha256'] == INPUT, 'Wrong scope/input')
    for key in ('new_service_authority', 'production_default_changed', 'fidelity_verified',
                'stability_verified', 'timeout_cause_verified', 'independent_semantic_acceptance',
                'old_scope_reopened', 'old49_scores_replaced', 'real_person_fidelity_verified'):
        require(data[key] is False, 'Unsupported claim: ' + key)
    require(data['all_sources_fictional'] is True, 'Fiction boundary differs')
    require(data['implementation_sha256'] == p.implementation(), 'Implementation drift')
    require(p.sha(HERE / 'protocol.json') == PROTOCOL_SHA, 'Frozen protocol bytes differ')
    protocol = p.read(HERE / 'protocol.json')
    require(data['intake_protocol'] == protocol, 'Protocol drift')
    require(protocol['max_new_local_cli_attempts'] == 1 and protocol['reader_calls'] == 0
            and protocol['follow_on_automatic_calls'] == 0 and protocol['approved'] is False,
            'Frozen one-extraction intake differs')
    require(data['sources'] == {'a8r': p.inputs()['sources']['a8r']}, 'Source differs')
    record, state = data['record'], data['status']
    request = p.request(p.slots()[9])
    require(record['request'] == request and p.digest(request) == REQUEST == record['request_sha256'],
            'Exact original source-only request differs')
    require(record['slot'] == 1 and type(record['slot']) is int and record['kind'] == 'extract'
            and record['profile'] == 'a8r' and record['simulated'] is False, 'Single attempt differs')
    require(record['local_cli_child_intent'] is True and record['timeout_seconds'] == 180
            and record['prompt_sha256'] == p.digest(request['prompt']), 'Bounded child differs')
    usage_rows = record['usage_rows']
    try:
        usage = engine.usage({'usage': usage_rows})
    except ValueError:
        usage = None
    require(usage == record['usage'], 'Usage receipt differs')
    answer, artifact = None, None
    invalid, error_type, product_error = False, None, None
    observed = 'failed'
    if record['raw_present']:
        raw = record['raw']
        require(type(raw) is str and p.digest(raw) == record['raw_value_sha256'], 'Raw differs')
        try:
            if usage is None:
                raise ValueError('Unknown usage')
            if record['backend'] != 'codex' or record['requested_model'] != p.MODEL:
                raise ValueError('Backend/model differs')
            if len(raw.encode()) > 256000:
                raise ValueError('Raw size differs')
            answer = parse_answer(raw)
            check_schema(answer, request['schema'])
            try:
                prompt = p.bind(p.slots()[9], answer)['prompt.md']
                if not 0 < len(prompt) <= 1536:
                    raise ValueError('Whole budget differs')
                artifact = {'profile': 'a8r', 'prompt': prompt, 'characters': len(prompt),
                    'answer_sha256': p.digest(answer), 'source_sha256': p.digest(p.inputs()['sources']['a8r'])}
            except (ValueError, KeyError, TypeError) as exc:
                invalid, product_error = True, type(exc).__name__
            observed = 'completed'
        except Exception as exc:
            error_type = type(exc).__name__
    else:
        require(type(record.get('error_type')) is str
                and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,80}', record['error_type']), 'Failure category differs')
        error_type = record['error_type']
    require(record['state'] == observed and record['product_invalid'] is invalid, 'State/validation differs')
    require(record.get('error_type') == error_type
            and record.get('product_error_type') == product_error, 'Failure category drift')
    if artifact is None:
        require('card' not in record and 'artifact_sha256' not in record, 'Unbound artifact inserted')
    else:
        require(record['card'] == artifact, 'Bound card differs')
        encoded = json.dumps(artifact, ensure_ascii=False, indent=2) + '\n'
        import hashlib
        require(hashlib.sha256(encoded.encode()).hexdigest() == record['artifact_sha256'], 'Artifact bytes differ')
    expected = {'status': 'stopped' if observed == 'failed' else 'completed_with_invalid_product' if invalid else 'complete',
        'scope_closed': True, 'attempt_reservations': 1, 'unused_slots_expire': 0,
        'local_cli_child_intents': 1, 'known_usage': usage, 'missing_usage': int(usage is None),
        'simulated': False, 'new_service_authority': False, 'reader_calls': 0,
        'fidelity_verified': False, 'stability_verified': False, 'old_scope_reopened': False,
        'no_retry_repair_resume_or_replenishment': True}
    require(state == expected, 'Closed result ledger differs')
    audit = literal_audit(answer if observed == 'completed' else None, artifact)
    require(data['literal_audit'] == audit, 'Literal/node audit differs')
    return {**expected, 'card_characters': artifact['characters'] if artifact else None,
        'literal_audit': audit, 'new_model_calls': 0, 'replay_is_offline_not_new_inference': True,
        'original49_timeout_replaced': False}


def check(path=DEFAULT):
    path = Path(path)
    require(p.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(p.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
