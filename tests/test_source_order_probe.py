"""22-slot fixture calibration,including order loss hidden by primary accuracy."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_order_probe_tests',ROOT/'benchmarks/source-order-probe-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


class Fixture:
    def __init__(self,fault=None,at=None):self.calls,self.fault,self.at=0,fault,at;self.data=e.plan.inputs()
    def __call__(self,req,folder,slot):
        self.calls+=1;fault=self.fault if slot['slot']==self.at else None
        if fault=='transport':raise TimeoutError('Offline fixture')
        if slot['kind']=='extract':
            source=next(s for s in self.data['sources']['j16']['sources'] if s['id']=='m16')
            offered=next(s for s in self.data['sources']['j16']['sources'] if s['id']=='m13')
            anchor={'source_id':'m16','quote':source['text']}
            node={'id':'fixture','kind':'base','target_kind':'choice','object_index':0,'question':'夹具方法',
                'requires':[],'action':e.plan.ORDERED,'priority':0,'decisions':[anchor],'contexts':[anchor]}
            if slot['method']=='source-order-v3':
                node['order_split']=None if fault=='no_annotation' else {'core_action':e.plan.ORDERED[1:],
                    'core_evidence':[{'source_id':'m13','quote':offered['text']}],'execution_question':'夹具先后'}
            answer={'version':req['schema']['properties']['version']['enum'][0],'name':'协议夹具','tagline':'不是模型表现。',
                    'objects':['夹具范围'],'nodes':[node],'unknowns':['未覆盖时未知。']}
            if fault=='product':node['object_index']=1
            if fault=='contamination':answer['unknowns'].append('另处仍保留'+e.plan.ORDERED+'。')
        else:
            questions=self.data['queries'][e.plan.question_bank(slot)]
            gold={q:r['gold'] for r in self.data['legacy_rows']+self.data['auxiliary_rows'] for q in r['query_ids']}
            answer={q['id']:'U' if slot['kind']=='none' or slot['variant']=='erased' else gold[q['id']] for q in questions}
            for r in self.data['disputed_rows']:
                for q in r['query_ids']:
                    if q in answer:answer[q]='U'
            if fault=='control':
                r=next(r for r in self.data['rows'] if r['gold']!='U');answer[r['query_ids'][0]]='U'
            if fault=='aux_control':answer['order_probe_a']='U'
            if fault=='guess_erased':answer={q['id']:e.plan.ORDERED for q in questions}
        if fault=='wire':answer={}
        return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,
            'usage':None if fault=='usage' else [{'input_tokens':0,'output_tokens':0}]}


class SourceOrderProbeTests(unittest.TestCase):
    def execute(self,temp,fixture):
        root=Path(temp)/'proposal';e.plan.prepare(root)
        return root,e.run(root,root/'fixture',fixture,lambda _: {},simulated=True)

    def test_source_only_extraction_and_auxiliary_facts_never_enter_primary_read_packets(self):
        slots=e.plan.slots();self.assertEqual(len(slots),22)
        self.assertEqual([s['kind'] for s in slots[:6]],['none','full']+['extract']*4)
        data=e.plan.inputs();self.assertEqual([len(data['queries'][k]) for k in ('j','order','control')],[48,2,50])
        for slot in slots[2:6]:
            req=e.plan.request(slot);body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
            self.assertEqual(body['sources'],data['sources']['j16'])
            self.assertNotIn('order_probe_a',req['prompt'])
        self.assertTrue(all(e.plan.question_bank(s)=='j' for s in slots[6:14]))
        self.assertTrue(all(e.plan.question_bank(s)=='order' for s in slots[14:]))

    def test22fixtures_keep_tasks_variants_separate_and_both_order_endpoints_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Fixture();root,r=self.execute(temp,f)
            self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(22,'complete',0))
            for m in e.plan.METHODS:self.assertEqual(r['scores']['per_method_strict'][m]['joint'],{'planned':23,'correct':23,'missing':0})
            aux=r['scores']['auxiliary_order']
            self.assertEqual(aux['strict_intact_source_order']['joint'],{'planned':1,'correct':1,'missing':0})
            self.assertEqual(aux['strict_erased_expected_unknown']['joint'],{'planned':1,'correct':1,'missing':0})
            self.assertTrue(r['scores']['planned_development_acceptance']['all_required'])
            self.assertTrue(all(not x['reference_accepted'] and not x['included_in_primary_or_gate'] for x in r['scores']['disputed_observations_not_scored']))
            self.assertEqual((r['local_cli_child_intents'],r['known_usage']['total_tokens']),(0,0))
            for rec in r['records']:
                if rec['kind']=='read' and rec['task']=='primary':
                    req=e.plan.read(root/'fixture'/rec['execution_id']/'request.json')
                    self.assertNotIn('order_probe_a',req['prompt'])
            with self.assertRaises(FileExistsError):e.run(root,root/'fixture',f,lambda _: {},simulated=True)

    def test_missing_or_redundant_generated_order_does_not_get_repaired_and_damage_stays_missing(self):
        for fault in ('no_annotation','contamination'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                f=Fixture(fault,4);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(20,'completed_with_ineligible_damage',2))
                self.assertTrue(all(s['task']=='order' and s['variant']=='erased' and s['generation']==0 for s in r['skipped']))
                self.assertEqual(r['scores']['per_method_strict']['source-order-v3']['joint']['correct'],23)
                self.assertEqual(r['scores']['auxiliary_order']['strict_erased_expected_unknown']['joint']['missing'],1)
                self.assertFalse(r['scores']['planned_development_acceptance']['all_required'])

    def test_primary_or_auxiliary_control_failure_closes_before_extract3(self):
        for fault in ('control','aux_control'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                f=Fixture(fault,2);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(2,'stopped',20))

    def test_invalid_parent_skips_exact_own_two_or_six_slots_and_keeps23missing(self):
        for at,method,skips in ((3,'policy-v2',2),(4,'source-order-v3',6)):
            with self.subTest(at=at),tempfile.TemporaryDirectory() as temp:
                f=Fixture('product',at);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],len(r['skipped'])),(22-skips,'completed_with_invalid_products',skips))
                self.assertTrue(all(e.plan.parent(s)==e.plan.parent(e.plan.slots()[at-1]) for s in r['skipped']))
                self.assertEqual(r['scores']['per_method_strict'][method]['joint'],{'planned':23,'correct':0,'missing':23})

    def test_guessing_order_after_erasure_is_detected_even_with_perfect_primary(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Fixture('guess_erased',16);_,r=self.execute(temp,f)
            self.assertEqual(r['scores']['per_method_strict']['source-order-v3']['joint']['correct'],23)
            self.assertEqual(r['scores']['auxiliary_order']['strict_erased_expected_unknown']['joint']['correct'],0)
            self.assertFalse(r['scores']['planned_development_acceptance']['all_required'])

    def test_wire_usage_and_final_failure_close_without_retry(self):
        for fault,at in (('wire',4),('usage',1),('transport',22)):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                f=Fixture(fault,at);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',22-at))

    def test_unapproved_exclusive_freeze_six_static_sixteen_dynamic_and_input_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'proposal';p=e.plan.prepare(root)
            self.assertFalse(p['approved']);self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root/'static-requests.json')),6)
            self.assertEqual(len(e.plan.read(root/'dynamic-rules.json')['slots']),16)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError):e.plan.prepare(root)
            (root/'sources.json').write_text('{}')
            with self.assertRaises(ValueError):e.plan.verify(root)


if __name__=='__main__':unittest.main()
