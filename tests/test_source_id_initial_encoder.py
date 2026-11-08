"""Source-ID initial extraction preserves old guards; no model calls or recovery scores."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('initial_id_encoder',ROOT/'benchmarks/source-id-initial-encoding-v1/candidate.py')
f=load('initial_id_fixture',ROOT/'tests/test_scope_alias_encoder.py')

def references(value):
    if isinstance(value,dict):
        if set(value)=={'source_id','quote'}:return dict(source_id=value['source_id'])
        return {k:references(v)for k,v in value.items()}
    if isinstance(value,list):return [references(v)for v in value]
    return value

def example():
    sources,old=f.example();answer=references(old);answer['version']=m.VERSION
    return sources,old,answer

class SourceIDInitialTests(unittest.TestCase):
    def test_request_uses_only_own_sources_budget_and_actual_ID_enums(self):
        sources,_,_=example();r=m.make_request(sources,768)
        body=json.loads(r['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
        self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
        self.assertEqual(body['sources'],sources);self.assertEqual(body['budget_characters'],768)
        def walk(v):
            if isinstance(v,dict):
                if v.get('type')=='object'and set(v.get('properties',{}))=={'source_id'}:
                    self.assertEqual(v['properties']['source_id']['enum'],[s['id']for s in sources['sources']])
                for x in v.values():walk(x)
            elif isinstance(v,list):
                for x in v:walk(x)
        walk(r['schema'])
        self.assertNotIn('reference.private',r['prompt'])
    def test_same_graph_keeps_exact_public_card_and_does_not_modify_inputs(self):
        sources,old,answer=example();before=copy.deepcopy((sources,old,answer))
        self.assertEqual(m.bind(answer,sources)['prompt.md'],m.base.bind(old,sources)['prompt.md'])
        self.assertEqual((sources,old,answer),before)
        self.assertFalse(m.bind(answer,sources)['source-id-initial.private.json']['behavioral_fidelity_verified'])
    def test_model_cannot_supply_freehand_quote_or_foreign_ID(self):
        sources,_,answer=example()
        for key,value in(('quote','additional words'),('source_id','foreign')):
            bad=copy.deepcopy(answer);bad['nodes'][0]['decisions'][0][key]=value
            with self.assertRaises(ValueError):m.bind(bad,sources)
    def test_literal_source_reconstruction_has_no_freehand_suffix(self):
        sources,old,answer=example();old['nodes'][0]['contexts'][0]['quote']+='额外字'
        with self.assertRaisesRegex(ValueError,'exact source quote'):m.base.bind(old,sources)
        resolved=m.resolve(answer,sources)
        self.assertEqual(resolved['nodes'][0]['contexts'][0]['quote'],sources['sources'][0]['text'])
        self.assertNotIn('额外字',resolved['nodes'][0]['contexts'][0]['quote'])
    def test_original_role_action_witness_ownership_and_alias_guards_remain(self):
        sources,_,answer=example()
        for fault in('assistant','missing_action','missing_name','wrong_owner','unclaimed'):
            bad=copy.deepcopy(answer)
            if fault=='assistant':bad['nodes'][0]['decisions'][0]['source_id']='a1'
            elif fault=='missing_action':bad['nodes'][0]['action']='发全版'
            elif fault=='missing_name':bad['object_aliases'][0]['evidence'][0]['source_id']='s1'
            elif fault=='wrong_owner':bad['object_aliases'][0]['object_index']=1
            else:bad['source_accounting']['s3']['alias_ids']=[]
            with self.subTest(fault=fault),self.assertRaises(ValueError):m.bind(bad,sources)
    def test_typed_expansion_does_not_confuse_accounting_key_with_anchor(self):
        sources,_,answer=example()
        sources['sources']=[dict(sources['sources'][0],id='source_id')]
        answer['nodes']=answer['nodes'][:1];answer['objects']=answer['objects'][:1]
        answer['object_aliases']=[]
        answer['source_accounting']={'source_id':answer['source_accounting']['s1']}
        for anchors in(answer['nodes'][0]['decisions'],answer['nodes'][0]['contexts'],answer['nodes'][0]['requires'][0]['evidence']):
            for anchor in anchors:anchor['source_id']='source_id'
        self.assertEqual(set(answer['source_accounting']),{'source_id'})
        self.assertEqual(m.resolve(answer,sources)['source_accounting']['source_id']['kind'],'direct_choice')
        self.assertIn('发简版',m.bind(answer,sources)['prompt.md'])
    def test_whole_public_budget_is_still_exact(self):
        sources,_,answer=example();answer['unknowns'].append(''.join(chr(0x4e00+i)for i in range(140)))
        size=len(m.bind(answer,sources)['prompt.md'])
        self.assertEqual(len(m.bind(answer,sources,size)['prompt.md']),size)
        with self.assertRaises(ValueError):m.bind(answer,sources,300)
    def test_two_measured_valid_alias_graphs_keep_original_public_cards_offline(self):
        data=json.loads((ROOT/'benchmarks/fresh-alias-generalization-v1/measured.synthetic.json').read_text())
        parents=[r for r in data['records']if r['kind']=='extract'and r['method']=='scope-alias-encoding-v1'and r['artifact']]
        self.assertEqual([r['slot']for r in parents],[10,13])
        for parent in parents:
            graph=json.loads(parent['raw']);answer=references(graph);answer['version']=m.VERSION
            source=data['prepared_files']['sources.json'][parent['profile']]
            prompt=m.bind(answer,source)['prompt.md']
            self.assertEqual(prompt,parent['artifact']['prompt'])
            self.assertFalse(m.bind(answer,source)['source-id-initial.private.json']['behavioral_fidelity_verified'])
        # This is graph replay, not a new automatic generation or model read.

    def test_full_message_witness_does_not_certify_semantic_choice_classification(self):
        sources,old,answer=example()
        sources['sources'][0]['text']='有许可时，纸笺候选有发简版、发全版，尚未选择。'
        def full(v):
            if isinstance(v,dict):
                if set(v)=={'source_id','quote'}:
                    return dict(source_id=v['source_id'],quote=next(s['text']for s in sources['sources']if s['id']==v['source_id']))
                return{k:full(x)for k,x in v.items()}
            if isinstance(v,list):return[full(x)for x in v]
            return v
        # This deliberately wrong semantic classification is an existing literal
        # witness limitation, not a new fidelity score or accepted user choice.
        legacy=m.base.bind(full(old),sources)
        proposed=m.bind(answer,sources)
        self.assertEqual(proposed['prompt.md'],legacy['prompt.md'])
        self.assertFalse(proposed['source-id-initial.private.json']['source_reference_semantics_verified'])

    def test_reference_cannot_bypass_original_literal_alias_requirement(self):
        sources,_,answer=example()
        # ID exists but its message does not contain both names. Presence of an
        # ID is not an endorsed identity or a semantic witness.
        answer['object_aliases'][0]['evidence']=[dict(source_id='s5')]
        answer['source_accounting']['s3']['alias_ids']=[];answer['source_accounting']['s5']['alias_ids']=['a0']
        with self.assertRaises(ValueError):m.bind(answer,sources)

if __name__=='__main__':unittest.main()
