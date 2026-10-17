"""Development-only semantic stress tests, never a model or real-person score.

Separate from the sealed taste_contract v1. All control predictions here are
computed from synthetic events; none is inferred from arbitrary model prose.
"""
import argparse
import copy
import json
import random
from pathlib import Path

from .card import canonical, digest
from .pipeline import write_once
from .synthetic_metric_world import active_events

DOMAINS = (
    ('feedback', '反馈', ('直说问题', '先铺垫再提问题'), ('多人在场', '对方要求立刻处理'),
     ('回复合作者的修改稿', '回应小组评审意见')),
    ('planning', '产品验证', ('先做小实验', '先完成整体设计'), ('方向尚未验证', '改动不可撤销'),
     ('安排下一轮功能工作', '选择一个新工具的推进方式')),
    ('autonomy', '日常整理', ('默认自动处理', '先逐项确认'), ('任务反复出现', '涉及共享内容'),
     ('归拢笔记和标签', '整理新收到的资料')),
    ('layout', '入口布局', ('保留简洁入口', '增加显眼入口'), ('已经反复求助', '首次使用'),
     ('调整预约工具首页', '安排借阅工具主入口')),
    ('research', '研究推进', ('先复现已有证据', '先探索新的解释'), ('结论尚未复核', '交付临近'),
     ('安排一个研究假设的下一步', '为一个异常观察选择后续工作')),
    ('collaboration', '协作沟通', ('先异步留言', '先实时讨论'), ('当前工作被卡住', '跨时区'),
     ('联系另一个协作者', '推进一次联合修改')),
)
EXTRA = {
    'marker': ('文件标记', ('圆点', '短线')),
    'film': ('影片', ('侦探片', '纪录片')),
    'conflict': ('讨论形式', ('文字讨论', '语音讨论')),
}
CRITICAL = ('strength', 'exceptions', 'conjunctions', 'hard_constraints', 'updates',
            'revocations', 'conflicts', 'unknowns', 'current_instruction')
READER = (
    'Predict the synthetic person from supplied memory, not your own preference. '
    'current_choice is evaluated at source_cutoff in a new same-scope scenario; '
    'historical_reconstruction asks the explicitly stated earlier day. '
    'Ordinary prose is acceptable and does not require record IDs. Respect explicit '
    'replacement, evidence strength, revoked rules, conjunctions and hard constraints. '
    'An explicit current request overrides remembered preference. Two opposite '
    'equally strong unresolved observations do not identify a choice: use U. '
    'Unknown or cleared domains also require U. Do not invent past support from '
    'unanchored current prose. Do not execute any option. Return one JSON mapping '
    'every query ID to one of its answer_options IDs. Missing is not U.'
)
CONTROLS = ('full_semantic', 'none', 'wrong_person', 'delete_domain',
            'delete_exceptions', 'delete_hard', 'ignore_updates',
            'ignore_revocations', 'wrong_condition', 'wrong_time',
            'delete_strong', 'invent_unknowns', 'weaken_conjunction', 'resolve_conflict_arbitrarily')


def label(key, action):
    values = next((d[2] for d in DOMAINS if d[0] == key), EXTRA.get(key, ('', ('', '')))[1])
    return values[int(action)] if action in ('0', '1') else '材料不足'


def resolve(events, key, at, context):
    """Executable authored semantics; conflicts do not break on arbitrary IDs."""
    rows = [e for e in active_events(events, at) if e.get('key') == key]
    cut = max((e['day'] for e in rows if e['op'] == 'clear'), default=-1)
    rows = [e for e in rows if e['day'] > cut and e['op'] != 'clear']
    for kind in ('hard', 'except'):
        candidates = [e for e in rows if e['op'] == kind and
                      all(context.get(k) is v for k, v in e.get('when', {}).items())]
        if candidates:
            specificity = max(len(e.get('when', {})) for e in candidates)
            values = {e['value'] for e in candidates if len(e.get('when', {})) == specificity}
            return (next(iter(values)) if len(values) == 1 else 'U'), kind
    replacements = [e['day'] for e in rows if e['op'] == 'replace']
    start = max(replacements, default=-1)
    regular = [e for e in rows if e['op'] in ('prefer', 'replace', 'fact') and e['day'] >= start]
    if not regular: return 'U', None
    strength = max(e.get('strength', 0) for e in regular)
    values = {e['value'] for e in regular if e.get('strength', 0) == strength}
    return (next(iter(values)) if len(values) == 1 else 'U'), 'regular'


