"""Literal/provenance/guard conservation,not semantic equivalence or LLM behavior."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('order_target_tests', ROOT/'benchmarks/order-targets-v1/prototype.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


def fixture():
    texts = {'s1': '路线可选走长廊或坐摆渡船；另有先给候选让对方挑的礼物安排。',
             's2': '在活动日且已获入园许可时，我先走长廊。',
             's3': '此前已走过长廊；先不发布也是给出的选项。', 's4': '助手猜测可免许可。'}
    source = {'schema_version':1, 'sources':[{'id':k,'episode_id':'toy','role':'assistant' if k=='s4' else 'user','text':v} for k,v in texts.items()]}
    def a(s): return {'source_id':s,'quote':texts[s]}
    row = {'object':'活动路线','question':'路线选择','requires':[{'text':x,'evidence':[a('s2')]} for x in ('活动日','已获入园许可')],
           'action':'先走长廊','priority':1,'decisions':[a('s2')],'contexts':[a('s1')],'supersedes':[]}
    past = dict(copy.deepcopy(row),question='既往事实',action='此前已走过长廊',requires=[],decisions=[a('s3')])
    gift = dict(copy.deepcopy(row),object='礼物',question='礼物选择',action='先给候选让对方挑',requires=[],decisions=[a('s1')])
    ledger = {'version':c.b.VERSION,'name':'长廊团','tagline':'方法和先后都带着。','rows':[row,past,gift],'unknowns':['未覆盖或缺许可时未知。']}
    bindings = [{'row_index':0,'core_action':'走长廊','core_evidence':[a('s1')],'execution_question':'执行先后'}]
    return source,ledger,bindings


class OrderTargetTests(unittest.TestCase):
    def test_explicit_mapping_retains_full_action_and_all_other_rows(self):
        s,l,b = fixture(); before = copy.deepcopy(l); after,trace = c.separate(l,s,b)
        self.assertEqual(after['rows'][0]['action'],'走长廊')
        self.assertEqual(after['rows'][-1]['action'],'先走长廊')
        self.assertEqual(after['rows'][1:3],l['rows'][1:])
        self.assertEqual(after['rows'][-1]['requires'],l['rows'][0]['requires'])
        self.assertEqual(after['rows'][-1]['priority'],1)
        self.assertEqual(l,before)
        self.assertFalse(trace['semantic_decomposition_independently_accepted'])

    def test_permission_and_event_guards_hold_on_both_targets_in_all_four_worlds(self):
        s,l,b = fixture(); after,_ = c.separate(l,s,b)
        for permission in (False,True):
            for event in (False,True):
                facts={'已获入园许可':permission,'活动日':event}
                for q,action in [('路线选择','走长廊'),('执行先后','先走长廊')]:
                    values={r['action'] for r in after['rows'] if r['question']==q and all(facts[x['text']] for x in r['requires'])}
                    self.assertEqual(values,{action} if permission and event else set())

    def test_negation_is_never_removed_and_unbound_ordered_gift_stays_intact(self):
        s,l,b = fixture(); l['rows'][0].update(action='先不发布',decisions=[{'source_id':'s3','quote':s['sources'][2]['text']}])
        b[0].update(core_action='不发布',core_evidence=[{'source_id':'s3','quote':s['sources'][2]['text']}])
        after,_=c.separate(l,s,b)
        self.assertEqual(after['rows'][0]['action'],'不发布')
        self.assertEqual(after['rows'][-1]['action'],'先不发布')
        self.assertEqual(after['rows'][2]['action'],'先给候选让对方挑')
        b[0]['core_action']='发布'
        with self.assertRaises(ValueError): c.separate(l,s,b)

    def test_bad_binding_quote_label_index_collision_and_duplicates_rejected(self):
        for fault in ('quote','label','index','bool','collision','duplicate','extra'):
            s,l,b=fixture()
            if fault=='quote': b[0]['core_evidence'][0]['quote']='invented'
            elif fault=='label': b[0]['core_action']='不存在的方法'
            elif fault=='index': b[0]['row_index']=29
            elif fault=='bool': b[0]['row_index']=False
            elif fault=='collision': b[0]['execution_question']='既往事实'
            elif fault=='duplicate': b.append(copy.deepcopy(b[0]))
            else: b[0]['unexpected']='field'
            with self.subTest(fault=fault),self.assertRaises(ValueError): c.separate(l,s,b)

    def test_public_binding_and_budget_keep_ordering_text_and_unverified_semantics(self):
        s,l,b=fixture(); f=c.bind(l,s,b)
        self.assertIn('→走长廊',f['prompt.md']);self.assertIn('→先走长廊',f['prompt.md'])
        self.assertFalse(f['summary.private.json']['old_semantic_equivalence_verified'])
        self.assertTrue(f['summary.private.json']['semantic_projection_roundtrip_exact'])
        with self.assertRaises(ValueError): c.bind(l,s,b,1)

    def test_assistant_guess_cannot_become_a_user_choice(self):
        s,l,b=fixture();l['rows'][0]['decisions']=[{'source_id':'s4','quote':s['sources'][3]['text']}]
        with self.assertRaises(ValueError): c.separate(l,s,b)


if __name__=='__main__':unittest.main()
