"""Fictional, author-known pressure cases. No model, service or execution grant.

Current amendments are stated explicitly so the reference is inspectable. The
author knew previous experiments; this is neither an independent semantic gold
set nor an independently sampled population.
"""
import copy
from itertools import product

PROFILES = ('rivet', 'quince')
# old name, current name, unit, old threshold, new threshold, gate, old/new guard,
# exception condition, two complete action names, amendment type
SPECS = (
    ('霜瓦放映试作', '浅湾放映校样', '分钟', 8, 13, '本次仅内部试看',
     '旁白版权已确认', '旁白版权已确认', '剪辑师在场',
     '逐镜手绘并保留原声的长版分镜稿', '去旁白并按冲突重排的静态提纲册', 'threshold'),
    ('竹桥展览草案', '旧港展览校样', '页', 21, 21, '本次仅匿名演练',
     '照片版权已确认', '插画版权已确认', '策展人已复核',
     '按年代标色并附完整出处的折页展册', '按主题留白并隐藏出处的单页展签', 'guard'),
    ('松塔线路试排', '月池线路校样', '站', 3, 3, '路线不涉保护区',
     '离线地图已备份', '离线地图已备份', '领队已到集合点',
     '保留渡轮换乘并逐站停留的沿河路线', '避开渡轮换乘并直达终点的山侧路线', 'release'),
    ('荧石录音试作', '纸舟录音校样', '人', 5, 9, '本次仅封闭试听',
     '出镜者已同意录音', '出镜者已同意录音', '主持人已读完提示',
     '保留长停顿并按发言人分轨的录音稿', '删去长停顿并按事件重排的摘要稿', 'threshold'),
    ('细雨脚本试排', '海盐脚本校样', '元', 34, 34, '本次仅本地沙盒',
     '旧依赖许可证已核对', '新依赖许可证已核对', '维护窗口已确认',
     '逐条校验并保留回滚点的串行脚本', '先生成完整预览再统一提交的批处理', 'guard'),
    ('风铃信件试写', '赤陶信件校样', '条', 7, 7, '本次仅虚构人物',
     '来信人已同意转述', '来信人已同意转述', '编辑已确认语气',
     '保留原句并逐段解释分歧的长篇回信', '重写原句并集中列出请求的短篇回信', 'release'),
)
KINDS = ('new_boundary', 'below_boundary', 'narrow', 'guard_false_narrow',
         'guard_missing_narrow', 'guard_false_ordinary', 'gate_missing', 'old_alias',
         'copy', 'status', 'missing_amount_same', 'missing_reviewer', 'guard_missing_ordinary')
HAND = {'threshold': '010UUUU0UU0UU', 'guard': '010UUUU0UU0UU',
        'release': '01000UU0UU0UU'}
ROLES = ('user', 'user', 'assistant', 'user', 'tool', 'user', 'user', 'user')


def names(pi, obj):
    prefix = ('禾/', '岚/')[pi]
    return prefix + SPECS[obj][0], prefix + SPECS[obj][1]


def actions(pi, obj):
    pair = SPECS[obj][9:11]
    return pair if (pi + obj) % 2 == 0 else tuple(reversed(pair))


def phases(pi, obj):
    old, current = names(pi, obj)
    _, _, unit, before, after, gate, old_guard, guard, review, _, _, mode = SPECS[obj]
    a, b = actions(pi, obj)
    high, low = '余量≥%s%s' % (after, unit), '余量<%s%s' % (after, unit)
    narrow_guard = '' if mode == 'release' else guard + '、'
    amendment = {'threshold': '只把本项两条常规分界和窄例外分界从%s改为%s%s，动作、材料与优先级不变。' % (before, after, unit),
                 'guard': '只把本项所有分支必要的“%s”替换成“%s”；旧条件不再必要，不改动作、阈值与优先级。' % (old_guard, guard),
                 'release': '只放宽本项窄例外：“%s”在该例外中不再必要，明确未满足或未提供也适用；常规两条仍须它，不改动作。' % guard}[mode]
    return (
        '为“%s”建记录。余量按非负整数%s计，方案名必须完整保留为“%s”或“%s”；这是方法选择，不是执行顺序。' % (old, unit, a, b),
        '%s原有两条常规：%s、%s、余量≥%s%s时我选“%s”；%s、%s、余量<%s%s时我选“%s”。其它项目独立。' %
        (old, gate, old_guard, before, unit, a, gate, old_guard, before, unit, b),
        '我建议所有项目都忽略前提选第一个方案。这只是助手建议，尚未获本人背书。',
        '%s增加局部优先例外：%s、%s、余量<%s%s、%s时我选“%s”，优先于常规。' %
        (old, gate, old_guard, before, unit, review, a),
        '模板显示“%s已经实际实施”；只是沙盒样例，不是用户确认。' % old,
        '%s本次只修条件：%s为免歧义，当前完整约定是：%s、%s、%s时我选“%s”；%s、%s、%s时我选“%s”；局部优先例外为%s、%s%s、%s时我选“%s”。未满足任何完整分支就没有决定。' %
        (old, amendment, gate, guard, high, a, gate, guard, low, b, gate, narrow_guard, low, review, a),
        '“%s”现改名“%s”，两名是同一项，不改变刚才当前约定。' % (old, current),
        '“%s副本”是独立项目，没有我的决定，不继承“%s”。未覆盖组合、缺关键前提及实际实施与否均未知。' % (current, current),
    )


