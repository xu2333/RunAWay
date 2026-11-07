"""Source-accounted scope aliases; an unmeasured repair candidate, not a default."""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('alias_accounted_base', HERE.parent / 'source-accounted-encoding-v1/candidate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
b = base.b
VERSION = 'scope_alias_accounted_graph_v1'
GUIDANCE = '''额外保留“选择归属于谁”的信息：no_choice只表示没有新的动作选择，不表示该消息可从记忆删除。
用户明确说旧名、新名仍指同一项时，在object_aliases输出同范围关系：id、object_index、canonical、alias、evidence。canonical必须是该objects名称中原样出现的当前名称，alias是同一范围的其它来源名称；同一个用户引文须同时包含两者。不要把跨项目相似、助手建议、示例引用、所有权转移或用户否认的同一关系当成改名。没有明确同一范围关系就不造alias。
source_accounting每条增加alias_ids：列出该条用户消息直接支持的所有同范围关系ID，没有则空。直接选择/指代确认继续分别保存其node_ids；改名消息通常仍是no_choice但alias_ids非空。每个关系的全部证据来源必须反向列出它，不能只在reason里描述关系就结束。reason和证据是私有核对材料，不会给读卡者看。
编译器会将alias无损加入对应公开对象名称；不从私有reason猜名称，不给读卡者另附解码表。关系不改变已有选择、条件、问题、优先级、改口链、事实边界或未知边界。保留全部必要的旧名称，不为节省预算删掉它们；完整公开字符上限不变，超限直接失败。程序只核对来源角色、逐字名称/引文、双向引用、归属冲突和公开投影，不证明同一关系的语义或已找齐全部关系。'''


def schema(sources):
    result = base.schema(sources)
    result['properties']['version']['enum'] = [VERSION]
    relation = b.obj({
        'id': b.txt(96),
        'object_index': {'type': 'integer', 'minimum': 0, 'maximum': 11},
        'canonical': b.txt(40), 'alias': b.txt(40),
        'evidence': b.arr(copy.deepcopy(b.ANCHOR), 1, 2),
    })
    result['properties']['object_aliases'] = b.arr(relation, 0, 24)
    result['required'].append('object_aliases')
    for entry in result['properties']['source_accounting']['properties'].values():
        entry['properties']['alias_ids'] = b.arr(b.txt(96), 0, 24)
        entry['required'].append('alias_ids')
    return result


def make_request(sources, budget=1536):
    request = base.make_request(sources, budget)
    request['schema'] = schema(sources)
    request['prompt'] = GUIDANCE + '\n' + request['prompt']
    return request


def project(answer, sources):
    """Project checked model-declared relations; never infer them from prose."""
    b.check(answer, schema(sources))
    b.validate_sources(sources)
    index = {s['id']: (i, s) for i, s in enumerate(sources['sources'])}
    relations = {row['id']: row for row in answer['object_aliases']}
    if len(relations) != len(answer['object_aliases']):
        raise ValueError('Duplicate alias relation ID')
    supporters = {key: set() for key in relations}
    normalized = copy.deepcopy(answer)
    normalized.pop('object_aliases')
    normalized['version'] = base.VERSION
    for sid, entry in normalized['source_accounting'].items():
        ids = entry.pop('alias_ids')
        if len(ids) != len(set(ids)) or any(key not in relations for key in ids):
            raise ValueError('Repeated or undefined source alias relation')
        for key in ids:
            supporters[key].add(sid)
    owners, seen_pairs, additions = {}, set(), {}
    for key, relation in relations.items():
        b.grouped.string(key, 'alias relation ID', 96)
        oi, canonical, alias = relation['object_index'], relation['canonical'], relation['alias']
        b.grouped.string(canonical, 'canonical alias name', 40)
        b.grouped.string(alias, 'source alias name', 40)
        if oi >= len(answer['objects']) or canonical == alias:
            raise ValueError('Undefined alias owner or identical names')
        if canonical not in answer['objects'][oi]:
            raise ValueError('Canonical name absent from original object')
        pair = (oi, canonical, alias)
        if pair in seen_pairs:
            raise ValueError('Duplicate same-scope relation')
        seen_pairs.add(pair)
        b.grouped._anchors(relation['evidence'], index, decisions=True)
        evidence_sources = {anchor['source_id'] for anchor in relation['evidence']}
        if supporters[key] != evidence_sources:
            raise ValueError('Alias evidence and source accounting disagree')
        if not all(canonical in anchor['quote'] and alias in anchor['quote'] for anchor in relation['evidence']):
            raise ValueError('Both names need a literal same-message witness')
        for name in (canonical, alias):
            if name in owners and owners[name] != oi:
                raise ValueError('Alias names claim different object owners')
            if any(name in obj for i, obj in enumerate(answer['objects']) if i != oi):
                raise ValueError('Alias name already labels another object')
            owners[name] = oi
        if alias not in additions.setdefault(oi, []):
            additions[oi].append(alias)
    projections = []
    for oi, aliases in additions.items():
        original = normalized['objects'][oi]
        # Append every relation name literally, even when it occurs as a substring
        # in prose. No semantic inference or substring-based omission is used.
        projected = original + '（又名' + '／'.join(aliases) + '）'
        b.grouped.string(projected, 'alias-expanded object', 40)
        normalized['objects'][oi] = projected
        projections.append({'object_index': oi, 'original': original, 'public': projected, 'aliases': aliases})
    for key in ('nodes', 'unknowns', 'name', 'tagline', 'derived_node_ids'):
        if normalized[key] != answer[key]:
            raise AssertionError('Alias projection changed decision content')
    return normalized, projections


def bind(answer, sources, budget=1536):
    normalized, projections = project(answer, sources)
    files = base.bind(normalized, sources, budget)
    prompt = files['prompt.md']
    # Existing codec escaping is preserved; compare after decoding its wire.
    decoded = base.base.base.graph.dense.decode(prompt)
    for projection in projections:
        if projection['public'] not in decoded:
            raise ValueError('Alias-expanded object missing from public card')
    files['scope-aliases.private.json'] = {
        'version': VERSION, 'answer': copy.deepcopy(answer), 'normalized_graph': normalized,
        'object_projections': projections, 'literal_alias_projection_checked': True,
        'same_scope_semantics_verified': False, 'source_alias_completeness_verified': False,
        'behavioral_fidelity_verified': False, 'production_default_changed': False,
    }
    return files
