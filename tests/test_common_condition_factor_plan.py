"""Offline preparation fixtures only; no model-reader observations or authority."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('common_factor_protocol_tests',ROOT/'benchmarks/common-condition-factor-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);p=e.plan


class CommonFactorPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);p.prepare(cls.root/'packet')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_exact_twenty_request_scope_and_eight_counted_views(self):
        v=p.values();self.assertEqual(len(v['slots.json']),20);self.assertEqual(len(v['static-requests.json']),20)
        self.assertEqual(len(v['views.public.json']),8);self.assertFalse(v['proposal.json']['approved'])
        self.assertEqual(len(v['reference.private.json']),120)
        for view in v['views.public.json']:
            self.assertLessEqual(view['characters'],768 if view['method']=='factored' else 1536)
            self.assertFalse(view['model_reader_fidelity_verified'])

    def test_only_own_public_view_and_unchanged_questions_are_sent(self):
        d=p.inputs();self.assertEqual(d,p.query_plan.inputs())
        for slot in p.slots():
            req=p.request(slot);payload=json.loads(req['prompt'].split('READER_INPUT_JSON:\n',1)[1])
            self.assertEqual(payload['queries'],p.questions(slot))
            self.assertEqual(set(req['schema']['properties']),{q['id']for q in p.questions(slot)})
            if slot['kind']=='read':
                self.assertEqual(payload['material'],p.view(slot)['prompt'])
                self.assertEqual(slot['budget'],p.view(slot)['whole_character_ceiling'])
            for private in('parent_raw_sha256','source_accounting','reference.private.json','def restore('):self.assertNotIn(private,req['prompt'])
        views=p.views()
        for person in p.PROFILES:
            for g in(0,1):
                flat=next(v for v in views if(v['profile'],v['method'],v['generation'])==(person,'flat',g))
                factored=next(v for v in views if(v['profile'],v['method'],v['generation'])==(person,'factored',g))
                self.assertEqual(p.factor_codec.restore(factored['prompt']),p.factor_codec.dense.decode(flat['prompt']))

    def test_frozen_packet_rejects_changed_views_and_cannot_be_overwritten(self):
        packet=self.root/'packet';self.assertTrue(p.verify(packet))
        with self.assertRaises(FileExistsError):p.prepare(packet)
        file=packet/'views.public.json';raw=file.read_bytes()
        try:
            file.write_bytes(raw+b' ')
            with self.assertRaises(ValueError):p.verify(packet,reconstruct=False)
        finally:file.write_bytes(raw)

    def run_fixture(self,destination,fail_slot=None,bad_full=False):
        calls=[]
        def invoke(req,folder,slot):
            calls.append(slot['slot'])
            rows=[r for r in p.inputs()['rows']if r['person']==slot['profile']]
            a={q['id']:'U'for q in p.questions(slot)}
            if slot['kind']!='none'and not(bad_full and slot['kind']=='full'):a={q:r['gold']for r in rows for q in r['query_ids']}
            return json.dumps(a,ensure_ascii=False),dict(backend='fixture',model_requested=p.MODEL,usage=[]if slot['slot']==fail_slot else[dict(input_tokens=1,output_tokens=1)])
        with patch('runaway.generation.codex_generate',side_effect=AssertionError('No model'))as backend:
            result=e.run(self.root/'packet',destination,invoke,lambda slot:dict(owned_active=True),simulated=True)
        backend.assert_not_called();return result,calls

    def test_twenty_slot_fixture_preserves_120cases_and_no_generation_claim(self):
        with tempfile.TemporaryDirectory()as tmp:
            result,calls=self.run_fixture(Path(tmp)/'run')
            self.assertEqual(calls,list(range(1,21)));self.assertEqual(result['status'],'complete')
            self.assertEqual(result['local_cli_child_intents'],0);self.assertTrue(result['usage_is_fixture_not_billable'])
            for method in p.METHODS:self.assertEqual(result['scores']['methods'][method]['strict_eight_answers']['joint'],dict(planned=120,correct=120,missing=0))
            self.assertFalse(result['scores']['generation_stability_retested'])

    def test_control_and_unknown_usage_failures_close_without_retries(self):
        for fail,bad,expected in((5,False,5),(None,True,3)):
            with self.subTest(fail=fail,bad=bad),tempfile.TemporaryDirectory()as tmp:
                result,calls=self.run_fixture(Path(tmp)/'run',fail_slot=fail,bad_full=bad)
                self.assertEqual(calls,list(range(1,expected+1)));self.assertEqual(result['status'],'stopped')
                self.assertEqual(result['unused_slots_expire'],20-expected)
                for method in p.METHODS:self.assertEqual(result['scores']['methods'][method]['strict_eight_answers']['joint']['missing'],120)


if __name__=='__main__':unittest.main()