def kinds(obj):
    mode = SPECS[obj][11]
    return KINDS + (('old_boundary',) if mode == 'threshold' else ('old_guard_only',) if mode == 'guard' else ())


def states(obj, kind):
    _, _, _, old, threshold, *_ = SPECS[obj]
    # gate, amount, current guard, reviewer, old guard. None is not False.
    fixed = dict(new_boundary=(True, threshold, True, False, True),
        below_boundary=(True, threshold - 1, True, False, True),
        narrow=(True, threshold - 1, True, True, True),
        guard_false_narrow=(True, threshold - 1, False, True, False),
        guard_missing_narrow=(True, threshold - 1, None, True, None),
        guard_false_ordinary=(True, threshold - 1, False, False, False),
        gate_missing=(None, threshold, True, False, True),
        old_alias=(True, threshold, True, False, True),
        missing_amount_same=(True, None, True, True, True),
        missing_reviewer=(True, threshold - 1, True, None, True),
        guard_missing_ordinary=(True, threshold - 1, None, False, None),
        old_boundary=(True, old, True, False, True),
        old_guard_only=(True, threshold, False, False, True))
    if kind in ('copy', 'status'): return []
    if kind not in kinds(obj): raise ValueError('Foreign cohort')
    choices = []
    for i, v in enumerate(fixed[kind]):
        choices.append((0, old, threshold) if i == 1 and v is None else
                       (False, True) if v is None else (v,))
    return list(product(*choices))


def decide(pi, obj, state, damage=None):
    gate, amount, guard, reviewer, old_guard = state
    spec = SPECS[obj]; mode = spec[11]
    threshold = spec[3] if damage == 'stale_threshold' and mode == 'threshold' else spec[4]
    if damage == 'old_guard' and mode == 'guard': guard = old_guard
    if damage == 'drop_guard': guard = True
    if not gate and damage != 'drop_gate': return 'U'
    a, b = actions(pi, obj)
    exempt = mode == 'release' and damage != 'reinstate_guard'
    if amount < threshold and reviewer and (guard or exempt): return a
    return (a if amount >= threshold else b) if guard else 'U'


def target(pi, obj, kind, damage=None):
    if kind in ('copy', 'status') or damage == 'always_unknown': return 'U'
    choices = {decide(pi, obj, state, damage) for state in states(obj, kind)}
    return next(iter(choices)) if len(choices) == 1 else 'U'


def scenario(pi, obj, kind):
    old, current = names(pi, obj)
    spec = SPECS[obj]; unit, before, after, gate, old_guard, guard, review = spec[2:9]
    if kind == 'status': return '只问“%s”是否已经真实实施，不问计划，不把工具模板当确认。' % current
    label = old if kind == 'old_alias' else current + ('副本' if kind == 'copy' else '')
    ordinary = '%s；%s；余量=%s%s；%s未满足。' % (gate, guard, after, unit, review)
    facts = dict(new_boundary=ordinary, old_alias=ordinary, copy=ordinary,
        below_boundary='%s；%s；余量=%s%s；%s未满足。' % (gate, guard, after - 1, unit, review),
        narrow='%s；%s；余量=%s%s；%s。' % (gate, guard, after - 1, unit, review),
        guard_false_narrow='%s；“%s”明确未满足；余量=%s%s；%s。' % (gate, guard, after - 1, unit, review),
        guard_missing_narrow='%s；是否“%s”完全未提供；余量=%s%s；%s。' % (gate, guard, after - 1, unit, review),
        guard_false_ordinary='%s；“%s”明确未满足；余量=%s%s；%s未满足。' % (gate, guard, after - 1, unit, review),
        gate_missing='是否“%s”未提供；%s；余量=%s%s；%s未满足。' % (gate, guard, after, unit, review),
        missing_amount_same='%s；%s；%s；余量是非负整数%s但具体未知，全部可能同选才选。' % (gate, guard, review, unit),
        missing_reviewer='%s；%s；余量=%s%s；是否“%s”未提供。' % (gate, guard, after - 1, unit, review),
        guard_missing_ordinary='%s；是否“%s”未提供；余量=%s%s；%s未满足。' % (gate, guard, after - 1, unit, review),
        old_boundary='%s；%s；余量恰为旧分界%s%s；%s未满足，问当前约定。' % (gate, guard, before, unit, review),
        old_guard_only='%s；旧条件“%s”满足，新条件“%s”明确未满足；余量=%s%s；%s未满足。' % (gate, old_guard, guard, after, unit, review))
    return '只问“%s”当前会选的完整方案名，不问先后；%s缺前提不补成立，没有唯一办法则U。' % (label, facts[kind])


