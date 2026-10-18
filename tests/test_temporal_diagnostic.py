import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runaway import temporal_diagnostic as td, temporal as t, generation


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        runtime = self.base / 'runtime.json'
        runtime.write_text(json.dumps({'python_executable': 'fake-unused', 'tokenizer': {'model_sha256': 'fake-unused'}, 'tokenizer_path': 'fake-unused'}))
        self.plan = self.base / 'plan'
        td.prepare(self.plan, runtime)
        self.people = td.read(self.plan / 'development.private.json')
        self.count = 0

    def tearDown(self):
        self.temp.cleanup()

    def fake(self, prompt, model, **kwargs):
        self.count += 1
        self.assertEqual(kwargs['timeout'], 180)
        if kwargs['schema'] == t.SCHEMA:
            for person in self.people:
                if t.make_request(person['sources']) == prompt:
                    answer = person['annotation']
                    break
            else:
                raise AssertionError('Unknown extraction input')
            self.assertNotIn('"gold"', prompt)
            self.assertNotIn('"cases"', prompt)
            self.assertNotIn('"annotation"', prompt)
        else:
            payload = json.loads(prompt.split('\nINPUT_JSON:\n', 1)[1])
            query = payload['queries'][0]['id']
            person = next(p for p in self.people if p['cases'][0]['public']['id'] == query)
            full = payload['memory'] == person['sources']['sources'][0]['text']
            answer = {c['public']['id']: c['gold'] if full or c['public']['task'] == 'current_choice' else 'U' for c in person['cases']}
        return json.dumps(answer, ensure_ascii=False), {'backend': 'fake_no_service', 'usage': [{'input_tokens': 1, 'output_tokens': 1}]}

    def execute(self, backend=None, name='out', count=lambda text: 100):
        with patch.object(generation, 'codex_generate', side_effect=AssertionError('No new service calls')):
            return td.execute(self.plan, self.base / name, backend=backend or self.fake, count=count)

    def test_six_call_path_and_retained_current_historical_denominators(self):
        report = self.execute()
        self.assertEqual((report['status'], self.count), ('complete', 6))
        self.assertEqual(report['external_model_calls'], 0)
        self.assertEqual(report['stage_attempts'], td.STAGES)
        self.assertEqual(report['scores']['full_history']['joint']['correct'], 20)
        self.assertEqual(report['scores']['temporal']['current_choice'], {'correct': 16, 'missing': 0, 'unknown_answers': 0, 'planned': 16})
        self.assertEqual(report['scores']['temporal']['historical_reconstruction'], {'correct': 0, 'missing': 0, 'unknown_answers': 4, 'planned': 4})
        self.assertFalse(report['real_person_fidelity_verified'])
        self.assertTrue(all(all(checks) for checks in report['source_to_event_checks'].values()))

    def test_reader_or_source_graph_failure_stops_no_retry_or_cherry_picking(self):
        def wrong_reader(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            value = json.loads(raw)
            if kwargs['schema'] != t.SCHEMA:
                value = {k: 'U' for k in value}
            return json.dumps(value), provenance
        report = self.execute(wrong_reader)
        self.assertEqual((report['status'], self.count), ('stopped', 2))
        self.assertEqual(report['scores']['temporal']['joint']['missing'], 20)
        self.count = 0
        def wrong_graph(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            if kwargs['schema'] == t.SCHEMA:
                value = json.loads(raw)
                # Flatten the nested retraction into another retraction of the constraint.
                value['events'][-1]['target'] = 'r16'
                raw = json.dumps(value)
            return raw, provenance
        report = self.execute(wrong_graph, 'bad-graph')
        self.assertEqual((report['status'], self.count), ('stopped', 3))
        self.assertEqual(report['stop_reason']['kind'], 'source_to_event_semantics_failed')
        self.assertEqual(report['scores']['temporal']['joint']['missing'], 20)

    def test_actual_budget_and_unknown_usage_stop_the_entire_remaining_batch(self):
        report = self.execute(name='budget', count=lambda text: 385)
        self.assertEqual((report['status'], self.count), ('stopped', 3))
        self.assertEqual(report['stop_reason']['kind'], 'whole_prompt_budget_failed')
        self.count = 0
        def unknown_usage(*args, **kwargs):
            raw, _ = self.fake(*args, **kwargs)
            return raw, {'backend': 'fake_unknown_usage'}
        report = self.execute(unknown_usage, 'unknown')
        self.assertEqual((report['status'], self.count), ('stopped', 1))
        self.assertEqual(report['calls']['executions_missing_usage'], 1)
        self.assertEqual(report['scores']['temporal']['joint']['missing'], 20)

    def test_unapproved_execution_and_drift_block_before_service(self):
        with patch.object(generation, 'codex_generate', side_effect=AssertionError('No new service calls')):
            with self.assertRaisesRegex(ValueError, 'human approval'):
                td.execute(self.plan, self.base / 'real')
        self.assertFalse((self.plan / 'execution-intent.json').exists())
        path = self.plan / 'jobs.json'
        path.write_text(path.read_text() + ' ')
        with self.assertRaises(ValueError):
            td.preflight(self.plan)


if __name__ == '__main__':
    unittest.main()
