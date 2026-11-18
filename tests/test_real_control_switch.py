import importlib.util
import unittest
from pathlib import Path

from tests.test_real_control_boundary import comparison
from tests.test_real_recording_card import protocol
from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-control-switch-v1/encoder.py'
spec = importlib.util.spec_from_file_location('switch_encoder', path)
encoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(encoder)


class SwitchExtractionTests(unittest.TestCase):
    def test_only_extends_previous_encoder_instruction(self):
        _, original, controls = protocol.prepare(fixture())
        previous = comparison.candidate_request(original)
        candidate = encoder.switch_request(previous)
        self.assertEqual(previous['system'], original['system'] + '\n' + comparison.GUIDANCE)
        self.assertEqual(candidate, dict(previous, system=previous['system'] + '\n' + encoder.SWITCH_GUIDANCE))
        self.assertNotIn(encoder.SWITCH_GUIDANCE, previous['system'])
        for request in controls.values():
            self.assertNotIn(encoder.SWITCH_GUIDANCE, request['prompt'] + request['system'])

    def test_addition_names_no_case_actions_or_source_identifiers(self):
        for literal in ('菜单', '战斗', '游戏', '移动', '视角', '触控', '控制器', 'm61'):
            self.assertNotIn(literal, encoder.SWITCH_GUIDANCE)
