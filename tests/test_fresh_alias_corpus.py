"""Fresh-world integrity and discriminating fixtures, not model measurements."""
import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c = load('fresh_alias_corpus_test', ROOT / 'benchmarks/fresh-alias-generalization-v1/corpus.py')
from runaway.card import canonical
from runaway.profile import validate_sources


class FreshAliasCorpusTests(unittest.TestCase):
    def test_four_people_two_families_and_exact_source_case_question_denominators(self):
        data = c.build()
        self.assertEqual((len(data['sources']), len(data['rows'])), (4, 176))
        self.assertEqual(sum(r['gold'] != 'U' for r in data['rows']), 112)
        self.assertEqual(len({(r['person'], r['case']) for r in data['rows']}), 176)
        forms = [q for bank in data['queries'].values() for q in bank]
        self.assertEqual(len(forms), 176)
        self.assertEqual(len({canonical(q) for q in forms}), 176)
        for person, sources in data['sources'].items():
            validate_sources(sources)
            self.assertEqual(len(sources['sources']), 48)
            self.assertEqual(sum(s['role'] == 'user' for s in sources['sources']), 36)
            self.assertEqual({s['role'] for s in sources['sources']}, {'user', 'assistant', 'tool', 'context'})
            self.assertGreater(sum(len(s['text']) for s in sources['sources']), 1536)
            self.assertLess(len(canonical(sources).encode()), 64000)
            own = [r for r in data['rows'] if r['person'] == person]
            self.assertEqual((len(own), sum(r['gold'] != 'U' for r in own)), (44, 28))
        for family in ('chain', 'qualified'):
            own = [r for r in data['rows'] if r['family'] == family]
            self.assertEqual((len(own), sum(r['gold'] != 'U' for r in own)), (88, 56))

    def test_no_prior_people_trajectories_or_old_action_vocabulary_are_reused(self):
        old = load('fresh_alias_old_world_check', ROOT / 'benchmarks/scope-binding-stress-v1/corpus.py').build()
        new = c.build()
        self.assertFalse(set(new['sources']) & set(old['sources']))
        before = {canonical(s) for s in old['sources'].values()}
        self.assertTrue(all(canonical(s) not in before for s in new['sources'].values()))
        texts = [s['text'] for source in new['sources'].values() for s in source['sources']]
        self.assertTrue(all('先发简版' not in t and '先发全版' not in t for t in texts))
        self.assertFalse(new['design']['independent_holdout'])
        self.assertFalse(new['design']['independent_semantic_gold'])

    def test_manual_constructor_table_catches_choice_or_composed_mapping_drift(self):
        with patch.object(c, 'BITS', tuple((1, 1, 1, 1) for _ in c.PROFILES)):
            with self.assertRaises(ValueError): c.build()
        with patch.object(c, 'OLD_MID', ((0, 1, 2, 3), c.OLD_MID[1])):
            with self.assertRaises(ValueError): c.build()
        first = c.build();first['sources']['otter']['sources'][0]['text'] = 'modified'
        self.assertNotEqual(first, c.build())

    def test_two_hop_chain_is_interleaved_without_terminal_old_user_coquotation(self):
        data = c.build()
        for pi in (0, 1):
            messages = data['sources'][c.PROFILES[pi]]['sources']
            self.assertEqual(len({s['episode_id'] for s in messages[:4]}), 4)
            for oi in range(4):
                episode = [s for s in messages if s['episode_id'] == 'journal%d' % oi]
                old, mid, current = c.CHAIN_OLD[oi], c.CHAIN_MID[c.OLD_MID[pi][oi]], c.CHAIN_CURRENT[c.old_current(pi, oi)]
                self.assertIn(old, episode[8]['text']);self.assertIn(mid, episode[8]['text'])
                self.assertIn(mid, episode[9]['text']);self.assertIn(current, episode[9]['text'])
                self.assertFalse(any(old in s['text'] and current in s['text'] for s in episode if s['role'] == 'user'))
                self.assertIn('现在我选', episode[7]['text'])
                self.assertIn('模拟许可、完整条件和优先关系沿用', episode[7]['text'])

    def test_qualified_homonyms_remain_distinct_and_denied_questions_do_not_give_away_U(self):
        data = c.build()
        for pi in (2, 3):
            for pair in ((0, 1), (2, 3)):
                self.assertNotEqual(c.BITS[pi][pair[0]], c.BITS[pi][pair[1]])
                self.assertNotEqual(c.BITS[pi][c.old_current(pi, pair[0])], c.BITS[pi][c.old_current(pi, pair[1])])
            for i in range(4):
                text = c.scenario('qualified', i, 'ambiguity')
                self.assertFalse(any(name in text for name in c.QUAL_CURRENT + c.QUAL_OLD))
        for family in ('chain', 'qualified'):
            for i in range(4):
                text = c.scenario(family, i, 'denied_name')
                self.assertIn(c.denied_name(family, i), text)
                self.assertNotIn('不是同一', text)
                self.assertNotIn('尚未选', text)
            bank = data['queries'][family]
            self.assertEqual(len({q['scenario'] for q in bank}), 44)
            for i in range(0, len(bank), 2):
                self.assertEqual(bank[i]['scenario'], bank[i + 1]['scenario'])
                self.assertEqual(bank[i]['options']['A'], bank[i + 1]['options']['B'])

    def test_ten_damages_expose_distinct_failures_without_becoming_model_scores(self):
        expected = dict(drop_positive_names=52, drop_chain_edges=24, guess_mapping=33,
                        merge_denied=16, erase_namespace=8, stale_revision=48,
                        drop_gate=16, tool_fact=16, over_abstain=16, always_unknown=112)
        damages = c.damage_summary()
        for key, n in expected.items():
            self.assertEqual(len(damages[key]['losses']), n)
            self.assertEqual(damages[key]['correct'], 176 - n)
            self.assertTrue(damages[key]['oracle_calibration_not_model_measurement'])
        self.assertTrue(all(x['gold'] == 'U' and x['damaged'] != 'U' for x in damages['merge_denied']['losses']))

    def test_source_navigation_is_own_role_aware_and_ambiguity_keeps_both_owners(self):
        data = c.build()
        for row in data['author_evidence']:
            source = {s['id']: s for s in data['sources'][row['person']]['sources']}
            self.assertEqual({source[s]['role'] for s in row['source_ids']}, {'user'})
            self.assertTrue(all(source[s]['role'] != 'user' for s in row['context_source_ids']))
            expected = 2 if row['person'] in ('tansy', 'sedge') and row['case'].endswith(('_ambiguity', '_same_choice_contexts')) else 1
            self.assertEqual(len({source[s]['episode_id'] for s in row['source_ids']}), expected)

    def test_literal_contract_exposes_naive_chain_closure_and_is_not_semantic_acceptance(self):
        a = load('fresh_alias_contract_fixture', ROOT / 'benchmarks/scope-alias-encoding-v1/candidate.py')
        sources = dict(schema_version=1, sources=[
            dict(id='u1', episode_id='chain', role='user', text='雾舟在许可时，我选先做小样。'),
            dict(id='u2', episode_id='chain', role='user', text='雾舟改为云栈，仍是同一项。'),
            dict(id='u3', episode_id='chain', role='user', text='云栈再改为晨桅，仍是同一项。')])
        anchor = lambda sid: dict(source_id=sid, quote=next(s['text'] for s in sources['sources'] if s['id'] == sid))
        answer = dict(version=a.VERSION, name='链条夹具', tagline='不是模型推理结果。', objects=['晨桅'],
                      unknowns=['许可外的选择未知。'], derived_node_ids=[],
                      nodes=[dict(id='n', kind='base', target_kind='choice', object_index=0, question='准备策略',
                                  requires=[dict(text='许可时', evidence=[anchor('u1')])], action='先做小样', priority=0,
                                  decisions=[anchor('u1')], contexts=[anchor('u1')], order_split=None)],
                      source_accounting={sid: dict(kind='direct_choice' if sid == 'u1' else 'no_choice', node_ids=['n'] if sid == 'u1' else [],
                                                   alias_ids=[] if sid == 'u1' else [sid], reason='结构诊断夹具，不是语义裁定。') for sid in ('u1', 'u2', 'u3')},
                      object_aliases=[dict(id='u2', object_index=0, canonical='晨桅', alias='雾舟', evidence=[anchor('u2')]),
                                      dict(id='u3', object_index=0, canonical='晨桅', alias='云栈', evidence=[anchor('u3')])])
        with self.assertRaisesRegex(ValueError, 'literal same-message witness'): a.bind(answer, sources)
        # A multi-name object allows a structural route using the intermediate
        # canonical field. That is not proof of compliance with semantic guidance
        # (which calls canonical a current name), nor a model-generation result.
        changed = copy.deepcopy(answer);changed['objects'] = ['晨桅/云栈'];changed['object_aliases'][0]['canonical'] = '云栈'
        files = a.bind(changed, sources)
        self.assertTrue(all(name in files['prompt.md'] for name in ('雾舟', '云栈', '晨桅')))
        self.assertFalse(files['scope-aliases.private.json']['same_scope_semantics_verified'])
        self.assertFalse(files['scope-aliases.private.json']['behavioral_fidelity_verified'])


if __name__ == '__main__':
    unittest.main()
