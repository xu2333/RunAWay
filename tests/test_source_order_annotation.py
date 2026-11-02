"""Model-annotation plumbing and damage controls;no generation/fidelity claim."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


c=load('source_order_annotation_tests',ROOT/'benchmarks/source-order-v3/candidate.py')
toy=load('source_order_annotation_toy',ROOT/'tests/test_order_targets.py')


def fixture():
    sources,ledger,bindings=toy.fixture();objects=list(dict.fromkeys(r['object'] for r in ledger['rows']))
    nodes=[]
    for i,row in enumerate(ledger['rows']):
        node={'id':'n%d'%i,'kind':'base','target_kind':'status' if i==1 else 'choice',
            'object_index':objects.index(row['object']),**{k:copy.deepcopy(row[k]) for k in
            ('question','requires','action','priority','decisions','contexts')},'order_split':None}
        if i==0:node['order_split']={k:copy.deepcopy(v) for k,v in bindings[0].items() if k!='row_index'}
        nodes.append(node)
    return sources,{'version':c.VERSION,'name':ledger['name'],'tagline':ledger['tagline'],
                    'objects':objects,'nodes':nodes,'unknowns':ledger['unknowns']}


class SourceOrderAnnotationTests(unittest.TestCase):
    def test_source_only_wire_has_no_manual_row_or_question_input(self):
        sources,_=fixture();req=c.make_request(sources)
        body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
        self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
        self.assertEqual(body['sources'],sources)
        self.assertNotIn('row_index',json.dumps(req['schema']))
        self.assertNotIn('约定固定安静时段',c.GUIDANCE)
        self.assertNotIn('w11',c.GUIDANCE)

    def test_node_annotation_produces_both_targets_with_model_origin_and_all_guards(self):
        sources,answer=fixture();before=copy.deepcopy(answer);f=c.bind(answer,sources)
        self.assertIn('→走长廊',f['prompt.md']);self.assertIn('→先走长廊',f['prompt.md'])
        self.assertFalse(f['decomposition.private.json']['developer_annotation_not_model_inference'])
        self.assertTrue(f['decomposition.private.json']['model_generated_annotation'])
        self.assertEqual(f['summary.private.json']['active_order_splits'],1)
        self.assertFalse(f['source-order.private.json']['semantic_action_assignment_verified'])
        rows=f['profile.private.json']['ledger']['rows']
        self.assertEqual(rows[0]['requires'],rows[-1]['requires'])
        self.assertEqual(answer,before)

    def test_superseded_decomposition_is_not_copied_to_new_action_and_past_fact_survives(self):
        sources,a=fixture();text='同情境我现在先坐摆渡船；原条件和已经发生的事实不变。'
        sources['sources'].append({'id':'s5','episode_id':'toy','role':'user','text':text})
        anchor={'source_id':'s5','quote':text}
        offered={'source_id':'s1','quote':sources['sources'][0]['text']}
        a['nodes'].append({'id':'new','kind':'action_revision','parent_id':'n0','action':'先坐摆渡船',
            'decisions':[anchor],'contexts':[anchor],'relation_evidence':[anchor],
            'order_split':{'core_action':'坐摆渡船','core_evidence':[offered],'execution_question':'执行先后'}})
        f=c.bind(a,sources)
        self.assertEqual(f['source-order.private.json']['full_ordered_actions'],['先坐摆渡船'])
        self.assertNotIn('→先走长廊',f['prompt.md'])
        self.assertIn('此前已走过长廊',f['prompt.md'])
        self.assertIn('→先给候选让对方挑',f['prompt.md'])

    def test_null_annotation_does_not_silently_fill_in_a_split_or_damage(self):
        s,a=fixture();a['nodes'][0]['order_split']=None;f=c.bind(a,s)
        self.assertEqual(f['summary.private.json']['active_order_splits'],0)
        self.assertIn('→先走长廊',f['prompt.md'])
        self.assertEqual(c.erase_order_targets(f),{'eligible':False,'reason':'no_active_generated_order_split'})

    def test_erasure_only_removes_generated_execution_target_and_keeps_choices_guards_other_order(self):
        s,a=fixture();f=c.bind(a,s);damage=c.erase_order_targets(f)
        self.assertTrue(damage['eligible'])
        value=c.graph.dense.parse(damage['prompt'])
        self.assertNotIn('先走长廊',damage['prompt'])
        self.assertIn('→走长廊',damage['prompt'])
        self.assertIn('→先给候选让对方挑',damage['prompt'])
        self.assertIn('已获入园许可',damage['prompt'])
        self.assertFalse(damage['semantic_erasure_proven'])
        self.assertEqual(len(damage['removed_execution_rows']),1)

    def test_redundant_order_literal_is_ineligible_not_stripped_or_repaired(self):
        s,a=fixture();a['unknowns'].append('另处仍记录先走长廊。');f=c.bind(a,s)
        self.assertEqual(c.erase_order_targets(f),{'eligible':False,'reason':'ordered_literal_remains_outside_designated_targets'})
        self.assertIn('另处仍记录先走长廊',f['prompt.md'])

    def test_status_bad_source_binding_and_budget_fail_without_repair(self):
        for fault in ('status','quote','core','budget'):
            s,a=fixture()
            if fault=='status':a['nodes'][1]['order_split']=copy.deepcopy(a['nodes'][0]['order_split'])
            elif fault=='quote':a['nodes'][0]['order_split']['core_evidence'][0]['quote']='invented'
            elif fault=='core':a['nodes'][0]['order_split']['core_action']='删除否定词'
            with self.subTest(fault=fault),self.assertRaises(ValueError):c.bind(a,s,1 if fault=='budget' else 1536)

    def test_inactive_annotation_quotes_are_still_checked(self):
        s,a=fixture();text='同情境改为坐摆渡船，原条件不变。'
        s['sources'].append({'id':'s5','episode_id':'toy','role':'user','text':text})
        anchor={'source_id':'s5','quote':text}
        a['nodes'].append({'id':'new','kind':'action_revision','parent_id':'n0','action':'坐摆渡船',
            'decisions':[anchor],'contexts':[anchor],'relation_evidence':[anchor],'order_split':None})
        a['nodes'][0]['order_split']['core_evidence'][0]['quote']='invented even though inactive'
        with self.assertRaises(ValueError):c.bind(a,s)


if __name__=='__main__':unittest.main()
