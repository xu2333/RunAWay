"""Reconstruct an unapproved prospective protocol; no service backend."""
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fresh_decision_check_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def check():
    if p.read(HERE / 'protocol.json') != p.values()['proposal.json']:
        raise ValueError('Protocol differs')
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / 'inputs'
        p.prepare(root)
        p.verify(root)
        if p.read(root / 'manifest.json') != p.read(HERE / 'prepared-manifest.json'):
            raise ValueError('Prepared manifest differs')
    return {'status': 'offline_preparation_verified', 'candidate_attempt_cap': 45,
            'fictional_people': 4, 'source_messages': 64, 'static_requests': 13,
            'dynamic_read_slots': 32, 'unique_person_cases_per_view': 64,
            'known': 48, 'unknown': 16, 'joint_answers_per_case': 8,
            'new_model_calls': 0, 'approved': False, 'new_service_authority': False,
            'measured_results_available': False, 'independent_holdout': False}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
