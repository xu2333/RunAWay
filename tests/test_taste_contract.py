import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runaway import taste_contract as tc
from runaway import taste_audit
from runaway import taste_plan

ROOT=Path(__file__).resolve().parents[1]


class TasteContractTests(unittest.TestCase):
    def test_current_task_retains_strength_exceptions_and_restored_constraints(self):
        world=tc.build_world();person=next(p for p in world['people'] if p['split']=='eval')
        self.assertEqual(tc.policy_signature(person)[:5],('gentle','direct','auto','ask','minimal'))
        self.assertEqual(len([c for c in person['cases'] if c['public']['task']=='current_choice']),16)
        self.assertEqual(len([c for c in person['cases'] if c['public']['task']=='historical_reconstruction']),8)
        self.assertEqual(tc.canonical_choice(person,person['cases'][12]),'ask')
        for a,b in zip(person['cases'][:16:2],person['cases'][1:16:2]):
            self.assertEqual(tc.canonical_choice(person,a),tc.canonical_choice(person,b))
            if a['gold']!='U':self.assertNotEqual(a['gold'],b['gold'])
        for c in person['cases']:
            if c['public']['task']=='historical_reconstruction' and c['key']=='auto':self.assertIn('无法撤销',c['public']['question'])

    def test_corruption_still_fails_core_requirements_and_unknown_is_not_missing(self):
        world=tc.build_world();result=tc.calibrate(world)['controls']
        self.assertEqual(result['full_semantic_oracle']['current_choice']['correct'],32)
        hard=result['delete_hard']['current_choice'];self.assertEqual(hard['correct'],28)
        self.assertEqual(hard['hard_constraint_errors'],4);self.assertEqual(hard['observed_hard_violations'],4)
        self.assertEqual(result['delete_exceptions']['current_choice']['matched_distinctions']['correct'],0)
        self.assertEqual(result['ignore_revocations']['current_choice']['correct'],24)
        self.assertEqual(result['none']['current_choice']['correct'],8)
        self.assertEqual(result['always_U']['current_choice']['correct'],4)
        self.assertEqual(result['none']['current_choice']['option_order_pairs']['correct'],4)
        self.assertEqual(result['none']['current_choice']['option_order_pairs']['consistent'],16)
        missing=tc.score(world,{},'current_choice');self.assertEqual((missing['correct'],missing['missing'],missing['planned']),(0,32,32))
        self.assertEqual(tc.score(world,{},'historical_reconstruction')['planned'],16)
        self.assertEqual(tc.score(world,{},'joint')['planned'],48)

    def test_finite_answerability_proofs_are_not_model_predictions(self):
        result=tc.calibrate(tc.build_world())
        self.assertEqual(result['external_model_calls'],0)
        self.assertTrue(all(p.get('same_current_projection',True) and p.get('all_answers_equal',True) for p in result['proofs']))
        for data in result['finite_answerability'].values():
            self.assertEqual(data['compatible_histories'],64);self.assertTrue(data['not_a_parser_of_model_memory'])
            self.assertEqual(sum(q['identified_in_this_finite_family'] for q in data['queries'] if q['task']=='current_choice'),16)
            self.assertEqual(sum(q['identified_in_this_finite_family'] for q in data['queries'] if q['task']=='historical_reconstruction'),0)

    def test_contract_written_before_fixture_generation_and_jobs_exclude_gold(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'fixture';original=tc.build_world
            def build(seed,mode):
                self.assertTrue((root/'contract.json').exists())
                return original(seed,mode)
            with patch.object(tc,'build_world',build):result=tc.freeze(root)
            self.assertEqual(result['external_model_calls'],0)
            for line in (root/'reader-job-templates.jsonl').read_text().splitlines():
                job=json.loads(line);self.assertEqual(job['source_cutoff'],20)
                for query in job['queries']:
                    for key in ('key','context','gold','canonical_options','tags'):self.assertNotIn(key,query)
            spec=json.loads((root/'contract.json').read_text());self.assertEqual(spec,tc.contract())

    def test_future_cohort_changes_parameters_and_wording_not_just_ids(self):
        dev=tc.build_world();future=tc.build_world(813247,'comparison')
        combinations={(p['parameters']['feedback'],p['parameters']['layout']) for p in dev['people']}
        old_questions={c['public']['question'] for p in dev['people'] for c in p['cases'][:12]}
        for p in future['people']:
            if p['split']!='eval':continue
            self.assertNotIn((p['parameters']['feedback'],p['parameters']['layout']),combinations)
            self.assertTrue(p['parameters']['hard_restored'])
            self.assertFalse(old_questions.intersection(c['public']['question'] for c in p['cases'][:12]))


class ActualTraceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=taste_audit.audit(ROOT/'examples/pilot-evidence.synthetic.zip')

    def test_all192_answers_and_eight_memories_replay_without_model_judgment(self):
        r=self.result;self.assertEqual(r['trace_count'],192);self.assertEqual(len(r['replayed_cells']),4)
        self.assertTrue(all(x['observed_answer']=='U' for x in r['traces']))
        self.assertTrue(all(c['actual_browser_and_bind_replay_equal'] for c in r['replayed_cells']))
        self.assertTrue(all(c['original_private_source_preserved'] for c in r['replayed_cells']))
        self.assertFalse(any(c['portable_has_day_or_record_anchor'] for c in r['replayed_cells']))
        self.assertEqual(r['external_model_calls'],0)

    def test_curated_cases_distinguish_true_loss_from_retained_but_unexplained_U(self):
        cases={c['id']:c for c in self.result['representative_cases']}
        self.assertEqual(len(cases),6)
        marker=cases['old_marker_missing_from_portable']['deterministic_witness']
        self.assertNotEqual(*marker['past_answers']);self.assertTrue(marker['both_have_cleared_current_marker'])
        revoke=cases['revocation_time_lost']['deterministic_witness']
        self.assertNotEqual(*revoke['past_answers']);self.assertEqual(*revoke['current_answers'])
        retained=cases['action_retained_reader_still_U'];self.assertIn(retained['deterministic_witness']['retained_span'],retained['memory'])
        self.assertFalse(retained['model_causal_effect_verified'])
        wrong=cases['invented_second_order_revocation']['deterministic_witness']
        self.assertEqual(wrong['current_default'],'minimal');self.assertNotIn('revoke',wrong['revoke_target_operation_types'])
        self.assertEqual(cases['known_base_choice_replaced_with_unknown']['deterministic_witness']['current_choice'],'auto')
        self.assertEqual(cases['genuine_unknown_domain']['gold'],['U'])


class ComparisonPlanTests(unittest.TestCase):
    def test_new_payloads_are_bounded_and_not_sealed_retries_or_encoder_leaks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'proposal'
            proposal=taste_plan.prepare(root,ROOT/'examples/pilot-evidence.synthetic.zip',813247)
            self.assertEqual(sum(proposal['matrix'].values()),24);self.assertEqual(proposal['external_model_calls_this_work'],0)
            jobs=[json.loads(s) for s in (root/'reader-jobs.jsonl').read_text().splitlines()]
            gen=[json.loads(s) for s in (root/'generation-jobs.jsonl').read_text().splitlines()]
            dynamic=json.loads((root/'dynamic-job-contracts.json').read_text())
            self.assertEqual((len(jobs),len(gen),len(dynamic)),(16,2,6))
            old={b['request_id'] for b in json.loads((root/'sealed-baselines.json').read_text())}
            self.assertFalse(old.intersection(j['request_id'] for j in jobs))
            future=json.loads((root/'future-fixtures.private.json').read_text())
            for j in gen:
                for person in future['people']:
                    for case in person['cases']:self.assertNotIn(case['public']['id'],j['request']['prompt'])
                self.assertNotIn('canonical_options',j['request']['prompt'])
                self.assertNotIn('"parameters"',j['request']['prompt']);self.assertNotIn('"seed"',j['request']['prompt'])
            self.assertFalse((root/'calls').exists())
            diagnostic=[j for j in jobs if j['phase']=='diagnostic']
            self.assertEqual(len(diagnostic),8)
            for pid in {j['persona_id'] for j in diagnostic}:
                cells={j['id']:json.loads(j['request']['prompt'].split('\nINPUT_JSON:\n')[1]) for j in diagnostic if j['persona_id']==pid}
                self.assertEqual(cells['reader_only']['memory'],cells['cutoff_only']['memory'])
                self.assertEqual(cells['cutoff_only']['memory'],cells['reader_and_cutoff']['memory'])
                self.assertNotIn('source_cutoff',cells['reader_only'])
                self.assertEqual(cells['cutoff_only']['source_cutoff'],15)
                self.assertNotIn('r06',cells['content_complete_prose']['memory'])


if __name__=='__main__':unittest.main()
