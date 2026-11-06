"""Reconstruct the unapproved protocol and inputs without any service call."""
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('single_repeat_check_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def check():
    values = p.values()
    if p.read(HERE / 'protocol.json') != values['proposal.json']:
        raise ValueError('Published protocol differs')
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / 'inputs'
        p.prepare(dest)
        p.verify(dest)
        if p.read(dest / 'manifest.json') != p.read(HERE / 'prepared-manifest.json'):
            raise ValueError('Prepared manifest differs')
    return {'status': 'offline_preparation_verified', 'candidate_attempt_cap': 45,
            'static_requests': len(values['static-requests.json']),
            'dynamic_read_slots': len(values['dynamic-rules.json']['slots']),
            'unique_person_cases_per_view': 64, 'answers_per_joint_case': 8,
            'new_model_calls': 0, 'approved': False, 'new_service_authority': False,
            'measured_repeat_results_available': False}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
