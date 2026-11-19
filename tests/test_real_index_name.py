import importlib.util
import unittest
from collections import Counter
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-index-name-v1/diagnostic.py'
spec = importlib.util.spec_from_file_location('index_diagnostic', path)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class IndexNameTests(unittest.TestCase):
    def test_only_insert_name_and_keep_card_bytes(self):
        for parent, phrase in d.TARGET_PHRASES.items():
            card = 'header\n\n' + phrase + '。\n'
            self.assertEqual(d.fixed_view(parent, card, 'original'), card)
            named = d.fixed_view(parent, card, 'named')
            self.assertEqual(named.replace(d.PARENTHETICAL, ''), card)
            self.assertIn(d.PARENTHETICAL + '前列模型', named)
            self.assertEqual(len(named) - len(card), 10)
            for invalid in (card * 2, 'missing', card + 'aa index', 'x' * 768 + card):
                with self.assertRaises(ValueError):
                    d.fixed_view(parent, invalid, 'named')

    def test_balanced_schedule_and_joint_score(self):
        self.assertEqual(Counter(d.ORDER), {(p, v): 2 for p in d.TARGET_PHRASES for v in ('original', 'named')})
        criteria = dict.fromkeys((*d.PLAN_CRITERIA, 'independence'), 'met')
        self.assertTrue(d.endpoints(criteria)['plan_and_independence'])
        criteria['independence'] = 'partial'
        self.assertEqual(d.endpoints(criteria), {'plan': True, 'plan_and_independence': False})
        criteria['calibration'] = 'absent'
        self.assertFalse(d.endpoints(criteria)['plan'])
