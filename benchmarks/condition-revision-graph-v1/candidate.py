"""Experimental condition-only revision edges;no model backend or promotion.

Historical observations remain private and source-accounted. Only the named
active parent is retired; all untouched fields and predicates are inherited.
The model still chooses the edge and its evidence: semantics are not certified.
"""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


original = load('condition_revision_id_base', HERE.parent / 'source-id-initial-encoding-v1/candidate.py')
order = load('condition_revision_order', HERE.parent / 'source-order-v3/candidate.py')
renderer = load('condition_revision_renderer', HERE.parent / 'fresh-direct-768-v1/candidate.py')
owned, dense = order.b, order.graph.dense
VERSION = 'condition_revision_source_id_graph_v1'
EVIDENCE = owned.arr(copy.deepcopy(owned.ANCHOR), 1, 2)
EDIT = owned.obj({'parent_condition': owned.txt(80),
    'replacement': {'anyOf': [{'type': 'null'}, copy.deepcopy(owned.CONDITION)]}})
CONDITION_REVISION = owned.obj({'id': owned.txt(96), 'kind': {'type':'string','enum':['condition_revision']},
    'parent_id': owned.txt(96), 'edits': owned.arr(EDIT, 1, 6),
    'decisions': EVIDENCE, 'contexts': EVIDENCE, 'relation_evidence': EVIDENCE})
GUIDANCE = '''本协议增加condition_revision，覆盖旧协议只会停用“改动作”父节点的局限；其它来源、归属、条件、别名与完整预算规则仍有效。
用户明确只改同一分支的条件、动作不变时，用condition_revision：parent_id指向更早、尚有效的choice节点。edits逐项给parent_condition，须逐字匹配父节点一个已有条件；replacement为替换后完整谓词及来源ID证据，null只删除该条件。未列条件、对象、问题、动作、优先级和执行顺序注释由程序原样继承，不能暗改。当前窄型不支持凭空新增没有替换对象的条件。
只有本次用户明确支持的局部改条件才能连边，relation_evidence给父选择之后、不晚于这次决定的用户更新证据。真正只改动作仍用action_revision，沿用旧的全条件继承。条件与动作同时变化应分别用有各自用户依据的边或保留未知，不伪造中间决定。既往status不能作为更新父节点；改规则不改已发生事实。
旧观察仍留nodes并由原source_accounting关联；新条件更新由自己的条目关联新节点。程序只停用被明确引用的父节点，不按消息ID全局删除同消息的其它分支。若新消息没重述动作名而明确承接既有选择，kind可为contextual_choice；直接重述完整做法才用direct_choice。不要为满足来源记账把已经被明确替换的旧规则另留为当前base；不要把旧观察错标no_choice来躲过记账。
保留数值比较、单位、非负/整数域及其余必要门槛；局部删一个门槛不放宽其它分支。每个关系和编辑的语义仍由你判断，程序只验证结构、来源、时间与字面关联，不证明分类或完整性。不看问题、参考、旧卡、旧响应或得分；不修补或重试。'''


def quoted_schema(sources):
    result = original.base.schema(sources)
    result['properties']['version']['enum'] = [VERSION]
    result['properties']['nodes']['items']['anyOf'].append(copy.deepcopy(CONDITION_REVISION))
    return result


def schema(sources):
    return original._reference_schema(quoted_schema(sources), [s['id'] for s in sources['sources']])


def make_request(sources, budget=1536):
    request = renderer.make_request(sources, budget)
    request['schema'] = schema(sources)
    request['prompt'] = GUIDANCE + '\n' + request['prompt']
    return request


def resolve(answer, sources):
    owned.validate_sources(sources); owned.check(answer, schema(sources))
    index = {s['id']:s for s in sources['sources']}
    result = original._expand(answer, quoted_schema(sources), index, list(index))
    owned.check(result, quoted_schema(sources))
    return result


