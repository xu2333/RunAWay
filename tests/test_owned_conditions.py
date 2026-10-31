"""Symbolic codec calibration, not NLP support or measured model fidelity."""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owned_condition_candidate_test', ROOT / 'benchmarks/owned-conditions-v1/candidate.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def fixture():
    texts = {'s1': '谈到花园路径，天晴且侧门已开时我通常走草地。已承诺带客人走回廊时，我优先走回廊；这个约定不要求天晴或侧门已开。',
             's2': '所有这些路线选择都只限已经获准进入花园的访客。',
             's3': '我猜可以走河边。',
             's4': '另有一盏阅读灯，夜间阅读的暖光和冷光两条便签同等有效，谁也没撤销谁。'}
    sources = {'schema_version': 1, 'sources': [{'id': k, 'episode_id': 'garden', 'role': 'assistant' if k == 's3' else 'user', 'text': v} for k, v in texts.items()]}
    def anchor(sid):
        return {'source_id': sid, 'quote': texts[sid]}
    def condition(text, sid):
        return {'text': text, 'evidence': [anchor(sid)]}
    common = condition('已获准进入花园', 's2')
    ordinary = condition('天晴且侧门已开', 's1')
    exception = condition('已承诺带客人走回廊', 's1')
    def row(requirements, action, priority):
        return {'object': '花园路径', 'question': '路线选择', 'requires': copy.deepcopy(requirements),
                'action': action, 'priority': priority, 'decisions': [anchor('s1')],
                'contexts': [anchor('s1')], 'supersedes': []}
    ledger = {'version': c.VERSION, 'name': '花园分岔团', 'tagline': '约定走哪条，就把前提放对格。',
              'rows': [row([common, ordinary], '走草地', 0), row([common, exception], '走回廊', 1)],
              'unknowns': ['未获准进入花园或没有唯一已知做法时未知。']}
    return sources, ledger


def choose(rows, facts):
    active = [r for r in rows if all(facts[c.condition_key(x)] for x in r['requires'])]
    if not active:
        return 'U'
    level = max(r['priority'] for r in active)
    actions = {r['action'] for r in active if r['priority'] == level}
    return next(iter(actions)) if len(actions) == 1 else 'U'


