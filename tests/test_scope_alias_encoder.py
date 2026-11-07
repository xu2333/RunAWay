"""Source-to-public alias conservation and refusal guards; no model fidelity claim."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('scope_alias_encoder_test', ROOT / 'benchmarks/scope-alias-encoding-v1/candidate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def example():
    sources = {'schema_version': 1, 'sources': [
        dict(id='s1', episode_id='one', role='user', text='有许可时，纸笺我选发简版。'),
        dict(id='s2', episode_id='two', role='user', text='有许可时，风筝我选发全版。'),
        dict(id='s3', episode_id='one', role='user', text='石头改名纸笺，旧新名指同一项。'),
        dict(id='s4', episode_id='two', role='user', text='羽毛改名风筝，旧新名指同一项。'),
        dict(id='s5', episode_id='boundary', role='user', text='缺许可的选择以及是否实际已发送未知。'),
        dict(id='a1', episode_id='one', role='assistant', text='石头与风筝也许是同一项。'),
    ]}
    answer = dict(version=m.VERSION, name='两只纸包', tagline='名字换了，选择还跟着。',
                  objects=['纸笺', '风筝'], nodes=[], unknowns=['缺许可的选择以及实际是否已发送未知。'],
                  derived_node_ids=[], source_accounting={}, object_aliases=[])
    for source in sources['sources']:
        if source['role'] == 'user':
            answer['source_accounting'][source['id']] = dict(kind='no_choice', node_ids=[], alias_ids=[], reason='边界或范围关系，没有新动作选择。')
    for i, action in enumerate(('发简版', '发全版')):
        source = sources['sources'][i]
        anchor = dict(source_id=source['id'], quote=source['text'])
        node = dict(id='n' + str(i), kind='base', target_kind='choice', object_index=i,
                    question='准备形式', requires=[dict(text='有许可', evidence=[anchor])],
                    action=action, priority=0, decisions=[anchor], contexts=[anchor], order_split=None)
        answer['nodes'].append(node)
        answer['source_accounting'][source['id']].update(kind='direct_choice', node_ids=[node['id']])
        relation_source = sources['sources'][i + 2]
        relation = dict(id='a' + str(i), object_index=i, canonical=answer['objects'][i],
                        alias=('石头', '羽毛')[i], evidence=[dict(source_id=relation_source['id'], quote=relation_source['text'])])
        answer['object_aliases'].append(relation)
        answer['source_accounting'][relation_source['id']]['alias_ids'] = [relation['id']]
    return sources, answer


class ScopeAliasEncoderTests(unittest.TestCase):
    def test_request_keeps_own_sources_budget_and_all_user_alias_accounting(self):
        sources, _ = example()
        request = m.make_request(sources, 768)
        body = json.loads(request['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
        self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
        self.assertEqual(body['sources'], sources)
        self.assertEqual(body['budget_characters'], 768)
        accounting = request['schema']['properties']['source_accounting']
        self.assertEqual(set(accounting['required']), {'s1', 's2', 's3', 's4', 's5'})
        self.assertTrue(all('alias_ids' in entry['required'] for entry in accounting['properties'].values()))

    def test_background_rename_survives_public_compilation_without_changing_decisions(self):
        sources, answer = example()
        before = copy.deepcopy(answer)
        projected, changes = m.project(answer, sources)
        self.assertEqual(projected['objects'], ['纸笺（又名石头）', '风筝（又名羽毛）'])
        for key in ('nodes', 'unknowns', 'name', 'tagline', 'derived_node_ids'):
            self.assertEqual(projected[key], answer[key])
        self.assertEqual(answer, before)
        self.assertEqual(answer['source_accounting']['s3']['kind'], 'no_choice')
        files = m.bind(answer, sources)
        expected = m.base.bind(projected, sources)
        self.assertEqual({k: v for k, v in files.items() if k != 'scope-aliases.private.json'}, expected)
        for change in changes:
            self.assertIn(change['public'], files['prompt.md'])
        self.assertFalse(files['scope-aliases.private.json']['behavioral_fidelity_verified'])

    def test_alias_references_are_bidirectional_and_cannot_be_missing_or_repeated(self):
        sources, original = example()
        for fault in ('unclaimed', 'undefined', 'repeated_ref', 'duplicate_id', 'duplicate_relation', 'missing_field'):
            answer = copy.deepcopy(original)
            if fault == 'unclaimed': answer['source_accounting']['s3']['alias_ids'] = []
            elif fault == 'undefined': answer['source_accounting']['s3']['alias_ids'] = ['foreign']
            elif fault == 'repeated_ref': answer['source_accounting']['s3']['alias_ids'] *= 2
            elif fault == 'duplicate_id': answer['object_aliases'][1]['id'] = 'a0'
            elif fault == 'duplicate_relation':
                duplicate = copy.deepcopy(answer['object_aliases'][0]);duplicate['id'] = 'a2'
                answer['object_aliases'].append(duplicate);answer['source_accounting']['s3']['alias_ids'].append('a2')
            else: del answer['source_accounting']['s3']['alias_ids']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.bind(answer, sources)

    def test_aliases_need_real_own_user_quotes_containing_both_literal_names(self):
        sources, original = example()
        for fault in ('forged', 'one_name', 'assistant', 'wrong_source', 'identical'):
            answer = copy.deepcopy(original)
            relation = answer['object_aliases'][0]
            if fault == 'forged': relation['evidence'][0]['quote'] += '伪造'
            elif fault == 'one_name': relation['evidence'][0]['quote'] = '纸笺'
            elif fault == 'assistant': relation.update(canonical='风筝', object_index=1, evidence=[dict(source_id='a1', quote=sources['sources'][-1]['text'])])
            elif fault == 'wrong_source': relation['evidence'][0]['source_id'] = 's4'
            else: relation['alias'] = relation['canonical']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.bind(answer, sources)

    def test_cross_object_name_collision_and_undefined_owner_reject(self):
        sources, original = example()
        for fault in ('owner', 'canonical', 'collision', 'blank_name', 'blank_id'):
            answer = copy.deepcopy(original)
            if fault == 'owner': answer['object_aliases'][0]['object_index'] = 11
            elif fault == 'canonical': answer['object_aliases'][0]['canonical'] = '外来对象'
            elif fault == 'collision': answer['objects'][1] = '风筝和石头'
            elif fault == 'blank_name': answer['object_aliases'][0]['alias'] = ' '
            else:
                answer['object_aliases'][0]['id'] = ' '
                answer['source_accounting']['s3']['alias_ids'] = [' ']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.bind(answer, sources)

    def test_existing_decision_witness_guard_and_exact_whole_card_budget_stay_active(self):
        sources, answer = example()
        # Incompressible fixture payload exercises the existing 300-char floor;
        # repeated prose would be shortened by the unchanged dictionary codec.
        answer['unknowns'].append(''.join(chr(0x4e00 + i) for i in range(140)))
        files = m.bind(answer, sources)
        size = len(files['prompt.md'])
        self.assertEqual(m.bind(answer, sources, size)['prompt.md'], files['prompt.md'])
        with self.assertRaises(ValueError):
            m.bind(answer, sources, 300)
        answer['nodes'][0]['action'] = '发全版'
        with self.assertRaisesRegex(ValueError, 'literal witness'):
            m.bind(answer, sources)

    def test_no_declared_aliases_is_identical_to_original_and_not_a_completeness_certificate(self):
        sources, answer = example()
        answer['object_aliases'] = []
        for entry in answer['source_accounting'].values(): entry['alias_ids'] = []
        normalized, changes = m.project(answer, sources)
        files = m.bind(answer, sources)
        self.assertEqual(changes, [])
        self.assertEqual(files['prompt.md'], m.base.bind(normalized, sources)['prompt.md'])
        self.assertNotIn('石头', files['prompt.md'])
        self.assertFalse(files['scope-aliases.private.json']['source_alias_completeness_verified'])

    def test_literal_binding_does_not_prove_same_scope_semantics_or_user_fidelity(self):
        sources, answer = example()
        source = sources['sources'][2]
        source['text'] = '石头与纸笺不是同一项。'
        answer['object_aliases'][0]['evidence'][0]['quote'] = source['text']
        files = m.bind(answer, sources)
        self.assertFalse(files['scope-aliases.private.json']['same_scope_semantics_verified'])
        self.assertFalse(files['scope-aliases.private.json']['behavioral_fidelity_verified'])

    def test_observed_bad_parent_projection_preserves_every_non_object_field_without_rewriting_evidence(self):
        spec = importlib.util.spec_from_file_location('scope_alias_diagnostic_test', ROOT / 'benchmarks/scope-alias-encoding-v1/diagnostic.py')
        diagnostic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(diagnostic)
        path = diagnostic.replay.DEFAULT
        original = path.read_bytes()
        result = diagnostic.build(json.loads(original))
        self.assertEqual((result['original_characters'], result['projected_characters']), (768, 793))
        self.assertTrue(result['all_four_old_names_literal_in_public'])
        self.assertTrue(result['non_object_ledger_fields_unchanged'])
        self.assertTrue(result['nodes_unchanged'])
        self.assertTrue(result['unknowns_unchanged'])
        self.assertFalse(result['automatic_generation_validated'])
        self.assertFalse(result['reader_recovery_measured'])
        self.assertEqual(result['new_model_calls'], 0)
        self.assertEqual(path.read_bytes(), original)

    def test_diagnostic_cli_runs_outside_checkout_without_pythonpath(self):
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, '-B', str(ROOT / 'benchmarks/scope-alias-encoding-v1/diagnostic.py')],
                                  cwd=tmp, env=env, text=True, capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result['new_model_calls'], 0)
        self.assertEqual(result['projected_characters'], 793)
        self.assertFalse(result['reader_recovery_measured'])


if __name__ == '__main__':
    unittest.main()