def materialize(answer, sources):
    """Resolve edits without guessing which historical branch should disappear."""
    owned.validate_sources(sources); owned.check(answer, quoted_schema(sources))
    index = {s['id']:(i,s) for i,s in enumerate(sources['sources'])}
    nodes, inactive, trace = {}, set(), []
    materialized = copy.deepcopy(answer)
    materialized['version'] = original.base.VERSION
    materialized['nodes'] = []
    for raw in answer['nodes']:
        key = raw['id']
        if key in nodes: raise ValueError('Duplicate revision graph node')
        positions = owned.grouped._anchors(raw['decisions'], index, decisions=True)
        owned.grouped._anchors(raw['contexts'], index)
        if raw['kind'] == 'base':
            node = copy.deepcopy(raw)
            root_contexts = node['contexts']
            compiled_contexts = node['contexts']
            supersedes = []
        else:
            parent_id = raw['parent_id']
            if parent_id not in nodes or parent_id in inactive: raise ValueError('Revision parent must be earlier and active')
            parent = nodes[parent_id]; node = copy.deepcopy(parent['node'])
            if node['target_kind'] != 'choice': raise ValueError('A policy revision cannot rewrite past status')
            relation = owned.grouped._anchors(raw['relation_evidence'], index, decisions=True)
            if min(positions) <= max(parent['decision_positions']) or min(relation) <= max(parent['decision_positions']) or max(relation) > max(positions):
                raise ValueError('Revision evidence must follow parent and not follow current decision')
            root_contexts = parent['root_contexts']
            compiled_contexts = owned._unique(root_contexts + raw['contexts'])
            supersedes = list(dict.fromkeys(a['source_id'] for a in parent['node']['decisions']))
            node.update(id=key, decisions=copy.deepcopy(raw['decisions']), contexts=copy.deepcopy(raw['contexts']))
            if raw['kind'] == 'action_revision':
                node.update(action=raw['action'], order_split=copy.deepcopy(raw['order_split']))
            else:
                by_text = {c['text']:c for c in node['requires']}
                changes = {edit['parent_condition']:edit['replacement'] for edit in raw['edits']}
                if len(changes) != len(raw['edits']) or not set(changes) <= set(by_text):
                    raise ValueError('Condition edit must identify a distinct existing parent predicate')
                before = copy.deepcopy(node['requires']); changed = []
                for condition in before:
                    if condition['text'] not in changes: changed.append(condition)
                    elif changes[condition['text']] is not None: changed.append(copy.deepcopy(changes[condition['text']]))
                if [c['text'] for c in changed] == [c['text'] for c in before]:
                    raise ValueError('A condition revision must change a predicate')
                node['requires'] = changed
                # object,question,action,priority and order annotation remain exact.
                for field in ('object_index','target_kind','question','action','priority','order_split'):
                    if node[field] != parent['node'][field]: raise AssertionError('Condition revision changed an inherited field')
                untouched = [c for c in before if c['text'] not in changes]
                if any(c not in changed for c in untouched): raise AssertionError('Condition revision dropped an untouched predicate')
            inactive.add(parent_id)
            trace.append(dict(node=key, parent=parent_id, kind=raw['kind'],
                untouched_fields_inherited_exactly=True, parent_retired_only=True))
        nodes[key] = dict(node=node, root_contexts=copy.deepcopy(root_contexts),
            compiled_contexts=compiled_contexts, supersedes=supersedes, decision_positions=positions)
        materialized['nodes'].append(node)
    # Reuse the old alias ownership and complete per-source observation checks on
    # all historical and current nodes, before selecting the active projection.
    aliased, alias_trace = original.base.project(materialized, sources)
    normalized, supporters = original.base.base.normalize(aliased, sources)
    for node in normalized['nodes']:
        # Validate every historical node's quotes,roles,conditions and annotation;
        # do not apply the30-active-row cap to the private history as a whole.
        order.bind(dict(version=order.VERSION, name=normalized['name'], tagline=normalized['tagline'],
            objects=normalized['objects'], nodes=[node], unknowns=normalized['unknowns']), sources, 16000)
    active = [node for node in normalized['nodes'] if node['id'] not in inactive]
    rows, bindings = [], []
    for node in active:
        state = nodes[node['id']]
        row = dict(object=normalized['objects'][node['object_index']], question=node['question'],
            requires=copy.deepcopy(node['requires']), action=node['action'], priority=node['priority'],
            decisions=copy.deepcopy(node['decisions']), contexts=copy.deepcopy(state['compiled_contexts']),
            supersedes=state['supersedes'])
        if node['order_split'] is not None: bindings.append(dict(row_index=len(rows), **copy.deepcopy(node['order_split'])))
        rows.append(row)
    ledger = dict(version=owned.VERSION, name=normalized['name'], tagline=normalized['tagline'],
                  rows=rows, unknowns=copy.deepcopy(normalized['unknowns']))
    owned.project(ledger, sources)  # The original active-row,scope and condition guards.
    return ledger, bindings, dict(active_node_ids=[n['id'] for n in active],
        retired_node_ids=sorted(inactive), revisions=trace, aliases=alias_trace,
        observed_source_supporters=supporters, edge_semantics_verified=False)


def bind(answer, sources, budget=1536):
    owned.grouped.budget_check(budget)
    resolved = resolve(answer, sources)
    ledger, bindings, trace = materialize(resolved, sources)
    files = order.projection.bind(ledger, sources, bindings, 16000) if bindings else dense.bind(ledger, sources, 16000)
    rendered = renderer.render(files['prompt.md'], budget)
    value = dense.parse(renderer.restore(rendered['prompt']))
    profile = dict(schema_version=1, artifact_type='experimental_condition_revision_profile',
        sources=copy.deepcopy(sources), graph=copy.deepcopy(answer), public_projection=dense.grouped_projection(value),
        budget_characters=budget, edge_semantics_verified=False, behavioral_fidelity_verified=False)
    profile['id'] = dense.digest(dense.canonical(profile))
    files['profile.private.json'] = profile
    files['condition-revision.private.json'] = dict(version=VERSION, answer=copy.deepcopy(answer),
        resolved=resolved, ledger=ledger, bindings=bindings, **trace)
    files['prompt.md'] = rendered['prompt']
    files['portable.json'] = dense.make_expression(rendered['prompt'], profile['id'], VERSION)
    files['encoding.private.json'] = rendered
    files['summary.private.json'].update(status='candidate_unvalidated', characters=len(rendered['prompt']),
        budget_characters=budget, public_layout=rendered['scheme'], behavioral_fidelity_verified=False,
        historical_nodes=len(answer['nodes']), active_nodes=len(trace['active_node_ids']),
        retired_nodes=len(trace['retired_node_ids']), edge_semantics_verified=False)
    return files
