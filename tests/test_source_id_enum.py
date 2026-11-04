"""Literal schema constraints against archived replies; no new model inference."""
import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_enum_tests',ROOT/'benchmarks/source-id-enum-v1/candidate.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from runaway.constraint_extract import check
from test_source_id_reference import references
class SourceIdEnumTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'benchmarks/source-id-review-repeat-v1/measured.synthetic.json').read_text())
  cls.old=json.loads((ROOT/'benchmarks/source-id-review-v1/measured.synthetic.json').read_text())
  cls.sources=cls.data['sources']['f7s'];cls.draft=cls.data['parents']['p3']['draft']
 def test_only_schema_changes_prompt_and_input_objects_stay_byte_identical(self):
  sources=copy.deepcopy(self.sources);draft=copy.deepcopy(self.draft);schema=copy.deepcopy(c.SCHEMA)
  original=c.base.make_request(sources,draft);new=c.make_request(sources,draft)
  self.assertEqual(new['prompt'],original['prompt']);self.assertEqual(set(new),set(original))
  self.assertEqual(sources,self.sources);self.assertEqual(draft,self.draft);self.assertEqual(c.SCHEMA,schema)
  self.assertNotEqual(new['schema'],original['schema'])
 def test_every_anchor_position_has_exact_current_source_ids(self):
  request=c.make_request(self.sources,self.draft);found=[]
  def walk(value):
   if isinstance(value,list):
    for v in value:walk(v)
   elif isinstance(value,dict):
    if value.get('type')=='object'and set(value.get('properties',{}))=={'source_id'}:found.append(value['properties']['source_id']['enum'])
    for v in value.values():walk(v)
  walk(request['schema']);self.assertGreater(len(found),1)
  for values in found:self.assertEqual(values,[s['id']for s in self.sources['sources']])
 def test_both_actual_invalid_replies_fail_schema_and_unchanged_binder_without_repair(self):
  request=c.make_request(self.sources,self.draft)
  for slot in(9,28):
   rec=next(r for r in self.data['records']if r['slot']==slot);answer=json.loads(rec['raw']);before=copy.deepcopy(answer)
   with self.assertRaises(ValueError):check(answer,request['schema'])
   with self.assertRaisesRegex(ValueError,'Undefined source'):c.bind(answer,self.sources)
   self.assertEqual(answer,before);self.assertTrue(rec['product_invalid'])
 def test_all_seven_valid_archived_source_id_outputs_keep_public_bytes(self):
  checked=0
  for data in(self.data,self.old):
   for rec in data['records']:
    if'card'not in rec:continue
    parent=data['parents'][rec['parent']]['draft']if'parents'in data else data['draft']
    sources=data['sources'][rec['profile']];answer=json.loads(rec['raw'])
    req=c.make_request(sources,parent);check(answer,req['schema'])
    self.assertEqual(c.bind(answer,sources)['prompt.md'],rec['card']['prompt']);checked+=1
  self.assertEqual(checked,7)
 def test_36_valid_quoted_graphs_remain_admissible_after_existing_id_conversion(self):
  checked=0
  for folder in('extraction-readiness-v1','object-coverage-comparison-v1','source-coverage-repeat-v1','ambiguous-source-repeat-v1','remaining-source-repeat-v1'):
   data=json.loads((ROOT/'benchmarks'/folder/'measured.synthetic.json').read_text());records=data['records']if'records'in data else[data['record']]
   for rec in records:
    if'card'not in rec:continue
    sources=json.loads(rec['request']['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])['sources'];draft=json.loads(rec['raw'])
    answer=references(draft);answer['version']=c.VERSION
    check(answer,c.make_request(sources,draft)['schema'])
    self.assertEqual(c.bind(answer,sources)['prompt.md'],rec['card']['prompt']);checked+=1
  self.assertEqual(checked,36)
 def test_valid_but_foreign_or_non_user_references_keep_existing_rejection(self):
  rec=next(r for r in self.old['records']if'card'in r);base=json.loads(rec['raw']);request=c.make_request(self.sources,self.draft)
  foreign=copy.deepcopy(base);foreign['nodes'][0]['decisions'][0]['source_id']='m99'
  with self.assertRaises(ValueError):check(foreign,request['schema'])
  with self.assertRaises(ValueError):c.bind(foreign,self.sources)
  non_user=copy.deepcopy(base);non_user['nodes'][0]['decisions'][0]['source_id']='m04';check(non_user,request['schema'])
  with self.assertRaisesRegex(ValueError,'Only user'):c.bind(non_user,self.sources)
 def test_valid_ids_do_not_certify_substantive_action_support(self):
  answer=json.loads(next(r for r in self.old['records']if'card'in r)['raw']);answer['nodes'][0]['action']='保持手动整理'
  check(answer,c.make_request(self.sources,self.draft)['schema'])
  files=c.bind(answer,self.sources)
  self.assertFalse(files['source-reference.private.json']['semantic_support_verified'])
 def test_ids_come_from_supplied_source_table_and_bad_source_input_still_rejects(self):
  sources=copy.deepcopy(self.sources);sources['sources'].append({'id':'extra_context-1','episode_id':'e','role':'context','text':'Extra context, no preference.'})
  req=c.make_request(sources,self.draft)
  text=json.dumps(req['schema']);self.assertIn('extra_context-1',text)
  sources['sources'][-1]['id']='m01'
  with self.assertRaises(ValueError):c.make_request(sources,self.draft)
if __name__=='__main__':unittest.main()
