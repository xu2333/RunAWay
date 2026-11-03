"""Verify authored finite-world inputs and unapproved protocol, without a service."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('epistemic_public_inputs', HERE / 'plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


def artifacts():
    data = plan.inputs()
    return {'sources.synthetic.json': data['sources'], 'questions.public.json': data['queries'],
            'author-reference.synthetic.json': data['rows'],
            'author-parameters.synthetic.json': data['author_parameters'],
            'design.json': data['design'], 'protocol.json': plan.values()['proposal.json'],
            'calibration.synthetic.json': calibration()}


def calibration():
    """Construct failure styles, not model responses or measurements."""
    data = plan.inputs()
    w = plan.corpus
    answers = {'reference_vector': [], 'always_unknown': [],
               'direct_observations_only': [], 'ignore_guarantee_withdrawal': []}
    cases = {c['id']: c for c in w.case_specs()}
    for row in data['rows']:
        case = cases[row['case']]
        stale = 'U'
        if case['domain'] is not None:
            evidence = data['author_parameters'][row['person']]['public_evidence'][case['domain']]
            value = w.oracle({'guarantee': True, 'observations': evidence['observations']}, case)
            if value != 'U':
                stale = w.DOMAINS[case['domain']][2][value]
        answers['reference_vector'].append(row['gold'])
        answers['always_unknown'].append('U')
        answers['direct_observations_only'].append(row['gold'] if row['cohort'] == 'observed_decision' else 'U')
        answers['ignore_guarantee_withdrawal'].append(stale)
    return {'kind': 'constructed_instrument_calibration_not_model_fidelity',
            'new_model_calls': 0, 'planned_cases_per_vector': 120,
            'vectors': {name: {'correct': sum(a == r['gold'] for a, r in zip(vector, data['rows'])),
                'known_correct': sum(a == r['gold'] for a, r in zip(vector, data['rows']) if r['gold'] != 'U'),
                'unknown_correct': sum(a == r['gold'] for a, r in zip(vector, data['rows']) if r['gold'] == 'U')}
                for name, vector in answers.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for name, value in artifacts().items():
        path = HERE / name
        text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.write:
            path.write_text(text, encoding='utf-8')
        elif path.read_text(encoding='utf-8') != text:
            raise ValueError('Public artifact differs: ' + name)
    print(json.dumps({'public_fictional_artifacts_verified': True, 'new_model_calls': 0,
                      'approved': False, 'independent_semantic_acceptance': False}, indent=2))


if __name__ == '__main__':
    main()
