"""Authored fictional task contrasts. No model, semantic oracle or service backend."""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('scenario_contracts', HERE.parent / 'task-contract-v1/authoring.py')
authoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authoring)

# Four authored template families; opposite people within a family are dependent.
DOMAINS = (
    ('repair', '社区维修活动', '场地许可', ('先摆工具后诊断', '先诊断后摆工具'),
     ('先验电再铺垫', '先铺垫再验电'), ('已归还', '尚未归还'), '工具箱借用', '远程值班'),
    ('field', '虚构田野采样', '样地准入', ('先拍照后取样', '先取样后拍照'),
     ('先校表再编号', '先编号再校表'), ('已经入库', '尚未入库'), '上次样本', '跨组代采'),
    ('kitchen', '社区烹饪活动', '厨房许可', ('先分菜后示范', '先示范后分菜'),
     ('先洗台再称量', '先称量再洗台'), ('已经清点', '尚未清点'), '上次餐具', '夜间备料'),
    ('music', '虚构合奏排练', '排练室许可', ('先合奏后分声部', '先分声部后合奏'),
     ('先调音再摆谱', '先摆谱再调音'), ('已经返还', '尚未返还'), '上次谱架', '远程领奏'),
)


def _contract(cid, target, intent, facts, options, reference, support, alternative, fault):
    temporal, kind, _ = authoring.KINDS[intent]
    return {'version': authoring.VERSION, 'id': cid, 'target_object': target, 'intent': intent,
            'temporal_role': temporal, 'answer_kind': kind, 'facts': facts, 'options': list(options),
            'reference': reference, 'unknown_reason': 'not_decided' if reference == 'U' else None,
            'support': [support], 'contrasts': [{'fault': fault, 'predicted_answer': alternative}]}


def build():
    sources, questions, rows, mutations, pairs = {}, {}, [], [], {}
    for domain, activity, permission, names, orders, states, past_object, proposal in DOMAINS:
        for side in (0, 1):
            pid = domain + str(side)
            pairs[pid] = domain + str(1 - side)
            choice = f'{permission}已落实时，下次{activity}我选择整套方案“{names[side]}”。'
            pending = f'{permission}未落实时，我还没有决定选哪套方案。'
            past = f'{past_object}的上一次实际记录是“{states[side]}”。'
            order = f'上次{activity}明确记录的实际执行先后是“{orders[side]}”。这不是下次整套方案的名称。'
            commitment = (f'关于{proposal}，我还没有决定。' if side == 0 else
                          f'关于{proposal}，我的明确决定是“接受安排”。')
            messages = [
                {'id': 'u1', 'role': 'user', 'text': choice + pending + '两套候选的登记全名分别是“' + names[0] + '”和“' + names[1] + '”。'},
                {'id': 'a1', 'role': 'assistant', 'text': f'我建议你接受{proposal}，也可以把活动改个新名字。'},
                {'id': 'u2', 'role': 'user', 'text': past},
                {'id': 'u3', 'role': 'user', 'text': order},
                {'id': 'u4', 'role': 'user', 'text': commitment},
                {'id': 'u5', 'role': 'user', 'text': '这几条分别记录未来方案、过去事实、实际先后和新安排的决定，请分开保存。'},
            ]
            source = {'schema_version': 1, 'sources': messages}
            sources[pid] = source
            definitions = [
                ('choice', activity + '的下次整套方案', 'preferred_option', permission + '已落实', names,
                 names[side], 'u1', choice, names[1 - side], 'reverse_personal_choice',
                 choice.replace(names[side], names[1 - side])),
                ('uncovered', activity + '的下次整套方案', 'preferred_option', permission + '未落实', names,
                 'U', 'u1', pending, names[side], 'invent_policy_for_undecided_condition',
                 f'{permission}未落实时，我明确选择整套方案“{names[side]}”。'),
                ('order', '上次' + activity, 'execution_order', '只读取实际执行先后，不问下次整套方案', orders,
                 orders[side], 'u3', order, orders[1 - side], 'reverse_recorded_execution',
                 order.replace(orders[side], orders[1 - side])),
                ('past', past_object, 'past_observation', '只读取上一次记录', states,
                 states[side], 'u2', past, states[1 - side], 'reverse_past_status',
                 past.replace(states[side], states[1 - side])),
                ('commitment', proposal, 'decision_polarity', '只判断本人对该安排的明确决定', ('接受安排', '拒绝安排'),
                 'U' if side == 0 else '接受安排', 'u4', commitment, '接受安排' if side == 0 else 'U',
                 'invent_assistant_proposal_adoption' if side == 0 else 'erase_explicit_commitment',
                 f'关于{proposal}，我的明确决定是“接受安排”。' if side == 0 else f'关于{proposal}，我还没有决定。'),
            ]
            questions[pid] = []
            for case, target, intent, facts, options, gold, sid, quote, alternative, fault, replacement in definitions:
                contract = _contract(domain + '_' + case, target, intent, facts, options, gold,
                                     {'source_id': sid, 'quote': quote}, alternative, fault)
                prepared = authoring.prepare(contract, source)
                questions[pid].extend(prepared['questions.public'])
                rows.append({'profile': pid, 'case': case, 'contract': contract,
                             'query_ids': [q['id'] for q in prepared['questions.public']]})
                modified = copy.deepcopy(source)
                entry = next(x for x in modified['sources'] if x['id'] == sid)
                if entry['text'].count(quote) != 1:
                    raise ValueError('Mutation anchor is not unique')
                entry['text'] = entry['text'].replace(quote, replacement, 1)
                altered = copy.deepcopy(contract)
                altered.update(reference=alternative,
                               unknown_reason='not_decided' if alternative == 'U' else None,
                               support=[{'source_id': sid, 'quote': replacement}],
                               contrasts=[{'fault': 'restore_baseline_source', 'predicted_answer': gold}])
                changed = authoring.prepare(altered, modified)
                if changed['questions.public'] != prepared['questions.public']:
                    raise ValueError('Source intervention changed the question')
                mutations.append({'profile': pid, 'case': case, 'operation': 'replace_exact_user_span',
                                  'source_id': sid, 'before': quote, 'after': replacement,
                                  'sources': modified, 'contract': altered,
                                  'semantic_transition_independently_verified': False})
    return {'sources': sources, 'questions': questions, 'rows': rows, 'mutations': mutations, 'pairs': pairs}