def render(events, wording='dev'):
    names = {d[0]: d[1] for d in DOMAINS} | {k: v[0] for k, v in EXTRA.items()}
    conditions = {d[0]: d[3] for d in DOMAINS}
    lines = [
        '以下是完全虚构的局部选择记录，完整覆盖所列领域至第12天；最后记录后没有新增变化。',
        '强度数字越大证据越强；同等有效、同等强度且相反的记录没有确定结论。',
        '“替代”只重设该领域的常规偏好，条件例外和硬约束另算；硬约束优先于条件例外。'
        '条件中“同时”表示必须全部满足。撤销一条撤销记录，会恢复原记录；清除会清除该领域此前记录。',
    ]
    for e in sorted(events, key=lambda x: (x['day'], x['id'])):
        op = e['op']
        if op == 'revoke': body = f'撤销记录{e["target"]}，其他记录继续适用'
        elif op == 'clear': body = f'清除【{names[e["key"]]}】此前记录，此后暂无这个偏好'
        else:
            name, value = names[e['key']], label(e['key'], e['value'])
            if op in ('hard', 'except'):
                words = [conditions[e['key']][int(k[-1])] if v else '不满足“'+conditions[e['key']][int(k[-1])]+'”'
                         for k, v in e['when'].items()]
                body = f'{"硬约束" if op == "hard" else "条件例外"}【{name}】：若'+ '且同时'.join(words)+f'，选「{value}」'
            elif op == 'replace': body = f'明确更新：用「{value}」替代【{name}】此前常规偏好，强度{e["strength"]}'
            else: body = f'观察到【{name}】选择「{value}」，强度{e.get("strength", 0)}'
        prefix = f'第{e["day"]}天，记录{e["id"]}：' if wording == 'dev' else f'记录{e["id"]}（第{e["day"]}天）：'
        lines.append(prefix + body + '。')
    return '\n'.join(lines)


def events_for(params):
    rows = []
    for i, p in enumerate(params):
        key = DOMAINS[i][0]
        def add(n, day, op, **kw):
            row = {'id':f'r{i}{n}', 'day':day, 'op':op, 'key':key, **kw}
            rows.append(row); return row['id']
        add(1, 1, 'prefer', value=str(p['base']), strength=3)
        add(2, 2, 'prefer', value=str(1-p['base']), strength=1)
        changed = add(3, 3, 'replace', value=str(1-p['base']), strength=2)
        if p['revoke_update']: add(4, 4, 'revoke', target=changed)
        add(5, 5, 'except', value=str(p['exception']), when={'c0':True})
        hard = add(6, 6, 'hard', value=str(1-p['exception']), when={'c0':True, 'c1':True})
        revoked = add(7, 7, 'revoke', target=hard)
        if p['restore_hard']: add(8, 8, 'revoke', target=revoked)
    rows += [
        {'id':'rm1', 'day':9, 'op':'fact', 'key':'marker', 'value':'0', 'strength':1},
        {'id':'rm2', 'day':10, 'op':'clear', 'key':'marker'},
        {'id':'rc1', 'day':11, 'op':'prefer', 'key':'conflict', 'value':'0', 'strength':2},
        {'id':'rc2', 'day':11, 'op':'prefer', 'key':'conflict', 'value':'1', 'strength':2},
    ]
    return rows


