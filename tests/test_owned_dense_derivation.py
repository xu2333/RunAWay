"""Derived layouts cannot overwrite old failures or turn into model evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dense_derivation_tests', ROOT / 'benchmarks/owned-dense-v1/evidence.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class DenseDerivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = e.p.read(e.DEFAULT)

    def test_both_original_failed_producers_have_exact_in_budget_new_layouts(self):
        result = e.check()
        self.assertEqual(result['dense_characters'], [1536, 1413])
        self.assertTrue(result['all_literal_projections_equal'])
        self.assertEqual(result['new_model_calls'], 0)
        self.assertFalse(result['behavioral_fidelity_verified'])
        for parent in self.data['parents']:
            decoded = e.codec.parse(parent['dense_prompt'])
            expected = e.codec.grouped_projection(decoded)
            self.assertEqual(expected, parent['semantic_projection'])
            self.assertEqual(e.codec.base.grouped.render_public(expected), parent['expanded_prompt'])

    def test_changed_projection_or_dense_literal_is_not_an_equal_derivation(self):
        for fault in ('projection', 'text'):
            d = copy.deepcopy(self.data)
            if fault == 'projection':
                d['parents'][0]['semantic_projection']['unknowns'][0] += 'changed'
            else:
                d['parents'][0]['dense_prompt'] += 'changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                e.replay(d)

    def test_parent_or_original_failure_cannot_be_replaced(self):
        for fault in ('parent', 'failure'):
            d = copy.deepcopy(self.data)
            if fault == 'parent':
                d['parents'][0]['raw_value_sha256'] = d['parents'][1]['raw_value_sha256']
            else:
                d['parents'][0]['original_failure'] = {}
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                e.replay(d)

    def test_offline_projection_cannot_be_claimed_as_fidelity_or_repaired_scope(self):
        for key in ('behavioral_fidelity_verified', 'replaces_closed_products', 'new_service_authority', 'production_default_changed'):
            d = copy.deepcopy(self.data); d[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                e.replay(d)


if __name__ == '__main__':
    unittest.main()
