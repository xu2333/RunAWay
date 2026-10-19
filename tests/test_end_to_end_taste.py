"""Author oracle, corruption controls, leakage and one-use execution boundaries."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from runaway import end_to_end_taste as et, end_to_end_runner as runner, generation
from runaway.card import canonical, digest
from runaway.selfplay import BROWSER_SCHEMA


class Fake:
    def __init__(self, f, fault=None):
        self.f, self.fault, self.calls = f, fault, []

    def __call__(self, prompt, model, **kw):
        self.calls.append((prompt, model, kw))
        if self.fault == 'transport':
            raise ValueError('Injected transport failure')
        if kw['schema'] == BROWSER_SCHEMA:
            sources = json.loads(prompt.split('\nSOURCE_JSON:\n')[1])
            pid = next(pid for pid in et.PEOPLE if et.person(self.f, pid)['sources'] == sources)
            value = {'name': '测试用小卡', 'tagline': '只测通路，不测模型效果',
                     'claims': [{'id': 'c1', 'statement': '仅合成测试', 'basis': 'self_report', 'scope': '测试',
                                 'conditions': [], 'exceptions': [], 'related_claim_ids': [],
                                 'evidence': [{'source_id': 's1', 'quote': sources['sources'][0]['text'][:20], 'relation': 'supports'}]}],
                     'unknowns': ['其他未知'], 'prompt': '测试占位材料-' + pid, 'covered_claim_ids': ['c1'],
                     'presentation': {'tell': '测试', 'boundary': '仅测试', 'claim_ids': ['c1']},
                     'manual': {'headline': '材料还不足以写使用说明', 'items': []}}
            if self.fault == 'over_budget':
                value['prompt'] = '长' * et.BUDGET
            if self.fault == 'bad_quote':
                value['claims'][0]['evidence'][0]['quote'] = '不存在的支持引文'
        else:
            payload = json.loads(prompt.split('\nINPUT_JSON:\n')[1])
            pid = next(pid for pid in et.PEOPLE if set(q['id'] for q in payload['queries']) == set(self.f['expected'][pid]))
            value = copy.deepcopy(self.f['expected'][pid])
            if self.fault == 'missing':
                value.pop(next(iter(value)))
        raw = canonical(value)
        if self.fault == 'duplicate_wire':
            key, val = next(iter(value.items()))
            raw = raw[:-1] + ',' + json.dumps(key) + ':' + json.dumps(val, ensure_ascii=False) + '}'
        usage = [{'input_tokens': 10, 'output_tokens': 2}]
        if self.fault == 'unknown_usage':
            usage = None
        if self.fault == 'contradictory_usage':
            usage[0]['cached_input_tokens'] = 100
        return raw, {'backend': 'fake_not_service', 'usage': usage}


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        # Replay the pre-consumption proposal in an isolated archive inventory.
        # The new real evidence must forbid these ten requests in today's live
        # runner; a separate evidence test checks that guard without mocking it.
        original = et.ROOT
        historical = self.root / 'pre-pilot'
        names = et.source_names() + [et.BASE + n for n in ('histories.synthetic.json', 'policies.synthetic.json')]
        names += [str(p.relative_to(original)) for p in (original / 'examples').glob('*evidence*.zip')
                  if p.name != 'end-to-end-taste-evidence.synthetic.zip']
        for name in names:
            dest = historical / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / name, dest)
        self.root_patch = patch.object(et, 'ROOT', historical)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.plan = self.root / 'plan'
        self.proposal = et.prepare(self.plan)
        self.f = et.fixtures()

    def tearDown(self):
        self.temp.cleanup()

    def run_fake(self, fault=None):
        fake = Fake(self.f, fault)
        with patch.object(generation, 'codex_generate', side_effect=AssertionError('No service')):
            r = runner.execute(self.plan, self.root / (fault or 'out'), backend=fake)
        return fake, r

    def test_oracle_matches_hand_table_and_all_option_orders(self):
        for pid in et.PEOPLE:
            for q in self.f['cases'][pid]:
                label = self.f['expected'][pid][q['public']['id']]
                actual = q['semantics'].get(label, label)
                expected = self.f['policies']['hand_expected_semantics'][pid][q['scene']]
                self.assertEqual(actual, expected)
        self.assertEqual([sum(v == 'U' for v in self.f['expected'][p].values()) for p in et.PEOPLE], [6, 4])

    def test_corruption_controls_and_missing_denominators(self):
        gold = copy.deepcopy(self.f['expected'])
        perfect = et.score(self.f, gold)
        self.assertEqual((perfect['correct'], perfect['planned']), (48, 48))
        self.assertEqual(perfect['matched_distinctions'], {'planned': 4, 'correct': 4})
        self.assertEqual(perfect['option_order_pairs']['both_correct'], 24)
        controls = {'all_unknown': {p: {k: 'U' for k in v} for p, v in gold.items()},
                    'all_A': {p: {k: 'A' for k in v} for p, v in gold.items()},
                    'missing': {}, 'one_omitted': copy.deepcopy(gold), 'one_changed': copy.deepcopy(gold),
                    'wrong_person': {}}
        key = next(k for k, v in gold[et.PEOPLE[0]].items() if v != 'U')
        controls['one_omitted'][et.PEOPLE[0]].pop(key)
        controls['one_changed'][et.PEOPLE[0]][key] = 'U'
        # Donor semantics must be re-labelled under the target options, rather
        # than naively copying A/B labels from another person's shuffled test.
        for i, pid in enumerate(et.PEOPLE):
            donor = et.PEOPLE[1-i]
            controls['wrong_person'][pid] = {}
            for q in self.f['cases'][pid]:
                sem = self.f['policies']['hand_expected_semantics'][donor][q['scene']]
                controls['wrong_person'][pid][q['public']['id']] = next((k for k, v in q['semantics'].items() if v == sem), 'U')
        scored = {k: et.score(self.f, v) for k, v in controls.items()}
        self.assertTrue(all(v['planned'] == 48 and v['correct'] < 48 for v in scored.values()))
        self.assertEqual(scored['all_unknown']['correct'], 10)
        self.assertEqual(scored['missing']['missing'], 48)
        self.assertEqual(scored['one_omitted']['missing'], 1)
        self.assertEqual(scored['one_changed']['correct'], 47)
        self.assertEqual(scored['one_changed']['option_order_pairs']['consistent'], 23)
        self.assertEqual(scored['wrong_person']['matched_distinctions']['correct'], 0)
        self.assertEqual(scored['wrong_person']['option_order_pairs']['consistent'], 24)
        self.assertEqual(scored['all_unknown']['option_order_pairs']['consistent'], 24)
        opposite = et.report(self.f, {'wrong': controls['wrong_person']})
        self.assertEqual(opposite['wrong_prompt_against_donor_policy']['correct'], 48)
        self.assertEqual(opposite['scores']['wrong']['correct'], 28)
        self.assertFalse(et.report(self.f, {'own': gold})['retention_defined'])
        same = {c: gold for c in et.CONDITIONS}
        self.assertFalse(et.report(self.f, same)['retention_defined'])

    def test_complete10_mock_calls_use_actual_browser_and_no_leakage(self):
        fake, r = self.run_fake()
        self.assertEqual((r['status'], len(fake.calls)), ('complete', 10))
        self.assertEqual(r['external_model_calls'], 0)
        self.assertEqual(r['stage_attempts'], et.CAPS)
        self.assertEqual(r['planned_predictions'], 192)
        self.assertTrue(all(v['correct'] == 48 for v in r['scores'].values()))
        self.assertTrue(all(k['timeout'] == 180 for _, _, k in fake.calls))
        for prompt, _, kw in fake.calls:
            self.assertNotIn('hand_expected_semantics', prompt)
            self.assertNotIn('character_ratio_to_role_labelled_history', prompt)
            if kw['schema'] == BROWSER_SCHEMA:
                for expected in self.f['expected'].values():
                    for qid in expected:
                        self.assertNotIn(qid, prompt)
                self.assertNotIn(et.READER, prompt)
            else:
                data = json.loads(prompt.split('\nINPUT_JSON:\n')[1])
                self.assertEqual(set(data), {'material', 'queries'})
                self.assertTrue(all(set(q) == {'id', 'scenario', 'options'} for q in data['queries']))
        own_calls = fake.calls[6:8]
        wrong_calls = fake.calls[8:10]
        for index, pid in enumerate(et.PEOPLE):
            own = json.loads(own_calls[index][0].split('\nINPUT_JSON:\n')[1])['material']
            wrong = json.loads(wrong_calls[index][0].split('\nINPUT_JSON:\n')[1])['material']
            self.assertEqual(own, r['memories'][pid]['text'])
            self.assertEqual(wrong, r['memories'][et.PEOPLE[1-index]]['text'])
            self.assertTrue(own.startswith('Tentative preferences;'))

    def test_failure_controls_stop_and_preserve_all_denominators(self):
        for fault, count in [('transport', 1), ('unknown_usage', 1), ('contradictory_usage', 1),
                             ('duplicate_wire', 1), ('missing', 1), ('over_budget', 5), ('bad_quote', 5)]:
            with self.subTest(fault=fault):
                fake, r = self.run_fake(fault)
                self.assertEqual((r['status'], len(fake.calls)), ('stopped', count))
                self.assertEqual(r['planned_predictions'], 192)
                self.assertEqual(r['scores']['own']['missing'], 48)
                self.assertEqual(r['scores']['wrong']['missing'], 48)

    def test_bad_score_keeps_running_not_cherry_picked(self):
        fake = Fake(self.f)
        def wrong(*args, **kw):
            raw, p = fake(*args, **kw)
            if kw['schema'] != BROWSER_SCHEMA:
                raw = canonical({k: 'U' for k in json.loads(raw)})
            return raw, p
        r = runner.execute(self.plan, self.root/'bad-score', backend=wrong)
        self.assertEqual((r['status'], len(fake.calls)), ('complete', 10))
        self.assertEqual(r['scores']['own']['correct'], 10)
        self.assertFalse(r['retention_defined'])

    def test_changed_freeze_and_unapproved_real_are_rejected(self):
        with patch.object(generation, 'codex_generate', side_effect=AssertionError('No service')):
            with self.assertRaisesRegex(ValueError, 'human authorization'):
                runner.execute(self.plan, self.root/'unapproved')
        self.assertFalse((self.plan/'execution-intent.json').exists())
        path = self.plan/'static-requests.synthetic.json'
        data = json.loads(path.read_text())
        data['none'][et.PEOPLE[0]]['prompt'] += 'changed'
        path.write_text(canonical(data))
        with self.assertRaisesRegex(ValueError, 'Static requests'):
            et.preflight(self.plan)

    def test_existing_single_use_intent_blocks_every_backend(self):
        (self.plan/'execution-intent.json').write_text('{}')
        fake = Fake(self.f)
        with self.assertRaisesRegex(ValueError, 'already claimed'):
            runner.execute(self.plan, self.root/'claimed', backend=fake)
        self.assertFalse(fake.calls)


if __name__ == '__main__':
    unittest.main()
