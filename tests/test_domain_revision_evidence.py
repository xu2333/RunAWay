"""Mutation checks on sealed fourteen-attempt evidence;all replay uses archived responses."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

r=load('guard_template_test_replay','replay_domain_revision.py')
t=load('guard_template_test_trace','inspect_domain_revision.py')

class DomainRevisionEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=r.p.read(r.DEFAULT);cls.report=r.check()

    def reject(self,data):
        with self.assertRaises((ValueError,AssertionError,KeyError,TypeError,IndexError)):r.replay(data)

    def test_fixed_denominators_and_eight_answers_with_old_and_new_cases(self):
        report=self.report
        self.assertEqual((report['fixed_cases_per_method'],report['known'],report['unknown']),(94,36,58))
        self.assertEqual(report['old82anchors']['planned'],82);self.assertEqual(report['new12domaincases']['planned'],12)
        for m in r.p.METHODS:
            c=report['methods'][m]['strict'];self.assertEqual([c[k]['planned']for k in('joint','known','unknown')],[94,36,58])
        self.assertEqual(sum(report['observed_transitions'].values()),94)
        self.assertTrue(all(len(c[m]['answers'])==8 for c in report['all_case_transitions']for m in r.p.METHODS))
        self.assertFalse(report['new_source_only768_generation_tested']);self.assertFalse(report['independent_semantic_gold'])
        self.assertEqual(report['new_service_calls_from_replay'],0)

    def test_frozen_packet_source_question_reference_and_views_reject_edits(self):
        for name in r.p.FILES:
            d=copy.deepcopy(self.data);d['prepared_files'][name]={};self.reject(d)

    def test_updated_raw_hash_does_not_hide_changed_answer(self):
        rec=next(x for x in self.data['records']if x['raw_present']and x['state']=='completed')
        d=copy.deepcopy(self.data);x=next(x for x in d['records']if x['slot']==rec['slot'])
        x['raw']+='invalid';x['raw_value_sha256']=r.p.digest(x['raw']);self.reject(d)

    def test_changed_exact_request_cannot_be_hidden_by_rehash(self):
        d=copy.deepcopy(self.data);x=d['records'][0]
        x['request']['prompt']+=' extra';x['request_sha256']=r.p.digest(x['request']);x['execution_record']['request_sha256']=x['request_sha256'];self.reject(d)

    def test_routing_order_and_generation_are_frozen(self):
        for key in('profile','method','view','generation','budget','read_repeat'):
            d=copy.deepcopy(self.data);x=d['records'][0];x[key]='foreign';x['execution_record'][key]='foreign';self.reject(d)
        d=copy.deepcopy(self.data);d['records'].append(copy.deepcopy(d['records'][0]));self.reject(d)

    def test_usage_child_flags_and_remaining_slots_cannot_change(self):
        for key in('attempt_reservations','local_cli_child_intents','unused_slots_expire'):
            d=copy.deepcopy(self.data);d['status'][key]=True;self.reject(d)
        d=copy.deepcopy(self.data);d['status']['known_usage']['total_tokens']+=1;self.reject(d)
        d=copy.deepcopy(self.data);d['records'][0]['local_cli_child_intent']=1;self.reject(d)

    def test_original_scores_and_missing_denominators_cannot_change(self):
        for method in r.p.METHODS:
            d=copy.deepcopy(self.data);d['status']['scores']['methods'][method]['strict']['joint']['planned']-=1;self.reject(d)
        d=copy.deepcopy(self.data);d['status']['scope_closed']=False;self.reject(d)

    def test_unreviewed_private_fields_and_claims_reject(self):
        for key in r.FALSE_CLAIMS:
            d=copy.deepcopy(self.data);d[key]=True;self.reject(d)
        d=copy.deepcopy(self.data);d['human_authorization']='private';self.reject(d)
        d=copy.deepcopy(self.data);d['records'][0]['machine_path']='private';self.reject(d)

    def test_checksum_guard_detects_file_corruption(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'evidence.json';p.write_bytes(r.DEFAULT.read_bytes());p.with_suffix('.sha256').write_text(r.p.sha(p)+'\n')
            p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaises(ValueError):r.check(p)

    def test_source_trace_preserves_both_generations_and_complete_episodes(self):
        c=self.report['all_case_transitions'][0];before=r.p.digest(self.data)
        for method in r.p.METHODS:
            for generation in(0,1):
                trace=t.trace(self.data,self.report,c['case'],method,generation)
                self.assertEqual(len(trace['complete_related_source_episodes']),8)
                self.assertEqual({x['role']for x in trace['complete_related_source_episodes']},{'user','assistant','tool'})
                self.assertEqual(len(trace['public_queries']),2)
                self.assertEqual(trace['planned_answers_this_generation'],c[method]['answers'][generation*4:generation*4+4])
                self.assertEqual(trace['new_service_calls'],0)
        self.assertEqual(r.p.digest(self.data),before)
        for case,method,generation in [('foreign','current',0),('0_new_boundary','foreign',0),('0_new_boundary','current',True)]:
            with self.assertRaises(ValueError):t.trace(self.data,self.report,case,method,generation)

    def test_missing_and_unknown_are_not_conflated_with_semantic_recovery(self):
        good=dict(correct=True,missing=False);bad=dict(correct=False,missing=False);absent=dict(correct=False,missing=True)
        for a,b,label in[(good,good,'kept'),(good,bad,'new_observed_loss'),(bad,good,'recovered'),(absent,good,'baseline_missing'),(good,absent,'candidate_missing'),(absent,absent,'both_missing')]:
            self.assertEqual(r.transition(a,b),label)
        self.assertEqual(r.loss_kind('choice',[None,'U']),'missing')
        self.assertEqual(r.loss_kind('choice',['U']*8),'all_unknown_from_known')
        self.assertEqual(r.loss_kind('U',['choice']*8),'choice_when_reference_unknown')

    def test_replay_and_trace_clis_work_outside_checkout_without_pythonpath(self):
        import os,subprocess,sys
        env={k:v for k,v in os.environ.items()if k!='PYTHONPATH'}
        with tempfile.TemporaryDirectory()as tmp:
            for script,args in [('replay_domain_revision.py',[]),('inspect_domain_revision.py',['0_new_boundary'])]:
                proc=subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/script),*args],cwd=tmp,env=env,capture_output=True,text=True,timeout=120)
                self.assertEqual(proc.returncode,0,proc.stderr)
                self.assertIsInstance(json.loads(proc.stdout),dict)

if __name__=='__main__':unittest.main()
