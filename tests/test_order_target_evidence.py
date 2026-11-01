"""Counterfactual source/conservation lineage controls;no behavioral observations."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('order_target_evidence_tests',ROOT/'benchmarks/order-targets-v1/evidence.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


class OrderTargetEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=e.p.read(e.DEFAULT)

    def test_recorded_refactoring_confound_remains_reproducible_without_calls(self):
        r=e.check(mode='refactored-v1')
        self.assertEqual(r['new_model_calls'],0)
        self.assertEqual(r['split_characters'],[775,772])
        old=e.p.read(e.REFACTORED_V1)
        for old_parent,new_parent in zip(old['parents'],self.data['parents']):
            self.assertEqual(old_parent['raw_parent_value_sha256'],new_parent['raw_parent_value_sha256'])
            self.assertNotEqual(old_parent['split_prompt'],new_parent['split_prompt'])
        self.assertFalse(r['semantic_decomposition_independently_accepted'])

    def test_both_chronological_parents_fit_with_original_ordered_text_retained(self):
        r=e.check();self.assertEqual(r['new_model_calls'],0)
        self.assertEqual(r['original_characters'],[727,724])
        self.assertTrue(all(n<=1536 for n in r['split_characters']))
        self.assertFalse(r['behavioral_fidelity_verified'])
        self.assertTrue(r['literal_ordered_action_retained'])
        self.assertEqual([p['generation'] for p in self.data['parents']],[0,1])
        for p in self.data['parents']:
            self.assertIn('→先约定固定安静时段',p['split_prompt'])
            self.assertIn('执行先后',p['split_prompt'])
            self.assertEqual(len(p['conservation']['trace']),1)
            original=p['original_prompt'].splitlines()
            split=p['split_prompt'].splitlines()
            added=[line for line in split if '执行先后|' in line]
            self.assertEqual(len(added),1)
            changed=[line for line in original if line.endswith('→先约定固定安静时段')]
            self.assertEqual(len(changed),1)
            expected=[line[:-len('先约定固定安静时段')]+'约定固定安静时段' if line in changed else line for line in original]
            self.assertEqual([line for line in split if line not in added],expected)

    def test_parent_raw_lineage_and_unmodified_original_views_cannot_change(self):
        for field in ('raw_parent_value_sha256','parent_answer_sha256','original_prompt'):
            d=copy.deepcopy(self.data);d['parents'][0][field]+='changed'
            with self.subTest(field=field),self.assertRaises(ValueError):e.replay(d)

    def test_ordering_guard_binding_and_execution_target_changes_are_detected(self):
        for fault in ('prompt','binding','guard','generation'):
            d=copy.deepcopy(self.data);p=d['parents'][0]
            if fault=='prompt':p['split_prompt']=p['split_prompt'].replace('先约定','约定')
            elif fault=='binding':p['developer_binding']['core_action']='different'
            elif fault=='guard':p['conservation']['trace'][0]['all_original_conditions_preserved_on_both_targets']=False
            else:p['generation']=1
            with self.subTest(fault=fault),self.assertRaises(ValueError):e.replay(d)

    def test_developer_annotation_is_not_a_semantic_proof_new_generation_or_repaired_trial(self):
        for field,value in [('actual_new_model_calls',1),('post_hoc_case_informed_developer_annotation',False),
                ('automatic_parser_or_new_generation',True),('semantic_decomposition_independently_accepted',True),
                ('old_semantic_equivalence_verified',True),('behavioral_fidelity_verified',True),
                ('replaces_closed_cards_or_scores',True),('production_default_changed',True)]:
            d=copy.deepcopy(self.data);d[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):e.replay(d)


if __name__=='__main__':unittest.main()
