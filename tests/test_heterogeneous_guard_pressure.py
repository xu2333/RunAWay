"""New source semantics and author-projection capacity; zero model calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


c = load('pressure_test_check', ROOT / 'benchmarks/heterogeneous-guard-pressure-v1/check.py')
p = c.p


class HeterogeneousGuardPressureTests(unittest.TestCase):
    def test_people_messages_and_information_vary_from_previous_measured_sources(self):
        data = p.inputs(); old = p.seed.inputs()
        self.assertFalse(set(data['sources']) & set(old['sources']))
        before = {s['text'] for source in old['sources'].values() for s in source['sources']}
        now = [s['text'] for source in data['sources'].values() for s in source['sources']]
        self.assertEqual(len(now), 96); self.assertFalse(set(now) & before)
        self.assertEqual(len({s[2] for s in p.corpus.SPECS}), 6)
        self.assertEqual(len({a for s in p.corpus.SPECS for a in s[9:11]}), 12)
        self.assertEqual({s[11] for s in p.corpus.SPECS}, {'threshold', 'guard', 'release'})

    def test_hand_table_policy_and_unique_public_text_match_full_denominators(self):
        data = p.inputs()
        self.assertEqual((len(data['rows']), sum(r['personal_known'] for r in data['rows'])), (164, 72))
        self.assertEqual(len({p.digest({k:q[k] for k in ('scenario','options')})
            for bank in data['queries'].values() for q in bank}), 328)
        for person in p.PROFILES:
            own = [r for r in data['rows'] if r['person'] == person]
            self.assertEqual(len(own), 82)
            ids = {q['id'] for q in data['queries'][person]}
            self.assertEqual(ids, {q for r in own for q in r['query_ids']})
            for row in own:
                pair = [q for q in data['queries'][person] if q['id'] in row['query_ids']]
                self.assertEqual(pair[0]['scenario'], pair[1]['scenario'])
                self.assertEqual(pair[0]['options']['A'], pair[1]['options']['B'])

    def test_author_current_graph_preserves_all164_choices_through_public_projection(self):
        data = p.inputs()
        for person in p.PROFILES:
            files = p.candidate.bind(p.corpus.graph(person), data['sources'][person], 1536)
            value = p.candidate.dense.parse(p.candidate.restore(files['prompt.md']))
            self.assertEqual(sum(len(g['rules']) for g in value['groups']), 18)
            self.assertTrue(all(c.public_target(value, r) == r['gold'] for r in data['rows'] if r['person'] == person))
            for obj in range(6):
                self.assertTrue(all(a in files['prompt.md'] for a in p.corpus.actions(p.PROFILES.index(person), obj)))

    def test_complete_author_projection_fails768_but_fit_is_not_model_fidelity(self):
        report = c.check()
        self.assertEqual(json.loads((p.HERE / 'preflight.synthetic.json').read_text()), report)
        self.assertEqual([x['expanded_characters'] for x in report['author_fixture_capacity']], [974, 977])
        for parent in report['author_fixture_capacity']:
            self.assertFalse(next(x for x in parent['caps'] if x['budget'] == 768)['fits'])
            self.assertTrue(next(x for x in parent['caps'] if x['budget'] == 1536)['fits'])
            self.assertTrue(parent['not_an_information_theoretic_lower_bound'])
        self.assertEqual(report['new_model_calls'], 0)
        self.assertFalse(report['model_results_available'])

    def test_threshold_amendment_moves_the_old_boundary_without_reversing_actions(self):
        data = p.inputs()
        for pi, person in enumerate(p.PROFILES):
            for obj in (0, 3):
                a, b = p.corpus.actions(pi, obj)
                self.assertEqual(p.corpus.target(pi, obj, 'old_boundary'), b)
                self.assertEqual(p.corpus.target(pi, obj, 'new_boundary'), a)
                self.assertEqual(p.corpus.target(pi, obj, 'old_boundary', 'stale_threshold'), a)
                source = next(s for s in data['sources'][person]['sources']
                    if s['episode_id'] == 'project%d' % obj and '本次只修条件' in s['text'])
                self.assertIn('不变', source['text'])

    def test_guard_replacement_does_not_accept_the_obsolete_guard(self):
        for pi in (0, 1):
            for obj in (1, 4):
                self.assertEqual(p.corpus.target(pi, obj, 'old_guard_only'), 'U')
                self.assertEqual(p.corpus.target(pi, obj, 'old_guard_only', 'old_guard'), p.corpus.actions(pi, obj)[0])

    def test_narrow_release_does_not_spread_to_ordinary_branches_or_missing_gate(self):
        for pi in (0, 1):
            for obj in (2, 5):
                a = p.corpus.actions(pi, obj)[0]
                self.assertEqual(p.corpus.target(pi, obj, 'guard_false_narrow'), a)
                self.assertEqual(p.corpus.target(pi, obj, 'guard_missing_narrow'), a)
                self.assertEqual(p.corpus.target(pi, obj, 'guard_false_ordinary'), 'U')
                self.assertEqual(p.corpus.target(pi, obj, 'gate_missing'), 'U')

    def test_public_damage_and_separate_policy_expose_the_same_specific_omissions(self):
        report = c.check()
        self.assertEqual(report['public_projection_damage_case_counts'], dict(
            stale_threshold=12, old_guard=4, reinstate_guard=8, drop_gate=12, drop_guard=44))
        self.assertTrue(report['damage_is_constructed_not_observed_model_loss'])

    def test_bad_source_id_role_alias_and_unknown_public_predicate_are_not_repaired(self):
        sources = p.inputs()['sources']['rivet']; original = p.corpus.graph('rivet')
        for fault in ('id', 'role', 'alias'):
            answer = copy.deepcopy(original)
            if fault == 'id': answer['nodes'][0]['decisions'][0]['source_id'] = 'not-in-source'
            elif fault == 'role':
                sid = next(s['id'] for s in sources['sources'] if s['role'] == 'assistant')
                answer['nodes'][0]['decisions'][0]['source_id'] = sid
            else: answer['object_aliases'][0]['alias'] = '虚构的来源外别名'
            with self.subTest(fault=fault), self.assertRaises(ValueError): p.candidate.bind(answer, sources, 1536)
        value = p.candidate.dense.parse(p.candidate.restore(p.candidate.bind(original, sources, 1536)['prompt.md']))
        value['groups'][0]['rules'][0]['requires'].append('按常识总会成立')
        with self.assertRaises(ValueError): c.choose(value, 0, (True, 13, True, False, True))

    def test_preparation_and_check_entrypoints_work_outside_checkout_without_pythonpath(self):
        env = dict(os.environ); env.pop('PYTHONPATH', None)
        with tempfile.TemporaryDirectory() as tmp:
            for script, extra in (('check.py', []), ('plan.py', ['--out', str(Path(tmp) / 'packet')])):
                proc = subprocess.run([sys.executable, '-B', str(p.HERE / script), *extra], cwd=tmp,
                                      env=env, text=True, capture_output=True, timeout=60)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                report = json.loads(proc.stdout)
                self.assertEqual(report['new_model_calls'], 0); self.assertFalse(report['approved'])
            self.assertTrue(p.verify(Path(tmp) / 'packet'))


if __name__ == '__main__': unittest.main()
