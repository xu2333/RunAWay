import copy
import json
from pathlib import Path
import tempfile
import unittest

from runaway import production_adapters as adapters
from runaway.metric_jobs import prepare, score_trials
from runaway.selfplay import Calls, browser
from runaway.synthetic_metric import freeze, byte_count
from runaway.demo import demo_bundle
from runaway.bound_memory import bind


def mock_generate(prompt, model, **kwargs):
    """Schema fixture only. It intentionally makes no fidelity claim."""
    if '\nSOURCE_JSON:\n' in prompt:
        data = json.loads(prompt.split('\nSOURCE_JSON:\n')[1])
        source = next(s for s in data['sources'] if s['role'] == 'user')
        answer = {'name':'测试', 'tagline':'非质量实验', 'claims':[
            {'id':'c1', 'statement':'这是一段合成历史。', 'basis':'self_report',
             'scope':'测试', 'conditions':[], 'exceptions':[], 'related_claim_ids':[],
             'evidence':[{'source_id':source['id'], 'quote':source['text'][:80], 'relation':'supports'}]}],
            'unknowns':['测试未推断偏好。'], 'prompt':'这是一段合成历史，其余偏好未知。',
            'covered_claim_ids':['c1'], 'presentation':{'tell':'合成历史', 'boundary':'测试', 'claim_ids':['c1']},
            'manual':{'headline':'材料还不足以写使用说明', 'items':[]}}
    else:
        answer = {'scope':'仅测试。', 'clauses':[{'claim_ids':['c1'], 'text':'这是一段合成历史'}], 'unknown':'其余未知。'}
    return json.dumps(answer, ensure_ascii=False), {'backend':'mock_not_inference', 'usage':[]}


