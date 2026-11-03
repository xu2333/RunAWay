"""Counterexample: deleting unused metadata clears a flag without changing memory."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('incidence_invariance_origin', ROOT / 'scripts/replay_extraction_readiness.py')
origin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(origin)
DEFAULT = ROOT / 'benchmarks/fixed-card-fidelity-v1/incidence-invariance.synthetic.json'


def evidence():
    origin.check()
    data = origin.p.read(origin.DEFAULT)
    answer = json.loads(data['record']['raw'])
    original_prompt = data['record']['card']['prompt']
    before = origin.coverage.graph_incidence(answer)
    if before['unreferenced_object_indices'] != [1] or len(answer['objects']) != 2:
        raise ValueError('This counterexample is bound to the observed two-object graph')
    variant = copy.deepcopy(answer)
    del variant['objects'][1]  # fixture-only metadata edit; never written back or sent to a model
    after = origin.coverage.graph_incidence(variant)
    prompt = origin.p.bind(origin.p.slots()[9], variant)['prompt.md']
    if prompt != original_prompt or after['unreferenced_object_indices']:
        raise ValueError('Metadata-only invariance counterexample changed')
    describe = lambda report, text: {'objects': report['object_count'], 'nodes': report['node_count'],
        'unreferenced_object_indices': report['unreferenced_object_indices'],
        'public_characters': len(text), 'public_prompt_utf8_sha256': hashlib.sha256(text.encode()).hexdigest()}
    return {'kind': 'metadata_only_incidence_counterexample_not_model_repair',
        'source_snapshot': str(origin.DEFAULT.relative_to(ROOT)),
        'source_snapshot_sha256': origin.p.sha(origin.DEFAULT),
        'original': describe(before, original_prompt),
        'counterfactual': describe(after, prompt),
        'public_memory_identical': True, 'incidence_flag_cleared': True,
        'counterfactual_passes_existing_structural_binding': True,
        'original_observation_changed': False, 'fixed_reader_requests_changed': False,
        'semantic_fidelity_gain_established': False, 'new_model_calls': 0,
        'new_behavioral_samples': 0, 'automatic_pipeline_repair': False,
        'interpretation': 'An incidence flag is an advisory diagnostic, not a source-completeness or behavioral-fidelity endpoint. Removing unused object metadata can clear it while leaving every public memory byte unchanged.'}


def check():
    value = evidence()
    if DEFAULT.read_text(encoding='utf-8') != json.dumps(value, ensure_ascii=False, indent=2) + '\n':
        raise ValueError('Derived counterexample differs')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        DEFAULT.write_text(json.dumps(evidence(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = check()
    print(json.dumps({k: result[k] for k in ('public_memory_identical', 'incidence_flag_cleared',
        'semantic_fidelity_gain_established', 'new_model_calls')}, indent=2))
