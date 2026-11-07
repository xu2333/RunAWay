"""Reference-aware mocked responses;no fidelity or inference evidence."""
import json


class Fixture:
    def __init__(self, plan, fault=None):
        self.plan, self.fault, self.calls = plan, fault, []

    def __call__(self, req, folder, slot):
        self.calls.append(slot)
        p = self.plan
        if self.fault == 'transport' and slot['slot'] == 6:
            raise ValueError('Offline transport fixture')
        rows = [r for r in p.inputs()['rows'] if r['person'] == (slot['profile'] or p.PROFILES[0])]
        answer = {q: 'U' if slot['kind'] == 'none' else r['gold'] for r in rows for q in r['query_ids']}
        if self.fault == 'control' and slot['slot'] == 2:
            row = next(r for r in rows if r['primary'] and r['personal_known'])
            answer[row['query_ids'][0]] = 'U'
        if self.fault == 'one_order' and slot['slot'] == 6:
            row = next(r for r in rows if r['primary'] and r['personal_known'])
            answer[row['query_ids'][1]] = 'U'
        if self.fault == 'wire' and slot['slot'] == 6:
            answer.pop(next(iter(answer)))
        return json.dumps(answer, ensure_ascii=False), {
            'backend': 'offline_fixture',
            'model_requested': 'foreign' if self.fault == 'model' and slot['slot'] == 6 else p.MODEL,
            'usage': None if self.fault == 'usage' and slot['slot'] == 6 else [{'input_tokens': 0, 'output_tokens': 0}]}
