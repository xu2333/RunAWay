"""User-facing trial wiring with archived responses and a simulated CLI;no model calls."""
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('try_memory_test', ROOT / 'scripts/try_memory.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TryMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = m.read_json(ROOT / 'benchmarks/single-pass-repeat-v1/measured.synthetic.json', 4000000)
        cls.rec = next(r for r in cls.data['records'] if r['kind'] == 'extract')
        cls.sources = cls.data['prepared_files']['sources.json']['pavo']

    def fake_cli(self, raw=None, code=0):
        raw = self.rec['raw'] if raw is None else raw
        lines = [dict(type='item.completed', item=dict(type='agent_message', text=raw)),
                 dict(type='turn.completed', usage=dict(input_tokens=7, output_tokens=3))]
        return subprocess.CompletedProcess([], code, '\n'.join(json.dumps(x) for x in lines), 'PRIVATE_BACKEND_SECRET')

    def backend(self, result=None, side_effect=None):
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(m.generation.shutil, 'which', return_value='/mock/codex'))
        stack.enter_context(patch.object(m.generation.subprocess, 'check_output', return_value='offline CLI fixture'))
        fake = stack.enter_context(patch.object(m.generation, 'run_bounded',
                                              return_value=result or self.fake_cli(), side_effect=side_effect))
        return stack, fake

    def test_all_eight_archived_cards_round_trip_without_changing_the_request(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            records = [r for r in self.data['records'] if r['kind'] == 'extract']
            self.assertEqual(len(records), 8)
            for i, rec in enumerate(records):
                sources = self.data['prepared_files']['sources.json'][rec['profile']]
                request = dict(rec['request'])
                request.pop('model')
                self.assertEqual(m.request(sources), request)
                prepared = root / str(i) / 'request'
                m.prepare(sources, 1536, prepared)
                out = root / str(i) / 'candidate'
                result = m.import_answer(prepared, m.parse_answer(rec['raw']), out)
                self.assertEqual((out / 'prompt.md').read_text(), rec['artifact']['prompt'])
                self.assertEqual(result['status'], 'candidate_unvalidated')
                self.assertFalse(result['behavioral_fidelity_verified'])
                self.assertFalse(result['semantic_support_verified'])
            backend.assert_not_called()

    def test_one_explicit_call_sends_exact_prompt_schema_and_private_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'trial'
            def inspect_call(argv, prompt, timeout):
                self.assertEqual(m.read_json(argv[argv.index('--output-schema') + 1]), self.rec['request']['schema'])
                setting = next(x for x in argv if x.startswith('model_instructions_file='))
                file = json.loads(setting.split('=', 1)[1])
                self.assertEqual(Path(file).read_text(), self.rec['request']['system'])
                return self.fake_cli()
            stack, backend = self.backend(side_effect=inspect_call)
            with stack:
                result = m.generate(self.sources, 1536, 'explicit-model', root)
            backend.assert_called_once()
            argv, prompt, timeout = backend.call_args.args
            self.assertEqual(prompt, self.rec['request']['prompt'])
            self.assertEqual(timeout, 180)
            self.assertEqual(argv[argv.index('-m') + 1], 'explicit-model')
            self.assertEqual((root / 'candidate/prompt.md').read_text(), self.rec['artifact']['prompt'])
            self.assertEqual((result['backend_calls_attempted'], result['local_cli_children']), (1, 1))
            self.assertFalse(result['automatic_retry'])
            self.assertTrue((root / 'backend-call-intent.private.json').exists())
            for file in [root] + list(root.rglob('*')):
                self.assertEqual(file.stat().st_mode & 0o077, 0)

    def test_existing_output_invalid_model_and_oversize_sources_make_no_call(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            (root / 'existing').mkdir()
            (root / 'existing/marker').write_text('keep')
            with self.assertRaises(FileExistsError):
                m.generate(self.sources, 1536, 'model', root / 'existing')
            self.assertEqual((root / 'existing/marker').read_text(), 'keep')
            with self.assertRaises(ValueError):
                m.generate(self.sources, 1536, ' ', root / 'blank')
            bad = copy.deepcopy(self.sources)
            bad['sources'][0]['text'] = 'x' * 64001
            with self.assertRaises(ValueError):
                m.generate(bad, 1536, 'model', root / 'too-large')
            self.assertFalse((root / 'too-large').exists())
            backend.assert_not_called()

    def test_failed_transport_or_invalid_answer_preserves_attempt_without_retry(self):
        for raw, code in ((self.rec['raw'], 1), ('{"PRIVATE_ANSWER_SECRET":}', 0)):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'trial'
                stack, backend = self.backend(self.fake_cli(raw, code))
                with stack, self.assertRaises(m.TrialFailure) as err:
                    m.generate(self.sources, 1536, 'model', root)
                backend.assert_called_once()
                self.assertEqual(err.exception.summary['backend_calls_attempted'], 1)
                self.assertFalse(err.exception.summary['candidate_created'])
                self.assertNotIn('PRIVATE_', json.dumps(err.exception.summary))
                self.assertTrue((root / 'backend-call-intent.private.json').exists())
                with patch.object(m.generation, 'codex_generate') as another:
                    with self.assertRaises(FileExistsError):
                        m.generate(self.sources, 1536, 'model', root)
                    another.assert_not_called()

    def test_changed_packet_quote_and_compiler_are_rejected_before_import(self):
        for fault in ('source', 'request', 'manual', 'compiler', 'quote'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                prepared = root / 'prepared'
                m.prepare(self.sources, 1536, prepared)
                answer = m.parse_answer(self.rec['raw'])
                if fault == 'quote':
                    answer['nodes'][0]['decisions'][0]['quote'] = 'ABSENT_QUOTE'
                elif fault == 'manual':
                    file = prepared / 'request.private.md'
                    file.write_text(file.read_text() + 'changed')
                else:
                    name = {'source': 'sources.private.json', 'request': 'request.private.json',
                            'compiler': 'manifest.private.json'}[fault]
                    file = prepared / name
                    data = m.read_json(file)
                    if fault == 'source': data['sources'][0]['text'] += 'changed'
                    elif fault == 'request': data['prompt'] += 'changed'
                    else: data['compiler_sha256'] = {}
                    file.write_text(json.dumps(data, ensure_ascii=False))
                with self.assertRaises(ValueError):
                    m.import_answer(prepared, answer, root / 'candidate')
                self.assertFalse((root / 'candidate').exists())
        self.assertNotIn('runaway/taste_executor.py', m.compiler_hashes())
        self.assertNotIn('runaway/cli.py', m.compiler_hashes())

    def test_timeout_records_attempt_and_unknown_usage_without_echoing_private_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / 'source.json'
            file.write_text(json.dumps(self.sources, ensure_ascii=False))
            stack, backend = self.backend(side_effect=m.generation.GenerationTimeout({'usage': None}))
            stdout, stderr = io.StringIO(), io.StringIO()
            with stack, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = m.main(['generate', '--input', str(file), '--backend', 'codex',
                               '--model', 'model', '--out', str(root / 'trial')])
            self.assertEqual(code, 2)
            backend.assert_called_once()
            result = json.loads(stderr.getvalue())
            self.assertEqual((result['backend_calls_attempted'], result['local_cli_children']), (1, 1))
            self.assertFalse(result['candidate_created'])
            self.assertIsNone(m.read_json(root / 'trial/provenance.private.json')['usage'])
            self.assertEqual(stdout.getvalue(), '')

    def test_additional_backend_child_is_blocked_even_if_backend_requests_it(self):
        def malicious(prompt, model, **kwargs):
            m.generation.run_bounded(['/mock/codex'], prompt, 180)
            m.generation.run_bounded(['/mock/codex'], prompt, 180)
            raise AssertionError('Second child must not execute')
        with tempfile.TemporaryDirectory() as tmp:
            stack, backend = self.backend()
            with stack, patch.object(m.generation, 'codex_generate', side_effect=malicious):
                with self.assertRaises(m.TrialFailure) as err:
                    m.generate(self.sources, 1536, 'model', Path(tmp) / 'trial')
            backend.assert_called_once()
            self.assertEqual(err.exception.summary['local_cli_children'], 1)

    def test_demo_is_archived_and_existing_harness_dry_run_stays_local(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            result = m.demo(root / 'demo')
            backend.assert_not_called()
            self.assertTrue(result['synthetic_archive_replay'])
            self.assertFalse(result['new_inference'])
            self.assertEqual(result['characters'], 439)
            project = root / 'project'
            project.mkdir()
            p = subprocess.run([sys.executable, '-B', '-m', 'runaway', 'attach',
                                str(root / 'demo/candidate/portable.json'), '--project', str(project),
                                '--target', 'codex,claude,opencode,antigravity,deepseek', '--dry-run'],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(list(project.iterdir()), [])

    def test_symlink_packet_and_ambiguous_source_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            m.prepare(self.sources, 1536, root / 'prepared')
            file = root / 'prepared/sources.private.json'
            target = root / 'source.json'
            file.rename(target)
            file.symlink_to(target)
            with self.assertRaises(ValueError): m.prepared(root / 'prepared')
            target.write_text('{"schema_version":1,"sources":[{"id":"s","episode_id":"e",'
                              '"role":"assistant","role":"user","text":"PRIVATE_SECRET"}]}')
            with self.assertRaises(ValueError): m.sources_file(target)
            target.write_text('[' * 2000 + '0' + ']' * 2000)
            with self.assertRaises(ValueError): m.sources_file(target)

    def test_offline_cli_and_error_reporting_never_claim_a_paid_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.json'
            source.write_text(json.dumps(self.sources, ensure_ascii=False))
            answer = root / 'answer.json'
            answer.write_text(self.rec['raw'])
            stdout = io.StringIO()
            with patch.object(m.generation, 'codex_generate') as backend, contextlib.redirect_stdout(stdout):
                self.assertEqual(m.main(['prepare', '--input', str(source), '--out', str(root / 'prepared')]), 0)
                self.assertEqual(m.main(['import', '--prepared', str(root / 'prepared'),
                                         '--answer', str(answer), '--out', str(root / 'candidate')]), 0)
                backend.assert_not_called()
            self.assertEqual((root / 'candidate/prompt.md').read_text(), self.rec['artifact']['prompt'])
            source.write_text('{"PRIVATE_INPUT_SECRET":}')
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(m.main(['prepare', '--input', str(source), '--out', str(root / 'bad')]), 2)
            self.assertNotIn('PRIVATE_INPUT_SECRET', stderr.getvalue())
            self.assertEqual(json.loads(stderr.getvalue())['backend_calls_attempted'], 0)

    def test_storage_failure_after_call_preserves_usage_and_attempt_reporting(self):
        for failed_file in ('answer.private.txt', 'result.private.json'):
            with self.subTest(failed_file=failed_file), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'trial'
                writer = m.write_new
                def fail_write(path, value):
                    if Path(path).name == failed_file:
                        raise OSError('PRIVATE_STORAGE_ERROR')
                    return writer(path, value)
                stack, backend = self.backend()
                with stack, patch.object(m, 'write_new', side_effect=fail_write):
                    with self.assertRaises(m.TrialFailure) as err:
                        m.generate(self.sources, 1536, 'model', root)
                backend.assert_called_once()
                self.assertEqual(err.exception.summary['backend_calls_attempted'], 1)
                self.assertEqual(m.read_json(root / 'provenance.private.json')['usage'][0]['input_tokens'], 7)
                self.assertNotIn('PRIVATE_STORAGE_ERROR', json.dumps(err.exception.summary))

    def test_missing_cli_keeps_an_offline_request_without_claiming_a_backend_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'trial'
            with patch.object(m.generation.shutil, 'which', return_value=None), patch.object(m.generation, 'codex_generate') as backend:
                with self.assertRaises(m.TrialFailure) as err:
                    m.generate(self.sources, 1536, 'model', root)
            backend.assert_not_called()
            self.assertEqual(err.exception.summary['status'], 'backend_unavailable')
            self.assertEqual(err.exception.summary['backend_calls_attempted'], 0)
            self.assertTrue((root / 'request.private.md').exists())
            self.assertFalse((root / 'backend-call-intent.private.json').exists())


if __name__ == '__main__':
    unittest.main()
