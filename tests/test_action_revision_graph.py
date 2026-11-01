"""Typed-edge calibration, not NLP classification or empirical model fidelity."""
import copy
import importlib.util
import itertools
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('action_graph_tests', ROOT / 'benchmarks/action-revision-graph-v1/candidate.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def fixture():
    texts = {'s1': '通常花园参观须已获准入园且天晴；我选草地。上次已按草地走过。',
        's2': '同样情境只改路线，我现在选细石路；入园许可和天晴前提不变。',
        's3': '独立预约回廊专场，已获准入园且确认预约即可走回廊，不要求天晴，优先于通常路线。',
        's4': '助手猜测无需许可也可进园。'}
    sources = {'schema_version': 1, 'sources': [{'id': k, 'episode_id': 'toy', 'role': 'assistant' if k == 's4' else 'user', 'text': v} for k, v in texts.items()]}
    def a(s): return {'source_id': s, 'quote': texts[s]}
    def cond(text, sid): return {'text': text, 'evidence': [a(sid)]}
    permit, sun, event = cond('已获准入园', 's1'), cond('天晴', 's1'), cond('已确认回廊专场预约', 's3')
    def base(n, q, reqs, action, sid, kind='choice', priority=0):
        return {'id': n, 'kind': 'base', 'target_kind': kind, 'object_index': 0, 'question': q,
            'requires': copy.deepcopy(reqs), 'action': action, 'priority': priority, 'decisions': [a(sid)], 'contexts': [a(sid)]}
    graph = {'version': c.VERSION, 'name': '继承小园丁', 'tagline': '改路线，也记得门票。', 'objects': ['花园路线'],
        'nodes': [base('old', '路线选择', [permit, sun], '草地', 's1'),
                  base('past', '既往实施状态', [], '上次已走草地', 's1', 'status'),
                  {'id': 'new', 'kind': 'action_revision', 'parent_id': 'old', 'action': '细石路',
                   'decisions': [a('s2')], 'contexts': [a('s2')], 'relation_evidence': [a('s2')]},
                  base('exception', '路线选择', [permit, event], '回廊', 's3', priority=1)],
        'unknowns': ['缺必要条件或未知分支时未知。']}
    return sources, graph


def choose(rows, facts):
    rows = [r for r in rows if r['question'] == '路线选择' and all(facts[x['text']] for x in r['requires'])]
    if not rows: return 'U'
    level = max(r['priority'] for r in rows)
    actions = {r['action'] for r in rows if r['priority'] == level}
    return next(iter(actions)) if len(actions) == 1 else 'U'


class ActionGraphTests(unittest.TestCase):
    def test_action_revision_inherits_all_parent_conditions_and_keeps_same_message_past_fact(self):
        sources, graph = fixture(); before = copy.deepcopy(graph)
        ledger, trace = c.compile_graph(graph, sources)
        revised = next(r for r in ledger['rows'] if r['action'] == '细石路')
        self.assertEqual(revised['requires'], graph['nodes'][0]['requires'])
        self.assertEqual(revised['object'], '花园路线')
        self.assertEqual(revised['question'], '路线选择')
        self.assertEqual(trace['inactive_node_ids'], ['old'])
        self.assertIn('past', trace['active_node_ids'])
        self.assertTrue(any(r['action'] == '上次已走草地' for r in ledger['rows']))
        self.assertEqual(graph, before)

    def test_exhaustive_permission_weather_exception_worlds_keep_both_sides_of_scope(self):
        sources, graph = fixture(); ledger, _ = c.compile_graph(graph, sources)
        for permit, sun, event in itertools.product((False, True), repeat=3):
            facts = {'已获准入园': permit, '天晴': sun, '已确认回廊专场预约': event}
            expected = 'U' if not permit else '回廊' if event else '细石路' if sun else 'U'
            self.assertEqual(choose(ledger['rows'], facts), expected)
        self.assertEqual(choose(ledger['rows'], {'已获准入园': True, '天晴': False, '已确认回廊专场预约': True}), '回廊')

    def test_missing_permission_does_not_become_known_and_erasure_would_change_result(self):
        sources, graph = fixture(); ledger, _ = c.compile_graph(graph, sources)
        answers = {choose(ledger['rows'], {'已获准入园': p, '天晴': True, '已确认回廊专场预约': False}) for p in (False, True)}
        self.assertEqual(answers, {'U', '细石路'})
        damaged = copy.deepcopy(ledger['rows'])
        for row in damaged:
            if row['action'] == '细石路': row['requires'] = [x for x in row['requires'] if x['text'] != '已获准入园']
        answers = {choose(damaged, {'已获准入园': p, '天晴': True, '已确认回廊专场预约': False}) for p in (False, True)}
        self.assertEqual(answers, {'细石路'})

    def test_bad_parent_status_duplicate_timing_and_nonuser_relation_are_rejected(self):
        for fault in ('parent', 'status', 'duplicate', 'timing', 'role', 'override'):
            sources, graph = fixture(); rev = graph['nodes'][2]
            if fault == 'parent': rev['parent_id'] = 'future'
            elif fault == 'status': rev['parent_id'] = 'past'
            elif fault == 'duplicate': rev['id'] = 'old'
            elif fault == 'timing': rev['decisions'] = copy.deepcopy(graph['nodes'][0]['decisions'])
            elif fault == 'role': rev['relation_evidence'] = [{'source_id': 's4', 'quote': sources['sources'][3]['text']}]
            else: rev['requires'] = []
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                c.compile_graph(graph, sources)

    def test_source_only_request_budget_and_no_feedback_or_targets(self):
        import json
        sources, _ = fixture(); req = c.make_request(sources)
        body = json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
        self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
        self.assertEqual(body['sources'], sources)
        self.assertEqual(body['budget_characters'], 1536)

    def test_dense_binding_keeps_graph_trace_unverified_and_hard_limits(self):
        sources, graph = fixture(); files = c.bind(graph, sources)
        self.assertLessEqual(len(files['prompt.md']), 1536)
        self.assertFalse(files['action-revision-graph.private.json']['semantic_edge_classification_verified'])
        self.assertTrue(files['summary.private.json']['semantic_projection_roundtrip_exact'])
        with self.assertRaises(ValueError): c.bind(graph, sources, 1)


if __name__ == '__main__': unittest.main()
