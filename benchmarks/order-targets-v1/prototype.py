"""Opt-in counterfactual target separation; no automatic semantic parser."""
import copy
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('order_target_dense', HERE.parent/'owned-dense-v1/codec.py')
dense = importlib.util.module_from_spec(spec); spec.loader.exec_module(dense)
b = dense.base
BINDING = b.obj({'row_index': {'type': 'integer', 'minimum': 0, 'maximum': 29},
    'core_action': b.txt(80), 'core_evidence': b.arr(copy.deepcopy(b.ANCHOR), 1, 2),
    'execution_question': b.txt(40)})
SCHEMA = b.arr(BINDING, 1, 4)


def separate(ledger, sources, bindings):
    """Conserve the complete ordered action on a separate,conditional target.

    Only an explicitly annotated `先`+source-offered label is supported. This
    is not a claim that such a decomposition is semantically right everywhere.
    """
    b.project(ledger, sources); b.check(bindings, SCHEMA)
    original = copy.deepcopy(ledger); result = copy.deepcopy(ledger)
    index = {s['id']: (i, s) for i, s in enumerate(sources['sources'])}
    occupied = {(r['object'], r['question']) for r in ledger['rows']}
    selected, trace = set(), []
    for binding in bindings:
        n = binding['row_index']
        if n in selected or n >= len(ledger['rows']): raise ValueError('Duplicate or undefined row binding')
        selected.add(n)
        row, core = ledger['rows'][n], binding['core_action']
        b.grouped.string(core, 'core action', 80)
        b.grouped._anchors(binding['core_evidence'], index)
        if row['action'] != '先'+core or not any(core in a['quote'] for a in binding['core_evidence']):
            raise ValueError('Only source-bound leading-order decomposition supported')
        q = b.grouped.string(binding['execution_question'], 'execution target', 40)
        target = row['object'], q
        if target in occupied: raise ValueError('Execution target collides with another decision/fact')
        occupied.add(target)
        result['rows'][n]['action'] = core
        note = copy.deepcopy(row)
        note.update(question=q, supersedes=[])
        result['rows'].append(note)
        # All original guards and scope remain on both targets; ordering text
        # is retained exactly,not dropped or interpreted as an executed fact.
        assert note['action'] == row['action'] and note['requires'] == row['requires']
        trace.append({'row_index': n, 'core_action': core, 'execution_question': q,
            'original_ordered_action_retained_exactly': True,
            'all_original_conditions_preserved_on_both_targets': True})
    for n, row in enumerate(original['rows']):
        expected = copy.deepcopy(row)
        if n in selected:
            expected['action'] = next(v['core_action'] for v in bindings if v['row_index'] == n)
        if result['rows'][n] != expected: raise ValueError('Unintended original-row change')
    b.project(result, sources)
    return result, {'bindings': copy.deepcopy(bindings), 'trace': trace,
        'developer_annotation_not_model_inference': True,
        'semantic_decomposition_independently_accepted': False,
        'old_semantic_equivalence_verified': False}


def bind_refactored_v1(ledger, sources, bindings, budget=1536):
    separated, trace = separate(ledger, sources, bindings)
    files = dense.bind(separated, sources, budget)
    files['decomposition.private.json'] = trace
    files['summary.private.json'].update(developer_annotation_not_model_inference=True,
        semantic_decomposition_independently_accepted=False, old_semantic_equivalence_verified=False)
    return files


def bind(ledger, sources, bindings, budget=1536):
    """Keep original public scope placement;only add the annotated target.

    The generic owned-row factorer intentionally unhoists guards across different
    questions. Its v1counterfactual is retained separately. This diagnostic uses
    an explicit source-validated grouped projection to avoid that extra change.
    """
    separated, trace = separate(ledger, sources, bindings)
    grouped, plans = b.project(ledger, sources)
    grouped = copy.deepcopy(grouped)
    original = dense.bind(ledger, sources, budget)
    value = dense.parse(original['prompt.md'])
    for binding in bindings:
        n = binding['row_index']
        gi, ri = next((gi,ri) for gi,plan in enumerate(plans)
                      for ri,member in enumerate(plan['members']) if member['index']==n)
        rule = grouped['groups'][gi]['rules'][ri]
        full = copy.deepcopy(rule)
        rule['choose'] = binding['core_action']
        old_prefix = '所问为'+ledger['rows'][n]['question']
        if not full['when'].startswith(old_prefix): raise ValueError('Original target prefix differs')
        full.update(when='所问为'+binding['execution_question']+full['when'][len(old_prefix):],supersedes=[])
        grouped['groups'][gi]['rules'].append(full)
        public_rule = value['groups'][gi]['rules'][ri]
        note = copy.deepcopy(public_rule)
        public_rule['choose'] = binding['core_action']
        note['question'] = binding['execution_question']
        value['groups'][gi]['rules'].append(note)
    b.grouped.validate_answer(grouped, sources)
    expected = b.grouped.projection(grouped)
    if dense.grouped_projection(value)!=expected: raise ValueError('Explicit grouped projection differs')
    expanded = dense._render(value)
    text, encoding = dense.pack(expanded,budget,prefix=dense.prefix(value))
    if dense.grouped_projection(dense.parse(text))!=expected: raise ValueError('Public target roundtrip differs')
    profile = {'schema_version':1,'artifact_type':'experimental_order_target_profile',
        'sources':copy.deepcopy(sources),'original_ledger':copy.deepcopy(ledger),'ledger':separated,
        'explicit_grouped_projection':expected,'budget_characters':budget,
        'semantic_decomposition_independently_accepted':False,'old_semantic_equivalence_verified':False}
    profile['id']=dense.digest(dense.canonical(profile))
    return {'prompt.md':text,'portable.json':dense.make_expression(text,profile['id'],'order_target_diagnostic_v2'),
        'profile.private.json':profile,'decomposition.private.json':trace,'encoding.private.json':encoding,
        'summary.private.json':{'characters':len(text),'budget_characters':budget,
            'semantic_projection_roundtrip_exact':True,'developer_annotation_not_model_inference':True,
            'semantic_decomposition_independently_accepted':False,'old_semantic_equivalence_verified':False,
            'original_public_scope_placement_preserved':True}}
