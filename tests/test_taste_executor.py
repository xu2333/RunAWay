import ast
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import shutil
import unittest
from unittest.mock import patch

from runaway import taste_executor as ex,taste_contract as tc,taste_plan
from runaway import generation,bound_memory
from runaway.card import canonical,digest
from runaway.pipeline import write_once
from runaway.execution_ledger import start_attempt
from runaway.selfplay import BROWSER_SCHEMA

ROOT=Path(__file__).resolve().parents[1]


class FakeModel:
    """Routing/gate fixture only; no claim about language-model fidelity."""
    def __init__(self,root,fail_gate=None,raise_error=False):
        world=json.loads((root/'future-fixtures.private.json').read_text())
        self.people=[p for p in world['people'] if p['split']=='eval']
        self.queries={c['public']['id']:(p,c) for p in self.people for c in p['cases']}
        self.calls=[];self.fail_gate=fail_gate;self.raise_error=raise_error

    def __call__(self,prompt,model,**kwargs):
        self.calls.append({'model':model,'timeout':kwargs['timeout'],'schema':kwargs['schema'],'prompt':prompt})
        if self.raise_error:raise ValueError('mock transport failure')
        schema=kwargs['schema']
        if schema==BROWSER_SCHEMA:
            source=json.loads(prompt.split('\nSOURCE_JSON:\n',1)[1])['sources'][0]
            value={'name':'测试','tagline':'非模型效果','claims':[{'id':'c1','statement':'局部记录。','basis':'self_report','scope':'合成测试','conditions':[],'exceptions':[],'related_claim_ids':[],
                'evidence':[{'source_id':source['id'],'quote':source['text'][:40],'relation':'supports'}]}],
                'unknowns':['其他未知。'],'prompt':'仅合成测试。','covered_claim_ids':['c1'],
                'presentation':{'tell':'合成测试','boundary':'非真人','claim_ids':['c1']},'manual':{'headline':'材料还不足以写使用说明','items':[]}}
        elif schema==bound_memory.SCHEMA:
            value={'scope':'合成测试。','clauses':[{'claim_ids':['c1'],'text':'依来源作局部判断。'}],'unknown':'其他未知。'}
        else:
            payload=json.loads(prompt.split('\nINPUT_JSON:\n',1)[1]);memory=payload['memory'];value={}
            for query in payload['queries']:
                if query['id'] not in self.queries:value[query['id']]='U';continue
                person,case=self.queries[query['id']];twin=next(p for p in self.people if p['id']==person['twin'])
                kind='full_history' if memory==person['history'] else 'wrong_person_history' if memory==twin['history'] else 'current_policy_oracle' if memory==tc.current_prose(person) else 'none' if memory=='' else 'actual'
                if kind==self.fail_gate:
                    value[query['id']]=case['gold'] if kind=='wrong_person_history' else 'U'
                elif kind=='wrong_person_history':value[query['id']]=tc.gold(twin,case)
                elif kind=='current_policy_oracle' and case['public']['task']=='historical_reconstruction':value[query['id']]='U'
                elif kind=='none' and case['current_instruction'] is None:value[query['id']]='U'
                else:value[query['id']]=case['gold']
        return json.dumps(value,ensure_ascii=False),{'backend':'mock_no_service','usage':[{'input_tokens':1,'output_tokens':1}]}


class TasteExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.plan=self.root/'plan';taste_plan.prepare(self.plan,ROOT/'examples/pilot-evidence.synthetic.zip',813247)
    def tearDown(self):self.temp.cleanup()
    def execute(self,fake):
        with patch.object(generation,'codex_generate',side_effect=AssertionError('No service allowed')):
            return ex.execute(self.plan,self.root/'output',backend=fake,count=lambda text:len(text.encode()),require_evidence=False)

    def test_all_static_and_dynamic_entries_are180_and_matrix_is24(self):
        fake=FakeModel(self.plan);report=self.execute(fake)
        self.assertEqual(report['status'],'complete');self.assertEqual(len(fake.calls),24)
        self.assertTrue(all(c['timeout']==180 for c in fake.calls))
        self.assertEqual(sum(c['schema']==BROWSER_SCHEMA for c in fake.calls),2)
        self.assertEqual(sum(c['schema']==bound_memory.SCHEMA for c in fake.calls),2)
        self.assertEqual(report['calls']['execution_records'],24)
        for call in fake.calls:
            if call['schema'] not in (BROWSER_SCHEMA,bound_memory.SCHEMA):continue
            for person in fake.people:
                self.assertNotIn(tc.current_prose(person),call['prompt'])
                for case in person['cases']:self.assertNotIn(case['public']['id'],call['prompt'])
        self.assertTrue(report['comparison_interpretable'])
        # Current-only oracle's historic losses survive the passed current gate.
        oracle=report['fresh_scores']['current_policy_oracle']
        self.assertEqual(oracle['current_choice']['correct'],32)
        self.assertLess(oracle['historical_reconstruction']['correct'],16)
        self.assertEqual(oracle['historical_reconstruction']['planned'],16)
        self.assertEqual(len(report['legacy_diagnostic_scores']),4)

    def test_each_reader_gate_stops_all_later_stages_and_keeps_every_denominator(self):
        for gate_name,expected_calls in [('full_history',2),('wrong_person_history',4),('current_policy_oracle',6)]:
            with self.subTest(gate=gate_name):
                out=self.root/('out-'+gate_name);fake=FakeModel(self.plan,fail_gate=gate_name)
                report=ex.execute(self.plan,out,backend=fake,count=len,require_evidence=False)
                self.assertEqual(len(fake.calls),expected_calls);self.assertEqual(report['status'],'stopped')
                self.assertEqual(report['stop_reason']['gate'],gate_name)
                for method in ('current_browser','new_bound'):
                    scores=report['fresh_scores'][method]
                    self.assertEqual((scores['current_choice']['planned'],scores['current_choice']['missing']),(32,32))
                    self.assertEqual((scores['historical_reconstruction']['planned'],scores['historical_reconstruction']['missing']),(16,16))
                    self.assertEqual(scores['joint']['planned'],48)
                self.assertTrue(all(q['planned']==48 and q['missing']==48 for q in report['legacy_diagnostic_scores'].values()))

    def test_global_stop_on_model_failure_and_unresolved_or_corrupt_attempt(self):
        fake=FakeModel(self.plan,raise_error=True);report=self.execute(fake)
        self.assertEqual(len(fake.calls),1);self.assertFalse(report['comparison_interpretable'])
        self.assertEqual(report['calls']['executions_missing_usage'],1)
        _,config,slots=ex.preflight(self.plan,False)
        calls=ex.FrozenCalls(self.root/'orphan',config,slots,fake)
        slot=next(iter(slots));request=slots[slot]['request'];key=digest(canonical(request))
        write_once(calls.out/'calls'/(key+'.request.json'),request);start_attempt(calls.out/'calls'/(key+'.attempt.json'),key)
        before=len(fake.calls)
        with self.assertRaises(ex.Stopped):calls.call(slot)
        with self.assertRaises(ex.Stopped):calls.call(slot)
        self.assertEqual(len(fake.calls),before);self.assertTrue(calls.stopped)
        # Corrupt evidence also latches stop instead of allowing another call.
        (calls.out/'calls'/(key+'.attempt.json')).write_text('{}')
        calls.update();self.assertTrue(calls.ledger['integrity_uncertain'])

    def test_sealed_original_requests_are_offline_only_and_caps_cannot_expand(self):
        _,config,slots=ex.preflight(self.plan,False);self.assertEqual(len(slots),24)
        self.assertEqual(dict(__import__('collections').Counter(s['stage'] for s in slots.values())),ex.STAGE_CAPS)
        fake=FakeModel(self.plan);calls=ex.FrozenCalls(self.root/'blocked',config,slots,fake)
        old=taste_plan.load(ROOT/'examples/pilot-evidence.synthetic.zip')
        key=config['forbidden_sealed_request_ids'][0]
        slots['forbidden']={'stage':'diagnostic','request':json.loads(old['calls/'+key+'.request.json'])}
        with self.assertRaisesRegex(ex.Stopped,'offline'):calls.call('forbidden')
        self.assertEqual(len(fake.calls),0);self.assertFalse(list((calls.out/'calls').glob('*.attempt.json')))
        cfg_path=self.plan/'executor-config.json';cfg=json.loads(cfg_path.read_text());cfg['global_cap']=25
        cfg_path.write_text(json.dumps(cfg))
        with self.assertRaises(ValueError):ex.preflight(self.plan,False)

    def test_numeric_oracle_qualification_catches_critical_loss_not_only_total(self):
        world=json.loads((self.plan/'future-fixtures.private.json').read_text())
        preds={p['id']:{c['public']['id']:c['gold'] for c in p['cases']} for p in world['people'] if p['split']=='eval'}
        q=tc.score(world,preds,'current_choice');self.assertTrue(ex.gate('current_policy_oracle',q)['passed'])
        weakened=copy.deepcopy(q);weakened['layers']['strength']['correct']-=1
        self.assertGreaterEqual(weakened['accuracy'],.9)
        self.assertFalse(ex.gate('current_policy_oracle',weakened)['passed'])
        weakened=copy.deepcopy(q);weakened['hard_constraint_errors']=1
        self.assertFalse(ex.gate('current_policy_oracle',weakened)['passed'])

    def test_uncertainty_between_intent_and_backend_also_blocks_the_backend(self):
        _,config,slots=ex.preflight(self.plan,False);fake=FakeModel(self.plan)
        calls=ex.FrozenCalls(self.root/'race',config,slots,fake);original=calls.update;inserted=[]
        selected=list(slots)[:2]
        def update():
            if calls.current is not None and not inserted:
                request=slots[selected[1]]['request'];key=digest(canonical(request))
                write_once(calls.out/'calls'/(key+'.request.json'),request)
                start_attempt(calls.out/'calls'/(key+'.attempt.json'),key);inserted.append(True)
            original()
        calls.update=update
        with self.assertRaises(ex.Stopped):calls.call(selected[0])
        self.assertEqual(len(fake.calls),0);self.assertTrue(calls.stopped)

    def test_preflight_and_missing_approval_cannot_invoke_real_backend(self):
        with patch.object(generation,'codex_generate',side_effect=AssertionError('No real service')) as backend:
            with self.assertRaises(ValueError):ex.preflight(self.plan)
            with self.assertRaises(ValueError):ex.execute(self.plan,self.root/'real',require_evidence=False)
            backend.assert_not_called();self.assertFalse((self.root/'real').exists())

    def test_proposal_execution_intent_is_single_use_across_output_directories(self):
        proposal,_,_=ex.preflight(self.plan,False)
        approval={'human_source':'isolated-test-receipt-not-authorization'}
        ex.claim_execution(self.plan,proposal,approval,self.root/'first')
        with self.assertRaises(FileExistsError):ex.claim_execution(self.plan,proposal,approval,self.root/'second')
        self.assertFalse((self.plan/'calls').exists())
        shutil.copytree(self.plan,self.root/'copy')
        with self.assertRaises(ValueError):ex.preflight(self.root/'copy',False)

    def test_only_one_backend_entry_and_subprocess_rejects240_before_start(self):
        tree=ast.parse(Path(ex.__file__).read_text());entries=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='backend':
                entries.append(node);self.assertEqual(next(k.value.id for k in node.keywords if k.arg=='timeout'),'TIMEOUT')
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):self.assertNotEqual(node.func.id,'Calls')
        self.assertEqual(len(entries),1);self.assertEqual(ex.TIMEOUT,180)
        _,config,slots=ex.preflight(self.plan,False);calls=ex.FrozenCalls(self.root/'deadline',config,slots,FakeModel(self.plan))
        with patch.object(ex,'ORIGINAL_RUN_BOUNDED') as runner:
            with self.assertRaises(ex.Stopped):calls.observed_runner(['codex','exec'],'test',240)
            runner.assert_not_called()

    def test_unchanged_cleanup_has_only2second_drain_and2second_wait(self):
        waits=[];drains=[]
        class Pipe:
            def close(self):pass
        class Process:
            pid=123456789;stdin=Pipe();stdout=Pipe();stderr=Pipe()
            def communicate(self,*args,timeout):
                drains.append(timeout);raise subprocess.TimeoutExpired(['fake'],timeout,output=b'',stderr=b'')
            def wait(self,timeout):waits.append(timeout);return -9
        with patch.object(generation.subprocess,'Popen',return_value=Process()),patch.object(generation.os,'killpg'):
            with self.assertRaises(generation.GenerationTimeout):generation.run_bounded(['fake'],'test',180)
        self.assertEqual(drains,[180,2]);self.assertEqual(waits,[2])


if __name__=='__main__':unittest.main()
