"""Damage actual fresh-source contrast evidence; never call a model service."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fresh_contrast_evidence_tests', ROOT / 'scripts/replay_fresh_source_contrast.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


class FreshContrastEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = a.engine.plan.read(a.DEFAULT)

    def test_closed_actual_scope_preserves48case_and_eight_answer_endpoint(self):
        r = a.check()
        self.assertLessEqual(r['actual_original_attempts'], 46)
        self.assertEqual((r['new_model_calls'], r['answers_per_primary_case'], r['fresh_generations_planned']), (0, 8, 8))
        for method in ('tail','card'):
            scores = r['scores']['per_method_strict'][method]
            self.assertEqual((scores['joint']['planned'], scores['known']['planned'], scores['unknown']['planned'],
                              scores['personal_known']['planned']), (48, 32, 16, 20))
        self.assertFalse(r['independent_generalization']); self.assertEqual(r['template_families'],2)
        self.assertFalse(r['pair_rescoring_independent'])

    def test_source_reference_disputed_mask_and_legacy_annotation_cannot_drift(self):
        for fault in ('source', 'reference', 'disputed', 'legacy', 'design'):
            d = copy.deepcopy(self.data)
            if fault == 'source': d['sources']['t0']['sources'][0]['text'] += 'changed'
            elif fault == 'reference': d['reference_rows'][0]['gold'] = 'changed'
            elif fault == 'disputed': d['disputed_rows'] = [{'unexpected':'j16'}]
            elif fault == 'legacy': d['legacy_rows'][0]['gold'] = 'changed'
            else: d['design']['primary_cases'] = 96
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_profile_generation_or_method_swaps_cannot_borrow_another_card(self):
        for field, value in (('profile', 'foreign'), ('generation', 8), ('method', 'scope-v1'),('view','foreign')):
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
        for fault in ('gate', 'denominator', 'missing', 'disputed_inclusion', 'pair_independence', 'pair_score'):
            d = copy.deepcopy(self.data)
            if fault == 'gate': d['status']['control_gates']['t0']['qualified'] = not d['status']['control_gates']['t0']['qualified']
            elif fault == 'denominator': d['status']['scores']['per_method_strict']['card']['joint']['planned'] = 22
            elif fault == 'missing': d['status']['scores']['per_method_strict']['card']['joint']['missing'] += 1
            elif fault == 'disputed_inclusion': d['status']['scores']['disputed_observations_not_scored']=[{'unexpected':'j16'}]
            elif fault == 'pair_independence': d['status']['scores']['paired_diagnostic_is_algebraically_dependent'] = False
            else: d['status']['scores']['pair_rescoring'][0]['opposite_personal_reference']['joint']['planned'] = 0
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

    def test_false_independent_baseline_or_new_default_claims_rejected(self):
        for field,value in [('answers_per_primary_case',4),('fresh_generations_planned',1),
                ('independent_reference_acceptance',True),('independent_generalization',True),
                ('encoder_changed_for_new_sources',True),('pair_rescoring_independent',True),
                ('token_matched_tail',True),('optimal_tail_selection',True),
                ('source_only_model_generated_annotation',False),('development_informed',False),
                ('template_paired_families',False),('independent_holdout',True),('production_default_changed',True)]:
            d = copy.deepcopy(self.data); d[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): a.replay(d)


if __name__ == '__main__': unittest.main()
