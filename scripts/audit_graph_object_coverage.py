"""Report unused graph objects locally; incidence is not semantic coverage."""
import argparse
import json
from pathlib import Path


def graph_incidence(answer):
    if type(answer) is not dict or type(answer.get('objects')) is not list or type(answer.get('nodes')) is not list:
        raise ValueError('Provide a graph with objects and nodes arrays')
    objects, nodes = answer['objects'], answer['nodes']
    if any(type(label) is not str or not label.strip() for label in objects):
        raise ValueError('Object labels must be nonempty strings')
    references = [[] for _ in objects]
    resolved = {}
    for position, node in enumerate(nodes):
        if type(node) is not dict or type(node.get('id')) is not str or not node['id'] or node['id'] in resolved:
            raise ValueError('Nodes need unique nonempty IDs')
        if node.get('kind') == 'action_revision':
            parent = node.get('parent_id')
            if type(parent) is not str or parent not in resolved or 'object_index' in node:
                raise ValueError('Revision must inherit a previously defined parent object')
            index = resolved[parent]
        elif node.get('kind') == 'base':
            index = node.get('object_index')
        else:
            raise ValueError('Unsupported graph node kind')
        if type(index) is not int or not 0 <= index < len(objects):
            raise ValueError('Node must reference an existing object index')
        resolved[node['id']] = index
        references[index].append(position)
    return {'kind': 'structural_object_node_incidence_only', 'object_labels': objects,
        'object_count': len(objects), 'node_count': len(nodes),
        'referenced_object_indices': [i for i, refs in enumerate(references) if refs],
        'unreferenced_object_indices': [i for i, refs in enumerate(references) if not refs],
        'node_indices_by_object': references,
        'revision_object_inheritance_resolved': True,
        'semantic_coverage_verified': False, 'source_support_verified': False,
        'export_blocked': False, 'automatic_repair': False, 'new_model_calls': 0}


def read_graph(path):
    path = Path(path)
    if path.stat().st_size > 2_000_000:
        raise ValueError('Graph/archive exceeds2MB; explicitly select a smaller input')
    value = json.loads(path.read_text(encoding='utf-8'))
    if type(value) is dict and 'record' in value:
        value = json.loads(value['record']['raw'])
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Raw graph JSON or a single-extraction public snapshot')
    args = parser.parse_args()
    print(json.dumps(graph_incidence(read_graph(args.input)), ensure_ascii=False, indent=2))
