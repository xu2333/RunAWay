"""Reconstruct an unapproved fixed-card diagnostic;no model service."""
import importlib.util
import json
import tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('partial_information_check_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def check():
    if p.read(HERE / 'protocol.json') != p.values()['proposal.json']:
        raise ValueError('Published protocol differs')
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / 'inputs'
        p.prepare(root)
        p.verify(root)
        if p.read(root / 'manifest.json') != p.read(HERE / 'prepared-manifest.json'):
            raise ValueError('Prepared manifest differs')
    return {'status': 'offline_preparation_verified', 'candidate_attempt_cap': 37,
            'static_requests': 37, 'new_extractions': 0, 'fixed_existing_cards': 8,
            'all_cases_per_view': 64, 'primary_partial_cases_per_view': 48,
            'primary_known': 16, 'primary_unknown': 32, 'complete_anchor_cases': 16,
            'answers_per_joint_case': 8, 'new_model_calls': 0,
            'approved': False, 'new_service_authority': False, 'measured_results_available': False}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
