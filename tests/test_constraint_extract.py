"""Product integration on development-only toy inputs. No real model calls."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from runaway import constraint_extract as ce
from runaway import constraint_memory as cm
from runaway.card import canonical, digest
from runaway.portable import validate_expression, render_expression

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    read = lambda name: json.loads((ROOT / 'examples' / name).read_text(encoding='utf-8'))
    return read('constraints-answer.synthetic.json'), read('constraints-sources.synthetic.json')


class ConstraintExtractionTests(unittest.TestCase):
    def setUp(self):
        self.answer, self.sources = fixture()

    def test_request_only_selected_sources_budget_and_deep_copied_schema(self):
        request = ce.make_request(self.sources, 512)
        body = json.loads(request['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
        self.assertEqual(body, {'sources': self.sources, 'budget_characters': 512})
        self.assertEqual(set(request), {'system', 'schema', 'prompt'})
        request['schema']['required'].clear()
        self.assertIn('family', ce.make_request(self.sources)['schema']['required'])

    def test_finite_observations_remain_unknown_elsewhere_and_fit_whole_budget(self):
        files = ce.bind(self.answer, self.sources, 512)
        contract = files['contract.private.json']
        self.assertIsNone(contract['family'])
        self.assertEqual(files['compilation.private.json']['mode'], 'observations_only')
        for presence, expected in [('无人', '熄灯'), ('有人', 'U')]:
            result = cm.decide(contract, self.sources, scope='lamp',
                               values={'presence': presence}, offered=['熄灯', '亮灯'])
            self.assertEqual(result['choice'], expected)
        public = files['prompt.md']
        self.assertEqual(public, cm.render(contract, self.sources, 512))
        self.assertEqual(len(public), files['summary.private.json']['characters'])
        self.assertIn('没有观察的完整组合未知', public)
        self.assertLessEqual(len(public), 512)

    def test_exact_quotes_do_not_claim_semantic_or_personal_validation(self):
        files = ce.bind(self.answer, self.sources)
        for value in (files['profile.private.json']['validation'], files['summary.private.json']):
            self.assertFalse(value['semantic_support_verified'])
            self.assertFalse(value['behavioral_fidelity_verified'])
        self.assertEqual(files['profile.private.json']['artifact_type'], 'source_constraints_profile')
        self.assertEqual(files['summary.private.json']['status'], 'candidate_unvalidated')

    def test_private_content_bound_portable_exports_and_input_not_mutated(self):
        before = copy.deepcopy((self.answer, self.sources))
        files = ce.bind(self.answer, self.sources)
        self.assertEqual(before, (self.answer, self.sources))
        portable = validate_expression(files['portable.json'])
        self.assertEqual(render_expression(portable), files['prompt.md'])
        self.assertEqual(portable['method'], 'automatic_source_constraints_v2')
        profile = files['profile.private.json']
        self.assertEqual(profile['id'], digest(canonical({k: v for k, v in profile.items() if k != 'id'})))
        self.assertEqual(profile['source_sha256'], digest(canonical(self.sources)))
        self.assertNotIn('source_id', files['prompt.md'])
        self.assertEqual(set(portable), {'schema_version','artifact_type','status','text','profile_id','method','id'})

    def test_duplicate_feature_pairs_extra_keys_bad_types_and_bad_quotes_rejected(self):
        variants = []
        answer = copy.deepcopy(self.answer)
        answer['observations'][0]['values'] *= 2
        variants.append(answer)
        answer = copy.deepcopy(self.answer); answer['gold'] = '熄灯'; variants.append(answer)
        answer = copy.deepcopy(self.answer); answer['family'] = False; variants.append(answer)
        answer = copy.deepcopy(self.answer); answer['observations'][0]['decision']['quote'] = '不存在'; variants.append(answer)
        for answer in variants:
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                ce.bind(answer, self.sources)

    def test_strict_json_import_rejects_duplicate_keys_and_constants(self):
        for raw in ('{"family":null,"family":null}', '{"n":NaN}', '{"n":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                ce.parse_answer(raw)

    def test_budget_source_size_and_observation_requirements_fail_before_output(self):
        for budget in (True, 299, 16001):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                ce.make_request(self.sources, budget)
        sources = copy.deepcopy(self.sources)
        sources['sources'][0]['text'] += '界' * 40000
        with self.assertRaisesRegex(ValueError, '96KB'):
            ce.make_request(sources)
        self.answer['observations'] = []
        with self.assertRaises(ValueError):
            ce.bind(self.answer, self.sources)

    def test_closed_family_wire_conversion_keeps_alternatives_and_disagreement(self):
        from test_constraint_memory import fixture as greenhouse_fixture
        contract, sources = greenhouse_fixture()
        answer = copy.deepcopy(contract)
        pairs = lambda values: [{'feature': k, 'value': v} for k, v in values.items()]
        for observation in answer['observations']:
            observation['values'] = pairs(observation['values'])
        for rule in answer['family']['rules']:
            rule['any_of'] = [{'all_of': pairs(clause)} for clause in rule['any_of']]
        files = ce.bind(answer, sources, 16000)
        self.assertEqual(files['contract.private.json'], contract)
        self.assertEqual(files['compilation.private.json']['compatible_rule_ids'], ['either', 'xor'])
        self.assertIn('water if exactly one tray is dry', files['prompt.md'])
        answer['tagline'] = '保持来源条件。' * 8
        with self.assertRaisesRegex(ValueError, 'exceeds budget'):
            ce.bind(answer, sources, 300)

    def test_mock_generation_matches_import_and_persists_exact_request(self):
        calls = []
        def backend(prompt, model, **kwargs):
            calls.append((prompt, model, kwargs))
            return json.dumps(self.answer), {'backend': 'local_fixture_not_model'}
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'output'
            result = ce.generate(self.sources, out, 'fixture', 512, backend)
            self.assertEqual(len(calls), 1)
            self.assertEqual(result['model_calls'], 1)  # Mock attempt count, not a real invocation.
            request = ce.make_request(self.sources, 512)
            self.assertEqual(calls[0], (request['prompt'], 'fixture',
                                      {'system': request['system'], 'schema': request['schema']}))
            self.assertEqual(json.loads((out / 'request.private.json').read_text()), dict(request, model='fixture'))
            self.assertEqual((out / 'prompt.md').read_text(), ce.bind(self.answer, self.sources)['prompt.md'])
            if os.name == 'posix':
                self.assertEqual(out.stat().st_mode & 0o777, 0o700)
                for path in out.iterdir():
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                ce.generate(self.sources, out, 'fixture', backend=backend)
            self.assertEqual(len(calls), 1)

    def test_invalid_or_failed_generation_persists_failure_without_retry_or_card(self):
        for raw in ('{}', '{"family":null,"family":null}', None):
            calls = []
            def backend(*args, **kw):
                calls.append(True)
                if raw is None:
                    raise TimeoutError('local fixture timeout')
                return raw, {'backend': 'local_fixture_not_model'}
            with tempfile.TemporaryDirectory() as folder:
                out = Path(folder) / 'output'
                with self.assertRaises((ValueError, TimeoutError)):
                    ce.generate(self.sources, out, 'fixture', backend=backend)
                self.assertEqual(len(calls), 1)
                self.assertTrue((out / 'request.private.json').exists())
                self.assertFalse((out / 'portable.json').exists())
                failure = json.loads((out / 'failure.private.json').read_text())
                self.assertFalse(failure['automatic_retry'])

    def test_cli_zero_call_import_export_choice_attach_and_incompatible_relayout(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'card'
            run = lambda *args: subprocess.run([sys.executable, '-B', '-m', 'runaway', *map(str,args)],
                                                capture_output=True, text=True)
            base = ('distill', '--format', 'constraints-v2', '--input', ROOT/'examples/constraints-sources.synthetic.json', '--budget-chars', '512')
            prep = run(*base, '--prepare')
            self.assertEqual(prep.returncode, 0, prep.stderr)
            self.assertEqual(json.loads(prep.stdout), ce.make_request(self.sources))
            result = run(*base, '--answer', ROOT/'examples/constraints-answer.synthetic.json', '--out', out)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['model_calls'], 0)
            export = run('export', out/'portable.json')
            self.assertEqual(export.returncode, 0, export.stderr)
            self.assertEqual(export.stdout, (out/'prompt.md').read_text())
            choices = run('choices', 'prepare', '--card', out/'portable.json', '--questions', ROOT/'examples/constraints-questions.synthetic.json', '--answer-format', 'text')
            self.assertEqual(choices.returncode, 0, choices.stderr)
            reader = json.loads(choices.stdout)['prompt']
            body = json.loads(reader.split('\nREADER_INPUT_JSON:\n')[1])
            self.assertEqual((out/'prompt.md').read_text(), body['material'])
            project = Path(folder) / 'project'; project.mkdir()
            attach = run('attach', out/'portable.json', '--project', project, '--target', 'codex,claude,opencode,antigravity,deepseek')
            self.assertEqual(attach.returncode, 0, attach.stderr)
            self.assertIn((out/'prompt.md').read_text().strip(), (project/'AGENTS.md').read_text())
            doctor = run('doctor', '--project', project)
            self.assertEqual(doctor.returncode, 0, doctor.stderr)
            relayout = run('relayout', out/'profile.private.json', '--layout', 'rows', '--out', Path(folder)/'rows')
            self.assertNotEqual(relayout.returncode, 0)
            self.assertIn('source-support', relayout.stderr)

    def test_cli_rejects_mixed_modes_layout_and_duplicate_sources_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder/'sources.json'; source.write_text(json.dumps(self.sources))
            answer = ROOT/'examples/constraints-answer.synthetic.json'
            out = folder/'output'
            run = lambda *args: subprocess.run([sys.executable, '-B', '-m', 'runaway', 'distill',
                '--format', 'constraints-v2', '--input', str(source), *map(str,args)], capture_output=True,text=True)
            for flags in (('--prepare', '--backend', 'codex'), ('--prepare', '--layout', 'rows'),
                          ('--answer', answer, '--backend', 'codex', '--out', out), ('--model','fixture','--out',out)):
                result = run(*flags)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(out.exists())
            source.write_text('{"schema_version":1,"sources":[],"sources":[]}')
            result = run('--prepare')
            self.assertIn('Duplicate JSON key', result.stderr)


if __name__ == '__main__':
    unittest.main()
