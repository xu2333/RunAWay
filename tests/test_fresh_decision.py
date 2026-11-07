"""Prospective protocol and accounting tests; all backend answers are mock/oracle."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/fresh-decision-v1'
spec = importlib.util.spec_from_file_location('fresh_decision_test_engine', HERE / 'engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
fixtures = p.load('fresh_decision_test_fixtures', HERE / 'fixtures.py')


class FreshDecisionTests(unittest.TestCase):
    def run_fixture(self, fault=None, simulated=True, before=None):
        f = fixtures.Fixture(p, fault)
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / 'inputs', Path(tmp) / 'out'
            p.prepare(root)
            result = e.run(root, out, f, before or (lambda _: {}), simulated=simulated)
        return f, result

    def test_new_sources_roles_counts_and_reference_are_distinct_from_consumed_people(self):
        data = p.inputs()
        self.assertTrue(set(p.PROFILES).isdisjoint(p.repeat.PROFILES))
        self.assertEqual(len(data['rows']), 64)
        self.assertEqual(len(data['queries']['all']), 32)
        self.assertEqual(sum(r['personal_known'] for r in data['rows']), 48)
        self.assertEqual(sum(r['derived_known'] for r in data['rows']), 16)
        self.assertEqual(sum(len(v['sources']) for v in data['sources'].values()), 64)
        self.assertEqual(sum(s['role'] == 'user' for v in data['sources'].values() for s in v['sources']), 48)
        for pid, sources in data['sources'].items():
            self.assertGreater(sum(len(s['text']) for s in sources['sources']), 1536)
            self.assertEqual(len({s['id'] for s in sources['sources']}), 16)
            self.assertEqual({s['episode_id'] for s in sources['sources']}, {'draft', 'roster', 'support', 'research'})

    def test_shared_forms_counterbalance_text_and_opposite_pairs_disagree_on_all_known_cells(self):
        data = p.inputs()
        queries = {q['id']: q for q in data['queries']['all']}
        for left, right in data['design']['opposite_pairs']:
            a = {r['case']: r for r in data['rows'] if r['person'] == left}
            b = {r['case']: r for r in data['rows'] if r['person'] == right}
            for case, row in a.items():
                first, second = (queries[q] for q in row['query_ids'])
                self.assertEqual(first['scenario'], second['scenario'])
                self.assertEqual(list(first['options'].values()), list(reversed(list(second['options'].values()))))
                if row['gold'] == 'U':
                    self.assertEqual(b[case]['gold'], 'U')
                else:
                    self.assertNotEqual(row['gold'], b[case]['gold'])
                    self.assertIn(row['gold'], first['options'].values())
        for pid, domain_anchors in data['author_evidence'].items():
            own = {s['id'] for s in data['sources'][pid]['sources'] if s['role'] == 'user'}
            self.assertTrue(all(set(ids) <= own for ids in domain_anchors.values()))

    def test_method_schedule_and_encoder_inputs_keep_existing_algorithm_and_no_gold(self):
        self.assertIs(e.run, e.shared.run)
        self.assertEqual(p.BUDGET, p.repeat.BUDGET)
        self.assertEqual(p.VIEWS, p.repeat.VIEWS)
        slots = p.slots()
        self.assertEqual(len(slots), 45)
        self.assertEqual([s['slot'] for s in slots], list(range(1, 46)))
        for s in slots:
            if s['kind'] != 'extract':
                continue
            req = p.request(s)
            expected = p.producer.make_request(p.inputs()['sources'][s['profile']], 1536)
            self.assertEqual({k: v for k, v in req.items() if k not in ('model', 'system')}, expected)
            self.assertEqual(req['system'], p.repeat.request(p.repeat.slots()[0])['system'])
            for marker in ('draft_0_ab', 'unrecorded_target', 'author_evidence', 'personal_known'):
                self.assertNotIn(marker, req['prompt'])
            for other in set(p.PROFILES) - {s['profile']}:
                self.assertNotIn(other + '_m', req['prompt'])
        self.assertNotIn('runaway/taste_executor.py', p.implementation())

    def test_oracle45_is_only_bookkeeping_and_all_cohort_denominators_remain(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            f, out = self.run_fixture()
        backend.assert_not_called()
        self.assertEqual((len(f.calls), out['status'], out['unused_slots_expire']), (45, 'complete', 0))
        self.assertTrue(out['simulated'])
        self.assertEqual(out['local_cli_child_intents'], 0)
        for view in p.VIEWS:
            self.assertEqual(out['scores']['joint'][view]['joint'], {'planned': 64, 'correct': 64, 'missing': 0})
            self.assertEqual(out['scores']['slices']['known'][view]['joint']['correct'], 48)
            self.assertEqual(out['scores']['slices']['unknown'][view]['joint']['correct'], 16)
            for cohort in out['scores']['cohort_slices'].values():
                self.assertEqual(cohort[view]['joint'], {'planned': 16, 'correct': 16, 'missing': 0})

    def test_one_bad_order_in_one_generation_is_not_averaged_away(self):
        _, out = self.run_fixture('one_order')
        self.assertEqual(out['scores']['joint']['card']['joint']['correct'], 63)
        self.assertEqual(out['scores']['per_generation']['0']['card']['joint']['correct'], 64)
        self.assertEqual(out['scores']['per_generation']['1']['card']['joint']['correct'], 63)
        self.assertEqual(out['scores']['joint']['tail']['joint']['correct'], 64)

    def test_invalid_product_keeps_missing_and_skips_only_own_four_readers(self):
        for fault in ('product', 'quote'):
            with self.subTest(fault=fault):
                f, out = self.run_fixture(fault)
                self.assertEqual((len(f.calls), len(out['skipped']), out['unused_slots_expire']), (41, 4, 4))
                self.assertEqual({(x['profile'], x['generation_repeat']) for x in out['skipped']}, {('auri', 0)})
                for view in p.VIEWS:
                    self.assertEqual(out['scores']['joint'][view]['joint'], {'planned': 64, 'correct': 48, 'missing': 16})
                    self.assertEqual(out['scores']['per_generation']['1'][view]['joint']['correct'], 64)

    def test_control_and_fatal_failures_close_scope_without_retries(self):
        f, out = self.run_fixture('control')
        self.assertEqual((len(f.calls), out['stop'], out['unused_slots_expire']), (2, 'full_control_not_qualified', 43))
        for fault in ('transport', 'wire', 'usage', 'model'):
            with self.subTest(fault=fault):
                f, out = self.run_fixture(fault)
                self.assertEqual((len(f.calls), out['status'], out['unused_slots_expire']), (6, 'stopped', 39))
                self.assertTrue(out['scope_closed'])
                self.assertEqual(out['scores']['joint']['card']['joint']['missing'], 64)

    def test_parent_specific_tail_and_foreign_evidence_refuse(self):
        graphs = {(pid, g): fixtures.graph(p, pid, g) for pid in p.PROFILES for g in (0, 1)}
        for pid in p.PROFILES:
            graphs[pid, 1]['name'] += '-extra'
        for s in p.slots():
            if s['kind'] != 'read' or s['view'] != 'tail':
                continue
            # A reader with the other view has another slot number.
            own = next(x for x in p.slots() if x['kind'] == 'read' and x['view'] == 'card'
                       and all(x[k] == s[k] for k in ('profile', 'generation_repeat', 'read_repeat')))
            card, tail = p.material(own, graphs), p.material(s, graphs)
            self.assertEqual(tail, p.transcript(p.inputs()['sources'][s['profile']])[-len(card):])
            self.assertEqual(len(tail), len(card))
        with self.assertRaises(ValueError):
            p.bind('bryn', graphs['auri', 0])

    def test_output_directory_and_guard_precede_every_backend_attempt(self):
        f, out = self.run_fixture(simulated=False)
        self.assertEqual((f.calls, out['attempt_reservations']), ([], 0))
        with tempfile.TemporaryDirectory() as tmp:
            root, dest = Path(tmp) / 'inputs', Path(tmp) / 'out'
            p.prepare(root)
            f, claims = fixtures.Fixture(p), []
            def before(slot):
                self.assertTrue(dest.is_dir())
                claims.append(slot['slot'])
                return {}
            e.run(root, dest, f, before, simulated=True)
            self.assertEqual(len(claims), 45)
            claims.clear()
            f.calls.clear()
            with self.assertRaises(FileExistsError):
                e.run(root, dest, f, before, simulated=True)
            self.assertEqual((claims, f.calls), ([], []))

    def test_damaged_rehashed_extra_and_symlink_inputs_fail_before_execution(self):
        for fault in ('reference', 'extra', 'symlink', 'boolean_zero'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root, out = Path(tmp) / 'inputs', Path(tmp) / 'out'
                p.prepare(root)
                if fault == 'reference':
                    path = root / 'reference.private.json'
                    rows = p.read(path)
                    rows[0]['gold'] = 'changed'
                    path.write_text(json.dumps(rows))
                    manifest = p.read(root / 'manifest.json')
                    manifest['files'][path.name] = p.sha(path)
                    (root / 'manifest.json').write_text(json.dumps(manifest))
                elif fault == 'extra':
                    (root / 'extra.json').write_text('{}')
                elif fault == 'boolean_zero':
                    manifest = p.read(root / 'manifest.json')
                    manifest['new_model_calls'] = False
                    (root / 'manifest.json').write_text(json.dumps(manifest))
                else:
                    path = root / 'sources.json'
                    target = Path(tmp) / 'target.json'
                    path.rename(target)
                    path.symlink_to(target)
                f, claims = fixtures.Fixture(p), []
                with self.assertRaises(ValueError):
                    e.run(root, out, f, lambda s: claims.append(s), simulated=True)
                self.assertEqual((claims, f.calls, out.exists()), ([], [], False))

    def test_published_preparation_and_claims_do_not_grant_execution(self):
        check = p.load('fresh_decision_test_check', HERE / 'check.py').check()
        self.assertEqual((check['static_requests'], check['dynamic_read_slots']), (13, 32))
        proposal = p.values()['proposal.json']
        for key in ('approved', 'new_service_authority', 'independent_holdout',
                    'real_person_fidelity_verified', 'source_reference_semantics_verified',
                    'semantic_reference_acceptance_verified', 'population_generation_stability_verified',
                    'production_default_changed', 'old_scores_replaced', 'old_scopes_reopened'):
            self.assertIs(proposal[key], False)
        self.assertEqual(proposal['max_new_local_cli_attempts'], 45)
        self.assertFalse(check['measured_results_available'])


if __name__ == '__main__':
    unittest.main()
