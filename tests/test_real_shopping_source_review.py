import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-shopping-source-review-v1/study.py'
spec = importlib.util.spec_from_file_location('shopping_review', path)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class SourceReviewTests(unittest.TestCase):
    def test_review_inputs_are_exactly_parent_and_prior_extractor(self):
        _, requests = study.previous.prepare(fixture())
        original = requests['candidate']
        parent = 'A draft with a newline\nand quotes "like this"'
        reviewed = study.review_request(original, parent)
        prefix, payload = reviewed['prompt'].split('\n\n', 1)
        self.assertEqual(json.loads(prefix.removeprefix('DRAFT_JSON:\n')), parent)
        self.assertEqual(payload, original['prompt'])
        self.assertEqual(reviewed['schema'], original['schema'])
        self.assertEqual(reviewed['system'], original['system'] + '\n' + study.REVIEW_GUIDANCE)
        for invalid in ('', 'a' * 769):
            with self.assertRaises(ValueError):
                study.review_request(original, invalid)

    def test_two_reads_per_fixed_view_with_same_reader(self):
        _, requests = study.previous.prepare(fixture())
        cards = {arm: 'card ' + arm for arm in study.DELIVERIES}
        self.assertEqual(Counter(study.DELIVERIES), dict.fromkeys(cards, 2))
        self.assertEqual(len(cards), 4)
        self.assertEqual(study.REVIEWS, ('candidate1', 'candidate2'))
        for arm in cards:
            request = study.delivery(arm, requests, cards)
            self.assertEqual(request, study.previous.delivery(arm, requests, cards))
            body = json.loads(request['prompt'].split('INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'current', 'memory'})
            self.assertEqual(body['memory'], cards[arm])
