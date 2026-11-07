"""Selectable alias encoder, legacy packets and one-call privacy guards; no services."""
import contextlib
import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load('alias_trial_test', ROOT / 'scripts/try_memory.py')
fixture = load('alias_trial_source_fixture', ROOT / 'tests/test_scope_alias_encoder.py')


class TryMemoryAliasTests(unittest.TestCase):
    def backend(self, answer, code=0):
        lines = [dict(type='item.completed', item=dict(type='agent_message', text=json.dumps(answer, ensure_ascii=False))),
                 dict(type='turn.completed', usage=dict(input_tokens=7, output_tokens=3))]
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(m.generation.shutil, 'which', return_value='/mock/codex'))
        stack.enter_context(patch.object(m.generation.subprocess, 'check_output', return_value='offline CLI fixture'))
        child = stack.enter_context(patch.object(m.generation, 'run_bounded', return_value=
                                                subprocess.CompletedProcess([], code, '\n'.join(json.dumps(x) for x in lines), 'PRIVATE_STDERR')))
        return stack, child

    def test_encoder_selection_keeps_legacy_packet_and_binds_alias_packet_to_its_own_compilers(self):
        sources, _ = fixture.example()
        original = m.request(sources)
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            m.prepare(sources, 1536, root / 'legacy')
            m.prepare(sources, 1536, root / 'alias', encoder_id='scope-alias')
            legacy = m.prepared(root / 'legacy')[2]
            alias = m.prepared(root / 'alias')[2]
            self.assertEqual(legacy['protocol'], m.PROTOCOL)
            self.assertNotIn('encoder_id', legacy)
            self.assertEqual(m.request(sources), original)
            self.assertEqual(alias['protocol'], m.ALIAS_PROTOCOL)
            self.assertEqual(alias['encoder_id'], 'scope-alias')
            self.assertEqual(set(alias['compiler_sha256']) - set(legacy['compiler_sha256']), {
                'benchmarks/source-accounted-encoding-v1/candidate.py', 'benchmarks/scope-alias-encoding-v1/candidate.py'})
            request = m.prepared(root / 'alias')[1]
            body = json.loads(request['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], sources)
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            backend.assert_not_called()

    def test_alias_import_preserves_names_private_permissions_and_existing_harness_dry_run(self):
        sources, answer = fixture.example()
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            m.prepare(sources, 1536, root / 'prepared', encoder_id='scope-alias')
            result = m.import_answer(root / 'prepared', answer, root / 'candidate')
            self.assertEqual(result['encoder_id'], 'scope-alias')
            self.assertEqual(result['status'], 'candidate_unvalidated')
            self.assertFalse(result['behavioral_fidelity_verified'])
            prompt = (root / 'candidate/prompt.md').read_text()
            self.assertTrue(all(name in prompt for name in ('石头', '纸笺', '羽毛', '风筝')))
            for path in list((root / 'prepared').rglob('*')) + list((root / 'candidate').rglob('*')):
                self.assertEqual(path.stat().st_mode & 0o077, 0)
            project = root / 'project';project.mkdir()
            proc = subprocess.run([sys.executable, '-B', '-m', 'runaway', 'attach',
                                   str(root / 'candidate/portable.json'), '--project', str(project),
                                   '--target', 'codex,claude,opencode,antigravity,deepseek', '--dry-run'],
                                  cwd=ROOT, text=True, capture_output=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(list(project.iterdir()), [])
            backend.assert_not_called()

    def test_protocol_encoder_and_compiler_tampering_reject_before_candidate_or_backend(self):
        sources, answer = fixture.example()
        for fault in ('missing_encoder', 'wrong_encoder', 'unknown_encoder', 'protocol', 'compiler', 'type'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
                root = Path(tmp);m.prepare(sources, 1536, root / 'prepared', encoder_id='scope-alias')
                file = root / 'prepared/manifest.private.json';manifest = m.read_json(file)
                if fault == 'missing_encoder': del manifest['encoder_id']
                elif fault == 'wrong_encoder': manifest['encoder_id'] = 'coverage'
                elif fault == 'unknown_encoder': manifest['encoder_id'] = '../foreign'
                elif fault == 'protocol': manifest['protocol'] = m.PROTOCOL
                elif fault == 'compiler': del manifest['compiler_sha256']['benchmarks/scope-alias-encoding-v1/candidate.py']
                else: manifest = []
                file.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError): m.import_answer(root / 'prepared', answer, root / 'candidate')
                self.assertFalse((root / 'candidate').exists())
                backend.assert_not_called()

    def test_explicit_alias_generate_sends_exact_selected_request_in_one_simulated_child(self):
        sources, answer = fixture.example()
        expected = m.request(sources, 1536, 'scope-alias')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'trial';stack, child = self.backend(answer)
            with stack: result = m.generate(sources, 1536, 'explicit-model', root, encoder_id='scope-alias')
            child.assert_called_once()
            argv, prompt, timeout = child.call_args.args
            self.assertEqual(prompt, expected['prompt'])
            self.assertEqual(m.read_json(root / 'request.private.json')['schema'], expected['schema'])
            self.assertEqual((timeout, result['backend_calls_attempted'], result['local_cli_children']), (180, 1, 1))
            self.assertEqual(result['encoder_id'], 'scope-alias')
            self.assertFalse(result['automatic_retry'])
            self.assertTrue((root / 'backend-call-intent.private.json').exists())

    def test_invalid_alias_or_transport_records_one_attempt_without_fallback_or_retry(self):
        sources, original = fixture.example()
        for fault in ('relation', 'transport'):
            answer = copy.deepcopy(original)
            if fault == 'relation': answer['object_aliases'][0]['evidence'][0]['quote'] = 'PRIVATE_FORGED'
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'trial';stack, child = self.backend(answer, 1 if fault == 'transport' else 0)
                with stack, self.assertRaises(m.TrialFailure) as error:
                    m.generate(sources, 1536, 'explicit-model', root, encoder_id='scope-alias')
                child.assert_called_once()
                self.assertEqual(error.exception.summary['backend_calls_attempted'], 1)
                self.assertFalse(error.exception.summary['candidate_created'])
                self.assertNotIn('PRIVATE_', json.dumps(error.exception.summary))
                with patch.object(m.generation, 'codex_generate') as backend, self.assertRaises(FileExistsError):
                    m.generate(sources, 1536, 'explicit-model', root, encoder_id='scope-alias')
                backend.assert_not_called()

    def test_alias_cli_preparation_and_import_work_outside_checkout_without_pythonpath(self):
        sources, answer = fixture.example();env = dict(os.environ);env.pop('PYTHONPATH', None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);(root / 'source.json').write_text(json.dumps(sources));(root / 'answer.json').write_text(json.dumps(answer))
            for args in (['prepare', '--input', str(root / 'source.json'), '--encoder', 'scope-alias', '--out', str(root / 'prepared')],
                         ['import', '--prepared', str(root / 'prepared'), '--answer', str(root / 'answer.json'), '--out', str(root / 'candidate')]):
                proc = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/try_memory.py'), *args],
                                      cwd=root, env=env, text=True, capture_output=True, timeout=30)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)['backend_calls_attempted'], 0)

    def test_every_new_measured_alias_parent_uses_the_same_user_request_and_public_compilation(self):
        file = ROOT / 'benchmarks/scope-alias-comparison-v1/measured.synthetic.json'
        before = file.read_bytes();data = json.loads(before)
        records = [r for r in data['records'] if r['kind'] == 'extract' and r['method'] == 'scope-alias-encoding-v1' and r['artifact']]
        self.assertTrue(records)
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            root = Path(tmp)
            for record in records:
                sources = data['prepared_files']['sources.json'][record['profile']]
                expected = dict(record['request']);expected.pop('model')
                self.assertEqual(m.request(sources, record['budget'], 'scope-alias'), expected)
                folder = root / str(record['slot']);m.prepare(sources, record['budget'], folder, encoder_id='scope-alias')
                m.import_answer(folder, m.parse_answer(record['raw']), folder / 'candidate')
                self.assertEqual((folder / 'candidate/prompt.md').read_text(), record['artifact']['prompt'])
            backend.assert_not_called()
        self.assertEqual(file.read_bytes(), before)

    def test_unknown_encoder_rejects_before_output_or_backend(self):
        sources, _ = fixture.example()
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.generation, 'codex_generate') as backend:
            out = Path(tmp) / 'out'
            with self.assertRaises(ValueError): m.generate(sources, 1536, 'model', out, encoder_id='foreign')
            self.assertFalse(out.exists());backend.assert_not_called()


if __name__ == '__main__':
    unittest.main()
