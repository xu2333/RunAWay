"""Damage actual fixed-parent question-contract read evidence; never call a model service."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('question_contract_evidence_tests', ROOT / 'scripts/replay_question_contract_diagnostic.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


class QuestionContractEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = a.engine.plan.read(a.DEFAULT)

    def test_closed8fixed_views_preserve12cases_without_new_generation(self):
        r=a.check()
        self.assertLessEqual(r['actual_original_attempts'],8)
        self.assertEqual((r['new_model_calls'],r['new_extractions'],r['inherited_parent_generations']),(0,0,1))
        for method in a.engine.plan.METHODS:
            c=r['scores']['methods'][method]['strict_both_reads']
            self.assertEqual((c['joint']['planned'],c['known']['planned'],c['unknown']['planned'],c['personal_known']['planned']),(12,8,4,5))
        self.assertFalse(r['fresh_generation_stability_test'])
        self.assertTrue(r['posthoc_task_clarification'])
        self.assertFalse(r['semantic_equivalence_independently_accepted'])

    def test_source_reference_disputed_mask_and_legacy_annotation_cannot_drift(self):
        for fault in ('source', 'reference', 'disputed', 'legacy','question'):
            d = copy.deepcopy(self.data)
            if fault == 'source': d['sources']['e0']['sources'][0]['text'] += 'changed'
            elif fault == 'reference': d['reference_rows'][0]['gold'] = 'changed'
            elif fault == 'disputed': d['disputed_rows'] = [{'foreign':'row'}]
            elif fault=='legacy': d['legacy_rows'][0]['gold'] = 'changed'
            else: d['queries']['explicit'][4]['scenario']+='changed'
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
            if fault == 'gate': d['status']['control_gates']['original']['qualified'] = not d['status']['control_gates']['original']['qualified']
            elif fault == 'denominator': d['status']['scores']['methods']['explicit']['strict_both_reads']['joint']['planned'] = 22
            elif fault == 'missing': d['status']['scores']['methods']['explicit']['strict_both_reads']['joint']['missing'] += 1
            else: d['status']['scores']['answers_per_case_per_view'] = 8
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
        for field,value in [('posthoc_task_clarification',False),
                ('fresh_generation_stability_test',True),('semantic_equivalence_independently_accepted',True),
                ('automatic_encoder_fixed',True),('validates_all_fresh48',True),
                ('uniquely_proves_question_wording_cause',True),('answers_per_primary_case',8),
                ('inherited_parents',2),('same_memory_across_conditions',False),('packets_isolated_calls',False),
                ('old_question_gold_replaced',True),('semantic_paraphrase_equivalence_accepted',True),
                ('independent_holdout',True),('production_default_changed',True)]:
            d=copy.deepcopy(self.data);d[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):a.replay(d)
        d=copy.deepcopy(self.data);d['fixed_views'][0]['prompt']+='changed'
        with self.assertRaises(ValueError):a.replay(d)


if __name__ == '__main__': unittest.main()