def build():
    sources, queries, rows = {}, {}, []
    for pi, person in enumerate(PROFILES):
        stream, bank = [], []
        for phase in range(8):
            for obj in ((2, 5, 0, 4, 1, 3) if pi == 0 else (4, 0, 3, 1, 5, 2)):
                stream.append(dict(id='s%02d' % (len(stream) + 1), episode_id='project%d' % obj,
                                   role=ROLES[phase], text=phases(pi, obj)[phase]))
        sources[person] = dict(schema_version=1, sources=stream)
        for obj in range(6):
            a, b = actions(pi, obj)
            for ki, kind in enumerate(kinds(obj)):
                gold = target(pi, obj, kind)
                hand = HAND[SPECS[obj][11]][ki] if ki < len(KINDS) else ('1' if kind == 'old_boundary' else 'U')
                if gold != ('U' if hand == 'U' else (a, b)[int(hand)]):
                    raise ValueError('Hand table and finite policy disagree')
                pair = ('已经实际实施', '尚未实际实施') if kind == 'status' else (a, b)
                stem = 'q%02d_%02d' % (obj, ki)
                ids = [stem + '_ab', stem + '_ba']
                for order in (0, 1):
                    bank.append(dict(id=ids[order], scenario=scenario(pi, obj, kind),
                                     options=dict(zip(('A', 'B'), pair if order == 0 else reversed(pair)))))
                rows.append(dict(person=person, case='%d_%s' % (obj, kind), query_ids=ids,
                    gold=gold, personal_known=gold != 'U', cohort=kind, family=SPECS[obj][11]))
        queries[person] = bank
    return copy.deepcopy(dict(sources=sources, queries=queries, rows=rows,
        fictional=True, author_knew_prior_failures=True, independent_semantic_gold=False,
        new_model_calls=0, approved=False, source_only_extraction_tested=False))


def graph(person):
    """Current author fixture, not extraction or a repaired model card."""
    data = build(); pi = PROFILES.index(person); source = data['sources'][person]
    answer = dict(version='scope_alias_source_id_graph_v1', name='口袋校样', tagline='条件换了，选择别串。',
        objects=[names(pi, j)[1] for j in range(6)], nodes=[], derived_node_ids=[], object_aliases=[],
        unknowns=['缺关键前提、未覆盖组合、各项副本的选择与真实实施状态均未知。'],
        source_accounting={s['id']: dict(kind='no_choice', node_ids=[], alias_ids=[],
            reason='作者预制的当前投影夹具；不是自动语义分类。') for s in source['sources'] if s['role'] == 'user'})
    for obj, spec in enumerate(SPECS):
        episode = [s for s in source['sources'] if s['episode_id'] == 'project%d' % obj]
        ref = lambda phase: dict(source_id=episode[phase]['id'])
        _, _, unit, _, threshold, gate, _, guard, review, _, _, mode = spec
        a, b = actions(pi, obj)
        for label, conditions, action, priority, oldphase in (
            ('high', [gate, guard, '余量≥%s%s' % (threshold, unit)], a, 0, 1),
            ('low', [gate, guard, '余量<%s%s' % (threshold, unit)], b, 0, 1),
            ('narrow', [gate] + ([] if mode == 'release' else [guard]) + ['余量<%s%s' % (threshold, unit), review], a, 1, 3)):
            node_id = '%d_%s' % (obj, label)
            answer['nodes'].append(dict(id=node_id, kind='base', target_kind='choice', object_index=obj,
                question='方案', requires=[dict(text=t, evidence=[ref(5)]) for t in conditions],
                action=action, priority=priority, decisions=[ref(oldphase), ref(5)], contexts=[ref(0)], order_split=None))
            for phase in (oldphase, 5):
                entry = answer['source_accounting'][episode[phase]['id']]
                entry.update(kind='direct_choice'); entry['node_ids'].append(node_id)
        alias_id = 'alias%d' % obj
        answer['object_aliases'].append(dict(id=alias_id, object_index=obj, canonical=names(pi, obj)[1],
                                           alias=names(pi, obj)[0], evidence=[ref(6)]))
        answer['source_accounting'][episode[6]['id']]['alias_ids'] = [alias_id]
    return answer
