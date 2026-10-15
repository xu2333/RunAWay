import math
import unittest
from runaway.selfplay_world import build_world,gold
from runaway.selfplay import CONDITIONS
from runaway.selfplay_local import summarize,encode
from runaway.selfplay_diagnostics import diagnose

class LocalSelfPlayTests(unittest.TestCase):
    def test_true_log_loss_pairing_and_token_ratios(self):
        world=build_world();mem={p['id']:{c:'memory' for c in CONDITIONS} for p in world['personas']}
        plan={'id':'test','world':world,'conditions':list(CONDITIONS),'memories':mem,'model':{'sha256':'test'}}
        rows=[];tokens={}
        for p in world['personas']:
            pid=p['id'];tokens[pid]={c:(0 if c=='none' else 100 if c=='detailed' else 20) for c in CONDITIONS}
            for condition in CONDITIONS:
                for case in world['test']:
                    wanted='U' if case['kind']=='unobserved' else gold(p['policy'],case)
                    probabilities={v:(1/3 if condition=='none' else .8 if v==wanted else .1) for v in ('A','B','U')}
                    rows.append({'persona':pid,'condition':condition,'case_id':case['public']['id'],'log_probs':{k:math.log(v) for k,v in probabilities.items()},'choice':max(probabilities,key=probabilities.get),'label_mass':.9})
        result=summarize(plan,rows,tokens)
        self.assertFalse(diagnose(plan,rows)['degenerate_oracle_decoder'])
        collapsed=[{**row,'choice':'A'} for row in rows]
        diagnostic=diagnose(plan,collapsed)
        self.assertTrue(diagnostic['degenerate_oracle_decoder'])
        self.assertEqual(diagnostic['controls']['oracle']['order_consistency'],0)
        with self.assertRaises(ValueError):diagnose(plan,rows[:-1])
        self.assertAlmostEqual(result['conditions']['compact']['nll_nats'],-math.log(.8))
        self.assertAlmostEqual(result['conditions']['compact']['closed_choice_relative_information_gain'],1+math.log(.8)/math.log(3))
        self.assertAlmostEqual(result['paired_comparisons']['detailed']['compact_token_ratio'],.2)
        self.assertFalse(result['true_person_fidelity_verified'])
        plan['memories']['p01']['compact']=None
        result=summarize(plan,rows,tokens)
        self.assertEqual(result['conditions']['compact']['personas'],5)
        self.assertNotIn('p01',result['paired_comparisons']['detailed']['personas'])

    def test_local_encoder_only_receives_memory_and_public_case(self):
        class Model:
            def __init__(self):self.segments=[]
            def tokenize(self,text,add_bos,special):self.segments.append((text.decode(),special));return list(text)
        model=Model();q={'question':'测试情境','A':'左','B':'右','id':'id'}
        encode(model,'MEMORY',q)
        ordinary=''.join(s for s,sp in model.segments if not sp)
        self.assertIn('MEMORY',ordinary);self.assertIn('测试情境',ordinary)
        self.assertNotIn('gold',ordinary);self.assertNotIn('rollback_guard',ordinary)
        self.assertTrue(any(sp for _,sp in model.segments))
if __name__=='__main__':unittest.main()
