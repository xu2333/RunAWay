"""Developer-annotated fixed-card projection diagnostic; zero model/reader calls."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load('alias_diagnostic_candidate', HERE / 'candidate.py')
replay = load('alias_diagnostic_replay', HERE.parents[1] / 'scripts/replay_scope_binding.py')
# Post-hoc navigation annotations for one observed bad card, never encoder input.
ANNOTATIONS = ((0, '纸鹤', '松塔', 'm37'), (1, '风铃', '茶杯', 'm38'),
               (2, '青苔', '灯塔', 'm39'), (3, '石榴', '蒲公英', 'm40'))


def build(data):
    record = next(x for x in data['records'] if x['slot'] == 7)
    if (record['kind'], record['profile'], record['method'], record['budget'], record['generation']) != (
            'extract', 'kestrel', 'source-accounted-graph-v1', 1536, 0):
        raise ValueError('Different fixed diagnostic parent')
    original = replay.e.parse_answer(record['raw'])
    sources = data['prepared_files']['sources.json']['kestrel']
    original_files = candidate.base.bind(original, sources, 1536)
    if original_files['prompt.md'] != record['artifact']['prompt']:
        raise ValueError('Original parent changed')
    annotated = copy.deepcopy(original)
    annotated.update(version=candidate.VERSION, object_aliases=[])
    for entry in annotated['source_accounting'].values():
        entry['alias_ids'] = []
    for oi, canonical, alias, sid in ANNOTATIONS:
        source = next(x for x in sources['sources'] if x['id'] == sid)
        key = 'developer_alias_' + str(oi)
        annotated['object_aliases'].append(dict(id=key, object_index=oi, canonical=canonical,
                                               alias=alias, evidence=[dict(source_id=sid, quote=source['text'])]))
        annotated['source_accounting'][sid]['alias_ids'] = [key]
    files = candidate.bind(annotated, sources, 1536)
    before = original_files['profile.private.json']['ledger']['rows']
    after = files['profile.private.json']['ledger']['rows']
    stripped = [{k: v for k, v in row.items() if k != 'object'} for row in before]
    if stripped != [{k: v for k, v in row.items() if k != 'object'} for row in after]:
        raise ValueError('Diagnostic changed a non-object row field')
    return {
        'kind': 'developer_annotated_fixed_parent_alias_projection', 'parent_slot': 7,
        'original_characters': len(record['artifact']['prompt']), 'projected_characters': len(files['prompt.md']),
        'original_prompt': record['artifact']['prompt'], 'projected_prompt': files['prompt.md'],
        'developer_annotations': annotated['object_aliases'],
        'all_four_old_names_literal_in_public': all(alias in files['prompt.md'] for _, _, alias, _ in ANNOTATIONS),
        'nodes_unchanged': annotated['nodes'] == original['nodes'],
        'non_object_ledger_fields_unchanged': True, 'unknowns_unchanged': annotated['unknowns'] == original['unknowns'],
        'new_model_calls': 0, 'automatic_generation_validated': False,
        'reader_recovery_measured': False, 'independent_validation': False,
        'production_default_changed': False,
    }


if __name__ == '__main__':
    replay.check()
    print(json.dumps(build(replay.p.read(replay.DEFAULT)), ensure_ascii=False, indent=2))
