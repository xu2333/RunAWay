import importlib.util
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_recording_card import protocol
from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-fixed-card-reader-v1/reader.py'
spec = importlib.util.spec_from_file_location('fixed_card_reader', path)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class FixedCardReaderTests(unittest.TestCase):
    def test_only_reader_instruction_changes(self):
        _, _, controls = protocol.prepare(fixture())
        old = protocol.card_request(controls['none'], 'unmodified fixture\n')
        new = reader.revised_request(old)
        self.assertEqual(new, dict(old, system=protocol.SYSTEM + '\n' + reader.GUIDANCE))
        self.assertEqual(old['system'], protocol.SYSTEM)
        for cue in ('游戏', '迁移', '复用', '菜单', '战斗', '控制器', '572', '575'):
            self.assertNotIn(cue, reader.GUIDANCE)

    def test_both_cards_get_two_reads_by_each_reader(self):
        cells = {(card, method) for card in ('575', '572') for method in ('old', 'new')}
        self.assertEqual(Counter(reader.ORDER), Counter({cell: 2 for cell in cells}))
        self.assertEqual(set(reader.ORDER[:4]), cells)
        self.assertEqual(reader.ORDER[:4], reader.ORDER[4:][::-1])