class ProductionAdaptersTests(unittest.TestCase):
    def setup_run(self, root, budgets=(4096,)):
        metric = root/'metric'; freeze(metric, pairs=1, budgets=budgets)
        plan = adapters.freeze(root/'adapter', metric, list(budgets), 'mock-model')
        return metric, plan

    def test_actual_product_functions_request_isolation_reuse_and_metric_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); metric, plan=self.setup_run(root)
            observed=[]
            def generate(prompt, model, **kwargs):
                observed.append(prompt); return mock_generate(prompt, model, **kwargs)
            calls=Calls(root/'adapter', generate)
            result=adapters.run(root/'adapter', calls, byte_count, plan['tokenizer'])
            self.assertEqual(len(observed),4)  # Two shared extractions + two new compressions.
            self.assertEqual(plan['calls_upper_bound'],4)
            self.assertTrue(all(s['status']=='usable' for s in result['stages']))
            again=adapters.run(root/'adapter', calls, byte_count, plan['tokenizer'])
            self.assertEqual(again,result); self.assertEqual(len(observed),4)
            world=json.loads((metric/'world.private.json').read_text())
            requests='\n'.join(observed)
            for p in world['people']:
                for query in p['queries']:
                    self.assertNotIn(query['public']['id'],requests)
            self.assertNotIn('allowed_answers',requests)
            self.assertNotIn('"parameters"',requests)
            self.assertEqual(len(result['rows']),4)
            manifest=prepare(metric,result['rows'],root/'jobs',adapters.CONDITIONS,[4096])
            self.assertEqual(len(manifest['trials']),4)
            scored=score_trials(metric,root/'jobs/trials.private.json',{})
            self.assertTrue(all(r['quality']['planned']==48 and r['quality']['missing']==48 for r in scored['rows']))

    def test_over_token_budget_preserves_shared_profile_and_all_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); metric, plan=self.setup_run(root,(128,))
            calls=Calls(root/'adapter',mock_generate)
            result=adapters.run(root/'adapter',calls,lambda text:999,plan['tokenizer'])
            self.assertTrue(all(r['memory'] is None for r in result['rows']))
            self.assertEqual(len(list((root/'adapter/calls').glob('*.response.json'))),4)
            self.assertEqual(sum(s['status']=='validation_failed' for s in result['stages']),4)
            prepare(metric,result['rows'],root/'jobs',adapters.CONDITIONS,[128])
            self.assertEqual((root/'jobs/decoder-jobs.jsonl').read_text(),'')
            self.assertTrue(all(r['quality']['missing']==48 for r in score_trials(metric,root/'jobs/trials.private.json',{})['rows']))

    def test_malformed_extraction_skips_dependent_stage_without_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); _,plan=self.setup_run(root)
            calls=Calls(root/'adapter',lambda *a,**k:('{}',{'backend':'mock'}))
            result=adapters.run(root/'adapter',calls,len,plan['tokenizer'])
            self.assertEqual(len(list((root/'adapter/calls').glob('*.response.json'))),2)
            self.assertTrue(all(r['memory'] is None for r in result['rows']))
            self.assertFalse(result['stopped_after_backend_failure'])

    def test_timeout_stops_subsequent_calls_and_tampered_plan_cannot_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); _,plan=self.setup_run(root)
            seen=[]
            def fail(*a,**k):seen.append(1); raise ValueError('mock timeout')
            result=adapters.run(root/'adapter',Calls(root/'adapter',fail),len,plan['tokenizer'])
            self.assertEqual(len(seen),1)
            self.assertEqual(len(result['rows']),4)
            self.assertTrue(result['stopped_after_backend_failure'])
            self.assertTrue(all(r['memory'] is None for r in result['rows']))
            path=root/'adapter/adapter-plan.json'; plan['generator_model']='changed';path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,'changed'):adapters.run(root/'adapter',None,len,plan['tokenizer'])

    def test_empty_profile_skips_only_new_stage_and_keeps_current_unknown_memory(self):
        def empty(prompt,model,**kwargs):
            raw,prov=mock_generate(prompt,model,**kwargs); answer=json.loads(raw)
            answer.update(claims=[],covered_claim_ids=[],presentation={'tell':'材料不足','boundary':'测试','claim_ids':[]})
            return json.dumps(answer,ensure_ascii=False),prov
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);_,plan=self.setup_run(root)
            result=adapters.run(root/'adapter',Calls(root/'adapter',empty),byte_count,plan['tokenizer'])
            self.assertEqual(len(list((root/'adapter/calls').glob('*.response.json'))),2)
            self.assertTrue(all(r['memory'] for r in result['rows'] if r['condition']=='current_browser'))
            self.assertTrue(all(r['memory'] is None for r in result['rows'] if r['condition']=='new_bound'))
            self.assertFalse(result['stopped_after_backend_failure'])

    def test_existing_packaged_synthetic_profile_replays_through_actual_browser_and_binding(self):
        profile=demo_bundle()[0]['profile.private.json'];claims=copy.deepcopy(profile['claims'])
        answer={'name':'回放', 'tagline':'已有合成档案', 'claims':claims, 'unknowns':profile['unknowns'],
                'prompt':'依据已有阅读小组记录，在已观察范围内选择。', 'covered_claim_ids':[c['id'] for c in claims],
                'presentation':{'tell':'已有记录', 'boundary':'非真人', 'claim_ids':[claims[0]['id']]},
                'manual':{'headline':'材料还不足以写使用说明', 'items':[]}}
        bundle=browser('validate',profile['sources'],16000,answer)
        value={'scope':'已有合成档案。', 'clauses':[{'claim_ids':[c['id']],'text':c['statement']} for c in claims], 'unknown':'其余未知。'}
        text,binding=bind(value,bundle['profile'],16000)
        self.assertIn(claims[0]['statement'].rstrip('；。'),text)
        self.assertEqual(len(binding['bindings']),len(claims))
        self.assertNotIn('original_facets',bundle['portable']['text'])


if __name__=='__main__': unittest.main()
