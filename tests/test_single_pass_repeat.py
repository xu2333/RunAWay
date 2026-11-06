"""Damage and accounting checks; the fixtures deliberately do not simulate fidelity."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/single-pass-repeat-v1'
spec = importlib.util.spec_from_file_location('single_repeat_test_engine', HERE / 'engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
fixtures = p.seed.load('single_repeat_test_fixtures', HERE / 'fixtures.py')


class SinglePassRepeatTests(unittest.TestCase):
    def run_fixture(self, fault=None, simulated=True, before=None):
        f = fixtures.Fixture(p, fault)
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / 'inputs', Path(tmp) / 'output'
            p.prepare(root)
            state = e.run(root, out, f, before or (lambda _: {}), simulated=simulated)
        return f, state

    def test_published_material_matches_consumed_source_and_frozen_preparation(self):
        self.assertEqual(p.inputs(), p.seed.inputs())
        check = p.seed.load('single_repeat_test_check', HERE / 'check.py')
        out = check.check()
        self.assertEqual((out['static_requests'], out['dynamic_read_slots']), (13, 32))
        self.assertEqual(out['new_model_calls'], 0)
        self.assertFalse(out['approved'])
        self.assertFalse(out['measured_repeat_results_available'])

    def test_exact45_schedule_separates_two_generations_and_reuses_no_response(self):
        slots = p.slots()
        self.assertEqual([s['slot'] for s in slots], list(range(1, 46)))
        self.assertEqual(sum(s['kind'] == 'extract' for s in slots), 8)
        self.assertFalse(any(s['kind'] == 'review' for s in slots))
        for pid in p.PROFILES:
            ex = [s for s in slots if s['kind'] == 'extract' and s['profile'] == pid]
            self.assertEqual(p.request(ex[0]), p.request(ex[1]))
            self.assertEqual(p.request(ex[0]), p.seed.request(next(
                s for s in p.seed.slots() if s['kind'] == 'extract' and s['profile'] == pid)))
            for generation in (0, 1):
                readers = [s for s in slots if s['kind'] == 'read' and s['profile'] == pid
                           and s['generation_repeat'] == generation]
                self.assertEqual({(s['view'], s['read_repeat']) for s in readers},
                                 {(v, r) for v in p.VIEWS for r in (0, 1)})
            req = p.request(ex[0])['prompt']
            for text in ('n01_ab', 'author_evidence', 'derived_known'):
                self.assertNotIn(text, req)
            for other in p.PROFILES:
                if other != pid:
                    self.assertNotIn(other + '_r', req)

    def test_oracle45_checks_bookkeeping_only_without_backend_or_new_people(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            f, out = self.run_fixture()
        backend.assert_not_called()
        self.assertEqual((len(f.calls), out['status'], out['unused_slots_expire']), (45, 'complete', 0))
        self.assertEqual(out['local_cli_child_intents'], 0)
        self.assertTrue(out['simulated'])
        for v in p.VIEWS:
            self.assertEqual(out['scores']['joint'][v]['joint'], {'planned': 64, 'correct': 64, 'missing': 0})
            self.assertEqual(out['scores']['slices']['known'][v]['joint']['correct'], 24)
            self.assertEqual(out['scores']['slices']['unknown'][v]['joint']['correct'], 40)
        self.assertEqual(out['scores']['fictional_people'], 4)
        self.assertFalse(out['scores']['population_generation_stability_verified'])

    def test_one_wrong_order_in_second_generation_survives_joint_scoring(self):
        _, out = self.run_fixture('one_order')
        scores = out['scores']
        self.assertEqual(scores['joint']['card']['joint'], {'planned': 64, 'correct': 63, 'missing': 0})
        self.assertEqual(scores['per_generation']['0']['card']['joint']['correct'], 64)
        self.assertEqual(scores['per_generation']['1']['card']['joint']['correct'], 63)
        self.assertEqual(scores['joint']['tail']['joint']['correct'], 64)

    def test_invalid_parent_skips_only_own_four_reads_and_retains_missing(self):
        for fault in ('product', 'quote'):
            with self.subTest(fault=fault):
                f, out = self.run_fixture(fault)
                self.assertEqual((len(f.calls), len(out['skipped']), out['unused_slots_expire']), (41, 4, 4))
                self.assertEqual({(s['profile'], s['generation_repeat']) for s in out['skipped']}, {('pavo', 0)})
                self.assertTrue(any(s['kind'] == 'extract' and s['profile'] == 'pavo'
                                    and s['generation_repeat'] == 1 for s in f.calls))
                for v in p.VIEWS:
                    self.assertEqual(out['scores']['joint'][v]['joint'], {'planned': 64, 'correct': 48, 'missing': 16})
                    self.assertEqual(out['scores']['per_generation']['1'][v]['joint']['correct'], 64)

    def test_control_failure_stops_before_any_extraction(self):
        f, out = self.run_fixture('control')
        self.assertEqual((len(f.calls), out['stop'], out['unused_slots_expire']), (2, 'full_control_not_qualified', 43))
        self.assertEqual(out['scores']['joint']['card']['joint']['missing'], 64)

    def test_fatal_wire_transport_unknown_usage_and_model_do_not_retry(self):
        for fault in ('wire', 'transport', 'usage', 'model'):
            with self.subTest(fault=fault):
                f, out = self.run_fixture(fault)
                self.assertEqual((len(f.calls), out['status'], out['unused_slots_expire']), (6, 'stopped', 39))
                self.assertEqual(out['scores']['joint']['card']['joint']['missing'], 64)
                self.assertTrue(out['scope_closed'])

    def test_each_generation_tail_uses_own_card_and_foreign_parent_is_rejected(self):
        graphs = {(pid, g): fixtures.graph(p, pid, g) for pid in p.PROFILES for g in (0, 1)}
        for pid in p.PROFILES:
            graphs[pid, 1]['name'] += '-extra'
        for s in p.slots():
            if s['kind'] != 'read' or s['view'] != 'tail':
                continue
            card_slot = next(x for x in p.slots() if x['kind'] == 'read' and x['view'] == 'card'
                             and all(x[k] == s[k] for k in ('profile', 'generation_repeat', 'read_repeat')))
            card, tail = p.material(card_slot, graphs), p.material(s, graphs)
            self.assertEqual(tail, p.transcript(p.inputs()['sources'][s['profile']])[-len(card):])
        with self.assertRaises(ValueError):
            p.bind('rill', graphs['pavo', 0])
        with self.assertRaises(ValueError):
            p.request({**p.slots()[0], 'slot': 99})

    def test_output_directory_precedes_claim_and_existing_output_uses_neither(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / 'inputs', Path(tmp) / 'output'
            p.prepare(root)
            f = fixtures.Fixture(p)
            claims = []
            def before(slot):
                self.assertTrue(out.is_dir())
                claims.append(slot['slot'])
                return {}
            e.run(root, out, f, before, simulated=True)
            self.assertEqual(len(claims), 45)
            claims.clear()
            f.calls.clear()
            with self.assertRaises(FileExistsError):
                e.run(root, out, f, before, simulated=True)
            self.assertEqual((claims, f.calls), ([], []))

    def test_damaged_inputs_even_with_rehashed_manifest_refuse_before_claim(self):
        for fault in ('reference', 'extra', 'symlink'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root, out = Path(tmp) / 'inputs', Path(tmp) / 'output'
                p.prepare(root)
                if fault == 'reference':
                    file = root / 'reference.private.json'
                    data = p.read(file)
                    data[0]['gold'] = 'changed'
                    file.write_text(json.dumps(data))
                    manifest = p.read(root / 'manifest.json')
                    manifest['files'][file.name] = p.sha(file)
                    (root / 'manifest.json').write_text(json.dumps(manifest))
                elif fault == 'extra':
                    (root / 'injected.json').write_text('{}')
                else:
                    file = root / 'sources.json'
                    target = Path(tmp) / 'source-target.json'
                    file.rename(target)
                    file.symlink_to(target)
                f, claims = fixtures.Fixture(p), []
                with self.assertRaises(ValueError):
                    e.run(root, out, f, lambda s: claims.append(s), simulated=True)
                self.assertEqual((f.calls, claims, out.exists()), ([], [], False))

    def test_missing_owned_guard_and_pre_call_failure_reserve_no_backend_attempt(self):
        f, out = self.run_fixture(simulated=False)
        self.assertEqual((len(f.calls), out['attempt_reservations']), (0, 0))
        self.assertTrue(out['stop'].startswith('pre_call_failure:PermissionError'))
        def before(slot):
            if slot['slot'] == 6:
                raise PermissionError('Offline guard fixture')
            return {}
        f, out = self.run_fixture(before=before)
        self.assertEqual((len(f.calls), out['unused_slots_expire']), (5, 40))

    def test_unrelated_executor_is_not_refrozen_and_protocol_claims_stay_limited(self):
        self.assertNotIn('runaway/taste_executor.py', p.implementation())
        protocol = p.values()['proposal.json']
        for key in ('approved', 'new_service_authority', 'independent_holdout',
                    'population_generation_stability_verified', 'real_person_fidelity_verified',
                    'source_reference_semantics_verified', 'production_default_changed',
                    'old_scores_replaced', 'old_scopes_reopened'):
            self.assertIs(protocol[key], False)


if __name__ == '__main__':
    unittest.main()