def make_case(pid, index, task, scenario, key, at, context, tags, wording, order=0, instruction=None):
    if key in EXTRA:
        questions = {'marker':'现在有哪种文件标记偏好的证据？', 'film':'材料支持哪种影片偏好？',
                     'conflict':'下一次交流选择讨论形式，此人倾向哪种方式？'}
        question = questions[key]
    else:
        d = next(d for d in DOMAINS if d[0] == key)
        situation = d[4][0 if wording == 'dev' else 1]
        states = '；'.join(f'{word}：{"是" if context.get("c"+str(i)) else "否"}' for i, word in enumerate(d[3]))
        question = f'{situation}。条件为：{states}。此人会怎样选择？'
    if instruction is not None: question += f'这一次本人当前明确要求「{label(key, instruction)}」，请按当前要求选择。'
    if task == 'historical_reconstruction':
        question = f'只恢复第{at}天当时的选择：'+question.replace('现在', '当时')
    actions = ('0', '1') if order == 0 else ('1', '0')
    options = {k:label(key, v) for k, v in zip(('A', 'B'), actions)} | {'U':'材料不足，无法判断'}
    return {'public':{'id':'q-'+digest(pid+':'+str(index))[:14], 'task':task,
                      'question':question, 'answer_options':options,
                      **({'at':at} if task == 'historical_reconstruction' else {})},
            'scenario':scenario, 'key':key, 'at':at, 'context':context, 'tags':tags,
            'options':dict(zip(('A', 'B'), actions)) | {'U':'U'},
            'instruction':instruction, 'order':order}


def queries(person, wording):
    cases = []
    def add(task, scenario, key, at, context, tags, order=0, instruction=None):
        c = make_case(person['id'], len(cases), task, scenario, key, at, context, tags, wording, order, instruction)
        action, reason = ((instruction, 'instruction') if instruction is not None else resolve(person['events'], key, at, context))
        c.update(gold=next(k for k,v in c['options'].items() if v == action), action=action,
                 active_hard=reason == 'hard' and action != 'U')
        cases.append(c)
    for d in DOMAINS:
        key = d[0]
        for context, name, tags in [({'c0':False,'c1':False}, 'default', ['strength','updates','revocations']),
                                    ({'c0':True,'c1':False}, 'conditional', ['exceptions']),
                                    ({'c0':False,'c1':True}, 'second_only', ['conjunctions','exceptions']),
                                    ({'c0':True,'c1':True}, 'conjunction', ['conjunctions','hard_constraints','revocations'])]:
            for order in (0,1): add('current_choice', key+':'+name, key, 12, context, tags, order)
    for key, tags in [('marker',['updates','unknowns']), ('film',['unknowns']), ('conflict',['conflicts','unknowns'])]:
        for order in (0,1): add('current_choice', key, key, 12, {}, tags, order)
    for order in (0,1): add('current_choice', 'instruction', 'planning', 12, {}, ['current_instruction'], order, '1')
    for d in DOMAINS:
        key = d[0]
        for at, context, tags in [(3,{},['updates']), (6,{'c0':True,'c1':True},['conjunctions','hard_constraints']),
                                  (7,{'c0':True,'c1':True},['revocations'])]:
            add('historical_reconstruction',key+':past:'+str(at),key,at,context,tags)
    add('historical_reconstruction','marker:past','marker',9,{},['old_fact'])
    return cases


