"""Replay the sealed comparison and accounting without another service call."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from runaway.card import canonical, digest
from runaway.execution_ledger import collect, summarize
from runaway import taste_contract as tc
from runaway.taste_executor import gate, score_rows
from runaway.taste_plan import reader_job
from runaway.synthetic_metric import score as legacy_score

ROOT = Path(__file__).resolve().parents[1]


class ComparisonEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        with zipfile.ZipFile(ROOT / 'examples/comparison-evidence.synthetic.zip') as archive:
            for name in archive.namelist():
                path = Path(name)
                if path.is_absolute() or '..' in path.parts: raise AssertionError('Unsafe archive')
            archive.extractall(cls.root)
        cls.replay = cls.root / 'd0016'
        cls.raw = json.loads((cls.replay / 'raw-report.synthetic.json').read_text())
        cls.world = json.loads((cls.replay / 'fixtures.synthetic.json').read_text())
        cls.answers = json.loads((cls.replay / 'fresh-answers.synthetic.json').read_text())

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_manifest_and_explicit_synthetic_scope(self):
        manifest = json.loads((self.replay / 'manifest.json').read_text())
        for name, expected in manifest.items():
            self.assertEqual(hashlib.sha256((self.replay / name).read_bytes()).hexdigest(), expected)
            for forbidden in ('approval', 'auth.json', 'central-agent', 'unit-plan'):
                self.assertNotIn(forbidden, name)
        self.assertEqual(self.world['origin'], 'fully_synthetic')
        summary = json.loads((self.replay / 'report.synthetic.json').read_text())
        self.assertEqual(summary, json.loads((ROOT / 'examples/comparison-results.synthetic.json').read_text()))
        self.assertFalse(self.raw['real_person_fidelity_verified'])

    def test_all_fresh_scores_and_original_gates(self):
        for condition, expected in self.raw['fresh_scores'].items():
            self.assertEqual(score_rows(self.world, self.answers.get(condition, {})), expected)
            self.assertEqual([expected[t]['planned'] for t in ('current_choice', 'historical_reconstruction', 'joint')], [32, 16, 48])
        full = self.raw['fresh_scores']['full_history']['current_choice']
        for name, expected in self.raw['gates'].items():
            self.assertEqual(gate(name, self.raw['fresh_scores'][name]['current_choice'], full), expected)
            self.assertTrue(expected['passed'])
        for name in ('current_browser', 'new_bound'):
            row = self.raw['fresh_scores'][name]
            self.assertEqual((row['current_choice']['correct'], row['historical_reconstruction']['correct']), (32, 2))

    def test_every_reader_answer_links_to_raw_service_checkpoint(self):
        jobs = [json.loads(s) for s in (self.replay / 'reader-jobs.synthetic.jsonl').read_text().splitlines()]
        legacy = json.loads((self.replay / 'legacy-answers.synthetic.json').read_text())
        for job in jobs:
            key = digest(canonical(job['request']))
            response = json.loads((self.replay / 'calls' / (key + '.response.json')).read_text())
            source = legacy if job['phase'] == 'diagnostic' else self.answers
            self.assertEqual(source[job['id']][job['persona_id']], response['answer'])
        lookup = {p['id']: p for p in self.world['people']}
        for memory in self.raw['memories']:
            pid, condition = memory['persona_id'], memory['condition']
            queries = [c['public'] for c in lookup[pid]['cases']]
            request = reader_job('actual_memory', pid, memory['text'], queries, tc.READER, 20, 'actual_memory')['request']
            key = digest(canonical(request))
            response = json.loads((self.replay / 'calls' / (key + '.response.json')).read_text())
            self.assertEqual(self.answers[condition][pid], response['answer'])

    def test_old_diagnostics_recompute_without_changing_old_baseline(self):
        with zipfile.ZipFile(ROOT / 'examples/pilot-evidence.synthetic.zip') as archive:
            world = json.loads(archive.read('d0015/metric/world.private.json'))
        people = [p for p in world['people'] if p['split'] == 'eval']
        answers = json.loads((self.replay / 'legacy-answers.synthetic.json').read_text())
        for name, expected in self.raw['legacy_diagnostic_scores'].items():
            self.assertEqual(legacy_score(people, answers.get(name, {})), expected)
            self.assertEqual(expected['planned'], 48)
        self.assertEqual(hashlib.sha256((ROOT / 'examples/pilot-evidence.synthetic.zip').read_bytes()).hexdigest(),
                         'f4cfef8019bbbe8b7877d730f1c40594a54e921dc3bc40ebdb22f828600ceb73')

    def test_actual_usage_and_single_attempts_recompute(self):
        ledger = summarize(collect(self.replay))
        self.assertEqual(ledger, self.raw['calls'])
        self.assertEqual(ledger['execution_records'], 24)
        self.assertEqual(ledger['unique_request_fingerprints'], 24)
        self.assertEqual(ledger['outcomes'], {'completed': 24})
        self.assertEqual(ledger['executions_missing_usage'], 0)
        self.assertEqual(self.raw['status'], 'complete')
        self.assertEqual(self.raw['local_validation_failures'], {})


if __name__ == '__main__': unittest.main()
