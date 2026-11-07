"""Accounting,licensed joins and abstention damage checks;all responses are mocks."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/partial-information-v1'
spec = importlib.util.spec_from_file_location('partial_information_test_engine', HERE / 'engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
p = e.plan
fixtures = p.load('partial_information_test_fixtures', HERE / 'fixtures.py')


class PartialInformationTests(unittest.TestCase):
    def run_fixture(self, fault=None, wrapper=None, simulated=True, before=None):
        f = fixtures.Fixture(p, fault)
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / 'inputs', Path(tmp) / 'out'
            p.prepare(root)
            def invoke(req, folder, slot):
                raw, prov = f(req, folder, slot)
                return wrapper(raw, prov, slot) if wrapper else (raw, prov)
            result = e.run(root, out, invoke, before or (lambda _: {}), simulated=simulated)
        return f, result

    def test_reference_joins_only_licensed_branches_and_separates_new_partial_cases(self):
        d = p.inputs()
        self.assertEqual((len(d['rows']), len(d['queries']['all']), len(d['parents'])), (64, 32, 8))
        primary = [r for r in d['rows'] if r['primary']]
        self.assertEqual((len(primary), sum(r['gold'] != 'U' for r in primary)), (48, 16))
        self.assertEqual(sum(r['gold'] != 'U' for r in d['rows']), 32)
        self.assertTrue(all(r['gold'] != 'U' for r in d['rows'] if not r['primary']))
        for row, proof in zip(d['rows'], d['reference_derivation']):
            self.assertEqual(row['gold'], p.common_choice(proof['previous_licensed_choices']))
            self.assertTrue(set(proof['original_cases']) <= {row['case'].split('_')[0] + '_' + str(i) for i in (0, 1, 2)})
        self.assertEqual(p.common_choice(['one', 'one']), 'one')
        self.assertEqual(p.common_choice(['one', 'other']), 'U')
        for invalid in ([], ['U'], ['one', 'U'], [None], [True]):
            with self.assertRaises(ValueError):
                p.common_choice(invalid)

    def test_every_original_card_is_verbatim_and_input_cache_returns_independent_copies(self):
        original = p.read(p.PARENT)
        originals = {(r['profile'], r['generation_repeat']): r['artifact']['prompt']
                     for r in original['records'] if r['artifact'] is not None}
        d = p.inputs()
        self.assertEqual(len(originals), 8)
        for parent in d['parents'].values():
            self.assertEqual(parent['prompt'], originals[parent['profile'], parent['parent_generation']])
        d['parents']['auri/g0']['prompt'] = 'changed'
        self.assertNotEqual(p.inputs()['parents']['auri/g0']['prompt'], 'changed')
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'changed.json'
            file.write_text('{}')
            with patch.object(p, 'PARENT', file), self.assertRaises(ValueError):
                p.inputs()

    def test37schedule_has_only_fixed_readers_and_tail_material_matches_own_parent(self):
        slots = p.slots()
        self.assertEqual(len(slots), 37)
        self.assertEqual([s['slot'] for s in slots], list(range(1, 38)))
        self.assertEqual(sum(s['kind'] == 'full' for s in slots), 4)
        self.assertFalse(any(s['kind'] == 'extract' for s in slots))
        for s in slots:
            if s['kind'] != 'read':
                continue
            d = p.inputs()
            parent = d['parents']['%s/g%d' % (s['profile'], s['generation_repeat'])]
            expected = parent['prompt'] if s['view'] == 'card' else p.transcript(d['sources'][s['profile']])[-parent['characters']:]
            self.assertEqual(p.material(s), expected)
            self.assertEqual(len(expected), parent['characters'])
            request = p.request(s)
            payload = json.loads(request['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
            self.assertEqual(payload, {'material': expected, 'queries': d['queries']['all']})
            for word in ('primary_known', 'reference_derivation', 'previous_licensed_choices', 'complete_anchor'):
                self.assertNotIn(word, request['prompt'])
        with self.assertRaises(ValueError):
            p.request({**slots[-1], 'slot': 99})

    def test_oracle37_only_checks_bookkeeping_and_keeps_all_nested_denominators(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            f, out = self.run_fixture()
        backend.assert_not_called()
        self.assertEqual((len(f.calls), out['status'], out['unused_slots_expire']), (37, 'complete', 0))
        self.assertEqual(out['new_extractions'], 0)
        self.assertEqual(out['local_cli_child_intents'], 0)
        for v in p.VIEWS:
            self.assertEqual(out['scores']['joint'][v]['joint'], {'planned': 64, 'correct': 64, 'missing': 0})
            self.assertEqual(out['scores']['primary'][v]['joint'], {'planned': 48, 'correct': 48, 'missing': 0})
            self.assertEqual(out['scores']['primary'][v]['known']['correct'], 16)
            self.assertEqual(out['scores']['primary'][v]['unknown']['correct'], 32)
            self.assertEqual(out['scores']['anchors'][v]['joint']['correct'], 16)

    def test_always_unknown_cannot_pass_the_known_partial_endpoint(self):
        def all_u(raw, prov, slot):
            answer = json.loads(raw)
            if slot['kind'] == 'read':
                answer = {k: 'U' for k in answer}
            return json.dumps(answer), prov
        _, out = self.run_fixture(wrapper=all_u)
        for v in p.VIEWS:
            self.assertEqual(out['scores']['primary'][v]['joint']['correct'], 32)
            self.assertEqual(out['scores']['primary'][v]['known']['correct'], 0)
            self.assertEqual(out['scores']['primary'][v]['unknown']['correct'], 32)
            self.assertEqual(out['scores']['anchors'][v]['joint']['correct'], 0)

    def test_overconfident_answers_do_not_become_successful_unknowns(self):
        def guess(raw, prov, slot):
            answer = json.loads(raw)
            if slot['kind'] == 'read':
                qmap = {q['id']: q for q in p.inputs()['queries']['all']}
                answer = {k: qmap[k]['options']['A'] if value == 'U' else value for k, value in answer.items()}
            return json.dumps(answer, ensure_ascii=False), prov
        _, out = self.run_fixture(wrapper=guess)
        for v in p.VIEWS:
            self.assertEqual(out['scores']['primary'][v]['known']['correct'], 16)
            self.assertEqual(out['scores']['primary'][v]['unknown']['correct'], 0)
            self.assertEqual(out['scores']['primary'][v]['joint']['correct'], 16)

    def test_one_wrong_order_is_not_hidden_by_the_other_seven_answers_or_anchors(self):
        _, out = self.run_fixture('one_order')
        self.assertEqual(out['scores']['joint']['card']['joint']['correct'], 63)
        self.assertEqual(out['scores']['primary']['card']['joint']['correct'], 47)
        self.assertEqual(out['scores']['anchors']['card']['joint']['correct'], 16)
        self.assertEqual(out['scores']['joint']['tail']['joint']['correct'], 64)

    def test_controls_require_primary_known_gain_not_only_complete_anchor_success(self):
        f, out = self.run_fixture('control')
        self.assertEqual((len(f.calls), out['stop'], out['unused_slots_expire']), (2, 'full_control_not_qualified', 35))
        def none_matches_first(raw, prov, slot):
            if slot['kind'] == 'none':
                rows = [r for r in p.inputs()['rows'] if r['person'] == p.PROFILES[0]]
                raw = json.dumps({q: r['gold'] for r in rows for q in r['query_ids']}, ensure_ascii=False)
            return raw, prov
        f, out = self.run_fixture(wrapper=none_matches_first)
        self.assertEqual((len(f.calls), out['stop']), (2, 'full_control_not_qualified'))
        self.assertEqual(out['control_gate']['auri']['full_all']['joint']['correct'], 16)

    def test_fatal_transport_wire_model_and_unknown_usage_stop_without_retries(self):
        for fault in ('transport', 'wire', 'usage', 'model'):
            with self.subTest(fault=fault):
                f, out = self.run_fixture(fault)
                self.assertEqual((len(f.calls), out['status'], out['unused_slots_expire']), (6, 'stopped', 31))
                self.assertTrue(out['scope_closed'])
                self.assertEqual(out['scores']['primary']['card']['joint']['missing'], 48)

    def test_guard_and_existing_output_protect_every_backend_entry(self):
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
            self.assertEqual(len(claims), 37)
            claims.clear()
            f.calls.clear()
            with self.assertRaises(FileExistsError):
                e.run(root, dest, f, before, simulated=True)
            self.assertEqual((claims, f.calls), ([], []))

    def test_rehashed_changed_reference_parent_extra_or_symlink_never_reaches_backend(self):
        for fault in ('reference.private.json', 'parents.public.json', 'extra', 'symlink'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root, dest = Path(tmp) / 'inputs', Path(tmp) / 'out'
                p.prepare(root)
                if fault in ('reference.private.json', 'parents.public.json'):
                    file = root / fault
                    file.write_text('{}')
                    m = p.read(root / 'manifest.json')
                    m['files'][fault] = p.sha(file)
                    (root / 'manifest.json').write_text(json.dumps(m))
                elif fault == 'extra':
                    (root / 'extra.json').write_text('{}')
                else:
                    file, target = root / 'sources.json', Path(tmp) / 'target.json'
                    file.rename(target)
                    file.symlink_to(target)
                f, claims = fixtures.Fixture(p), []
                with self.assertRaises(ValueError):
                    e.run(root, dest, f, lambda s: claims.append(s), simulated=True)
                self.assertEqual((f.calls, claims, dest.exists()), ([], [], False))

    def test_published_preparation_is_a_posthoc_fixed_parent_diagnostic_not_a_grant(self):
        result = p.load('partial_information_test_check', HERE / 'check.py').check()
        self.assertEqual(result['static_requests'], 37)
        self.assertEqual(result['new_model_calls'], 0)
        proposal = p.values()['proposal.json']
        self.assertTrue(proposal['fixed_posthoc_diagnostic'])
        for k in ('approved', 'new_service_authority', 'measured_results_available', 'independent_holdout',
                  'new_initial_generation_stability_verified', 'real_person_fidelity_verified',
                  'independent_semantic_gold_verified', 'cross_provider_verified',
                  'old_scopes_reopened', 'old_scores_replaced', 'production_default_changed'):
            self.assertIs(proposal[k], False)


if __name__ == '__main__':
    unittest.main()
