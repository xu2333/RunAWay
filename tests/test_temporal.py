import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runaway import temporal as t
from runaway.cli import main
from runaway.portable import validate_expression
from runaway.adapters import attach


def fixture():
    lines = [
        '产品验证：一开始我选快试，证据强度3。',
        '产品验证：后来明确改为先设计，强度2；替代此前常规偏好。',
        '产品验证：若方向未验证，先快试。',
        '产品验证：若方向未验证且改动不可撤销，必须先设计。',
        '撤销第四条硬约束。',
        '撤销第五条撤销。',
        '产品验证：又观察到一次快试，强度1。',
        '文件标记我选圆点。',
        '清除文件标记偏好。',
        '撤销上一条清除。',
        '我今天带了一把蓝伞🐈。',
    ]
    sources = {'schema_version': 1, 'sources': [{'id': 'story', 'episode_id': 'development', 'role': 'user', 'text': '\n'.join(lines)}]}
    spans = t.spans(sources)
    def event(i, kind, domain='', action='', strength=0, when=(), target=''):
        return {'id': 'e' + str(i), 'kind': kind, 'domain': domain, 'action': action,
                'strength': strength, 'when_all': [{'predicate': p, 'equals': v} for p, v in when],
                'target': target, 'span_ids': [spans[i - 1]['id']]}
    answer = {'scope': '完全合成的开发记录，仅这些取舍。', 'events': [
        event(1, 'regular', '产品验证', '快试', 3),
        event(2, 'replace', '产品验证', '先设计', 2),
        event(3, 'exception', '产品验证', '快试', when=[('方向未验证', True)]),
        event(4, 'constraint', '产品验证', '先设计', when=[('方向未验证', True), ('改动不可撤销', True)]),
        event(5, 'retract', target='e4'), event(6, 'retract', target='e5'),
        event(7, 'regular', '产品验证', '快试', 1),
        event(8, 'regular', '文件标记', '圆点'), event(9, 'clear', '文件标记'), event(10, 'retract', target='e9')],
        'unmodeled': [{'span_id': spans[-1]['id'], 'reason': '雨伞事实没有建立选择偏好。'}]}
    return sources, answer


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.sources, self.answer = fixture()
        self.artifact = t.bind(self.answer, self.sources)

    def test_retraction_of_retraction_restores_constraint_all_four_conditions(self):
        for a, b, expected in [(False, False, '先设计'), (True, False, '快试'),
                               (False, True, '先设计'), (True, True, '先设计')]:
            got = t.resolve(self.artifact, '产品验证', {'方向未验证': a, '改动不可撤销': b})
            self.assertEqual(got['action'], expected)
        context = {'方向未验证': True, '改动不可撤销': True}
        self.assertEqual(t.resolve(self.artifact, '产品验证', context, 'e4')['action'], '先设计')
        self.assertEqual(t.resolve(self.artifact, '产品验证', context, 'e5')['action'], '快试')
        self.assertEqual(t.resolve(self.artifact, '产品验证', context, 'e6')['action'], '先设计')

    def test_clear_retraction_replacement_and_strength_are_distinct_operations(self):
        self.assertEqual(t.resolve(self.artifact, '文件标记', {}, 'e9')['status'], 'unobserved')
        self.assertEqual(t.resolve(self.artifact, '文件标记', {})['action'], '圆点')
        self.assertEqual(t.resolve(self.artifact, '产品验证', {}, 'e1')['action'], '快试')
        # Replacement resets prior stronger evidence, later weaker observation cannot undo it.
        context = {'方向未验证': False, '改动不可撤销': False}
        self.assertEqual(t.resolve(self.artifact, '产品验证', context)['action'], '先设计')
        answer = copy.deepcopy(self.answer)
        answer['events'][4]['target'] = 'e2'
        answer['events'][5]['target'] = 'e4'  # two active retractions, no restoration
        changed = t.bind(answer, self.sources)
        self.assertEqual(t.resolve(changed, '产品验证', {'方向未验证': False})['action'], '快试')

    def test_unknown_context_never_assumed_false_and_equal_evidence_stays_conflict(self):
        self.assertEqual(t.resolve(self.artifact, '产品验证', {'方向未验证': True})['status'], 'context_unknown')
        self.assertEqual(t.resolve(self.artifact, '没有记录', {})['status'], 'unobserved')
        answer = copy.deepcopy(self.answer)
        answer['events'][6]['strength'] = 2
        artifact = t.bind(answer, self.sources)
        self.assertEqual(t.resolve(artifact, '产品验证', {'方向未验证': False})['status'], 'conflict')

    def test_independent_retractions_need_each_disabler_retracted(self):
        sources = {'schema_version': 1, 'sources': [{'id': 's', 'episode_id': 'e', 'role': 'user',
            'text': '操作：不可撤销时先确认。\n撤销a。\n再次撤销a。\n撤销b。\n撤销c。'}]}
        spans = t.spans(sources)
        events = [{'id': 'a', 'kind': 'constraint', 'domain': '操作', 'action': '先确认', 'strength': 0,
                   'when_all': [{'predicate': '不可撤销', 'equals': True}], 'target': '', 'span_ids': [spans[0]['id']]}]
        for i, (eid, target) in enumerate((('b', 'a'), ('c', 'a'), ('d', 'b'), ('e', 'c')), 1):
            events.append({'id': eid, 'kind': 'retract', 'domain': '', 'action': '', 'strength': 0,
                           'when_all': [], 'target': target, 'span_ids': [spans[i]['id']]})
        artifact = t.bind({'scope': '合成开发。', 'events': events, 'unmodeled': []}, sources)
        self.assertEqual(t.resolve(artifact, '操作', {'不可撤销': True}, 'd')['status'], 'unobserved')
        self.assertEqual(t.resolve(artifact, '操作', {'不可撤销': True})['action'], '先确认')

    def test_graph_and_source_coverage_fail_closed(self):
        for change in ('forward', 'missing_span', 'foreign_span', 'fake_quote', 'same_condition_twice'):
            answer = copy.deepcopy(self.answer)
            if change == 'forward':
                answer['events'][4]['target'] = 'e6'
            elif change == 'missing_span':
                answer['unmodeled'] = []
            elif change == 'foreign_span':
                answer['events'][0]['span_ids'] = ['made-up']
            elif change == 'fake_quote':
                answer['events'][0]['quote'] = 'model-rewritten quote'
            else:
                answer['events'][3]['when_all'].append({'predicate': '方向未验证', 'equals': False})
            with self.assertRaises(ValueError, msg=change):
                t.bind(answer, self.sources)
        changed = copy.deepcopy(self.artifact)
        changed['source_spans'][0]['text'] += 'edited'
        with self.assertRaises(ValueError):
            t.validate(changed)

    def test_exact_codepoint_spans_and_no_assistant_support(self):
        source = self.sources['sources'][0]['text']
        for span in self.artifact['source_spans']:
            self.assertEqual(source[span['start']:span['end']], span['text'])
        self.assertIn('🐈', self.artifact['source_spans'][-1]['text'])
        altered = copy.deepcopy(self.sources)
        altered['sources'][0]['role'] = 'assistant'
        with self.assertRaises(ValueError):
            t.bind(self.answer, altered)

    def test_full_budget_preflight_blocks_instead_of_truncating_or_selecting(self):
        complete = t.render(self.artifact, 10000)
        self.assertIn('「方向未验证」成立且「改动不可撤销」成立', complete['text'])
        self.assertIn('硬约束', complete['text'])
        self.assertFalse(complete['source_semantic_fidelity_verified'])
        self.assertFalse(complete['historical_reconstruction_supported'])
        blocked = t.render(self.artifact, complete['required_characters'] - 1)
        self.assertEqual(blocked['status'], 'budget_blocked')
        self.assertIsNone(blocked['text'])
        self.assertEqual(blocked['included_domains'], ['产品验证', '文件标记'])
        partial = t.render(self.artifact, 10000, ['文件标记'])
        self.assertEqual(partial['omitted_domains'], ['产品验证'])
        self.assertNotIn('【产品验证】', partial['text'])
        with self.assertRaises(ValueError):
            t.render(self.artifact, 10000, budget_tokens=128)
        # This injectable byte counter exercises rejection, not real token quality.
        counted = t.render(self.artifact, 10000, count=lambda text: len(text.encode()), budget_tokens=1)
        self.assertIsNone(counted['text'])

    def test_manual_cli_exports_attachable_prompt_or_preserves_blocked_profile_without_service(self):
        with tempfile.TemporaryDirectory() as temporary, patch('runaway.cli.codex_generate', side_effect=AssertionError('No new service calls')):
            base = Path(temporary)
            source, answer = base / 'sources.json', base / 'answer.json'
            source.write_text(json.dumps(self.sources, ensure_ascii=False))
            answer.write_text(json.dumps(self.answer, ensure_ascii=False))
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                main(['timeline', 'prepare', '--input', str(source)])
            self.assertIn('retraction OF a retraction', captured.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                main(['timeline', 'import', '--input', str(source), '--answer', str(answer), '--out', str(base / 'ok')])
            expression = json.loads((base / 'ok/portable.json').read_text())
            validate_expression(expression)
            self.assertIn('硬约束', expression['text'])
            project = base / 'harness-project'; project.mkdir()
            attach(expression, project, ['codex', 'claude', 'opencode'], False)
            for name in ('AGENTS.md', '.claude/rules/runaway.md'):
                text = (project / name).read_text()
                self.assertIn(expression['text'], text)
                self.assertNotIn('撤销第五条撤销', text)
            with contextlib.redirect_stdout(io.StringIO()):
                main(['timeline', 'export', str(base / 'ok/timeline.private.json'), '--out', str(base / 'blocked'), '--budget-chars', '100'])
            self.assertTrue((base / 'blocked/timeline.private.json').exists())
            self.assertFalse((base / 'blocked/portable.json').exists())


if __name__ == '__main__':
    unittest.main()
