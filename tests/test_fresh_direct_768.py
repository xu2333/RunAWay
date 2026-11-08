"""Fresh corpus, composed renderers and source-loss calibration; no model calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


c = load('test_direct768_contract', ROOT / 'benchmarks/fresh-direct-768-v1/check.py')
p, fixtures = c.p, c.fixtures


class FreshDirect768Tests(unittest.TestCase):
    def test_new_trajectories_are_disjoint_from_previous_people_and_exact_messages(self):
        data = p.inputs()
        old = p.seed.inputs()
        old_text = {s['text'] for v in old['sources'].values() for s in v['sources']}
        self.assertFalse(set(data['sources']) & set(old['sources']))
        self.assertFalse(old_text & {s['text'] for v in data['sources'].values() for s in v['sources']})
        self.assertEqual([len(v['sources']) for v in data['sources'].values()], [54] * 4)
        self.assertEqual([sum(s['role'] == 'user' for s in v['sources']) for v in data['sources'].values()], [36] * 4)
        self.assertTrue(all(len({s['episode_id'] for s in v['sources'][:6]}) == 6 for v in data['sources'].values()))

    def test_explicit_table_policy_queries_and_source_episode_links_match(self):
        data = p.inputs()
        self.assertEqual(len(data['rows']), 384)
        self.assertEqual([sum(r['personal_known'] for r in data['rows'] if r['person'] == x) for x in p.PROFILES], [36, 36, 48, 48])
        for family, bank in data['queries'].items():
            self.assertEqual(len(bank), 192)
            self.assertEqual(len({q['id'] for q in bank}), 192)
            for person in p.PROFILES:
                if p.bank(person) != family: continue
                self.assertEqual({q for r in data['rows'] if r['person'] == person for q in r['query_ids']}, {q['id'] for q in bank})
        for row in data['author_evidence']:
            self.assertTrue(set(row['source_ids']) < set(row['complete_episode_source_ids']))
            self.assertTrue(row['author_navigation_not_independent_gold'])

    def test_material_relaxation_and_missing_time_are_not_global_abstention(self):
        data = p.inputs()
        for row in data['rows']:
            if row['cohort'] in ('missing_material_narrow', 'failed_material_narrow'):
                self.assertEqual(row['gold'] == 'U', row['family'] == 'strict')
            if row['cohort'] in ('paired_same_choice', 'missing_time_same_choice'):
                self.assertNotEqual(row['gold'], 'U')
            if row['cohort'] in ('crossed_conditions', 'failed_material_ordinary', 'missing_material_ordinary'):
                self.assertEqual(row['gold'], 'U')

    def test_actual_public_damage_detects_five_different_source_loss_mechanisms(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            report = c.check()
        backend.assert_not_called()
        self.assertEqual(report['public_projection_damage_losses'], dict(drop_gate=24, drop_material=96,
            inherit_material=24, stale_revision=144, omit_second_choice=24))
        self.assertEqual(report['other_policy_calibration_losses']['always_unknown'], 168)
        self.assertFalse(report['measured_results_available'])

    def test_same_source_graph_preserves_all_ordered_fields_in_both_renderers(self):
        for person in p.PROFILES:
            sources = p.inputs()['sources'][person]; graph = fixtures.graph(person)
            before = copy.deepcopy((sources, graph))
            flat = p.candidate.base.bind(graph, sources, 768)
            compact = p.candidate.bind(graph, sources, 768)
            self.assertEqual(p.candidate.restore(compact['prompt.md']), p.candidate.dense.decode(flat['prompt.md']))
            self.assertEqual((sources, graph), before)
            self.assertLessEqual(len(compact['prompt.md']), len(flat['prompt.md']))
            self.assertEqual(compact['portable.json']['text'], compact['prompt.md'])
            self.assertEqual(compact['profile.private.json']['budget_characters'], 768)
            self.assertFalse(compact['summary.private.json']['behavioral_fidelity_verified'])

    def test_dictionary_only_fallback_is_size_based_and_not_a_condition_repair(self):
        person = p.PROFILES[0]; graph = fixtures.graph(person)
        files = p.candidate.bind(graph, p.inputs()['sources'][person], 768)
        self.assertEqual(files['encoding.private.json']['scheme'], 'dense')
        self.assertEqual(files['encoding.private.json']['common_conditions'], [])
        self.assertTrue(files['encoding.private.json']['available_common_conditions'])
        self.assertNotIn('先展开=', p.candidate.restore(files['prompt.md']))
        self.assertEqual(len(p.candidate.dense.parse(p.candidate.restore(files['prompt.md']))['groups']), 6)

    def test_composed_common_and_dictionary_layout_restores_exactly(self):
        # Force dictionary use after the counted common-condition clause while
        # retaining actual Unicode escaping and exact ordered conditions.
        value = dict(name='语法夹具', tagline='不是模型结果。', unknowns=['其它未知。'], groups=[])
        for i in range(3):
            value['groups'].append(dict(scope='范围%d' % i, rules=[dict(question='方法',
                requires=['仅限本题所问项目已确认的离线可撤销模拟',
                          '独立长条件&原样保留|不换序' * 4 if i < 2 else '另一条独立限制'],
                choose='方法甲', priority=0)]))
        expanded = p.candidate.dense._render(value)
        factored = p.candidate.factor.factor(expanded, 4096)['prompt']
        encoded, _ = p.candidate.dense.pack(factored, len(factored) - 1, prefix=p.candidate.dense.prefix(value))
        self.assertEqual(p.candidate.restore(encoded), expanded)
        self.assertIn('先展开=', encoded)

    def test_original_role_alias_action_guards_and_budget_cannot_be_bypassed(self):
        person = p.PROFILES[0]; sources = p.inputs()['sources'][person]; graph = fixtures.graph(person)
        for fault in ('role', 'action', 'alias', 'budget'):
            bad = copy.deepcopy(graph)
            if fault == 'role': bad['nodes'][0]['decisions'][0]['source_id'] = next(s['id'] for s in sources['sources'] if s['role'] == 'assistant')
            if fault == 'action': bad['nodes'][0]['action'] = '来源未选的新办法'
            if fault == 'alias': bad['object_aliases'][0]['evidence'][0]['source_id'] = sources['sources'][0]['id']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                p.candidate.bind(bad, sources, 300 if fault == 'budget' else 768)

    def test_structural_accounting_still_does_not_prove_both_choices_were_kept(self):
        person = p.PROFILES[0]; sources = p.inputs()['sources'][person]; bad = fixtures.graph(person)
        bad['nodes'] = [n for n in bad['nodes'] if n['id'] != '0_low']
        for entry in bad['source_accounting'].values():
            entry['node_ids'] = [n for n in entry['node_ids'] if n != '0_low']
        files = p.candidate.bind(bad, sources, 768)
        value = p.candidate.dense.parse(p.candidate.restore(files['prompt.md']))
        row = next(r for r in p.inputs()['rows'] if (r['person'], r['case']) == (person, '0_ordinary'))
        self.assertNotEqual(c.public_target(value, row), row['gold'])
        self.assertFalse(files['summary.private.json']['behavioral_fidelity_verified'])

    def test_public_entrypoints_are_isolated_and_never_call_a_model(self):
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
        with tempfile.TemporaryDirectory() as tmp:
            for script, args in (('check.py', []), ('plan.py', ['--out', str(Path(tmp) / 'packet')])):
                proc = subprocess.run([sys.executable, '-I', '-B', str(p.HERE / script), *args],
                    cwd=tmp, env=env, capture_output=True, text=True, timeout=90)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertFalse(json.loads(proc.stdout)['approved'])
            denied = subprocess.run([sys.executable, '-I', '-B', str(p.HERE / 'gate.py')], cwd=tmp,
                env=env, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn('zero model calls', denied.stderr)


if __name__ == '__main__': unittest.main()
