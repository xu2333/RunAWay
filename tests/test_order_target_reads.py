"""Fixed-view ten-slot diagnostic fixtures;oracle values are not LLM evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('order_target_read_tests',ROOT/'benchmarks/order-target-read-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


class Fixture:
    def __init__(self,fault=None,at=None):self.calls,self.fault,self.at=0,fault,at;self.data=e.plan.inputs()
    def __call__(self,req,folder,slot):
        self.calls+=1;fault=self.fault if slot['slot']==self.at else None
        if fault=='transport':raise TimeoutError('Offline fixture')
        answer={q['id']:'U' for q in self.data['queries']['j']} if slot['kind']=='none' else {q:r['gold'] for r in self.data['legacy_rows'] for q in r['query_ids']}
        for r in self.data['disputed_rows']:
            for q in r['query_ids']:answer[q]='U'
        if fault=='control':
            row=next(r for r in self.data['rows'] if r['gold']!='U');answer[row['query_ids'][0]]='U'
        if fault=='wire':answer={}
        return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,
            'usage':None if fault=='usage' else [{'input_tokens':0,'output_tokens':0}]}


class OrderTargetReadTests(unittest.TestCase):
    def execute(self,temp,fixture):
        root=Path(temp)/'proposal';e.plan.prepare(root)
        return root,e.run(root,root/'fixture',fixture,lambda _: {},simulated=True)

    def test10static_slots4capped_views_and_no_parent_replacement(self):
        slots=e.plan.slots();self.assertEqual([s['kind'] for s in slots],['none','full']+['read']*8)
        self.assertEqual(len(e.plan.views()),4)
        self.assertEqual([v['characters'] for v in e.plan.views()],[727,757,724,754])
        for v in e.plan.views():self.assertEqual(v['memory_ceiling'],1536)
        with self.assertRaises(ValueError):e.plan.request(slots[2],{'replacement':'card'})

    def test10fixtures_keep23case_denominator_fixed_hashes_and_w14unscored(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Fixture();root,r=self.execute(temp,f)
            self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(10,'complete',0))
            self.assertEqual((r['local_cli_child_intents'],r['known_usage']['total_tokens']),(0,0))
            pairs={}
            for rec in r['records']:
                if rec['kind']=='read':
                    self.assertEqual(rec['view_sha256'],e.plan.digest(e.plan.view(rec)))
                    pairs.setdefault(e.plan.parent(rec),[]).append(rec['request_sha256'])
            self.assertTrue(all(len(v)==2 and v[0]==v[1] for v in pairs.values()))
            for m in e.plan.METHODS:self.assertEqual(r['scores']['methods'][m]['strict_all_parents_and_reads']['joint'],{'planned':23,'correct':23,'missing':0})
            self.assertFalse(r['scores']['fresh_generation_stability_test'])
            for d in r['scores']['disputed_observations_not_scored']:
                self.assertFalse(d['reference_accepted']);self.assertFalse(d['included_in_primary_or_gate'])
            with self.assertRaises(FileExistsError):e.run(root,root/'fixture',f,lambda _: {},simulated=True)

    def test_control_wire_usage_and_final_failures_close_without_retry_or_skips(self):
        for fault,at in [('control',2),('wire',3),('usage',1),('transport',10)]:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                f=Fixture(fault,at);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',10-at))
                self.assertFalse(r['invalid_products']);self.assertFalse(r['skipped'])

    def test_unapproved_static_freeze_and_view_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'proposal';p=e.plan.prepare(root)
            self.assertFalse(p['approved']);self.assertFalse(p['new_service_authority'])
            self.assertTrue(p['post_hoc_case_informed_developer_annotation'])
            self.assertEqual(len(e.plan.read(root/'static-requests.json')),10)
            self.assertFalse(e.plan.read(root/'dynamic-rules.json')['slots'])
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError):e.plan.prepare(root)
            (root/'views.public.json').write_text('[]')
            with self.assertRaises(ValueError):e.plan.verify(root)

    def test_unread_views_remain_missing_and_do_not_prove_decomposition(self):
        r=e.score.summarize(e.plan.inputs()['rows'],{})
        for m in e.plan.METHODS:self.assertEqual(r['methods'][m]['strict_all_parents_and_reads']['joint'],{'planned':23,'correct':0,'missing':23})
        self.assertEqual(r['paired_strict']['split_missing'],23)
        self.assertEqual(r['new_extractions'],0)
        self.assertFalse(r['semantic_decomposition_independently_accepted'])


if __name__=='__main__':unittest.main()
