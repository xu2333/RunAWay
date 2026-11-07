"""Reference-aware accounting mocks; they deliberately do not measure fidelity."""
import json


def graph(plan, pid, generation):
    source = plan.inputs()['sources'][pid]['sources'][1]
    anchor = {'source_id': source['id'], 'quote': source['text']}
    return {'version': plan.producer.VERSION, 'name': pid + '-mock-' + str(generation),
            'tagline': '离线记账假响应，不是模型测量', 'objects': ['共同写稿时的交付形态'],
            'nodes': [{'id': 'x', 'kind': 'base', 'target_kind': 'choice', 'object_index': 0,
                       'question': '交付形态', 'requires': [], 'action': '先交结构稿', 'priority': 0,
                       'decisions': [anchor], 'contexts': [dict(anchor)], 'order_split': None}],
            'unknowns': ['这张记账假卡故意不完整，参考由测试夹具独立返回，不能证明保真。']}


class Fixture:
    def __init__(self, plan, fault=None):
        self.plan, self.fault, self.calls, self.requests = plan, fault, [], []

    def __call__(self, req, folder, slot):
        self.calls.append(slot)
        self.requests.append(req)
        p = self.plan
        if self.fault == 'transport' and slot['slot'] == 6:
            raise ValueError('Offline transport fixture')
        if slot['kind'] == 'extract':
            answer = graph(p, slot['profile'], slot['generation_repeat'])
            if slot['slot'] == 6:
                if self.fault == 'product':
                    answer['nodes'][0]['object_index'] = 9
                elif self.fault == 'quote':
                    answer['nodes'][0]['decisions'][0]['quote'] = '不存在的来源引文'
                elif self.fault == 'wire':
                    answer.pop('nodes')
        else:
            rows = [r for r in p.inputs()['rows'] if r['person'] == (slot['profile'] or p.PROFILES[0])]
            answer = {q: 'U' if slot['kind'] == 'none' else r['gold'] for r in rows for q in r['query_ids']}
            if ((self.fault == 'control' and slot['slot'] == 2) or
                    (self.fault == 'one_order' and slot['profile'] == p.PROFILES[0] and slot['view'] == 'card'
                     and slot['generation_repeat'] == 1 and slot['read_repeat'] == 1)):
                row = next(r for r in rows if r['personal_known'])
                answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), {
            'backend': 'offline_fixture',
            'model_requested': 'foreign' if self.fault == 'model' and slot['slot'] == 6 else p.MODEL,
            'usage': None if self.fault == 'usage' and slot['slot'] == 6 else [{'input_tokens': 0, 'output_tokens': 0}]}
