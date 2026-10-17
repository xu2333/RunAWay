"""Injected fake responses test execution plumbing, never model quality."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runaway import fidelity_plan as fp, fidelity_runner as fr, fidelity_stress as fs
from runaway import generation, bound_memory
from runaway.execution_ledger import start_attempt
from runaway.card import canonical, digest
from runaway.pipeline import write_once
from runaway.selfplay import BROWSER_SCHEMA


class FakeModel:
    def __init__(self,root,fail=None,transport=False):
        self.world=json.loads((root/'fixtures.private.json').read_text());self.fail=fail;self.transport=transport;self.calls=[]
        self.people={p['id']:p for p in self.world['people']}
        self.cases={c['public']['id']:(p,c) for p in self.world['people'] for c in p['cases']}

    def __call__(self,prompt,model,**kw):
        self.calls.append((prompt,kw))
        if self.transport:raise ValueError('fake transport failure')
        if kw['schema']==BROWSER_SCHEMA:
            source=json.loads(prompt.split('\nSOURCE_JSON:\n',1)[1])['sources'][0]
            # Vary budget texts so the complete fake matrix can exercise48calls.
            small='256' in prompt
            value={'name':'测试','tagline':'非模型效果','claims':[{'id':'c1','statement':'局部记录。','basis':'self_report','scope':'合成测试','conditions':[],'exceptions':[],'related_claim_ids':[],
                'evidence':[{'source_id':source['id'],'quote':source['text'][:40],'relation':'supports'}]}],
                'unknowns':['其他未知。'],'prompt':'仅合成测试，小预算。' if small else '仅合成测试，大预算。','covered_claim_ids':['c1'],
                'presentation':{'tell':'合成测试','boundary':'非真人','claim_ids':['c1']},'manual':{'headline':'材料还不足以写使用说明','items':[]}}
        elif kw['schema']==bound_memory.SCHEMA:
            # make_request carries the declared character bound as JSON.
            value={'scope':'合成测试。','clauses':[{'claim_ids':['c1'],'text':'依来源作局部判断。'+('小' if '256' in prompt else '大')}],'unknown':'其他未知。'}
        else:
            data=json.loads(prompt.split('\nINPUT_JSON:\n',1)[1]);value={}
            for q in data['queries']:
                p,c=self.cases[q['id']];twin=self.people[p['twin']];memory=data['memory']
                kind='full_history' if memory==p['history'] else 'wrong_person_history' if memory==twin['history'] else 'current_policy_oracle' if memory==fp.current_oracle(p) else 'none' if memory=='' else 'actual'
                if kind==self.fail:
                    action=c['action'] if kind in ('none','wrong_person_history') else 'U'
                elif kind=='wrong_person_history':action=c['instruction'] or fs.resolve(twin['events'],c['key'],c['at'],c['context'])[0]
                elif kind=='none':action=c['instruction'] or 'U'
                elif kind=='current_policy_oracle' and c['public']['task']=='historical_reconstruction':action='U'
                else:action=c['action']
                value[q['id']]=next(k for k,v in c['options'].items() if v==action)
        return json.dumps(value,ensure_ascii=False),{'backend':'fake_no_service','usage':[{'input_tokens':1,'output_tokens':1}]}


class FidelityRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.plan=self.root/'plan'
        # A source distribution has no operator runtime template; only its metadata
        # is needed in these fake tests. No tokenizer is loaded here.
        template={'python_executable':'unused-fake-runtime','tokenizer':{'model_sha256':'unused'},'tokenizer_path':'unused'}
        self.runtime=self.root/'runtime.json';self.runtime.write_text(json.dumps(template))
        fp.prepare(self.plan,829491,self.runtime)
    def tearDown(self):self.temp.cleanup()

    def run_fake(self,fake,name='out',count=lambda s:len(s.encode())//4):
        with patch.object(generation,'codex_generate',side_effect=AssertionError('No service allowed')):
            return fr.execute(self.plan,self.root/name,backend=fake,count=count)

    def test_complete_matrix_all48_entries_timeout180_and_leakage_boundary(self):
        fake=FakeModel(self.plan);r=self.run_fake(fake)
        self.assertEqual(r['status'],'complete');self.assertEqual(len(fake.calls),48)
        self.assertEqual(r['stage_attempts'],fp.STAGES);self.assertEqual(r['external_model_calls'],0)
        self.assertEqual(r['backend_kind'],'injected_fake_not_model_quality')
        self.assertTrue(all(kw['timeout']==180 for _,kw in fake.calls))
        self.assertEqual(r['calls']['executions_missing_usage'],0)
        for prompt,kw in fake.calls:
            if kw['schema'] not in (BROWSER_SCHEMA,bound_memory.SCHEMA):continue
            for p in fake.world['people']:
                self.assertNotIn(fp.current_oracle(p),prompt)
                for c in p['cases']:self.assertNotIn(c['public']['id'],prompt)
            for forbidden in ('"parameters"','"seed"','"events"','"gold"','"tags"','"target_axes"','latest on ties'):
                self.assertNotIn(forbidden,prompt)
        for row in r['scores'].values():
            self.assertEqual([row[k]['planned'] for k in ('current_choice','historical_reconstruction','joint')],[224,76,300])

    def test_every_control_failure_stops_all_later_stages_and_keeps_missing(self):
        for name,calls in [('full_history',4),('wrong_person_history',8),('current_policy_oracle',12),('none',16)]:
            fake=FakeModel(self.plan,fail=name);r=self.run_fake(fake,name)
            self.assertEqual((r['status'],len(fake.calls)),('stopped',calls))
            self.assertEqual(r['stop_reason']['gate'],name)
            for b in fp.BUDGETS:
                for condition in ('current_browser','new_bound'):
                    q=r['scores'][condition+':'+str(b)]['joint'];self.assertEqual((q['missing'],q['planned']),(300,300))

    def test_transport_unknown_usage_and_checkpoint_corruption_stop_globally(self):
        fake=FakeModel(self.plan,transport=True);r=self.run_fake(fake)
        self.assertEqual(len(fake.calls),1);self.assertEqual(r['status'],'stopped')
        self.assertEqual(r['calls']['executions_missing_usage'],1)
        out=self.root/'direct';out.mkdir();cfg=fp.preflight(self.plan);fake=FakeModel(self.plan)
        calls=fr.DirectCalls(out,cfg,fake)
        job=json.loads((self.plan/'reader-jobs.jsonl').read_text().splitlines()[0]);request=job['request'];key=digest(canonical(request))
        write_once(out/'calls'/(key+'.request.json'),request);start_attempt(out/'calls'/(key+'.attempt.json'),key)
        with self.assertRaises(ValueError):calls.call('full_history',request)
        self.assertEqual(len(fake.calls),0);self.assertTrue(calls.stopped)
        (out/'calls'/(key+'.attempt.json')).write_text('{}')
        with self.assertRaises(ValueError):calls.call('full_history',request)
        self.assertEqual(len(fake.calls),0)

        missing_usage=FakeModel(self.plan)
        def no_usage(*args,**kwargs):
            raw,_=missing_usage(*args,**kwargs);return raw,{'backend':'fake_no_usage'}
        r=self.run_fake(no_usage,'unknown-usage')
        self.assertEqual(len(missing_usage.calls),1);self.assertEqual(r['status'],'stopped')
        self.assertEqual(r['stop_reason']['kind'],'usage_unknown')
        self.assertEqual(r['calls']['outcomes'],{'completed':1})

    def test_stage_cap_is_enforced_before_fifth_invocation(self):
        out=self.root/'capped';out.mkdir();fake=FakeModel(self.plan);calls=fr.DirectCalls(out,fp.preflight(self.plan),fake)
        jobs=[json.loads(x) for x in (self.plan/'reader-jobs.jsonl').read_text().splitlines()]
        for job in [j for j in jobs if j['id']=='full_history']:calls.call('full_history',job['request'])
        before=len(fake.calls)
        with self.assertRaises(ValueError):calls.call('full_history',next(j for j in jobs if j['id']=='wrong_person_history')['request'])
        self.assertEqual(len(fake.calls),before);self.assertTrue(calls.stopped)

    def test_gate_requires_collapsed_scenarios_even_when_raw_answers_look_good(self):
        world=FakeModel(self.plan).world;q=fr.scores(world,fs.predict(world,'full_semantic'))
        counts=q['current_choice']['current_scenarios_option_orders_collapsed'];counts['correct']=int(counts['planned']*.85)
        gate=fp.gates('full_history',q)
        self.assertFalse(gate['passed']);self.assertFalse(gate['checks']['collapsed_scenario_accuracy'])
        self.assertTrue(gate['checks']['current_accuracy'])

    def test_identical_inputs_reuse_one_checkpoint_not_an_independent_invocation(self):
        out=self.root/'direct';out.mkdir();fake=FakeModel(self.plan);calls=fr.DirectCalls(out,fp.preflight(self.plan),fake)
        request=json.loads((self.plan/'reader-jobs.jsonl').read_text().splitlines()[0])['request']
        a=calls.call('full_history',request);b=calls.call('full_history',request)
        self.assertEqual(a,b);self.assertEqual(len(fake.calls),1);self.assertEqual(len(calls.reused),1)
        self.assertEqual(calls.ledger['execution_records'],1)

    def test_drift_caps_and_unapproved_service_are_blocked_before_backend(self):
        with patch.object(generation,'codex_generate',side_effect=AssertionError('No service allowed')):
            with self.assertRaisesRegex(ValueError,'human approval'):fr.execute(self.plan,self.root/'real')
        self.assertFalse((self.plan/'execution-intent.json').exists())
        p=json.loads((self.plan/'proposal.json').read_text());p['calls_max']=49
        p['id']=digest(canonical({k:v for k,v in p.items() if k!='id'}));(self.plan/'proposal.json').write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError,'policy'):fp.preflight(self.plan)

    def test_budget_rejection_never_truncates_or_repairs_and_keeps_denominator(self):
        fake=FakeModel(self.plan);r=self.run_fake(fake,count=lambda s:100000)
        self.assertEqual(r['status'],'complete');self.assertEqual(len(fake.calls),32)
        self.assertEqual(len(r['local_validation_failures']),16)
        self.assertEqual(r['memories'],[])
        self.assertEqual(r['scores']['new_bound:128']['current_choice']['missing'],224)


if __name__=='__main__':unittest.main()
