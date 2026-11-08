"""Author-known graphs and policy answers for local checks, never model inputs.

This is not extraction, a repaired model card, accepted semantic gold, or a model
fidelity result. The prospective experiment does not use these graph builders.
"""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('direct768_fixture_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def graph(person):
    pi = p.PROFILES.index(person); family = p.corpus.FAMILIES[pi]
    sources = p.inputs()['sources'][person]
    answer = dict(version=p.candidate.VERSION, name='口袋候鸟', tagline='条件随身，名字不串门。',
        objects=list(p.corpus.CURRENT[family]), nodes=[], unknowns=[
            '未覆盖组合、缺演练前提、副本的选择及实际实施情况未知。'],
        derived_node_ids=[], object_aliases=[], source_accounting={
            s['id']: dict(kind='no_choice', node_ids=[], alias_ids=[], reason='作者协议夹具；不是自动提炼或语义验收。')
            for s in sources['sources'] if s['role'] == 'user'})
    for obj in range(p.corpus.OBJECTS):
        episode = [s for s in sources['sources'] if s['episode_id'] == 'project%d' % obj]
        ref = lambda phase: dict(source_id=episode[phase]['id'])
        normal = p.corpus.ACTIONS[p.corpus.BITS[pi][obj]]
        other = p.corpus.ACTIONS[1 - p.corpus.BITS[pi][obj]]
        for label, condition, action in (('high', '剩余≥20分钟', normal), ('low', '剩余<20分钟', other)):
            key = '%d_%s' % (obj, label)
            answer['nodes'].append(dict(id=key, kind='base', target_kind='choice', object_index=obj,
                question='准备办法', requires=[dict(text=t, evidence=[ref(1)])
                    for t in ('仅离线演练', '材料齐备', condition)], action=action, priority=0,
                decisions=[ref(1)], contexts=[ref(0)], order_split=None))
            answer['source_accounting'][episode[1]['id']]['node_ids'].append(key)
        narrow = '%d_narrow' % obj
        conditions = ['仅离线演练'] + (['材料齐备'] if family == 'strict' else []) + ['剩余<20分钟', '复核员在场']
        answer['nodes'].append(dict(id=narrow, kind='base', target_kind='choice', object_index=obj,
            question='准备办法', requires=[dict(text=t, evidence=[ref(3)]) for t in conditions],
            action=other, priority=1, decisions=[ref(3)], contexts=[ref(0)], order_split=None))
        changed = '%d_changed' % obj
        answer['nodes'].append(dict(id=changed, kind='action_revision', parent_id=narrow,
            action=normal, decisions=[ref(5)], contexts=[ref(0)], relation_evidence=[ref(5)], order_split=None))
        for phase, keys in ((1, ['%d_high' % obj, '%d_low' % obj]), (3, [narrow]), (5, [changed])):
            answer['source_accounting'][episode[phase]['id']].update(kind='direct_choice', node_ids=keys)
        alias_id = 'a%d' % obj
        answer['object_aliases'].append(dict(id=alias_id, object_index=obj,
            canonical=p.corpus.CURRENT[family][obj], alias=p.corpus.OLD[family][obj], evidence=[ref(6)]))
        answer['source_accounting'][episode[6]['id']]['alias_ids'] = [alias_id]
    return copy.deepcopy(answer)


def answer_map(person):
    return {q: row['gold'] for row in p.inputs()['rows'] if row['person'] == person for q in row['query_ids']}