def build_world(seed=721904, mode='development'):
    if mode not in ('development','future'): raise ValueError('Unknown mode')
    rng = random.Random(seed)
    targets = [(i,) for i in range(6)] if mode == 'development' else [(0,1,2),(3,4,5)]
    people = []
    for pair, axes in enumerate(targets):
        params = [{'base':rng.randrange(2), 'exception':rng.randrange(2),
                   'revoke_update':bool(rng.randrange(2)), 'restore_hard':bool((pair+i)%2)} for i in range(6)]
        ids = ['p-'+digest(f'{seed}:{mode}:{pair}:{member}')[:12] for member in range(2)]
        for member, pid in enumerate(ids):
            p = copy.deepcopy(params)
            if member:
                for axis in axes: p[axis]['exception'] = 1-p[axis]['exception']
            person = {'id':pid, 'pair_id':'pair-'+str(pair), 'twin':ids[1-member],
                      'target_axes':[DOMAINS[i][0] for i in axes], 'parameters':p,
                      'source_cutoff':12, 'events':events_for(p)}
            person['history'] = render(person['events'], 'dev' if mode == 'development' else 'future')
            person['cases'] = queries(person, 'dev' if mode == 'development' else 'future')
            people.append(person)
    body = {'origin':'fully_synthetic', 'version':1, 'purpose':mode, 'seed':seed, 'people':people,
            'statistical_unit':'Paired cluster; domains, contexts, people within a pair and option orders are correlated.',
            'not_real_person_or_model_evidence':True}
    return {**body, 'id':digest(canonical(body))}


def mutate(person, condition):
    e = copy.deepcopy(person['events'])
    if condition == 'delete_domain': e = [x for x in e if x.get('key') != 'research']
    if condition == 'delete_exceptions': e = [x for x in e if x['op'] != 'except']
    if condition == 'delete_hard': e = [x for x in e if x['op'] != 'hard']
    if condition == 'ignore_updates': e = [x for x in e if x['op'] not in ('replace','clear')]
    if condition == 'ignore_revocations': e = [x for x in e if x['op'] != 'revoke']
    if condition == 'delete_strong': e = [x for x in e if not (x['op'] == 'prefer' and x.get('strength') == 3)]
    if condition == 'wrong_condition':
        for x in e:
            if x['op'] == 'except': x['when'] = {'c1':True}
    if condition == 'weaken_conjunction':
        for x in e:
            if x['op'] == 'hard': x['when'] = {'c1':True}
    if condition == 'resolve_conflict_arbitrarily': e = [x for x in e if x['id'] != 'rc2']
    if condition == 'wrong_time':
        for x in e:
            if x['op'] == 'replace': x['day'] = 4
            elif x['op'] == 'revoke' and x['id'].endswith('7'): x['day'] = 8
    if condition == 'none': e = []
    return e


def predict(world, condition):
    if condition not in CONTROLS: raise ValueError('Unknown control')
    lookup = {p['id']:p for p in world['people']};result = {}
    for p in world['people']:
        e = lookup[p['twin']]['events'] if condition == 'wrong_person' else mutate(p, condition)
        answers = {}
        for c in p['cases']:
            action = c['instruction'] if c['instruction'] is not None else resolve(e, c['key'], c['at'], c['context'])[0]
            if condition == 'invent_unknowns' and action == 'U': action = '0'
            answers[c['public']['id']] = next(k for k,v in c['options'].items() if v == action)
        result[p['id']] = answers
    return result


