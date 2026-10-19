"""Deterministic backend fixtures and intercepted subprocess only; no services."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from runaway import shared_schema_executor as s, generation, taste_executor
from runaway.card import canonical, digest
from runaway.execution_ledger import collect, summarize


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.base = Path(self.temp.name)
        self.plan = self.base / 'plan'; self.out = self.base / 'out'; self.seen = []
        self.runtime = dict(python_executable='/fixture/python', python_version='fixture', external_model_calls=0,
                            tools={k: dict(executable='/fixture/' + k, version='v25.6.0' if k == 'node' else 'fixture-codex') for k in ('node', 'codex')})
        self.p = s.prepare(self.plan, self.runtime)
        _, self.source, self.jobs = s.preflight(self.plan)
        self.sequence = [(stage, j) for stage in s.STAGES for j in self.jobs[stage]]

    def tearDown(self):
        self.temp.cleanup()

    def provenance(self):
        return dict(backend='codex', model_requested=s.MODEL, resolved_model=None, cli_version='fixture-codex',
                    usage=[dict(input_tokens=100, cached_input_tokens=20, output_tokens=30)])

    def fake(self, prompt, model, **kwargs):
        stage, job = self.sequence[len(self.seen)]; self.seen.append(job['request_id'])
        self.assertEqual(prompt, job['request']['prompt']); self.assertEqual(model, s.MODEL)
        self.assertEqual(kwargs, dict(timeout=180, schema=job['request']['schema'], system=job['request']['system']))
        payload = json.loads(prompt.split('\nINPUT_JSON:\n', 1)[1])
        self.assertEqual(set(payload), {'memory', 'queries'})
        self.assertEqual(job['request_id'], digest(canonical(job['request'])))
        split = 'holdout' if stage == 'holdout_jobs' else 'development'
        condition = 'wrong_person' if stage == 'wrong_person_jobs' else 'intact_dual_program'
        return canonical(dict(answers=self.source['records'][split][condition][job['person_id']])), self.provenance()

    def run_fake(self, backend=None):
        with patch.object(generation, 'codex_generate', side_effect=AssertionError('No real service')):
            return s.execute(self.plan, self.out, backend=backend or self.fake)

    def rehash(self, p):
        p['binding_id'] = digest(canonical({k: v for k, v in p.items() if k not in ('id', 'binding_id', 'acceptance')}))
        p['id'] = digest(canonical({k: v for k, v in p.items() if k != 'id'}))
        s.atomic(self.plan / 'proposal.json', p)

    def test_exact16_success_gates_families_ids_and_usage(self):
        report = self.run_fake()
        self.assertEqual(report['status'], 'complete'); self.assertEqual(len(self.seen), 16)
        self.assertEqual(report['stage_attempts'], s.CAPS)
        self.assertTrue(all(g['passed'] for g in report['gates'].values()))
        self.assertEqual(report['scores']['development_jobs']['strict_choice']['joint']['correct'], 96)
        self.assertEqual(report['scores']['holdout_jobs']['possible_outcomes']['joint']['correct'], 376)
        self.assertEqual(len(report['consumed_holdout_families']), 4)
        self.assertEqual(report['calls']['known_usage']['total_tokens'], 16 * 130)
        self.assertEqual(report['calls']['known_usage']['cached_input_tokens'], 16 * 20)
        self.assertEqual(report['external_model_calls'], 0)
        records = collect(self.out)
        self.assertEqual(len({r['execution_id'] for r in records}), 16)
        self.assertEqual({r['request_id'] for r in records}, set(self.seen))
        self.assertTrue((self.out / 'holdout-entry.json').exists())

    def test_development_failure_stops_at6_and_keeps_all_denominators(self):
        def bad(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            if len(self.seen) == 1:
                v = json.loads(raw); row = v['answers'][min(v['answers'])]
                row['strict_answer'] = 'B' if row['strict_answer'] != 'B' else 'A'; raw = canonical(v)
            return raw, provenance
        report = self.run_fake(bad)
        self.assertEqual(len(self.seen), 6); self.assertEqual(report['status'], 'stopped')
        self.assertFalse(report['gates']['development_jobs']['passed'])
        self.assertEqual(report['scores']['wrong_person_jobs']['strict_choice']['joint']['missing'], 40)
        self.assertEqual(report['scores']['holdout_jobs']['strict_choice']['joint']['missing'], 376)
        self.assertFalse((self.out / 'holdout-entry.json').exists())

    def test_wrong_person_intact_answers_fail_before_holdout(self):
        def intact(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            if len(self.seen) > 6:
                job = self.sequence[len(self.seen) - 1][1]
                raw = canonical(dict(answers=self.source['records']['development']['intact_dual_program'][job['person_id']]))
            return raw, provenance
        report = self.run_fake(intact)
        self.assertEqual(len(self.seen), 8)
        self.assertFalse(report['gates']['wrong_person_jobs']['passed'])
        self.assertEqual(report['scores']['holdout_jobs']['possible_outcomes']['joint']['missing'], 376)

    def test_valid_but_wrong_holdout_reported_without_extra_calls(self):
        def wrong(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            if len(self.seen) == 9:
                v = json.loads(raw); v['answers'][min(v['answers'])]['strict_answer'] = 'A'; raw = canonical(v)
            return raw, provenance
        report = self.run_fake(wrong)
        self.assertEqual(report['status'], 'complete'); self.assertEqual(len(self.seen), 16)
        self.assertEqual(report['scores']['holdout_jobs']['strict_choice']['joint']['planned'], 376)
        self.assertLess(report['scores']['holdout_jobs']['strict_choice']['joint']['correct'], 376)

    def test_all_predetermined_wire_corruptions_stop_without_repair(self):
        from runaway.shared_schema import corruptions
        job = self.jobs['development_jobs'][0]
        valid = dict(answers=self.source['records']['development']['intact_dual_program'][job['person_id']])
        mutations = corruptions(valid)
        rejected = [(name, wire) for name, wire in mutations if not s.shared.wire_result(wire, job['request']['schema'])['accepted']]
        for name, wire in rejected:
            with self.subTest(name=name):
                # Separate immutable proposal identity per mock experiment.
                plan = self.base / ('plan-' + name); s.prepare(plan, self.runtime)
                out = self.base / ('out-' + name); invoked = []
                def backend(*args, **kwargs):
                    invoked.append(True); return wire, self.provenance()
                report = s.execute(plan, out, backend=backend)
                self.assertEqual(len(invoked), 1); self.assertEqual(report['status'], 'stopped')
                self.assertEqual(report['calls']['known_usage']['total_tokens'], 130)
                self.assertEqual(report['scores']['development_jobs']['strict_choice']['joint']['missing'], 96)
                self.assertEqual((out / 'calls' / (job['request_id'] + '.raw.bin')).read_bytes(), wire if isinstance(wire, bytes) else wire.encode())

    def test_semantic_invalid_outcomes_rejected_even_when_schema_accepts(self):
        def malformed(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            value = json.loads(raw); value['answers'][min(value['answers'])]['possible_outcomes'] = [dict(status='conflict', action='invented')]
            self.assertTrue(s.shared.accepts(value, self.sequence[0][1]['request']['schema']))
            return canonical(value), provenance
        report = self.run_fake(malformed)
        self.assertEqual(len(self.seen), 1); self.assertEqual(report['status'], 'stopped')

    def test_unknown_usage_stops_and_is_not_zero(self):
        def unknown(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs); provenance['usage'] = None
            return raw, provenance
        report = self.run_fake(unknown)
        self.assertEqual(len(self.seen), 1)
        self.assertEqual(report['calls']['executions_missing_usage'], 1)
        self.assertEqual(report['calls']['known_usage']['total_tokens'], 0)
        self.assertIn('not zero', report['calls']['interpretation'])

    def test_identity_mismatch_and_malformed_usage_stop(self):
        cases = [('model_requested', 'other'), ('cli_version', 'drift'), ('backend', 'other'),
                 ('usage', [dict(input_tokens=-1, output_tokens=2)]), ('usage', [dict(input_tokens=True, output_tokens=2)]),
                 ('usage', [dict(input_tokens=1, cached_input_tokens=2, output_tokens=2)]),
                 ('usage', [dict(input_tokens=1, output_tokens=2, reasoning_output_tokens=3)])]
        for index, (key, value) in enumerate(cases):
            with self.subTest(key=key, value=value):
                plan = self.base / str(index); s.prepare(plan, self.runtime); invoked = []
                def backend(*args, **kwargs):
                    invoked.append(True); provenance = self.provenance(); provenance[key] = value
                    job = self.sequence[0][1]
                    return canonical(dict(answers=self.source['records']['development']['intact_dual_program'][job['person_id']])), provenance
                r = s.execute(plan, self.base / ('bad-' + str(index)), backend=backend)
                self.assertEqual(len(invoked), 1); self.assertEqual(r['status'], 'stopped')
                if key == 'usage':
                    self.assertEqual(r['calls']['executions_missing_usage'], 1)

    def test_transport_ref_rejection_and_timeout_stop_preserve_usage(self):
        for index, error in enumerate((ValueError('backend does not support refs'), generation.GenerationTimeout(self.provenance()))):
            with self.subTest(error=type(error).__name__):
                plan = self.base / str(index); s.prepare(plan, self.runtime); invoked = []
                def backend(*args, **kwargs): invoked.append(True); raise error
                r = s.execute(plan, self.base / ('error-' + str(index)), backend=backend)
                self.assertEqual(len(invoked), 1); self.assertEqual(r['status'], 'stopped')
                self.assertEqual(r['calls']['executions_missing_usage'], 1 if index == 0 else 0)
                self.assertEqual(r['scores']['holdout_jobs']['strict_choice']['joint']['missing'], 376)

    def test_no_retry_new_output_copy_or_existing_output(self):
        self.run_fake()
        with self.assertRaises(FileExistsError): s.execute(self.plan, self.base / 'other', backend=self.fake)
        with self.assertRaises(ValueError): s.execute(self.plan, self.out, backend=self.fake)
        copied = self.base / 'copy'; shutil.copytree(self.plan, copied)
        with self.assertRaisesRegex(ValueError, 'Copied'): s.preflight(copied)
        self.assertEqual(len(self.seen), 16)

    def test_crash_leaves_single_use_intent_and_unresolved_attempt(self):
        def crash(*args, **kwargs): raise KeyboardInterrupt()
        original = generation.run_bounded
        with self.assertRaises(KeyboardInterrupt): self.run_fake(crash)
        self.assertIs(generation.run_bounded, original)
        ledger = summarize(collect(self.out))
        self.assertEqual(ledger['outcomes']['unresolved_invocation_intent'], 1)
        self.assertEqual(ledger['executions_missing_usage'], 1)
        with self.assertRaises(FileExistsError): s.execute(self.plan, self.base / 'again', backend=self.fake)

    def test_request_source_snapshot_scope_acceptance_tampering(self):
        for name in s.INPUTS + ('frozen-source/runaway/shared_schema_executor.py',):
            with self.subTest(name=name):
                path = self.plan / name; original = path.read_bytes(); path.write_bytes(original + b' ')
                with self.assertRaises(ValueError): s.preflight(self.plan)
                path.write_bytes(original)
        evidence = dict(all_checks_passed=True, external_model_calls=0, binding_id=self.p['binding_id'], source_hashes=self.p['source_hashes'])
        s.bind_acceptance(self.plan, evidence)
        path = self.plan / 'executor-acceptance.json'; path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Acceptance'): s.preflight(self.plan)

    def test_rehashed_policy_old_ids_and_budget_edits_rejected(self):
        for field, value in [('calls_max', 17), ('timeout_seconds', 181), ('model', 'other'),
                             ('forbidden_request_ids', []), ('stage_order', list(reversed(s.STAGES)))]:
            with self.subTest(field=field):
                p = copy.deepcopy(self.p); p[field] = value; self.rehash(p)
                with self.assertRaises(ValueError): s.preflight(self.plan)
        s.atomic(self.plan / 'proposal.json', self.p)
        self.assertTrue(set(j['source_request_id'] for _, j in self.sequence) <= set(self.p['forbidden_request_ids']))
        self.assertFalse(set(j['request_id'] for _, j in self.sequence) & set(self.p['forbidden_request_ids']))

    def test_runtime_and_direct_approval_gate_before_any_intent(self):
        with patch.object(s, 'runtime_metadata', return_value=self.runtime), patch.object(generation, 'codex_generate') as service:
            with self.assertRaises(ValueError): s.execute(self.plan, self.out)
            e = dict(all_checks_passed=True, external_model_calls=0, binding_id=self.p['binding_id'], source_hashes=self.p['source_hashes'])
            final = s.bind_acceptance(self.plan, e)
            with self.assertRaisesRegex(ValueError, 'human approval'): s.execute(self.plan, self.out)
            with self.assertRaises(ValueError): s.execute(self.plan, self.out, approval=dict(status='approved', proposal_id=self.p['id'], calls_max=16, human_source={'fixture': True}))
            with patch.object(s, 'runtime_metadata', return_value=dict(self.runtime, python_version='drift')):
                with self.assertRaisesRegex(ValueError, 'runtime drifted'): s.preflight(self.plan, True, True)
            service.assert_not_called()
        self.assertFalse((self.plan / 'execution-intent.json').exists())
        self.assertNotEqual(final['id'], self.p['id'])

    def test_midcall_freeze_and_checkpoint_corruption_stop(self):
        def mutate(*args, **kwargs):
            raw, provenance = self.fake(*args, **kwargs)
            (self.plan / 'requests.synthetic.json').write_text('{}')
            return raw, provenance
        r = self.run_fake(mutate)
        self.assertEqual(len(self.seen), 1); self.assertEqual(r['status'], 'stopped')
        self.assertEqual(r['calls']['known_usage']['total_tokens'], 130)

    def test_intercepted_cli_exact_isolation_and_success_usage(self):
        def intercepted(args, prompt, timeout):
            raw, provenance = self.fake(prompt, s.MODEL, timeout=timeout,
                         schema=s.read(Path(args[args.index('--output-schema') + 1])),
                         system=Path(args[args.index('-C') + 1], 'system.txt').read_text())
            events = [dict(type='item.completed', item=dict(type='agent_message', text=raw)),
                      dict(type='turn.completed', usage=provenance['usage'][0])]
            return subprocess.CompletedProcess(args, 0, '\n'.join(json.dumps(e) for e in events), '')
        with patch.object(taste_executor, 'ORIGINAL_RUN_BOUNDED', side_effect=intercepted), \
             patch.object(generation.shutil, 'which', return_value='/fixture/codex'), \
             patch.object(generation.subprocess, 'check_output', return_value='fixture-codex'):
            r = s.execute(self.plan, self.out, backend=generation.codex_generate)
        self.assertEqual(r['status'], 'complete'); self.assertEqual(len(self.seen), 16)
        self.assertEqual(r['calls']['known_usage']['total_tokens'], 2080)

    def test_intercepted_cli_arg_system_schema_and_prompt_drift_blocked(self):
        stage, job = self.sequence[0]
        out = self.base / 'observer'; out.mkdir(); calls = s.Calls(out, self.p, self.fake, lambda: None)
        calls.current_job = job; calls.cli = '/fixture/codex'
        directory = self.base / 'empty'; directory.mkdir()
        (directory / 'system.txt').write_text(job['request']['system']); s.atomic(directory / 'schema.json', job['request']['schema'])
        with patch.object(taste_executor, 'ORIGINAL_RUN_BOUNDED') as transport:
            for args, prompt, timeout in [(['/fixture/codex','-C',str(directory)], job['request']['prompt'], 180),
                                          (['/fixture/codex','-C',str(directory)], 'changed', 180),
                                          (['/fixture/codex','-C',str(directory)], job['request']['prompt'], 181)]:
                with self.assertRaises(ValueError): calls.observed_runner(args, prompt, timeout)
            (directory / 'system.txt').write_text('changed')
            with self.assertRaises(ValueError): calls.observed_runner(['-C',str(directory)], job['request']['prompt'], 180)
            transport.assert_not_called()

    def test_direct_duplicate_out_of_order_and_exhausted_calls_block(self):
        out = self.base / 'calls-only'; out.mkdir(); calls = s.Calls(out, self.p, self.fake, lambda: None)
        calls.jobs = self.jobs; calls.source = self.source
        with self.assertRaises(ValueError): calls.call('holdout_jobs', self.jobs['holdout_jobs'][0])
        calls.call(*self.sequence[0])
        with self.assertRaises(ValueError): calls.call(*self.sequence[0])
        calls.counts['development_jobs'] = 6
        with self.assertRaises(ValueError): calls.call(*self.sequence[1])
        self.assertEqual(len(self.seen), 1)

    def test_ambiguous_or_corrupt_checkpoint_prevents_next_invocation(self):
        out = self.base / 'checkpoint'; out.mkdir(); calls = s.Calls(out, self.p, self.fake, lambda: None)
        calls.jobs = self.jobs; calls.source = self.source
        calls.call(*self.sequence[0])
        key = self.sequence[0][1]['request_id']; response = out / 'calls' / (key + '.response.json')
        data = response.read_text(); response.write_text('{}')
        with self.assertRaises(ValueError): calls.call(*self.sequence[1])
        response.write_text(data)
        # A crash leaves an intent with no terminal output; it cannot be skipped.
        response.unlink()
        with self.assertRaises(ValueError): calls.call(*self.sequence[1])
        self.assertEqual(len(self.seen), 1)

    def test_raw_missing_and_invalid_diagnostics_keep_unconditional_plan(self):
        for index, kind in enumerate(('missing_query', 'illegal_strict_answer')):
            plan = self.base / str(index); s.prepare(plan, self.runtime)
            stage, job = self.sequence[0]
            valid = dict(answers=self.source['records']['development']['intact_dual_program'][job['person_id']])
            wire = dict(s.shared.corruptions(valid))[kind]
            report = s.execute(plan, self.base / ('diag-' + str(index)), backend=lambda *a, **k: (wire, self.provenance()))
            diagnostic = report['rejected_output_diagnostics'][0]['diagnostic']
            self.assertEqual(diagnostic['status'], 'scored_raw_not_accepted')
            self.assertEqual(diagnostic['fields']['strict_choice']['planned'], 96)
            self.assertEqual(diagnostic['fields']['strict_choice']['invalid_answers'], index)
            self.assertGreater(diagnostic['fields']['strict_choice']['missing'], 0)

    def test_real_transport_local_rejection_records_zero_backend_entries(self):
        with patch.object(taste_executor, 'ORIGINAL_RUN_BOUNDED') as transport, \
             patch.object(generation.shutil, 'which', return_value='/fixture/codex'), \
             patch.object(generation.subprocess, 'check_output', return_value='fixture-codex'), \
             patch.object(s.Calls, 'verify_transport', side_effect=ValueError('isolation drift')):
            report = s.execute(self.plan, self.out, backend=generation.codex_generate)
            transport.assert_not_called()
        self.assertEqual(report['calls']['locally_blocked_before_backend'], 1)
        self.assertEqual(report['calls']['executions_missing_usage'], 0)
        self.assertEqual(report['status'], 'stopped')

    def test_rejected_raw_hash_and_non_wire_type_fail_closed(self):
        report = self.run_fake(lambda *a, **k: ('{}', self.provenance()))
        self.assertEqual(report['status'], 'stopped')
        raw = next((self.out / 'calls').glob('*.raw.bin'))
        raw.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'raw bytes changed'):
            s.records_checked(self.out)
        plan = self.base / 'non-wire'; s.prepare(plan, self.runtime)
        r = s.execute(plan, self.base / 'non-wire-out', backend=lambda *a, **k: (42, self.provenance()))
        self.assertEqual(r['status'], 'stopped')
        self.assertEqual(r['calls']['outcomes']['failed'], 1)
        self.assertEqual(r['calls']['known_usage']['total_tokens'], 130)


if __name__ == '__main__':
    unittest.main()
