import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-model-selection-transfer-v1/protocol.py'
spec = importlib.util.spec_from_file_location('model_selection_transfer', path)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ModelSelectionTransferTests(unittest.TestCase):
    def test_prior_only_and_frozen_encoder(self):
        case = fixture()
        sources, request, controls = p.prepare(case)
        expected_sources, old, original_controls = p.cards.prepare(case)
        self.assertEqual(request, p.switch.switch_request(p.boundary.candidate_request(old)))
        self.assertEqual(json.loads(request['prompt'].split('SOURCE_JSON:\n')[1]), expected_sources)
        self.assertEqual(sources, expected_sources)
        self.assertEqual(controls, original_controls)
        self.assertNotIn(case['quality_gate'], request['prompt'])

    def test_each_fixed_card_and_each_control_read_twice(self):
        _, _, controls = p.prepare(fixture())
        fixtures = {'card1': 'first\n', 'card2': 'second\n'}
        self.assertEqual(len(p.EXTRACTIONS), 2)
        counts = Counter(p.DELIVERIES)
        self.assertEqual(counts, Counter({k: 2 for k in ('none','full','card1_old','card1_new','card2_old','card2_new')}))
        for arm in ('none', 'full'):
            self.assertEqual(p.make_delivery(arm, controls, fixtures), controls[arm])
        for name, fixed in fixtures.items():
            old = p.make_delivery(name + '_old', controls, fixtures)
            new = p.make_delivery(name + '_new', controls, fixtures)
            self.assertEqual(new, p.reader.revised_request(old))
            self.assertEqual(json.loads(old['prompt'].split('INPUT_JSON:\n')[1]), {
                'current': json.loads(controls['none']['prompt'].split('INPUT_JSON:\n')[1])['current'],
                'memory': fixed})
        with self.assertRaises(ValueError):
            p.make_delivery('card1_oracle', controls, fixtures)
