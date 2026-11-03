"""Offline counterexamples only; no model, quote repair or fidelity evidence."""
import copy,importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ref7_plan_test',HERE.parent/'benchmarks/source-id-review-v1/plan.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
r=p.reviewer

def references(value):
 if isinstance(value,list):return [references(v)for v in value]
 if not isinstance(value,dict):return copy.deepcopy(value)
 if set(value)=={'source_id','quote'}:return {'source_id':value['source_id']}
 return {k:references(v)for k,v in value.items()}

class SourceReferenceTests(unittest.TestCase):
 def setUp(self):
  data=p.inputs();self.sources=copy.deepcopy(data['sources']['f7s']);self.draft=copy.deepcopy(data['draft'])
  self.answer=references(self.draft);self.answer['version']=r.VERSION
 def test_whole_message_resolution_preserves_fixed_valid_public_view_without_changing_input(self):
  before=copy.deepcopy(self.answer);s=copy.deepcopy(self.sources)
  files=r.bind(self.answer,self.sources)
  self.assertEqual(files['prompt.md'],p.inputs()['original']);self.assertEqual(len(files['prompt.md']),240)
  self.assertEqual(self.answer,before);self.assertEqual(self.sources,s)
  graph=files['source-reference.private.json']['normalized_graph'];idx={s['id']:s['text']for s in self.sources['sources']}
  def walk(v):
   if isinstance(v,list):
    for x in v:walk(x)
   elif isinstance(v,dict):
    if set(v)=={'source_id','quote'}:self.assertEqual(v['quote'],idx[v['source_id']])
    for x in v.values():walk(x)
  walk(graph);self.assertFalse(files['source-reference.private.json']['semantic_support_verified'])
 def test_unknown_ids_and_generated_quotes_are_rejected_instead_of_repaired(self):
  for fault in ('missing','quote'):
   a=copy.deepcopy(self.answer);ref=a['nodes'][0]['decisions'][0]
   if fault=='missing':ref['source_id']='not-a-source'
   else:ref['quote']='invented'
   with self.assertRaises(ValueError):r.bind(a,self.sources)
 def test_non_user_decision_and_empty_evidence_keep_existing_rejection(self):
  for fault in ('assistant','tool','empty'):
   a=copy.deepcopy(self.answer)
   if fault=='empty':a['nodes'][0]['decisions']=[]
   else:a['nodes'][0]['decisions'][0]['source_id']='m04'if fault=='assistant'else'm06'
   with self.assertRaises(ValueError):r.bind(a,self.sources)
 def test_old_quote_graph_is_not_silently_accepted_by_new_contract(self):
  with self.assertRaises(ValueError):r.bind(self.draft,self.sources)
 def test_large_whole_message_is_rejected_not_truncated(self):
  sid=self.answer['nodes'][0]['decisions'][0]['source_id']
  next(s for s in self.sources['sources']if s['id']==sid)['text']='x'*2001
  with self.assertRaisesRegex(ValueError,'whole message'):r.bind(self.answer,self.sources)
 def test_inheritance_duplicate_object_and_budget_checks_are_still_enforced(self):
  a=copy.deepcopy(self.answer);a['objects'].append(a['objects'][0])
  with self.assertRaises(ValueError):r.bind(a,self.sources)
  with self.assertRaises(ValueError):r.bind(self.answer,self.sources,1)
  a=copy.deepcopy(self.answer);node=a['nodes'][0]
  a['nodes'].append({'id':'bad-parent','kind':'action_revision','parent_id':'absent','action':'保持手动整理',
   'decisions':copy.deepcopy(node['decisions']),'contexts':copy.deepcopy(node['contexts']),
   'relation_evidence':copy.deepcopy(node['decisions']),'order_split':None})
  with self.assertRaises(ValueError):r.bind(a,self.sources)
 def test_source_only_request_contains_original_draft_but_no_reader_feedback(self):
  req=r.make_request(self.sources,self.draft)
  self.assertEqual(req['schema']['properties']['version']['enum'],[r.VERSION])
  self.assertEqual(json.loads(req['prompt'].split('\nREVIEW_DRAFT_JSON:\n')[1]),self.draft)
  body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1].split('\nREVIEW_DRAFT_JSON:\n')[0])
  self.assertEqual(body['sources'],self.sources);self.assertNotIn('e01_ab',req['prompt'])
  def walk(v):
   if isinstance(v,list):
    for x in v:walk(x)
   elif isinstance(v,dict):
    self.assertNotIn('quote',v.get('properties',{}))
    for x in v.values():walk(x)
  walk(req['schema'])
 def test_reference_presence_is_not_a_semantic_certificate(self):
  # A wrong substantive action still binds. This is a counterexample, not a repair.
  self.answer['nodes'][0]['action']='保持手动整理'
  files=r.bind(self.answer,self.sources)
  self.assertFalse(files['source-reference.private.json']['semantic_support_verified'])
  self.assertNotEqual(files['prompt.md'],p.inputs()['original'])
 def test_36_valid_archived_graphs_reencode_without_changing_public_bytes(self):
  checked=0
  for folder in('extraction-readiness-v1','object-coverage-comparison-v1','source-coverage-repeat-v1',
   'ambiguous-source-repeat-v1','remaining-source-repeat-v1'):
   file=p.ROOT/'benchmarks'/folder/'measured.synthetic.json'
   self.assertEqual(p.sha(file),file.with_suffix('.sha256').read_text().strip())
   data=json.loads(file.read_text());records=data['records']if'records'in data else[data['record']]
   for rec in records:
    if'card'not in rec:continue
    sources=json.loads(rec['request']['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])['sources']
    original=json.loads(rec['raw'])
    self.assertEqual(r.legacy.bind(original,sources)['prompt.md'],rec['card']['prompt'])
    candidate=references(original);candidate['version']=r.VERSION
    self.assertEqual(r.bind(candidate,sources)['prompt.md'],rec['card']['prompt'])
    checked+=1
  self.assertEqual(checked,36)
if __name__=='__main__':unittest.main()
