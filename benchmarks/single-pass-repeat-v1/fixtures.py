"""Reference-aware bookkeeping fixtures, never model or fidelity evidence."""
import copy
import json


def graph(plan, pid, generation):
    src = plan.inputs()['sources'][pid]['sources'][0]
    anchor = {'source_id': src['id'], 'quote': src['text']}
    return {'version': plan.producer.VERSION, 'name': pid + '-fixture-' + str(generation),
            'tagline': '离线记账假响应，不是模型测量',
            'objects': [plan.seed.corpus.DOMAINS[0][1]],
            'nodes': [{'id': 'x', 'kind': 'base', 'target_kind': 'choice', 'object_index': 0,
                       'question': '剪辑选择', 'requires': [], 'action': '保留原声',
                       'priority': 0, 'decisions': [copy.deepcopy(anchor)],
                       'contexts': [copy.deepcopy(anchor)], 'order_split': None}],
            'unknowns': ['故意不完整的假卡；参考答案由测试夹具独立返回，不证明这张卡保真。']}


class Fixture:
    def __init__(self, plan, fault=None):
        self.plan, self.fault = plan, fault
        self.calls, self.requests = [], []

    def __call__(self, req, folder, slot):
        self.calls.append(slot)
        self.requests.append(req)
        p, kind, pid = self.plan, slot['kind'], slot['profile']
        if self.fault == 'transport' and slot['slot'] == 6:
            raise ValueError('Offline transport fixture')
        if kind == 'extract':
            answer = graph(p, pid, slot['generation_repeat'])
            if slot['slot'] == 6:
                if self.fault == 'product':
                    answer['nodes'][0]['object_index'] = 9
                elif self.fault == 'quote':
                    answer['nodes'][0]['decisions'][0]['quote'] = '来源中没有的引文'
                elif self.fault == 'wire':
                    answer.pop('nodes')
        else:
            rows = [r for r in p.inputs()['rows'] if r['person'] == (pid or p.PROFILES[0])]
            answer = {q: 'U' if kind == 'none' else r['gold'] for r in rows for q in r['query_ids']}
            if ((self.fault == 'control' and slot['slot'] == 2) or
                    (self.fault == 'one_order' and pid == 'pavo' and slot['view'] == 'card'
                     and slot['generation_repeat'] == 1 and slot['read_repeat'] == 1)):
                row = next(r for r in rows if r['personal_known'])
                answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), {
            'backend': 'offline_fixture',
            'model_requested': 'foreign' if self.fault == 'model' and slot['slot'] == 6 else p.MODEL,
            'usage': None if self.fault == 'usage' and slot['slot'] == 6
            else [{'input_tokens': 0, 'output_tokens': 0}]}
