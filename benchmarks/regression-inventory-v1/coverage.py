"""Structural coverage inventory; neither an answer scorer nor service runner."""
from collections import Counter

BINDINGS = ('method_lock_sha256', 'method_sha256', 'source_sha256',
            'extraction_request_sha256', 'query_pair_sha256')
FIELDS = {'case_key', *BINDINGS, 'producer_artifact_sha256', 'read_raw_response_sha256',
          'reported_query_ids', 'evidence_id'}


def assess(requirements, observations, trusted_binding_verifier=None):
    index = {case['case_key']: case for case in requirements}
    if len(index) != len(requirements):
        raise ValueError('Duplicate required case')
    counts = Counter(row['case_key'] for row in observations
                     if type(row) is dict and type(row.get('case_key')) is str)
    accepted, rejected = set(), []
    for number, row in enumerate(observations):
        reasons = []
        key = row.get('case_key') if isinstance(row, dict) else None
        if type(row) is not dict or set(row) != FIELDS:
            reasons.append('observation_fields_differ_no_pass_or_score_receipt')
        elif type(key) is not str:
            reasons.append('case_key_must_be_string')
        elif key not in index:
            reasons.append('case_outside_required_scope')
        else:
            case = index[key]
            if counts[key] != 1:
                reasons.append('duplicate_case_observations_not_selected_posthoc')
            reasons += [name + '_mismatch' for name in BINDINGS if row[name] != case[name]]
            if row['reported_query_ids'] != case['query_ids']:
                reasons.append('both_frozen_option_orders_required')
            for name in ['producer_artifact_sha256', 'read_raw_response_sha256']:
                value = row[name]
                if type(value) is not str or len(value) != 64 or any(ch not in '0123456789abcdef' for ch in value):
                    reasons.append(name + '_invalid')
            if type(row['evidence_id']) is not str or not row['evidence_id'].strip():
                reasons.append('missing_evidence_id')
            if not reasons:
                if trusted_binding_verifier is None:
                    reasons.append('actual_artifact_and_request_binding_verifier_missing')
                elif trusted_binding_verifier(row, case) is not True:
                    reasons.append('actual_artifact_or_request_binding_unverified')
        if reasons:
            rejected.append({'row': number, 'case_key': key, 'reasons': reasons})
        else:
            accepted.add(key)
    return {
        'required_cases': len(index), 'structurally_bound_observed_cases': len(accepted),
        'missing_cases': sorted(set(index) - accepted), 'rejected_observations': rejected,
        'disputed_cases_retained': [case['case_key'] for case in requirements if case['reference_disputed']],
        'all_required_measurements_bound': len(accepted) == len(index),
        'reference_acceptance_or_accuracy_assessed': False,
        'regression_pass_claim': False, 'project_endpoint_proved': False,
        'hashes_or_json_flags_alone_prove_real_inference': False,
        'new_service_authority': False,
    }
