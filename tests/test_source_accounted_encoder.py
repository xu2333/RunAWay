"""Observation ownership and compiler conservation, not model fidelity evidence."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('accounted_encoder_test', ROOT / 'benchmarks/source-accounted-encoding-v1/candidate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def example():
    sources = {'schema_version': 1, 'sources': [
        dict(id='s1', episode_id='notes', role='user', text='外发且可恢复时，我选自动整理。'),
        dict(id='s2', episode_id='notes', role='user', text='本机且不可恢复时，我选手动整理。'),
        dict(id='s3', episode_id='signup', role='user', text='报名外发且可恢复时，我选手动分组。'),
        dict(id='s4', episode_id='scope', role='user', text='其它未记录组合和是否已执行保持未知。'),
        dict(id='a1', episode_id='notes', role='assistant', text='我建议全部自动。')]}
    answer = {'version': m.VERSION, 'name': '三格小笺', 'tagline': '逐项记住再收好。',
              'objects': ['笔记整理', '报名分组'], 'nodes': [],
              'unknowns': ['未记录组合和是否已执行未知。'], 'derived_node_ids': [],
              'source_accounting': {s['id']: dict(kind='no_choice', node_ids=[], reason='明确未知边界。')
                                    for s in sources['sources'] if s['role'] == 'user'}}
    for i, (action, condition) in enumerate((('自动整理', '外发且可恢复'), ('手动整理', '本机且不可恢复'), ('手动分组', '报名外发且可恢复'))):
        source = sources['sources'][i]
        anchor = dict(source_id=source['id'], quote=source['text'])
        node = dict(id='n' + str(i), kind='base', target_kind='choice', object_index=int(i == 2),
                    question='选择做法', requires=[dict(text=condition, evidence=[anchor])],
                    action=action, priority=0, decisions=[anchor], contexts=[anchor], order_split=None)
        answer['nodes'].append(node)
        answer['source_accounting'][source['id']] = dict(kind='direct_choice', node_ids=[node['id']], reason='来源直接选择了这个完整动作。')
    return sources, answer


class SourceAccountedEncoderTests(unittest.TestCase):
    def test_source_only_request_requires_all_user_messages_without_other_speakers(self):
        sources, _ = example()
        req = m.make_request(sources)
        props = req['schema']['properties']['source_accounting']
        self.assertEqual(set(props['required']), {'s1', 's2', 's3', 's4'})
        self.assertFalse(props['additionalProperties'])
        body = json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
        self.assertEqual(body['sources'], sources)
        self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
        self.assertEqual(body['budget_characters'], 1536)

    def test_normalization_keeps_every_original_compiler_output_and_guard(self):
        sources, answer = example()
        normalized, owners = m.normalize(answer, sources)
        self.assertEqual(owners, {'n0': ['s1'], 'n1': ['s2'], 'n2': ['s3']})
        expected = m.base.bind(normalized, sources, 1536)
        actual = m.bind(answer, sources, 1536)
        self.assertEqual({k: v for k, v in actual.items() if k != 'source-accounting.private.json'}, expected)
        self.assertEqual(normalized['nodes'], answer['nodes'])
        self.assertFalse(actual['source-accounting.private.json']['source_completeness_verified'])
        self.assertFalse(actual['source-accounting.private.json']['behavioral_fidelity_verified'])

    def test_opposite_observations_cannot_be_merged_as_common_decision_support(self):
        sources, answer = example()
        answer['nodes'][0]['decisions'].append(copy.deepcopy(answer['nodes'][1]['decisions'][0]))
        with self.assertRaisesRegex(ValueError, 'unaccounted decision'):
            m.bind(answer, sources)
        answer['source_accounting']['s2']['node_ids'].append('n0')
        with self.assertRaisesRegex(ValueError, 'no literal witness'):
            m.bind(answer, sources)

    def test_missing_disposition_or_orphan_duplicate_and_overlapping_nodes_reject(self):
        sources, original = example()
        for fault in ('missing_source', 'orphan', 'double_owner', 'duplicate_derived', 'overlap', 'empty_direct', 'no_choice_nodes'):
            answer = copy.deepcopy(original)
            if fault == 'missing_source': del answer['source_accounting']['s4']
            elif fault == 'orphan': answer['source_accounting']['s1'] = dict(kind='no_choice', node_ids=[], reason='背景')
            elif fault == 'double_owner': answer['source_accounting']['s2']['node_ids'].append('n0')
            elif fault == 'duplicate_derived': answer['derived_node_ids'] = ['n0', 'n0']
            elif fault == 'overlap': answer['derived_node_ids'] = ['n0']
            elif fault == 'empty_direct': answer['source_accounting']['s1']['node_ids'] = []
            else: answer['source_accounting']['s1']['kind'] = 'no_choice'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.bind(answer, sources)

    def test_wrong_literal_action_or_forged_quote_does_not_compile(self):
        sources, original = example()
        for fault in ('action', 'quote', 'budget'):
            answer = copy.deepcopy(original)
            if fault == 'action': answer['nodes'][0]['action'] = '手动整理'
            if fault == 'quote': answer['nodes'][0]['decisions'][0]['quote'] = '伪造自动整理'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.bind(answer, sources, 30 if fault == 'budget' else 1536)

    def test_contextual_confirmation_keeps_its_own_decision_and_original_context(self):
        sources, answer = example()
        sources['sources'][1]['text'] = '同一个完整条件，我确认按前一个决定执行。'
        answer['nodes'].pop(1)
        answer['nodes'][0]['decisions'].append(dict(source_id='s2', quote=sources['sources'][1]['text']))
        answer['source_accounting']['s2']['kind'] = 'contextual_choice'
        answer['source_accounting']['s2']['node_ids'] = ['n0']
        result = m.bind(answer, sources)
        self.assertEqual(result['source-accounting.private.json']['observed_node_supporters']['n0'], ['s1', 's2'])
        self.assertFalse(result['source-accounting.private.json']['source_semantic_classification_verified'])

    def test_historical_bad_graphs_fail_observation_ownership_without_rewriting_them(self):
        for archive, slot, person in (('remaining-source-repeat-v1', 49, 'f7s'), ('ambiguous-source-repeat-v1', 19, 'c2v')):
            path = ROOT / 'benchmarks' / archive / 'measured.synthetic.json'
            before = path.read_bytes()
            data = json.loads(before)
            record = next(r for r in data['records'] if r['slot'] == slot)
            answer = json.loads(record['raw'])
            sources = data['sources'][person]
            # Illustrative adapter only: no semantic labels/reference enter a request.
            # Assign each existing node to its first decision source,without repair.
            answer.update(version=m.VERSION, derived_node_ids=[], source_accounting={
                s['id']: dict(kind='no_choice', node_ids=[], reason='仅作结构损坏检查。')
                for s in sources['sources'] if s['role'] == 'user'})
            for node in answer['nodes']:
                entry = answer['source_accounting'][node['decisions'][0]['source_id']]
                entry['kind'] = 'direct_choice'
                entry['node_ids'].append(node['id'])
            with self.assertRaisesRegex(ValueError, 'unaccounted decision'):
                m.bind(answer, sources)
            self.assertEqual(path.read_bytes(), before)

    def test_false_semantic_classification_is_not_a_completeness_certificate(self):
        sources, answer = example()
        # A model could still misclassify all real decisions as background. Do
        # not claim that enumerating IDs alone solves semantic omissions.
        answer['nodes'] = []
        for entry in answer['source_accounting'].values():
            entry.update(kind='no_choice', node_ids=[], reason='错误的背景分类反例。')
        files = m.bind(answer, sources)
        self.assertFalse(files['source-accounting.private.json']['source_completeness_verified'])
        self.assertFalse(files['source-accounting.private.json']['source_semantic_classification_verified'])


if __name__ == '__main__':
    unittest.main()
