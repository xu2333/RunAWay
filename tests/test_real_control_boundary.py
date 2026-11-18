import importlib.util
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_recording_card import protocol
from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-control-boundary-v1/comparison.py'
spec = importlib.util.spec_from_file_location('boundary_comparison', path)
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class ControlBoundaryTests(unittest.TestCase):
    def test_only_extraction_instruction_changes(self):
        sources, original, controls = protocol.prepare(fixture())
        candidate = comparison.candidate_request(original)
        self.assertEqual(candidate, dict(original, system=original['system'] + '\n' + comparison.GUIDANCE))
        self.assertNotIn(comparison.GUIDANCE, original['system'])
        self.assertIn('qualifies', candidate['system'])
        for arm in controls.values():
            self.assertNotIn(comparison.GUIDANCE, arm['system'] + arm['prompt'])
        self.assertTrue(sources['sources'])

    def test_all_four_cards_have_two_readings(self):
        generations = comparison.EXTRACTIONS
        self.assertEqual(len(set(generations)), 4)
        self.assertEqual(Counter(comparison.DELIVERIES),
                         Counter({arm: 2 for arm in (*generations, 'none', 'full')}))
