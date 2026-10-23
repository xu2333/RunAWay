"""Consumed actual observation integrity plus independent toy scoring edge cases."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'benchmarks/natural-controls-v1'
spec=importlib.util.spec_from_file_location('natural_controls_check',HERE/'check.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)


class NaturalControlsEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((HERE/'observed.synthetic.json').read_text(encoding='utf-8'))

    def test_consumed_model_results_reproduce_without_a_call_or_compact_claim(self):
        report=bench.check()
        self.assertEqual((report['full_correct'],report['none_correct']),(56,18))
        self.assertEqual(report['known_tokens'],63457)
        self.assertEqual(report['new_model_calls'],0)
        self.assertFalse(report['compression_accuracy_measured'])
        self.assertFalse(report['human_fidelity_verified'])

    def test_source_and_same_query_request_damage_cannot_pass(self):
        for where in ('source','request'):
            data=copy.deepcopy(self.data)
            if where=='source':data['sources']['n31']['sources'][0]['text']+='changed'
            else:data['records'][0]['request']['prompt']+='changed'
            with self.subTest(where=where),self.assertRaises(ValueError):bench.replay(data)

    def test_missing_duplicate_and_mock_records_cannot_be_successes(self):
        for where in ('missing','duplicate','mock'):
            data=copy.deepcopy(self.data)
            if where=='missing':data['records'].pop()
            elif where=='duplicate':data['records'][1]['execution_id']=data['records'][0]['execution_id']
            else:data['records'][0]['simulated']=True
            with self.subTest(where=where),self.assertRaises(ValueError):bench.replay(data)

    def test_original_response_and_usage_damage_is_rejected(self):
        for where in ('response','usage'):
            data=copy.deepcopy(self.data)
            if where=='response':data['records'][0]['response']['raw']='{}'
            else:data['records'][0]['usage']['input_tokens']+=1
            with self.subTest(where=where),self.assertRaises(ValueError):bench.replay(data)

    def test_two_rotations_missing_denominators_and_qualification_on_toy_cases(self):
        rows=[{'person':'toy','case':'lamp','cohort':'development','gold':'off','query_ids':['qa','qb'],'personal_known':True},
              {'person':'toy','case':'outside','cohort':'development','gold':'U','query_ids':['qc','qd'],'personal_known':False}]
        result=bench.summarize(rows,{'toy':{'qa':'off','qb':'on'}},{'toy':{}})
        self.assertEqual(result['groups']['full']['joint'],{'planned':2,'correct':0,'missing':1})
        self.assertFalse(result['full_qualified'])
        full={'toy':{'qa':'off','qb':'off','qc':'U','qd':'U'}}
        result=bench.summarize(rows,full,{'toy':{'qa':'U','qb':'U','qc':'U','qd':'U'}})
        self.assertTrue(result['full_qualified'])
        self.assertFalse(result['next_stage_authorized'])


if __name__=='__main__':unittest.main()
