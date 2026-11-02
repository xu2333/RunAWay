"""Damage actual fixed-parent order-target read evidence; never call a model service."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('order_read_evidence_tests', ROOT / 'scripts/replay_order_target_reads.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


class OrderReadEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = a.engine.plan.read(a.DEFAULT)

    def test_closed10fixed_views_preserve23cases_without_new_generation(self):
        r=a.check()
        self.assertLessEqual(r['actual_original_attempts'],10)
        self.assertEqual((r['new_model_calls'],r['new_extractions'],r['inherited_parent_generations']),(0,0,2))
        for method in a.engine.plan.METHODS:
            c=r['scores']['methods'][method]['strict_all_parents_and_reads']
            self.assertEqual((c['joint']['planned'],c['known']['planned'],c['unknown']['planned'],c['personal_known']['planned']),(23,17,6,11))
        self.assertFalse(r['fresh_generation_stability_test'])
        self.assertTrue(r['post_hoc_case_informed_developer_annotation'])
        self.assertFalse(r['semantic_decomposition_independently_accepted'])

    def test_source_reference_disputed_mask_and_legacy_annotation_cannot_drift(self):
        for fault in ('source', 'reference', 'disputed', 'legacy'):
            d = copy.deepcopy(self.data)
            if fault == 'source': d['sources']['j16']['sources'][0]['text'] += 'changed'
            elif fault == 'reference': d['reference_rows'][0]['gold'] = 'changed'
            elif fault == 'disputed': d['disputed_rows'] = []
            else: d['legacy_rows'][0]['gold'] = 'changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_profile_generation_or_method_swaps_cannot_borrow_another_card(self):
        for field, value in (('profile', 'foreign'), ('generation', 8), ('method', 'scope-v1')):
            d = copy.deepcopy(self.data); d['records'][-1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): a.replay(d)

    def test_request_raw_and_artifact_mutation_rejected_even_with_fresh_value_hash(self):
        for fault in ('request', 'raw', 'artifact'):
            d = copy.deepcopy(self.data)
            if fault == 'request':
                r = d['records'][0]; r['request']['prompt'] += 'changed'; r['request_sha256'] = a.engine.plan.digest(r['request'])
            elif fault == 'raw':
                r = next(r for r in d['records'] if r['raw_present']); r['raw'] += 'changed'
                r['raw_value_sha256'] = a.engine.plan.digest(r['raw'])
            else:
                r = next((r for r in d['records'] if 'card' in r), d['records'][0]); r['card'] = {'prompt': 'borrowed'}
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_gate_denominator_missing_and_disputed_inclusion_are_recomputed(self):
        for fault in ('gate', 'denominator', 'missing', 'disputed_inclusion'):
            d = copy.deepcopy(self.data)
            if fault == 'gate': d['status']['control_gates']['j16']['qualified'] = not d['status']['control_gates']['j16']['qualified']
            elif fault == 'denominator': d['status']['scores']['methods']['split']['strict_all_parents_and_reads']['joint']['planned'] = 22
            elif fault == 'missing': d['status']['scores']['methods']['split']['strict_all_parents_and_reads']['joint']['missing'] += 1
            else: d['status']['scores']['disputed_observations_not_scored'][0]['included_in_primary_or_gate'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_removal_or_duplicate_execution_cannot_improve_the_record(self):
        for fault in ('remove', 'duplicate'):
            d = copy.deepcopy(self.data)
            if fault == 'remove':
                r = d['records'].pop(); d['status']['attempt_reservations'] -= 1; d['status']['unused_slots_expire'] += 1
                d['status']['local_cli_child_intents'] -= int(r['local_cli_child_intent'])
            else: d['records'][1]['execution_id'] = d['records'][0]['execution_id']
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_usage_subsets_and_runtime_integrity_cannot_change(self):
        for fault in ('usage', 'subset', 'runtime'):
            d = copy.deepcopy(self.data)
            if fault == 'runtime': d['implementation_sha256'] = {}
            else:
                row = next(r for r in d['records'] if r['usage_rows'])['usage_rows'][0]
                if fault == 'usage': del row['input_tokens']
                else: row['cached_input_tokens'] = row['input_tokens']+1
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_manual_annotation_is_not_independent_semantics_new_generation_or_default(self):
        for field,value in [('post_hoc_case_informed_developer_annotation',False),
                ('fresh_generation_stability_test',True),('semantic_decomposition_independently_accepted',True),
                ('old_semantic_equivalence_verified',True),('validates_h93_or_development',True),
                ('independent_holdout',True),('production_default_changed',True)]:
            d=copy.deepcopy(self.data);d[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):a.replay(d)
        d=copy.deepcopy(self.data);d['fixed_views'][0]['prompt']+='changed'
        with self.assertRaises(ValueError):a.replay(d)


if __name__ == '__main__': unittest.main()
