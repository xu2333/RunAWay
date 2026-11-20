import importlib.util
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_model_selection_transfer import fixture, p

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-decision-boundary-reader-v1/reader.py'
spec = importlib.util.spec_from_file_location('decision_reader', path)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class DecisionBoundaryReaderTests(unittest.TestCase):
    def test_only_system_changes_from_actual_prior_reader(self):
        _, _, controls = p.prepare(fixture())
        prior = p.reader.revised_request(p.cards.card_request(controls['none'], 'header\n\nfixture\n'))
        self.assertEqual(reader.revised_request(prior),
                         dict(prior, system=prior['system'] + '\n' + reader.GUIDANCE))
        for term in ('排名', '改题', '榜', '题库', '校准', '冻结', 'qwen', 'aa index', 'rank'):
            self.assertNotIn(term, reader.GUIDANCE.casefold())

    def test_two_reads_per_fixed_parent_and_method(self):
        self.assertEqual(Counter(reader.ORDER), {(p, m): 2 for p in ('candidate1','candidate2')
                                                 for m in ('prior','revised')})
        self.assertEqual(reader.ORDER[:4], reader.ORDER[4:][::-1])
