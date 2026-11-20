import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-shopping-scope-v1/study.py'
spec = importlib.util.spec_from_file_location('shopping_study', path)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class ShoppingScopeTests(unittest.TestCase):
    def test_extraction_and_all_four_delivery_conditions(self):
        sources, requests = study.prepare(fixture())
        self.assertEqual(requests['candidate'], study.encoder.candidate_request(requests['original']))
        self.assertEqual(json.loads(requests['original']['prompt'].split('SOURCE_JSON:\n')[1]), sources)
        cards = {arm: 'card ' + arm for arm in study.EXTRACTIONS}
        expected = {'none', 'full', *cards}
        self.assertEqual(Counter(study.DELIVERIES), {arm: 2 for arm in expected})
        for arm in expected:
            req = study.delivery(arm, requests, cards)
            prior = requests[arm] if arm in ('none','full') else study.transfer.cards.card_request(requests['none'], cards[arm])
            self.assertEqual(req, study.transfer.reader.revised_request(prior))
            body = json.loads(req['prompt'].split('INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'current'} | ({'memory'} if arm in cards else {'history'} if arm == 'full' else set()))
            if arm in cards:
                self.assertEqual(body['memory'], cards[arm])
        self.assertEqual(len({study.delivery(arm, requests, cards)['system'] for arm in expected}), 1)

    def test_independent_requirements(self):
        criteria = dict.fromkeys(study.REQUIREMENTS, 'met')
        self.assertTrue(study.joint(criteria))
        for key in criteria:
            self.assertFalse(study.joint(dict(criteria, **{key: 'partial'})))
