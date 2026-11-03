"""Rebuild incidence-only diagnostics on two closed public synthetic archives."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('closed_graph_incidence', ROOT / 'scripts/audit_graph_object_coverage.py')
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)
DEFAULT = ROOT / 'benchmarks/extraction-readiness-v1/incidence-inventory.synthetic.json'
SOURCES = ('benchmarks/long-task-probe-v1/measured.synthetic.json',
           'benchmarks/extraction-readiness-v1/measured.synthetic.json')


def inventory():
    archives, total = [], {'graphs': 0, 'objects': 0, 'nodes': 0, 'unreferenced_objects': 0}
    for relative in SOURCES:
        path = ROOT / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != path.with_suffix('.sha256').read_text().strip():
            raise ValueError('Source snapshot checksum differs')
        value = json.loads(path.read_text(encoding='utf-8'))
        records = [value['record']] if 'record' in value else value['records']
        graphs = []
        for record in records:
            if record['kind'] != 'extract' or record['state'] != 'completed' or not record['raw_present']:
                continue
            answer = json.loads(record['raw'])
            report = coverage.graph_incidence(answer)
            missing = report['unreferenced_object_indices']
            graphs.append({'slot': record['slot'], 'profile': record['profile'],
                'objects': report['object_count'], 'nodes': report['node_count'],
                'revision_nodes': sum(n['kind'] == 'action_revision' for n in answer['nodes']),
                'unreferenced_indices': missing,
                'unreferenced_labels': [report['object_labels'][i] for i in missing]})
            for key, count in (('graphs', 1), ('objects', report['object_count']),
                               ('nodes', report['node_count']), ('unreferenced_objects', len(missing))):
                total[key] += count
        archives.append({'path': relative, 'sha256': digest, 'graphs': graphs})
    return {'kind': 'offline_incidence_inventory_of_consumed_graphs', 'archives': archives,
        'summary': total, 'new_model_calls': 0, 'new_behavioral_reads': 0,
        'old_scores_changed': False, 'independent_evidence': False,
        'semantic_coverage_verified': False, 'source_support_verified': False,
        'automatic_repair': False, 'production_default_changed': False}


def check():
    value = inventory()
    expected = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if DEFAULT.read_text(encoding='utf-8') != expected:
        raise ValueError('Derived incidence inventory differs')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        DEFAULT.write_text(json.dumps(inventory(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(check()['summary'], indent=2))
