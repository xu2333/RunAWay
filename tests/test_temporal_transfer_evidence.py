import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class TransferEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(ROOT / 'examples/temporal-transfer-evidence.synthetic.zip') as archive:
            if any(not n.startswith('d0025/') or '..' in Path(n).parts for n in archive.namelist()): raise ValueError('Unsafe evidence member')
            archive.extractall(cls.temp.name)
        cls.base = Path(cls.temp.name) / 'd0025'

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def replay(self, optimized=False):
        return subprocess.run([sys.executable, *(['-O'] if optimized else []), '-B', str(ROOT / 'scripts/replay_temporal_transfer_evidence.py'), '--base', str(self.base)], capture_output=True, text=True)

    def test_stopped_actual_batch_replays_with_missing_denominators(self):
        result = self.replay(); self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(result.stdout); stored = json.loads((self.base / 'report.synthetic.json').read_text())
        self.assertTrue(stored['checks']['actual_tokenizer_recounted']); actual['checks']['actual_tokenizer_recounted'] = True
        self.assertEqual(actual, stored)
        self.assertEqual(stored, json.loads((ROOT / 'examples/temporal-transfer-results.synthetic.json').read_text()))
        self.assertEqual(stored['status'], 'stopped'); self.assertFalse(stored['strict_current_target_passed'])
        self.assertEqual(stored['calls']['execution_records'], 5); self.assertEqual(stored['calls']['known_usage']['total_tokens'], 82129)
        self.assertEqual(stored['scores']['full_history']['joint']['correct'], 300)
        self.assertEqual(stored['scores']['temporal']['current_choice']['missing'], 224)
        self.assertEqual(stored['scores']['temporal']['historical_reconstruction']['missing'], 76)
        self.assertEqual(stored['scores']['temporal']['joint']['planned'], 300)
        self.assertEqual(stored['paired_statistical_units'], 2); self.assertFalse(stored['real_person_fidelity_verified'])

    def test_manifest_source_input_bindings_and_privacy(self):
        manifest = json.loads((self.base / 'manifest.json').read_text())
        self.assertEqual(set(manifest), {str(p.relative_to(self.base)) for p in self.base.rglob('*') if p.is_file() and p.name != 'manifest.json'})
        for name, sha in manifest.items():
            data = (self.base / name).read_bytes(); self.assertEqual(hashlib.sha256(data).hexdigest(), sha)
            self.assertNotIn('approval', name); self.assertNotIn('execution-intent', name)
            if not name.startswith('frozen-source/'):
                for private in ('/Users/', 'human_source', 'access_token', 'refresh_token'): self.assertNotIn(private, data.decode())
        c = json.loads((self.base / 'contract.synthetic.json').read_text())
        for name, sha in c['source_hashes'].items(): self.assertEqual(hashlib.sha256((self.base / 'frozen-source' / name).read_bytes()).hexdigest(), sha)
        for name, sha in c['input_hashes'].items(): self.assertEqual(hashlib.sha256((self.base / c['input_aliases'][name]).read_bytes()).hexdigest(), sha)

    def test_tampered_gate_or_usage_is_rejected(self):
        for name in ('raw-report.synthetic.json', str(next((self.base / 'calls').glob('*.response.json')).relative_to(self.base))):
            p = self.base / name; original = p.read_bytes()
            try:
                d = json.loads(original)
                if name.startswith('calls/'): d['provenance']['usage'][0]['input_tokens'] += 1
                else: next(iter(d['source_to_event_checks'].values()))['event_span_coverage'] = True
                p.write_text(json.dumps(d)); self.assertNotEqual(self.replay().returncode, 0)
            finally: p.write_bytes(original)

    def test_optimized_mode_cannot_skip_checks(self):
        result = self.replay(True); self.assertNotEqual(result.returncode, 0); self.assertIn('Evidence replay requires assertions enabled', result.stderr)

    def test_actual_omitted_conflict_is_not_equivalent_to_unobserved_even_when_both_answer_unknown(self):
        # Hand-annotation is a regression fixture, never a repaired model result.
        from runaway import temporal as t
        r = json.loads((self.base / 'raw-report.synthetic.json').read_text()); original = next(iter(r['artifacts'].values()))
        self.assertEqual(t.resolve(original, '分享形式', {})['status'], 'unobserved')
        answer = copy.deepcopy(original['extraction']); units = {s['text'].split('（', 1)[0]: s for s in original['source_spans'] if s['text'].startswith('记录')}
        selected = []
        for eid, action in [('rc1', '短文'), ('rc2', '语音')]:
            span = units['记录' + eid]; selected.append(span['id'])
            answer['events'].append({'id': eid, 'kind': 'regular', 'domain': '分享形式', 'action': action, 'strength': 2, 'when_all': [], 'target': '', 'span_ids': [span['id']]})
        answer['unmodeled'] = [u for u in answer['unmodeled'] if u['span_id'] not in selected]
        corrected_fixture = t.bind(answer, original['sources'])
        self.assertEqual(t.resolve(corrected_fixture, '分享形式', {})['status'], 'conflict')
        self.assertIsNone(t.resolve(original, '分享形式', {})['action']); self.assertIsNone(t.resolve(corrected_fixture, '分享形式', {})['action'])
        self.assertNotIn('【分享形式】', t.render(original, 10000)['text'])
        self.assertIn('【分享形式】常规未定（等强冲突）', t.render(corrected_fixture, 10000)['text'])
        self.assertEqual(r['status'], 'stopped'); self.assertEqual(r['memories'], {})


if __name__ == '__main__': unittest.main()
