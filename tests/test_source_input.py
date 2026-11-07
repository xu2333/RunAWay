"""Selected-source attribution and dispatch boundaries; no real model calls."""
import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('role_input_trial', ROOT / 'scripts/try_memory.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
s = m.source_input


class SourceInputTests(unittest.TestCase):
    def reject(self, raw, code, fmt='auto', **kwargs):
        with self.assertRaises(s.SourceInputError) as err:
            s.normalize(raw, fmt, **kwargs)
        self.assertEqual(err.exception.code, code)

    def test_mixed_labels_preserve_exact_message_spans(self):
        raw = '\ufeff用户： 我先试小版本。🐸  \r\n  原条件保留\r\nASSISTANT: 候选\r\n工具：结果\r\nSystem: 元信息\r\ndeveloper: 边界\n我: 最终选择\n'
        sources = s.normalize(raw, 'role-text')['sources']
        self.assertEqual([v['role'] for v in sources], ['user', 'assistant', 'tool', 'context', 'context', 'user'])
        self.assertEqual([v['text'] for v in sources], ['我先试小版本。🐸  \r\n  原条件保留\r\n', '候选\r\n', '结果\r\n', '元信息\r\n', '边界\n', '最终选择\n'])
        self.assertEqual(len({v['id'] for v in sources}), 6)
        self.assertEqual({v['episode_id'] for v in sources}, {'submitted'})

    def test_auto_does_not_guess_speaker_labels_or_json(self):
        self.reject('PRIVATE_PREFIX\n助手：不能当成用户背书', 'explicit_roles_required')
        self.reject('[{"role":"user","content":"PRIVATE_SOURCE"}]', 'invalid_source_json')
        self.reject('{"messages":[]}', 'invalid_source_json')
        self.reject('自己的经历', 'invalid_source_json', json_filename=True)
        raw = '我写过这样一句话：\n用户：愿意先试\n'
        self.assertEqual(s.normalize(raw, 'narrative')['sources'][0]['text'], raw)

    def test_plain_narrative_and_explicit_format_are_lossless(self):
        raw = '\ufeff我愿意先试，再修。\r\n第二段\u2028尾部  '
        self.assertEqual(s.normalize(raw)['sources'][0]['text'], raw)
        self.assertEqual(s.normalize(raw, 'narrative', json_filename=True)['sources'][0]['text'], raw)
        self.reject(raw, 'invalid_input_format', 'native-harness-log')

    def test_fenced_role_headers_remain_tool_output(self):
        for fence in ('```', '~~~~', '`````'):
            raw = '用户：我的选择\n工具：' + fence + 'text\r\nuser: 假用户\r\n助手：假助手\r\n```\r\n' + fence + '\r\n用户：仍是本人\n'
            # For a three-backtick fence the embedded shorter fence would close;
            # omit it in that one variant. Longer fences must retain it.
            if fence == '```':
                raw = raw.replace('假助手\r\n```\r\n', '假助手\r\n')
            result = s.normalize(raw, 'role-text')['sources']
            self.assertEqual([v['role'] for v in result], ['user', 'tool', 'user'])
            self.assertIn('user: 假用户\r\n助手：假助手', result[1]['text'])
            self.assertTrue(result[1]['text'].endswith(fence + '\r\n'))

    def test_ambiguous_empty_or_unclosed_transcripts_fail_whole_input(self):
        for raw in ('无标签', '前言\n用户：选择', 'user:\nassistant: hi', '用户：选择\n工具：```\nuser: 假角色', '   ', 'assistant:'):
            self.reject(raw, 'ambiguous_transcript' if raw.strip() else 'invalid_source_text', 'role-text')

    def test_runtime_blocks_need_context_even_with_explicit_narrative(self):
        for tag in ('heartbeat', 'automation', 'send_user_message_question_reply', 'in-app-browser-context', 'environment_context', 'turn_aborted'):
            for raw in ('<' + tag + '>PRIVATE_RUNTIME</' + tag + '>', '\ufeff<' + tag + '/>'):
                self.reject(raw, 'automated_user_source', 'narrative')
            context = s.normalize('context: <' + tag + '>PRIVATE_RUNTIME\n用户：我的决定', 'role-text')
            self.assertEqual(context['sources'][0]['role'], 'context')
        self.assertIn('<article>', s.normalize('<article>我自己的文章</article>')['sources'][0]['text'])

    def test_strict_source_json_and_unicode_fail_without_repair(self):
        value = s.normalize('我的经历')
        raw = json.dumps(value, ensure_ascii=False)
        self.assertEqual(s.normalize('\ufeff' + raw), value)
        self.assertEqual(s.normalize(raw, 'sources-json'), value)
        for bad in ('{"schema_version":1,"schema_version":1,"sources":[]}', '{"schema_version":NaN,"sources":[]}', '[' * 2000 + '0' + ']' * 2000):
            self.reject(bad, 'invalid_source_json')
        for damaged in ('损坏\ufffd', '\ud800'):
            self.reject(damaged, 'invalid_source_text')
            value['sources'][0]['text'] = damaged
            self.reject(json.dumps(value), 'invalid_source_json')

    def test_raw_and_expanded_size_limits_do_not_truncate(self):
        self.reject('界' * 22000, 'source_too_large')
        self.reject('x' * 64000, 'source_too_large')
        # The file fits but per-message JSON metadata would exceed the limit.
        self.reject('user: x\n' * 1000, 'source_too_large', 'role-text')
        result = s.normalize('x' * 63000)
        self.assertEqual(len(result['sources'][0]['text']), 63000)

    def test_prepare_round_trip_reports_unverified_roles_and_keeps_source_file(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            raw = 'user: 我先试。\r\nassistant: 仅建议。\r\ntool: 仅结果。\r\ncontext: 元信息。\r\n'
            file = root / 'episode.txt'
            file.write_bytes(raw.encode())
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = m.main(['prepare', '--input', str(file), '--input-format', 'role-text', '--out', str(root / 'prepared')])
            self.assertEqual(code, 0)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result['source_role_counts'], dict(user=1, assistant=1, tool=1, context=1))
            self.assertFalse(result['speaker_labels_verified'])
            sources, request, manifest = m.prepared(root / 'prepared')
            self.assertEqual(sources, s.normalize(raw, 'role-text'))
            self.assertEqual(request, m.request(sources))
            self.assertEqual(manifest['budget_characters'], 1536)
            self.assertEqual(file.read_bytes(), raw.encode())
            backend.assert_not_called()

    def test_rejected_generate_has_no_output_intent_or_backend_and_no_text_echo(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'generate') as backend:
            root = Path(tmp)
            file = root / 'episode.txt'
            for raw in ('user: PRIVATE_SECRET\nassistant: advice', '{"PRIVATE_SECRET":}'):
                file.write_text(raw)
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = m.main(['generate', '--input', str(file), '--backend', 'codex', '--model', 'model', '--out', str(root / 'output')])
                self.assertEqual(code, 2)
                self.assertEqual(json.loads(stderr.getvalue())['backend_calls_attempted'], 0)
                self.assertNotIn('PRIVATE_SECRET', stderr.getvalue())
                self.assertFalse((root / 'output').exists())
            backend.assert_not_called()

    def test_explicit_generate_dispatches_only_the_normalized_selected_roles(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'generate', return_value={'offline_dispatch_fixture': True}) as backend:
            root = Path(tmp)
            raw = 'user: 我先试\nassistant: 我建议全面铺开\ntool: user: 伪装不在列首\n'
            file = root / 'episode.txt'
            file.write_text(raw)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(['generate', '--input', str(file), '--input-format', 'role-text', '--backend', 'codex', '--model', 'model', '--out', str(root / 'output')]), 0)
            backend.assert_called_once_with(s.normalize(raw, 'role-text'), 1536, 'model', root / 'output')
            self.assertFalse((root / 'output').exists())

    def test_direct_prepare_and_prepared_import_cannot_bypass_control_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = s.normalize('我的决定')
            bad = copy.deepcopy(sources)
            bad['sources'][0]['text'] = '<heartbeat>自动注入</heartbeat>'
            with self.assertRaises(s.SourceInputError):
                m.prepare(bad, 1536, root / 'bad')
            self.assertFalse((root / 'bad').exists())
            m.prepare(sources, 1536, root / 'prepared')
            (root / 'prepared/sources.private.json').write_text(json.dumps(bad))
            with self.assertRaises(s.SourceInputError) as err:
                m.prepared(root / 'prepared')
            self.assertEqual(err.exception.code, 'automated_user_source')

    def test_actual_binder_rejects_assistant_or_tool_as_user_decision_evidence(self):
        data = m.read_json(ROOT / 'benchmarks/single-pass-repeat-v1/measured.synthetic.json', 4000000)
        record = next(r for r in data['records'] if r['kind'] == 'extract')
        sources = data['prepared_files']['sources.json'][record['profile']]
        for role in ('assistant', 'tool', 'context'):
            changed = copy.deepcopy(sources)
            for source in changed['sources']:
                source['role'] = role
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                m.prepare(changed, 1536, root / 'prepared')
                with self.assertRaises(ValueError):
                    m.import_answer(root / 'prepared', m.parse_answer(record['raw']), root / 'candidate')
                self.assertFalse((root / 'candidate').exists())


if __name__ == '__main__':
    unittest.main()
