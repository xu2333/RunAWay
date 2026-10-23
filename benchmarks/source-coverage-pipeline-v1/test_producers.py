import copy,json,unittest
import producers as p
from coverage_contract import inventory

def toy():
 sources=[{'id':'u1','role':'user','text':'Only this toy light: off. Only this draft: questions.'}]
 def unit(uid,quote):
  anchor={'source_id':'u1','quote':quote}
  return {'id':uid,'kind':'choice','scope':'toy only','condition':uid,'content':quote,
   'decisions':[dict(anchor)],'contexts':[dict(anchor)],'supersedes':[]}
 units=[unit('light','off'),unit('draft','questions')]
 return sources,units,inventory(sources,units)

class ProducerTests(unittest.TestCase):
 def test_inventory_input_is_source_only_without_public_questions_or_budget(self):
  sources,units,ledger=toy();r=p.make_inventory_request(sources)
  body=json.loads(r['prompt'].split('\nINVENTORY_INPUT_JSON:\n')[1]);self.assertEqual(body,{'sources':sources})
  with self.assertRaises(TypeError):p.make_inventory_request(sources,queries=[])
 def test_import_inventory_checks_roles_quotes_and_duplicate_json(self):
  sources,units,ledger=toy();self.assertEqual(p.accept_inventory(json.dumps({'units':units}),sources),ledger)
  with self.assertRaises(ValueError):p.accept_inventory('{"units":[],"units":[]}',sources)
  sources[0]['role']='assistant'
  with self.assertRaises(ValueError):p.accept_inventory(json.dumps({'units':units}),sources)
 def test_compressor_sees_only_validated_inventory_and_counted_budget(self):
  sources,units,ledger=toy();r=p.make_card_request(ledger,512)
  body=json.loads(r['prompt'].split('\nCARD_INPUT_JSON:\n')[1]);self.assertEqual(set(body),{'unit_inventory','whole_budget_characters','required_public_header'})
  self.assertEqual(set(body['unit_inventory']),{'units','active','retired','inventory_sha256'})
  self.assertEqual(body['whole_budget_characters'],512);self.assertEqual(body['required_public_header'],p.HEADER)
 def test_complete_card_round_trip_keeps_unverified_semantics(self):
  sources,units,ledger=toy();text=p.HEADER+'Toy: off; questions'
  d=[{'unit_id':u['id'],'status':'represented','public_span':u['content'],'reason':None} for u in units]
  r=p.accept_card(json.dumps({'public_prompt':text,'dispositions':d}),ledger,len(text))
  self.assertEqual(r['prompt'],text);self.assertEqual(r['status'],'accounted_candidate_unvalidated')
  self.assertFalse(r['semantic_retention_verified']);self.assertFalse(r['portable_export_implemented'])
  self.assertEqual(p.accept_card(json.dumps({'public_prompt':text,'dispositions':d}),ledger,len(text)-1)['status'],'budget_unmet')
 def test_omission_needs_public_partial_label_and_is_not_known_fidelity(self):
  sources,units,ledger=toy();d=[{'unit_id':'light','status':'represented','public_span':'off','reason':None},
   {'unit_id':'draft','status':'omitted','public_span':None,'reason':'budget'}]
  with self.assertRaises(ValueError):p.accept_card(json.dumps({'public_prompt':p.HEADER+'off','dispositions':d}),ledger,512)
  r=p.accept_card(json.dumps({'public_prompt':p.HEADER+'部分卡：off','dispositions':d}),ledger,512)
  self.assertEqual(r['status'],'declared_partial_candidate');self.assertFalse(r['behavioral_fidelity_verified'])
 def test_damaged_ledger_and_oversize_source_fail_without_request_or_service(self):
  sources,units,ledger=toy();ledger['units'][0]['content']='changed'
  with self.assertRaises(ValueError):p.make_card_request(ledger,512)
  sources[0]['text']='z'*65000
  with self.assertRaises(ValueError):p.make_inventory_request(sources)
 def test_schema_copies_are_independent_and_nonfinite_json_refused(self):
  sources,units,ledger=toy();r=p.make_inventory_request(sources);r['schema'].clear()
  self.assertTrue(p.make_inventory_request(sources)['schema'])
  r=p.make_card_request(ledger,512);r['schema'].clear();self.assertTrue(p.make_card_request(ledger,512)['schema'])
  with self.assertRaises(ValueError):p.parse('{"number":NaN}')

if __name__=='__main__':unittest.main()