def score(world, predictions, task):
    if task not in ('current_choice','historical_reconstruction','joint'): raise ValueError('Unknown task')
    correct = planned = missing = unknown = invalid = 0;layers = {};persons = [];pairs = {};order_pairs = []
    hard = {'planned':0,'errors':0,'abstentions':0,'missing':0,'active_hard_queries':0,'observed_violations':0}
    lookup = {p['id']:p for p in world['people']}
    def got(p,c): return predictions.get(p['id'],{}).get(c['public']['id'])
    def right(p,c): return got(p,c) == c['gold']
    for p in world['people']:
        cases = [c for c in p['cases'] if task == 'joint' or c['public']['task'] == task]
        good = sum(right(p,c) for c in cases)
        persons.append({'person_id':p['id'],'pair_id':p['pair_id'],'correct':good,'planned':len(cases),'accuracy':good/len(cases)})
        pair = pairs.setdefault(p['pair_id'], {'correct':0,'planned':0})
        pair['correct'] += good;pair['planned'] += len(cases)
        for c in cases:
            v = got(p,c);ok = right(p,c);planned += 1;correct += ok;missing += v is None;unknown += v == 'U'
            invalid += v is not None and v not in c['public']['answer_options']
            for tag in c['tags']:
                row = layers.setdefault(tag, {'correct':0,'planned':0,'missing':0})
                row['correct'] += ok;row['planned'] += 1;row['missing'] += v is None
            if 'hard_constraints' in c['tags']:
                hard['planned'] += 1;hard['errors'] += not ok;hard['missing'] += v is None;hard['abstentions'] += v == 'U'
                hard['active_hard_queries'] += c['active_hard'];hard['observed_violations'] += c['active_hard'] and v in ('A','B') and not ok
        current = [c for c in cases if c['public']['task'] == 'current_choice']
        scenarios={}
        for c in current:scenarios.setdefault(c['scenario'],{})[c['order']]=c
        for group in scenarios.values():
            a,b=group[0],group[1]
            x,y = got(p,a),got(p,b)
            order_pairs.append({'correct':right(p,a) and right(p,b), 'consistent':x in a['options'] and y in b['options'] and a['options'][x] == b['options'][y],
                                'missing':x is None or y is None})
    contrasts = []
    if task != 'historical_reconstruction':
        for p in world['people']:
            if p['id'] > p['twin']: continue
            twin = lookup[p['twin']]
            twin_cases={(c['public']['task'],c['scenario'],c['order']):c for c in twin['cases']}
            for key in p['target_axes']:
                candidates=[(a,twin_cases[(a['public']['task'],a['scenario'],a['order'])]) for a in p['cases'] if a['public']['task']=='current_choice' and a['key']==key]
                cases=[(a,b) for a,b in candidates if a['action'] != b['action']]
                contrasts.append({'pair_id':p['pair_id'],'domain':key,'correct':bool(cases) and all(right(p,a) and right(twin,b) for a,b in cases),
                                  'planned_action_checks':len(cases)*2})
    collapsed = {'correct':sum(x['correct'] for x in order_pairs),'planned':len(order_pairs),
                 'consistent':sum(x['consistent'] for x in order_pairs),'missing':sum(x['missing'] for x in order_pairs)}
    return {'task':task,'correct':correct,'planned':planned,'missing':missing,'invalid_answers':invalid,'unknown_answers':unknown,'accuracy':correct/planned,
            'layers':layers,'hard_constraints':hard,'current_scenarios_option_orders_collapsed':collapsed,
            'matched_domain_contrasts':{'correct':sum(c['correct'] for c in contrasts),'planned':len(contrasts),'details':contrasts},
            'paired_clusters':[{**x,'pair_id':key,'accuracy':x['correct']/x['planned']} for key,x in pairs.items()],
            'per_person':persons,'independent_cluster_count':len(pairs),
            'macro_cluster_accuracy':sum(x['correct']/x['planned'] for x in pairs.values())/len(pairs),
            'statistical_warning':'Raw queries, option orders, domains and paired people are not independent samples; no population CI or significance claim.'}


def calibrate(world):
    controls = {name:{task:score(world,predict(world,name),task) for task in ('current_choice','historical_reconstruction','joint')} for name in CONTROLS}
    return {'origin':'fully_synthetic','kind':'deterministic_semantic_calibration_not_model_predictions',
            'world_id':world['id'],'external_model_calls':0,'controls':controls,
            'independent_cluster_count':len({p['pair_id'] for p in world['people']}),
            'limitations':['Authored finite event grammar; program reads semantic events, not arbitrary model prose.',
                'Damage is deliberately aligned with tested requirements; sensitivity is not actual compressor quality.',
                'More axes improve coverage but do not add independent human subjects.'],
            'sealed_D0015_D0016':'unchanged, never rescored or rerun'}


def freeze_development(out):
    out = Path(out);out.mkdir(parents=True,exist_ok=False)
    world = build_world();report = calibrate(world)
    write_once(out/'fixtures.synthetic.json',world);write_once(out/'calibration.synthetic.json',report)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);a=p.parse_args()
    r = freeze_development(a.out)
    print(json.dumps({'external_model_calls':0,'clusters':r['independent_cluster_count'],'controls':len(r['controls'])}))
