import importlib.util
import json
import unittest
from pathlib import Path

from tests.test_real_task_history import fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-recording-card-v1/protocol.py'
spec = importlib.util.spec_from_file_location('recording_protocol', path)
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)


class RecordingCardTests(unittest.TestCase):
    def test_source_boundary_and_read_inputs(self):
        case = fixture()
        sources, extraction, controls = protocol.prepare(case)
        prior = json.loads(extraction['prompt'].split('SOURCE_JSON:\n', 1)[1])
        self.assertEqual(prior, sources)
        self.assertEqual([m['text'] for m in prior['sources']], [m['text'] for m in case['messages'][:2]])
        self.assertNotIn(case['quality_gate'], extraction['prompt'])
        for message in case['messages'][2:]:
            self.assertNotIn(message['text'], extraction['prompt'])
        card = 'fixture card\n'
        rendered = protocol.card_request(controls['none'], card)
        data = json.loads(rendered['prompt'].split('INPUT_JSON:\n')[1])
        full = json.loads(controls['full']['prompt'].split('INPUT_JSON:\n')[1])
        self.assertEqual(data, {'memory': card, 'current': full['current']})
        with self.assertRaises(ValueError):
            protocol.card_request(controls['full'], card)
        with self.assertRaises(ValueError):
            protocol.card_request(controls['none'], '字' * 769)
