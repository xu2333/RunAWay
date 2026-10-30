"""Offline schedule, missing-denominator and controller damage fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/compression-stability-v1'
spec = importlib.util.spec_from_file_location('stability_engine_test', HERE / 'engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
plan, score = engine.plan, engine.score


class Fixture:
    """Oracle responses test plumbing only; partial cards are not fidelity data."""
    def __init__(self, fault=None, at=None):
        self.calls, self.fault, self.at = 0, fault, at
        self.data = plan.inputs()
        old = plan.read(ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json')['studies']['remaining_h']
        from runaway.constraint_extract import parse_answer
        self.raw = {r['person']: parse_answer(r['raw']) for r in old['records'] if r['group'] == 'extract'}
        self.raw['dev'] = plan.read(ROOT / 'benchmarks/decision-targets-v1/examples/partial-answer.synthetic.json')

    def __call__(self, req, folder, slot):
        self.calls += 1
        fault = self.fault if slot['slot'] == self.at else None
        if fault == 'transport':
            raise TimeoutError('Offline fixture')
        if slot['kind'] == 'extract':
            answer = copy.deepcopy(self.raw[slot['profile']])
            answer['groups'] = answer['groups'][:1]
            answer['unknowns'] = ['夹具只留一组，其余未知；不代表模型保真度。']
            answer['tagline'] = '离线夹具第%d份，不代表模型质量。' % slot['generation']
            if fault == 'product':
                answer['name'] = 'x'*21
        else:
            pid = slot['profile']
            if slot['kind'] == 'none':
                queries = self.data['queries'][plan.bank(pid)]
                answer = {q['id']: 'U' for q in queries}
            else:
                answer = {q: row['gold'] for row in self.data['rows'] if row['person'] == pid for q in row['query_ids']}
            if fault == 'control':
                answer = dict.fromkeys(answer, 'U')
            if fault == 'wrong':
                row = next(r for r in self.data['rows'] if r['person'] == pid and r['gold'] != 'U')
                answer[row['query_ids'][0]] = 'U'
        if fault == 'wire':
            answer = {}
        prov = {'backend': 'offline_fixture', 'model_requested': plan.MODEL,
                'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}
        if fault == 'model':
            prov['model_requested'] = 'unexpected'
        return json.dumps(answer, ensure_ascii=False), prov


class StabilityTests(unittest.TestCase):
    def prepared(self, t):
        path = Path(t) / 'proposal'
        plan.prepare(path)
        return path

    def run_fixture(self, t, fixture, before=None):
        root = self.prepared(t)
        with patch.object(plan.grouped_support, 'codex_generate', side_effect=AssertionError('No service')):
            result = engine.run(root, root / 'fixture-execution', fixture, before or (lambda _: {'fixture': True}), simulated=True)
        return root, result

    def test41slots17static24dynamic_and_all_generations_before_reads(self):
        slots = plan.slots()
        self.assertEqual(len(slots), 41)
        self.assertEqual([s['kind'] for s in slots[:5]], ['none', 'full', 'full', 'none', 'full'])
        self.assertTrue(all(s['kind'] == 'extract' for s in slots[5:17]))
        self.assertTrue(all(s['kind'] == 'read' for s in slots[17:]))
        self.assertEqual(len(set(plan.cells())), 12)
        self.assertEqual(len({s['key'] for s in slots}), 41)
        for cell in plan.cells():
            self.assertEqual(sum(s['kind'] == 'read' and plan.parent(s) == cell for s in slots), 2)

    def test_sources_queries_and_denominators_are_the_approved_old_fictional_material(self):
        data = plan.inputs()
        self.assertEqual(sum(len(v['sources']) for v in data['sources'].values()), 110)
        self.assertEqual(sum(len(v) for v in data['queries'].values()), 112)
        self.assertEqual(len(data['rows']), 96)
        self.assertNotIn('cached_v1', data)

    def test_extractions_are_source_only_identical_between_generations_and_not_target_v2(self):
        data = plan.inputs()
        for pid in plan.PROFILES:
            for budget in plan.BUDGETS:
                ss = [s for s in plan.slots() if s['kind'] == 'extract' and s['profile'] == pid and s['budget'] == budget]
                a, b = [plan.request(s) for s in ss]
                self.assertEqual(a, b)
                self.assertNotIn('DECISION_TARGET_REVISION_V1', a['prompt'])
                body = json.loads(a['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
                self.assertEqual(body['sources'], data['sources'][pid])
                self.assertEqual(body['budget_characters'], budget)
                self.assertFalse({'queries', 'facts', 'gold', 'target', 'scores', 'generation'} & set(body))

    def test_prepare_is_zero_call_exclusive_and_hash_frozen(self):
        with tempfile.TemporaryDirectory() as t, patch.object(plan.grouped_support, 'codex_generate', side_effect=AssertionError('No service')):
            root = self.prepared(t)
            self.assertTrue(plan.verify(root))
            self.assertEqual(len(plan.read(root / 'static-requests.json')), 17)
            self.assertEqual(len(plan.read(root / 'dynamic-rules.json')['slots']), 24)
            self.assertFalse(plan.read(root / 'proposal.json')['approved'])
            with self.assertRaises(FileExistsError):
                plan.prepare(root)
            (root / 'queries.public.json').write_text('{}')
            with self.assertRaises(ValueError):
                plan.verify(root)

    def test41simulated_attempts_have_no_service_cost_or_authority(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture()
            root, result = self.run_fixture(t, f)
            self.assertEqual((f.calls, result['status'], result['unused_slots_expire']), (41, 'complete', 0))
            self.assertEqual(result['known_usage']['total_tokens'], 0)
            self.assertEqual(result['local_cli_child_intents'], 0)
            self.assertTrue(result['usage_is_fixture_not_billable'])
            self.assertFalse(result['new_service_authority'])
            for budget in ('768', '1024'):
                self.assertEqual(result['scores']['per_budget_strict'][budget]['joint'], {'planned': 96, 'correct': 96, 'missing': 0})
                self.assertEqual(result['scores']['per_budget_strict'][budget]['untyped']['planned'], 80)
            grouped = {}
            for rec in result['records']:
                if rec['kind'] == 'read':
                    grouped.setdefault(plan.parent(rec), []).append(rec['request_sha256'])
            self.assertEqual(len(grouped), 12)
            self.assertTrue(all(len(v) == 2 and v[0] == v[1] for v in grouped.values()))
            with self.assertRaises(FileExistsError):
                engine.run(root, root / 'fixture-execution', f, lambda _: {}, simulated=True)
            self.assertEqual(f.calls, 41)

    def test_each_failed_full_control_closes_before_extractions(self):
        for at in (2, 3, 5):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture('control', at)
                _, r = self.run_fixture(t, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 41-at))

    def test_transport_wire_usage_or_model_failure_closes_without_retry(self):
        for fault in ('transport', 'wire', 'usage', 'model'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as t:
                f = Fixture(fault, 1)
                _, r = self.run_fixture(t, f)
                self.assertEqual((f.calls, r['status']), (1, 'stopped'))
                self.assertTrue(r['scope_closed'])
                self.assertEqual(r['scores']['per_budget_strict']['768']['joint']['missing'], 96)

    def test_invalid_product_skips_only_own_generation_not_its_sibling(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture('product', 6)
            _, r = self.run_fixture(t, f)
            self.assertEqual((f.calls, r['status']), (39, 'completed_with_invalid_products'))
            self.assertEqual(len(r['skipped']), 2)
            self.assertTrue(all(plan.parent(s) == ('h68', 768, 0) for s in r['skipped']))
            self.assertEqual(r['scores']['per_budget_strict']['768']['joint'], {'planned': 96, 'correct': 56, 'missing': 40})
            self.assertEqual(r['scores']['per_budget_strict']['1024']['joint']['correct'], 96)

    def test_valid_wrong_read_is_retained_and_not_fixed_by_its_successful_repeat(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture('wrong', 18)
            _, r = self.run_fixture(t, f)
            self.assertEqual((f.calls, r['status']), (41, 'complete'))
            self.assertEqual(r['scores']['per_budget_strict']['768']['joint']['correct'], 95)
            cell = r['scores']['profiles']['h68:768']['generations']['0']
            self.assertEqual(cell['within_card_read_disagreement']['disagreeing'], 1)
            self.assertEqual(cell['strict_both_reads']['joint']['correct'], 39)

    def test_last_attempt_failure_closes_all41_without_replenishment(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture('transport', 41)
            root, r = self.run_fixture(t, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (41, 'stopped', 0))
            self.assertTrue(r['scope_closed'])
            self.assertEqual(r['missing_usage'], 1)
            with self.assertRaises(FileExistsError):
                engine.run(root, root / 'fixture-execution', f, lambda _: {}, simulated=True)
            self.assertEqual(f.calls, 41)

    def test_missing_or_wrong_source_generation_cannot_build_reader(self):
        slot = next(s for s in plan.slots() if s['kind'] == 'read' and s['profile'] == 'h68')
        answer = plan.read(ROOT / 'benchmarks/decision-targets-v1/examples/partial-answer.synthetic.json')
        self.assertIsNone(plan.request(slot, {('h68', 768, 1): answer}))
        with self.assertRaises(ValueError):
            plan.request(slot, {plan.parent(slot): answer})

    def test_runtime_guard_failure_is_before_attempt_and_closes_scope(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture()
            def guard(slot):
                if slot['slot'] == 2:
                    raise PermissionError('Offline failed guard')
                return {'fixture': True}
            _, r = self.run_fixture(t, f, guard)
            self.assertEqual((f.calls, r['attempt_reservations'], r['unused_slots_expire']), (1, 1, 40))
            self.assertEqual(r['status'], 'stopped')

    def test_scoring_distinguishes_missing_unknown_wrong_stable_and_disagreement(self):
        rows = [{'person': 'p', 'query_ids': ['a', 'b'], 'gold': 'yes', 'personal_known': True},
                {'person': 'p', 'query_ids': ['c', 'd'], 'gold': 'U', 'personal_known': False, 'stratum': 'execution'}]
        good = {'a': 'yes', 'b': 'yes', 'c': 'U', 'd': 'U'}
        self.assertEqual(score.counts(rows, [good]*3+[{}])['joint'], {'planned': 2, 'correct': 0, 'missing': 2})
        all_u = dict.fromkeys(good, 'U')
        self.assertEqual(score.counts(rows, [all_u]*4)['known']['correct'], 0)
        self.assertEqual(score.counts(rows, [all_u]*4)['unknown']['correct'], 1)
        self.assertEqual(score.disagreement(rows, [all_u, all_u], [all_u, all_u])['disagreeing'], 0)
        self.assertEqual(score.counts(rows, [all_u]*4)['joint']['correct'], 1)
        self.assertEqual(score.disagreement(rows, [good, good], [all_u, all_u])['disagreeing'], 1)
        with self.assertRaises(ValueError):
            score.counts(rows, [])

    def test_usage_subsets_cannot_be_double_counted_or_unknown(self):
        value = engine.usage({'usage': [{'input_tokens': 100, 'output_tokens': 20, 'cached_input_tokens': 50, 'reasoning_output_tokens': 10}]})
        self.assertEqual(value['total_tokens'], 120)
        for row in ({'input_tokens': 10}, {'input_tokens': 10, 'output_tokens': 2, 'reasoning_output_tokens': 3}):
            with self.assertRaises(ValueError):
                engine.usage({'usage': [row]})

    def test_unbound_answers_cannot_restore_a_missing_generation(self):
        data = plan.inputs()
        responses = {}
        for pid, budget, generation in plan.cells():
            answer = {q: row['gold'] for row in data['rows'] if row['person'] == pid for q in row['query_ids']}
            for repeat in (0, 1):
                responses[pid, budget, generation, repeat] = answer
        result = score.summarize(data['rows'], responses, {})
        self.assertEqual(result['per_budget_strict']['768']['joint'], {'planned': 96, 'correct': 0, 'missing': 96})
        self.assertEqual(result['per_budget_strict']['1024']['joint']['missing'], 96)


if __name__ == '__main__':
    unittest.main()
