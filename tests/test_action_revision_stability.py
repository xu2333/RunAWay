"""Three-source fixed-denominator controller fixtures,not empirical fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('graph_stability_tests', ROOT / 'benchmarks/action-revision-stability-v1/engine.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None, alter_dispute=False):
        self.calls, self.fault, self.at, self.alter_dispute = 0, fault, at, alter_dispute
        self.data = e.plan.inputs()

    def __call__(self, req, folder, slot):
        self.calls += 1; pid, kind = slot['profile'], slot['kind']
        fault = self.fault if slot['slot'] == self.at else None
        if fault == 'transport': raise TimeoutError('Offline fixture')
        if kind == 'extract':
            source = next(s for s in self.data['sources'][pid]['sources'] if s['role'] == 'user')
            anchor = {'source_id': source['id'], 'quote': source['text'][:80]}
            answer = {'version': e.plan.candidate.VERSION, 'name': pid+str(slot['generation']),
                'tagline': '仅控制器夹具，不是实际提炼。', 'objects': ['夹具范围'], 'unknowns': ['未覆盖未知。'],
                'nodes': [{'id': 'base', 'kind': 'base', 'target_kind': 'choice', 'object_index': 0,
                    'question': '夹具选择', 'requires': [], 'action': '夹具做法', 'priority': 0,
                    'decisions': [anchor], 'contexts': [anchor]}]}
            if fault == 'product': answer['nodes'][0]['object_index'] = 1
        elif kind == 'none': answer = {q['id']: 'U' for q in self.data['queries'][e.plan.bank(pid)]}
        else:
            answer = {q: r['gold'] for r in self.data['legacy_rows'] if r['person'] == pid for q in r['query_ids']}
            if self.alter_dispute:
                for r in self.data['disputed_rows']:
                    if r['person'] == pid:
                        for q in r['query_ids']: answer[q] = 'U'
            if fault == 'control':
                row = next(r for r in self.data['rows'] if r['person'] == pid and r['gold'] != 'U')
                answer[row['query_ids'][0]] = 'U'
        if fault == 'wire': answer = {}
        return json.dumps(answer, ensure_ascii=False), {'backend': 'offline_fixture', 'model_requested': e.plan.MODEL,
            'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class GraphStabilityTests(unittest.TestCase):
    def execute(self, temp, fixture):
        root = Path(temp) / 'proposal'; e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test_schedule_source_isolation_counterbalancing_and_parent_binding(self):
        slots, data = e.plan.slots(), e.plan.inputs()
        self.assertEqual([s['kind'] for s in slots], ['none', 'full']*3+['extract']*6+['read']*12)
        self.assertEqual(sum(len(s['sources']) for s in data['sources'].values()), 96)
        self.assertEqual(sum(len(q) for q in data['queries'].values()), 160)
        self.assertEqual([s['profile'] for s in slots[6:12]], ['h93', 'j16', 'dev', 'dev', 'j16', 'h93'])
        for slot in slots[6:12]:
            req = e.plan.request(slot)
            body = json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            self.assertEqual(body['sources'], data['sources'][slot['profile']])
            self.assertEqual(req, e.plan.candidate.make_request(body['sources']) | {'model': e.plan.MODEL, 'system': e.plan.prior.grouped_support.SYSTEM})
        read = slots[12]
        self.assertIsNone(e.plan.request(read, {('j16', 'graph-v1', 0): {}}))
        with self.assertRaises(ValueError): e.plan.request(dict(read, generation=8))

    def test24fixture_calls_complete79cases_with_no_new_model_cost(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture(); root, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (24, 'complete', 0))
            self.assertEqual(r['scores']['strict_all_generations_and_reads']['joint'], {'planned': 79, 'correct': 79, 'missing': 0})
            self.assertEqual(r['scores']['answers_per_primary_case'], 8)
            self.assertEqual(set(r['control_gates']), {'h93', 'j16', 'dev'})
            self.assertEqual((r['local_cli_child_intents'], r['known_usage']['total_tokens']), (0, 0))
            pairs = {}
            for rec in r['records']:
                if rec['kind'] == 'read': pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
            self.assertEqual(len(pairs), 6)
            self.assertTrue(all(len(v) == 2 and v[0] == v[1] for v in pairs.values()))
            with self.assertRaises(FileExistsError): e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)

    def test_any_control_failure_stops_before_all_extractions(self):
        for at in (2, 4, 6):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as temp:
                f = Fixture('control', at); _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 24-at))
                self.assertFalse(any(rec['kind'] == 'extract' for rec in r['records']))

    def test_invalid_parent_skips_only_own_readers_and_cannot_be_rescued_by_other_generation(self):
        for at, missing in ((7, 40), (8, 23), (9, 16)):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as temp:
                f = Fixture('product', at); _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (22, 'completed_with_invalid_products', 2))
                self.assertEqual(len(r['skipped']), 2)
                parent = e.plan.parent(e.plan.slots()[at-1])
                self.assertTrue(all(e.plan.parent(s) == parent for s in r['skipped']))
                self.assertEqual(r['scores']['strict_all_generations_and_reads']['joint'],
                                 {'planned': 79, 'correct': 79-missing, 'missing': missing})

    def test_wire_usage_and_final_transport_failures_close_without_retry(self):
        for fault, at in (('wire', 7), ('usage', 1), ('transport', 24)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = Fixture(fault, at); _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 24-at))

    def test_single_wrong_order_in_one_read_loses_case_and_keeps_other_strata(self):
        data = e.plan.inputs(); cards = {(p, 'graph-v1', g): {'characters': 100} for p in e.plan.PROFILES for g in (0, 1)}
        answers = {key+(repeat,): {q: r['gold'] for r in data['rows'] if r['person'] == key[0] for q in r['query_ids']}
                   for key in cards for repeat in (0, 1)}
        for pid in e.plan.PROFILES:
            r = next(r for r in data['rows'] if r['person'] == pid and r['gold'] != 'U')
            changed = copy.deepcopy(answers); changed[(pid, 'graph-v1', 1, 1)][r['query_ids'][1]] = 'U'
            scored = e.score.summarize(data['rows'], changed, cards)
            self.assertEqual(scored['strict_all_generations_and_reads']['joint'], {'planned': 79, 'correct': 78, 'missing': 0})
            own = scored['profiles'][pid]
            self.assertEqual(own['generations']['1']['within_card_read_disagreement']['disagreeing'], 1)
            for other in set(e.plan.PROFILES)-{pid}:
                self.assertEqual(scored['profiles'][other]['strict_all_generations_and_reads']['joint']['missing'], 0)

    def test_disputed_w14_changes_neither_controls_nor_primary_score(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture(alter_dispute=True); _, r = self.execute(temp, f)
            self.assertTrue(all(g['qualified'] for g in r['control_gates'].values()))
            s = r['scores']; self.assertEqual(s['strict_all_generations_and_reads']['joint']['correct'], 79)
            d = s['disputed_observations_not_scored']; self.assertEqual(len(d), 1)
            self.assertEqual(d[0]['case'], 'w14'); self.assertFalse(d[0]['reference_accepted'])
            self.assertFalse(d[0]['included_in_primary_or_gate'])
            self.assertEqual(d[0]['generations_reads_orders'], [[['U', 'U'], ['U', 'U']]]*2)

    def test_exclusive_unapproved_freeze_and_old_scopes_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'proposal'; p = e.plan.prepare(root)
            self.assertFalse(p['approved']); self.assertFalse(p['new_service_authority'])
            self.assertFalse(p['changes_frozen_encoder_or_renderer'])
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 12)
            self.assertEqual(len(e.plan.read(root / 'dynamic-rules.json')['slots']), 12)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError): e.plan.prepare(root)
            (root / 'sources.json').write_text('{}')
            with self.assertRaises(ValueError): e.plan.verify(root)
        oldspec = importlib.util.spec_from_file_location('graph_stability_old_scope', ROOT / 'benchmarks/owned-conditions-v1/plan.py')
        old = importlib.util.module_from_spec(oldspec); oldspec.loader.exec_module(old)
        self.assertEqual((old.CAP, old.METHODS), (42, ('scope-v1', 'owned-v1')))


if __name__ == '__main__': unittest.main()
