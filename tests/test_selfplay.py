import copy
import json
from pathlib import Path
import tempfile
import unittest
from runaway.card import canonical
from runaway.selfplay_world import build_world, gold, action, synthetic_sources
from runaway.selfplay import (CONDITIONS, freeze, validate_snapshot, validate_predictions,
                              prediction_request, summarize, run, Calls, fallback_memories)


class SelfPlayTests(unittest.TestCase):
    def test_reproducible_world_and_disjoint_contexts(self):
        world=build_world()
        self.assertEqual(world,build_world())
        self.assertNotEqual(world['id'],build_world(123)['id'])
        self.assertEqual(len(world['personas']),6)
        self.assertEqual(len(world['training']),12)
        self.assertEqual(len(world['test']),30)
        ids=[c['public']['id'] for c in world['training']+world['test']]
        self.assertEqual(len(ids),len(set(ids)))
        train={c['public']['question'] for c in world['training']}
        self.assertFalse(train.intersection(c['public']['question'] for c in world['test']))
        for p in world['personas']:
            for c in world['test']:
                if c['kind']!='unobserved':
                    self.assertIn(gold(p['policy'],c),('A','B'))
            # Each matched pair differs in only one operational rule.
            twin=next(t for t in world['personas'] if t['id']==p['twin'])
            self.assertEqual(sum(p['policy'][k]!=twin['policy'][k] for k in p['policy']),1)

    def test_all_training_choices_identify_test_relevant_policy_in_frozen_family(self):
        # This does not claim arbitrary human preferences are identifiable.
        world=build_world()
        for p in world['personas']:
            compatible=[q for q in world['personas'] if all(gold(p['policy'],c)==gold(q['policy'],c) for c in world['training'])]
            self.assertEqual([q['id'] for q in compatible],[p['id']])

    def test_gold_changes_only_at_declared_conditions_and_swaps_reverse_label(self):
        w=build_world();p=w['personas'][0]['policy']
        self.assertNotEqual(action(p,'planning',False),action(p,'planning',True))
        self.assertNotEqual(action(p,'autonomy',False),action(p,'autonomy',True))
        self.assertNotEqual(action(p,'feedback',False),action(p,'feedback',True))
        self.assertNotEqual(action(p,'revision',False),action(p,'revision',True))
        cases={c['public']['id']:c for c in w['test']}
        for c in w['test']:
            if c['kind']=='order_swap':
                self.assertNotEqual(gold(p,c),gold(p,cases[c['original_id']]))

    def test_trajectory_preserves_speakers_without_heldout_labels_or_policy(self):
        w=build_world();rounds={i:{c['public']['id']:'A' for c in w['training'] if c['round']==i} for i in range(3)}
        sources=synthetic_sources(w,w['personas'][0],rounds)
        self.assertEqual(len(sources['sources']),36)
        payload=canonical(sources)
        self.assertNotIn('rollback_guard',payload)
        for c in w['test']:
            self.assertNotIn(c['public']['id'],payload)
            self.assertNotIn(c['public']['question'],payload)
        req=prediction_request('only this memory',[c['public'] for c in w['test']])
        for forbidden in ('rollback_guard','public_soft','original_id','"flag"','"kind"','"pair"'):
            self.assertNotIn(forbidden,req)

    def test_prediction_completeness_and_unknown(self):
        cases=[{'id':'x'},{'id':'y'}]
        good={'predictions':[{'id':'x','choice':'A'},{'id':'y','choice':'unknown'}]}
        self.assertEqual(validate_predictions(good,cases),{'x':'A','y':'unknown'})
        for bad in ({'predictions':good['predictions'][:1]}, {'predictions':good['predictions']*2}, {'predictions':[{'id':'x','choice':'C'},{'id':'y','choice':'B'}]}):
            with self.assertRaises(ValueError):validate_predictions(bad,cases)

    def test_scores_perfect_oracle_and_wrong_twin_not_invented_likelihood(self):
        w=build_world();snap={'world':w,'id':'frozen'}
        predictions={};mem={}
        for p in w['personas']:
            values={c['public']['id']:'unknown' if c['kind']=='unobserved' else gold(p['policy'],c) for c in w['test']}
            predictions[p['id']]={k:dict(values) for k in CONDITIONS};mem[p['id']]={k:'x'*100 for k in CONDITIONS}
        for p in w['personas']:
            predictions[p['id']]['wrong_person']=dict(predictions[p['twin']]['oracle'])
        report=summarize(snap,predictions,mem,{})
        self.assertEqual(report['conditions']['compact']['accuracy'],1)
        self.assertEqual(report['conditions']['compact']['counterfactual_pair_accuracy'],1)
        self.assertEqual(report['conditions']['compact']['order_consistency'],1)
        self.assertEqual(report['conditions']['compact']['unobserved_abstention'],1)
        self.assertEqual(report['conditions']['compact']['discordant_twin_pair_accuracy'],1)
        self.assertEqual(report['conditions']['wrong_person']['discordant_twin_pair_accuracy'],0)
        self.assertIsNone(report['rig']);self.assertFalse(report['true_person_fidelity_verified'])
        del predictions['p01']['compact']
        partial=summarize(snap,predictions,mem,{'p01/compact':'failed'})
        self.assertEqual(partial['conditions']['compact']['personas_completed'],5)
        self.assertEqual(partial['conditions']['compact']['planned_cases'],144)
        self.assertAlmostEqual(partial['conditions']['compact']['accuracy_counting_failures_as_wrong'],5/6)
        self.assertEqual(partial['status'],'complete_with_failures')

    def test_failed_extraction_does_not_remove_independent_baselines(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'p01').mkdir()
            source={'schema_version':1,'sources':[{'id':'synthetic','episode_id':'synthetic','role':'user','text':'fiction'}]}
            (out/'p01/trajectory.synthetic.json').write_text(json.dumps(source))
            p=build_world()['personas'][0]
            values=fallback_memories(p,{'p02':{'portable':{'text':'twin prompt'}}},out)
            self.assertEqual(json.loads(values['trajectory']),source)
            self.assertEqual(values['wrong_person'],'twin prompt')
            self.assertIsNone(values['compact'])

    def test_snapshot_tampering_rejected_and_model_failure_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            snap=freeze(Path(d)/'plan','test-model')
            validate_snapshot(snap)
            snap['world']['seed']=42
            with self.assertRaises(ValueError):validate_snapshot(snap)
            count=[]
            def fail(*a,**kw):count.append(1);raise ValueError('synthetic failure')
            calls=Calls(Path(d),fail)
            for _ in range(2):
                with self.assertRaises(ValueError):calls.call('test',{},'test-model')
            self.assertEqual(len(count),1)

    def test_end_to_end_actual_browser_validator_with_fake_model_no_service(self):
        calls=[]
        def fake(prompt,model,**kwargs):
            calls.append(prompt)
            if '\nSOURCE_JSON:\n' in prompt:
                sources=json.loads(prompt.split('\nSOURCE_JSON:\n')[1]);source=next(s for s in sources['sources'] if s['role']=='user' and s['id'].endswith('correction'))
                answer={'name':'合成测试','tagline':'仅供单元测试','claims':[{'id':'c1','statement':'记录里选择了一个方案','basis':'observed_choice','scope':'本次合成记录','conditions':[],'exceptions':[], 'evidence':[{'source_id':source['id'],'quote':source['text'],'relation':'supports'}],'related_claim_ids':[]}], 'unknowns':['未观察偏好未知'], 'prompt':'在记录中选择过一个方案，其余偏好未知。','covered_claim_ids':['c1'],'presentation':{'tell':'仅描述这次记录','boundary':'合成测试','claim_ids':['c1']},'manual':{'headline':'材料还不足以写使用说明','items':[]}}
            elif '\nINPUT_JSON:\n' in prompt:
                data=json.loads(prompt.split('\nINPUT_JSON:\n')[1]);answer={'predictions':[{'id':c['id'],'choice':'unknown'} for c in data['cases']]}
            else:answer={'text':'合成测试的选择记录，其余偏好未知。'}
            return json.dumps(answer,ensure_ascii=False),{'backend':'fake_unit_test','usage':[]}
        with tempfile.TemporaryDirectory() as d:
            freeze(Path(d)/'plan','fake-model')
            result=run(Path(d)/'plan/snapshot.synthetic.json',Path(d)/'run',workers=2,generate=fake,progress=lambda s:None)
            self.assertEqual(result['status'],'complete')
            self.assertEqual(result['conditions']['compact']['accuracy'],0)
            self.assertEqual(result['conditions']['compact']['unobserved_abstention'],1)
            before=len(calls)
            again=run(Path(d)/'plan/snapshot.synthetic.json',Path(d)/'run',workers=2,resume=True,generate=fake,progress=lambda s:None)
            self.assertEqual(len(calls),before)
            self.assertEqual(result,again)
            memories=json.loads((Path(d)/'run/memories.synthetic.json').read_text())
            for key in ('compact','tiny'):
                self.assertTrue(memories['p01'][key])

if __name__=='__main__':unittest.main()