class OwnedConditionTests(unittest.TestCase):
    def test_encoder_sees_only_source_no_budget_questions_or_teacher(self):
        sources, _ = fixture()
        request = c.make_request(sources)
        body = json.loads(request['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n')[1])
        self.assertEqual(body, {'sources': sources})
        self.assertEqual(request, c.make_request(sources))
        with self.assertRaises(TypeError):
            c.make_request(sources, 1024)

    def test_intersection_preserves_all_boolean_worlds_and_does_not_hoist_ordinary(self):
        _, ledger = fixture()
        plan = c.factor(ledger['rows'])[0]
        self.assertEqual([x['text'] for x in plan['common']], ['已获准进入花园'])
        keys = sorted({c.condition_key(x) for r in ledger['rows'] for x in r['requires']})
        for values in itertools.product((False, True), repeat=len(keys)):
            facts = dict(zip(keys, values))
            restored = [dict(m['row'], requires=plan['common']+m['residual']) for m in plan['members']]
            self.assertEqual(choose(ledger['rows'], facts), choose(restored, facts))

    def test_union_hoist_and_global_erasure_are_detectably_wrong(self):
        _, ledger = fixture()
        base, exception = ledger['rows']
        common, ordinary = base['requires']; trigger = exception['requires'][1]
        facts = {c.condition_key(common): True, c.condition_key(ordinary): False, c.condition_key(trigger): True}
        self.assertEqual(choose(ledger['rows'], facts), '走回廊')
        union = {c.condition_key(x): x for row in ledger['rows'] for x in row['requires']}
        damaged = [dict(r, requires=list(union.values())) for r in ledger['rows']]
        self.assertEqual(choose(damaged, facts), 'U')
        facts[c.condition_key(common)] = False
        self.assertEqual(choose(ledger['rows'], facts), 'U')
        erased = [dict(r, requires=[x for x in r['requires'] if c.condition_key(x) != c.condition_key(common)]) for r in ledger['rows']]
        self.assertEqual(choose(erased, facts), '走回廊')

    def test_missing_ordinary_condition_does_not_block_exception_but_real_global_does(self):
        _, ledger = fixture()
        common, ordinary = ledger['rows'][0]['requires']; trigger = ledger['rows'][1]['requires'][1]
        def possible(gvalues):
            answers = set()
            for g, a in itertools.product(gvalues, (False, True)):
                answers.add(choose(ledger['rows'], {c.condition_key(common): g, c.condition_key(ordinary): a, c.condition_key(trigger): True}))
            return answers
        self.assertEqual(possible([True]), {'走回廊'})
        self.assertEqual(possible([False, True]), {'U', '走回廊'})

    def test_different_questions_or_grounding_are_not_shared(self):
        _, ledger = fixture()
        altered = copy.deepcopy(ledger)
        altered['rows'][1]['question'] = '执行许可'
        self.assertEqual(c.factor(altered['rows'])[0]['common'], [])
        altered = copy.deepcopy(ledger)
        altered['rows'][1]['requires'][0]['evidence'][0]['source_id'] = 'different'
        self.assertEqual(c.factor(altered['rows'])[0]['common'], [])

    def test_compile_uses_original_renderer_and_keeps_all_owned_conditions(self):
        sources, ledger = fixture()
        projected, plans = c.project(ledger, sources)
        files = c.bind(ledger, sources, 1024)
        original = c.grouped.bind(projected, sources, 1024)
        self.assertEqual(files['prompt.md'], original['prompt.md'])
        self.assertEqual(files['portable.json'], original['portable.json'])
        self.assertIn('已获准进入花园', projected['groups'][0]['scope'])
        self.assertNotIn('天晴', projected['groups'][0]['scope'])
        self.assertIn('天晴', projected['groups'][0]['rules'][0]['when'])
        self.assertNotIn('天晴', projected['groups'][0]['rules'][1]['when'])
        self.assertFalse(files['owned-conditions.private.json']['annotation_semantics_verified'])
        self.assertTrue(all(rule['when'] for group in projected['groups'] for rule in group['rules']))

    def test_invalid_quotes_roles_duplicates_and_overbudget_do_not_trigger_repairs(self):
        sources, ledger = fixture()
        for fault in ('quote', 'role', 'duplicate', 'budget'):
            altered = copy.deepcopy(ledger)
            if fault == 'quote':
                altered['rows'][0]['requires'][0]['evidence'][0]['quote'] = 'invented'
            elif fault == 'role':
                source = sources['sources'][2]
                altered['rows'][0]['decisions'] = [{'source_id': source['id'], 'quote': source['text']}]
            elif fault == 'duplicate':
                altered['rows'][0]['requires'].append(copy.deepcopy(altered['rows'][0]['requires'][0]))
            before = copy.deepcopy(altered)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                c.bind(altered, sources, 1 if fault == 'budget' else 1024)
            self.assertEqual(altered, before)

    def test_same_priority_conflict_survives_projection(self):
        sources, ledger = fixture()
        anchor = {'source_id': 's4', 'quote': sources['sources'][3]['text']}
        for action in ('暖光', '冷光'):
            ledger['rows'].append({'object': '那盏阅读灯', 'question': '灯色', 'requires': [], 'action': action,
                'priority': 0, 'decisions': [anchor], 'contexts': [anchor], 'supersedes': []})
        projected, _ = c.project(ledger, sources)
        lamp = next(g for g in projected['groups'] if g['scope'] == '那盏阅读灯')
        self.assertEqual(len(lamp['rules']), 2)
        self.assertEqual({r['choose'] for r in lamp['rules']}, {'暖光', '冷光'})
        self.assertEqual({r['priority'] for r in lamp['rules']}, {0})
        c.bind(ledger, sources, 1024)


if __name__ == '__main__':
    unittest.main()
