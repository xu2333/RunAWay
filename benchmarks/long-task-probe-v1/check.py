"""Reconstruct public fictional inputs/protocol; no service capability."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('long_task_artifact_plan', HERE / 'plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


def artifacts():
    data = plan.inputs()
    proposal = plan.values()['proposal.json']
    return {'sources.synthetic.json': data['sources'], 'questions.public.json': data['queries'],
            'author-reference.synthetic.json': data['rows'], 'design.json': data['design'],
            'protocol.json': proposal}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for name, value in artifacts().items():
        path = HERE / name
        rendered = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.write:
            path.write_text(rendered, encoding='utf-8')
        elif path.read_text(encoding='utf-8') != rendered:
            raise ValueError('Published artifact drift: ' + name)
    print(json.dumps({'public_artifacts_reconstructed': True, 'new_model_calls': 0,
                      'approved': False, 'new_service_authority': False}, indent=2))


if __name__ == '__main__':
    main()
