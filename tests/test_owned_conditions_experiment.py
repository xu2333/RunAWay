"""Synthetic controller fixtures are not evidence of model fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owned_experiment_test', ROOT / 'benchmarks/owned-conditions-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None):
        self.calls, self.fault, self.at = 0, fault, at
        self.data = e.plan.inputs()

    def ledger(self, pid):
        source = next(s for s in self.data['sources'][pid]['sources'] if s['role'] == 'user')
        anchor = {'source_id': source['id'], 'quote': source['text'][:80]}
        return {'version': e.plan.candidate.VERSION, 'name': '离线小夹具', 'tagline': '只检查控制器。',
            'rows': [{'object': '离线夹具对象', 'question': '夹具选择', 'requires': [], 'action': '夹具做法',
                      'priority': 0, 'decisions': [anchor], 'contexts': [anchor], 'supersedes': []}],
            'unknowns': ['这是控制器夹具，不推断实际保真度。']}

    def __call__(self, req, folder, slot):
        self.calls += 1
        fault = self.fault if slot['slot'] == self.at else None
        pid, kind = slot['profile'], slot['kind']
        if fault == 'transport':
            raise TimeoutError('Offline fixture')
        if kind == 'extract':
            answer = self.ledger(pid)
            if fault == 'product':
                answer['rows'][0]['decisions'][0]['quote'] = 'nonexistent source quotation'
            if slot['method'] == 'scope-v1':
                # Same minimal code fixture, not a model-based baseline extraction.
                if fault == 'product':
                    answer = self.ledger(pid)
                answer = e.plan.candidate.project(answer, self.data['sources'][pid])[0]
                if fault == 'product':
                    answer['groups'][0]['rules'][0]['decisions'][0]['quote'] = 'nonexistent source quotation'
            if fault == 'wrong_method':
                answer = e.plan.candidate.project(self.ledger(pid), self.data['sources'][pid])[0]
        elif kind == 'none':
            answer = {q['id']: 'U' for q in self.data['queries'][e.plan.bank(pid)]}
        else:
            answer = {q: r['gold'] for r in self.data['legacy_rows'] if r['person'] == pid for q in r['query_ids']}
            if pid == 'j16':
                flagged = self.data['disputed_rows'][0]
                answer.update(dict.fromkeys(flagged['query_ids'], 'U'))
            if fault == 'control':
                row = next(r for r in self.data['rows'] if r['person'] == pid and r['gold'] != 'U')
                answer[row['query_ids'][0]] = 'U'
        if fault == 'wire':
            answer = {}
        prov = {'backend': 'offline_fixture', 'model_requested': e.plan.MODEL,
                'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}
        return json.dumps(answer, ensure_ascii=False), prov


class OwnedExperimentTests(unittest.TestCase):
    def execute(self, t, fixture):
        root = Path(t) / 'proposal'
        e.plan.prepare(root)
        with patch.object(e.plan.grouped_support, 'codex_generate', side_effect=AssertionError('No service')):
            result = e.run(root, root / 'fixture', fixture, lambda _: {'fixture': True}, simulated=True)
        return root, result

    def test42slots_have6controls_then12extracts_then24reads(self):
        slots = e.plan.slots()
        self.assertEqual(len(slots), 42)
        self.assertEqual([s['kind'] for s in slots[:6]], ['none', 'full'] * 3)
        self.assertTrue(all(s['kind'] == 'extract' for s in slots[6:18]))
        self.assertTrue(all(s['kind'] == 'read' for s in slots[18:]))
        self.assertEqual(len(set(e.plan.cells())), 12)
        self.assertEqual(e.plan.BUDGET, 1536)

    def test_fixed_source_counts_and_only_preexisting_dispute_excluded(self):
        d = e.plan.inputs()
        self.assertEqual(sum(len(s['sources']) for s in d['sources'].values()), 96)
        self.assertEqual(sum(map(len, d['queries'].values())), 160)
        self.assertEqual((len(d['legacy_rows']), len(d['rows']), len(d['disputed_rows'])), (80, 79, 1))
        self.assertEqual(d['disputed_rows'][0]['person'], 'j16')
        self.assertEqual(d['disputed_rows'][0]['case'], 'w14')
        self.assertEqual(sum(r['gold'] != 'U' for r in d['rows']), 50)
        self.assertEqual(sum(r['gold'] == 'U' for r in d['rows']), 29)
        self.assertEqual(sum(r['personal_known'] for r in d['rows']), 25)

    def test_encoders_only_get_own_source_and_ledger_does_not_see_budget(self):
        for slot in e.plan.slots()[6:18]:
            req = e.plan.request(slot)
            if slot['method'] == 'owned-v1':
                body = json.loads(req['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n')[1])
                self.assertEqual(set(body), {'sources'})
            else:
                body = json.loads(req['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
                self.assertEqual(body['budget_characters'], 1536)
            self.assertEqual(body['sources'], e.plan.inputs()['sources'][slot['profile']])
            self.assertFalse({'queries', 'gold', 'generation', 'legacy_rows', 'disputed_rows'} & set(body))
            other = next(s for s in e.plan.slots() if s['kind'] == 'extract' and s['profile'] == slot['profile'] and s['method'] == slot['method'] and s['generation'] != slot['generation'])
            self.assertEqual(req, e.plan.request(other))

    def test_complete_simulated42_has_no_backend_and_dispute_is_unscored(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture()
            root, r = self.execute(t, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (42, 'complete', 0))
            self.assertEqual((r['local_cli_child_intents'], r['known_usage']['total_tokens']), (0, 0))
            self.assertEqual(set(r['control_gates']), {'h93', 'j16', 'dev'})
            for method in e.plan.METHODS:
                self.assertEqual(r['scores']['per_method_strict'][method]['joint'], {'planned': 79, 'correct': 79, 'missing': 0})
            self.assertEqual(r['scores']['paired_strict_development_cases']['both_correct'], 79)
            self.assertEqual(len(r['scores']['disputed_observations_not_scored']), 2)
            self.assertTrue(all(not d['reference_accepted'] for d in r['scores']['disputed_observations_not_scored']))
            with self.assertRaises(FileExistsError):
                e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)
            self.assertEqual(f.calls, 42)

    def test_each_full_failure_including_slot6_stops_before_extraction7(self):
        for at in (2, 4, 6):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture('control', at)
                _, r = self.execute(t, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 42-at))
                self.assertFalse(any(x['kind'] == 'extract' for x in r['records']))

    def test_invalid_product_skips_only_own_method_generation_and_retains_denominator(self):
        for at in (7, 10):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture('product', at)
                _, r = self.execute(t, f)
                cell = e.plan.slots()[at-1]
                self.assertEqual((f.calls, r['status']), (40, 'completed_with_invalid_products'))
                self.assertEqual(len(r['skipped']), 2)
                self.assertTrue(all(e.plan.parent(x) == e.plan.parent(cell) for x in r['skipped']))
                affected = sum(x['person'] == cell['profile'] for x in f.data['rows'])
                self.assertEqual(r['scores']['per_method_strict'][cell['method']]['joint'], {'planned': 79, 'correct': 79-affected, 'missing': affected})
                other = next(m for m in e.plan.METHODS if m != cell['method'])
                self.assertEqual(r['scores']['per_method_strict'][other]['joint']['correct'], 79)
                self.assertEqual(r['scores']['paired_strict_development_cases']['both_correct'], 79-affected)
                expected_key = 'only_candidate_correct' if cell['method'] == 'scope-v1' else 'only_baseline_correct'
                self.assertEqual(r['scores']['paired_strict_development_cases'][expected_key], affected)

    def test_schema_usage_transport_or_last_attempt_failure_do_not_retry(self):
        for fault, at in (('transport', 1), ('wire', 7), ('usage', 1), ('wrong_method', 10), ('transport', 42)):
            with self.subTest(fault=fault, at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture(fault, at)
                _, r = self.execute(t, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 42-at))
                self.assertTrue(r['scope_closed'])

    def test_repeat_request_hashes_match_and_artifact_records_method(self):
        with tempfile.TemporaryDirectory() as t:
            root, r = self.execute(t, Fixture())
            pairs = {}
            for rec in r['records']:
                if rec['kind'] == 'read':
                    pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
                elif rec['kind'] == 'extract':
                    artifact = e.plan.read(root / 'fixture' / rec['execution_id'] / 'artifact.json')
                    self.assertEqual(artifact['method'], rec['method'])
            self.assertEqual(len(pairs), 12)
            self.assertTrue(all(len(x) == 2 and x[0] == x[1] for x in pairs.values()))

    def test_unbound_or_wrong_generation_reader_cannot_use_foreign_parent(self):
        slot = e.plan.slots()[18]
        f = Fixture()
        foreign = dict(slot, generation=1-slot['generation'])
        self.assertIsNone(e.plan.request(slot, {e.plan.parent(foreign): f.ledger(slot['profile'])}))
        with self.assertRaises(ValueError):
            e.plan.bind(slot, f.ledger(slot['profile']))
        bad = dict(slot, method='unapproved_method')
        with self.assertRaises(ValueError):
            e.plan.request(bad)

    def test_frozen_inputs_detect_drift_and_preparation_has_no_authority(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'proposal'
            p = e.plan.prepare(root)
            self.assertFalse(p['approved'])
            self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 18)
            self.assertTrue(e.plan.verify(root))
            (root / 'reference.consumed-development.private.json').write_text('{}')
            with self.assertRaises(ValueError):
                e.plan.verify(root)


if __name__ == '__main__':
    unittest.main()
