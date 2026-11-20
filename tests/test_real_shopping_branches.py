import unittest
from collections import Counter
from pathlib import Path
import importlib.util

from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-shopping-branches-v1/study.py'
spec = importlib.util.spec_from_file_location('shopping_branches', path)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class ShoppingBranchTests(unittest.TestCase):
    def test_same_source_and_reader_with_only_guidance_changed(self):
        case = fixture()
        src, requests = study.prepare(case)
        prior_src, prior = study.previous.prepare(case)
        self.assertEqual(src, prior_src)
        self.assertEqual(requests['original'], prior['candidate'])
        self.assertEqual(requests['candidate'], dict(prior['candidate'],
                         system=prior['candidate']['system'] + '\n' + study.GUIDANCE))
        cards = {arm: 'fixture ' + arm for arm in study.EXTRACTIONS}
        self.assertEqual(Counter(study.DELIVERIES), {arm: 2 for arm in cards})
        for arm in cards:
            self.assertEqual(study.delivery(arm, requests, cards),
                             study.previous.delivery(arm, prior, cards))

    def test_no_substitution_between_conditional_benefits(self):
        scores = dict.fromkeys(study.REQUIREMENTS, 'met')
        self.assertTrue(study.joint(scores))
        for key in ('tv_benefit', 'tablet_benefit', 'cashback', 'membership', 'television', 'bundle', 'quality'):
            self.assertFalse(study.joint(dict(scores, **{key: 'partial'})))
