"""Authored-world integrity and discriminating damage controls; no model results."""
import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binding_corpus_test', ROOT / 'benchmarks/scope-binding-stress-v1/corpus.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
from runaway.card import canonical
from runaway.profile import validate_sources


class ScopeBindingCorpusTests(unittest.TestCase):
    def test_population_source_size_roles_and_fixed_known_unknown_denominators(self):
        data = c.build()
        self.assertEqual((len(data['rows']), len(data['queries']['all'])), (64, 64))
        self.assertEqual(sum(r['gold'] != 'U' for r in data['rows']), 40)
        self.assertEqual(len({(r['person'], r['case']) for r in data['rows']}), 64)
        self.assertEqual(len({q['id'] for q in data['queries']['all']}), 64)
        for sources in data['sources'].values():
            validate_sources(sources)
            self.assertEqual(len(sources['sources']), 48)
            self.assertEqual(sum(s['role'] == 'user' for s in sources['sources']), 28)
            self.assertEqual({s['role'] for s in sources['sources']}, {'user', 'assistant', 'tool', 'context'})
            self.assertGreater(sum(len(s['text']) for s in sources['sources']), 1536)
            self.assertLess(len(canonical(sources).encode()), 64000)

    def test_project_interleaving_and_late_same_context_revision_precede_renaming(self):
        data = c.build()
        for pi, person in enumerate(c.PROFILES):
            messages = data['sources'][person]['sources']
            self.assertEqual(len({s['episode_id'] for s in messages[:4]}), 4)
            for i, old in enumerate(c.OLD):
                prior, revision, rename, reaffirm = [messages[phase * 4 + i] for phase in (6, 8, 9, 11)]
                self.assertEqual({s['episode_id'] for s in (prior, revision, rename, reaffirm)}, {'thread%d' % i})
                self.assertIn(old, revision['text'])
                self.assertIn(c.CURRENT[c.RENAME[pi][i]], rename['text'])
                self.assertIn('只改', revision['text'])
                self.assertIn('原有许可前提', revision['text'])
                self.assertNotIn('先发简版', revision['text'])
                self.assertNotIn('先发全版', revision['text'])

    def test_queries_share_action_vocabulary_without_supplying_an_alias_decoder(self):
        data = c.build()
        for query in data['queries']['all']:
            values = set(query['options'].values())
            self.assertIn(values, (set(c.ACTIONS), {'已实际发送', '尚未实际发送'}))
            self.assertNotIn('青扣', query['scenario'])
            self.assertNotIn('白扣', query['scenario'])
            self.assertNotIn('kestrel', query['scenario'])
            self.assertNotIn('willow', query['scenario'])
        for row in data['rows']:
            queries = [q for q in data['queries']['all'] if q['id'] in row['query_ids']]
            self.assertEqual(queries[0]['scenario'], queries[1]['scenario'])
            self.assertEqual(set(queries[0]['options'].values()), set(queries[1]['options'].values()))

    def test_all_evidence_links_stay_own_user_sources_and_execution_is_unknown(self):
        data = c.build()
        for row in data['author_evidence']:
            sources = {s['id']: s for s in data['sources'][row['person']]['sources']}
            self.assertEqual({sources[sid]['role'] for sid in row['source_ids']}, {'user'})
        execution = [r for r in data['rows'] if r['cohort'] == 'execution_fact']
        self.assertEqual(len(execution), 8)
        self.assertTrue(all(r['gold'] == 'U' for r in execution))
        self.assertEqual(sum(r['cohort'] in ('base_old_alias', 'revised_old_alias') for r in data['rows']), 16)
        self.assertEqual(sum(r['cohort'] in ('revised_current', 'revised_old_alias') for r in data['rows']), 16)

    def test_each_prespecified_damage_exposes_its_target_without_becoming_model_evidence(self):
        damage = c.damage_summary()
        expected = {'drop_alias': 4, 'unresolved_alias': 16, 'stale_revision': 16,
                    'drop_scope': 8, 'tool_fact': 8, 'always_unknown': 40}
        for key, losses in expected.items():
            self.assertEqual(len(damage[key]['losses']), losses)
            self.assertEqual(damage[key]['correct'], 64 - losses)
            self.assertTrue(damage[key]['oracle_calibration_not_model_measurement'])
        self.assertTrue(all(x['gold'] == 'U' for x in damage['tool_fact']['losses']))
        self.assertTrue(all(x['gold'] != 'U' and x['damaged'] == 'U' for x in damage['unresolved_alias']['losses']))

    def test_separate_hand_table_detects_constructor_drift_and_build_returns_fresh_values(self):
        with patch.object(c, 'HAND', tuple(tuple('U' for _ in range(32)) for _ in c.PROFILES)):
            with self.assertRaises(ValueError):
                c.build()
        first = c.build()
        first['sources'][c.PROFILES[0]]['sources'][0]['text'] = 'changed'
        self.assertNotEqual(first, c.build())
        self.assertFalse(c.build()['design']['independent_semantic_gold'])


if __name__ == '__main__':
    unittest.main()
