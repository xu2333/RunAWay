import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
import auditing as a
import producers as p
from coverage_contract import inventory
from test_coverage_contract import fixture

def clear_answer(ledger):
 rows=[]
 for source in ledger['sources']:
  ids=[u['id'] for u in ledger['units'] if any(x['source_id']==source['id'] for x in u['decisions'])]
  rows.append({'source_id':source['id'],'status':'context_only' if source['role']!='user' else 'covered' if ids else 'not_a_choice',
   'unit_ids':ids,'quote':source['text'],'reason':'Independent toy review; no fidelity proof.'})
 return {'coverage':rows,'findings':[]}

class AuditTests(unittest.TestCase):
 def test_source_only_request_and_bound_clear_import(self):
  s,u,l,d=fixture();req=a.make_audit_request(l);body=json.loads(req['prompt'].split('\nAUDIT_INPUT_JSON:\n')[1])
  self.assertEqual(set(body),{'sources','unit_inventory'});self.assertEqual(body['sources'],s)
  result=a.accept_audit(json.dumps(clear_answer(l)),l);self.assertTrue(result['clear_for_compression'])
  self.assertFalse(result['inventory_complete_verified']);self.assertFalse(result['fresh_inference_verified'])
  self.assertEqual(a.make_card_request(l,result,512),p.make_card_request(l,512))
 def test_all_sources_required_once_and_all_units_in_same_message_addressed(self):
  for fault in ('missing','duplicate','unit','status'):
   s,u,l,d=fixture();answer=clear_answer(l)
   if fault=='missing':answer['coverage'].pop()
   elif fault=='duplicate':answer['coverage'].append(copy.deepcopy(answer['coverage'][0]))
   elif fault=='unit':answer['coverage'][0]['unit_ids'].pop()
   else:answer['coverage'][0]['status']='not_a_choice'
   with self.subTest(fault=fault),self.assertRaises(ValueError):a.accept_audit(json.dumps(answer),l)
 def test_finding_blocks_compression_without_repairing_inventory(self):
  s,u,l,d=fixture();before=copy.deepcopy(l);answer=clear_answer(l)
  answer['findings']=[{'kind':'uncertain','anchors':[{'source_id':'s1','quote':'My draft: list questions.'}],
   'unit_ids':['draft'],'detail':'Toy uncertainty; do not silently rewrite source units.'}]
  audited=a.accept_audit(json.dumps(answer),l);self.assertFalse(audited['clear_for_compression'])
  with self.assertRaises(ValueError):a.make_card_request(l,audited,512)
  self.assertEqual(l,before)
 def test_uncertainty_blocks_even_without_findings(self):
  s,u,l,d=fixture();answer=clear_answer(l);answer['coverage'][0]['status']='uncertain'
  result=a.accept_audit(json.dumps(answer),l);self.assertEqual(result['status'],'audit_flagged')
  with self.assertRaises(ValueError):a.make_card_request(l,result,512)
 def test_role_quotes_and_finding_units_cannot_be_forged(self):
  for fault in ('context','quote','anchor','unit','kind'):
   s,u,l,d=fixture();answer=clear_answer(l)
   if fault=='context':answer['coverage'][1]['status']='covered'
   elif fault=='quote':answer['coverage'][0]['quote']='Invented'
   else:
    answer['findings']=[{'kind':'missing','anchors':[{'source_id':'s1','quote':'leave on'}],'unit_ids':[],'detail':'Toy review'}]
    if fault=='anchor':answer['findings'][0]['anchors'][0]['quote']='Invented'
    elif fault=='unit':answer['findings'][0]['unit_ids']=['invented']
    else:answer['findings'][0]['kind']='fix_it'
   with self.subTest(fault=fault),self.assertRaises(ValueError):a.accept_audit(json.dumps(answer),l)
 def test_forged_clear_flag_or_different_ledger_rejected(self):
  s,u,l,d=fixture();audited=a.accept_audit(json.dumps(clear_answer(l)),l)
  damaged=copy.deepcopy(audited);damaged['clear_for_compression']=False
  with self.assertRaises(ValueError):a.make_card_request(l,damaged,512)
  l2=copy.deepcopy(l);l2['units'][0]['content']='different';l2=inventory(l2['sources'],l2['units'])
  with self.assertRaises(ValueError):a.make_card_request(l2,audited,512)
 def test_counted_partial_card_and_budget_gate_remain_unverified(self):
  s,u,l,d=fixture();audited=a.accept_audit(json.dumps(clear_answer(l)),l)
  text=p.HEADER+'off; list questions; undecided';answer={'public_prompt':text,'dispositions':d}
  result=a.accept_card(json.dumps(answer),l,audited,len(text))
  self.assertEqual(result['audit_id'],audited['id']);self.assertFalse(result['independent_audit_semantics_verified'])
  self.assertEqual(a.accept_card(json.dumps(answer),l,audited,len(text)-1)['status'],'budget_unmet')
 def test_episode_metadata_is_preserved_and_part_of_source_binding(self):
  s,u,l,d=fixture()
  for source in s:source['episode_id']='toy-episode'
  l=inventory(s,u);req=p.make_inventory_request(s);body=json.loads(req['prompt'].split('\nINVENTORY_INPUT_JSON:\n')[1])
  self.assertEqual(body['sources'],s);a.make_audit_request(l)
  l['sources'][0]['episode_id']='changed'
  with self.assertRaises(ValueError):a.make_audit_request(l)
 def test_schema_mutation_and_duplicate_json_do_not_change_contract(self):
  s,u,l,d=fixture();request=a.make_audit_request(l);request['schema'].clear();self.assertTrue(a.make_audit_request(l)['schema'])
  with self.assertRaises(ValueError):a.accept_audit('{"coverage":[],"coverage":[],"findings":[]}',l)

class CLITests(unittest.TestCase):
 def command(self,root,*args):
  return subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('cli.py')),*args],cwd=root,text=True,capture_output=True)
 def write(self,root,name,value):
  path=root/name;path.write_text(json.dumps(value));return str(path)
 def test_all_six_commands_zero_call_and_private_no_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s,u,l,d=fixture()
   for source in s:source['episode_id']='toy'
   l=inventory(s,u)
   sources=self.write(root,'sources.json',{'schema_version':1,'sources':s});answer=self.write(root,'inventory.json',{'units':u})
   ledger=str(root/'ledger.json');r=self.command(root,'inventory-prepare','--sources',sources);self.assertEqual(r.returncode,0,r.stderr)
   r=self.command(root,'inventory-import','--sources',sources,'--answer',answer,'--out',ledger);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['model_calls'],0)
   self.assertEqual(os.stat(ledger).st_mode & 0o777,0o600)
   r=self.command(root,'inventory-import','--sources',sources,'--answer',answer,'--out',ledger);self.assertEqual(r.returncode,2)
   r=self.command(root,'audit-prepare','--ledger',ledger);self.assertEqual(r.returncode,0,r.stderr)
   audit_answer=self.write(root,'audit-answer.json',clear_answer(l));audit_file=str(root/'audit.json')
   r=self.command(root,'audit-import','--ledger',ledger,'--answer',audit_answer,'--out',audit_file);self.assertEqual(r.returncode,0,r.stderr)
   r=self.command(root,'card-prepare','--ledger',ledger,'--audit',audit_file,'--budget-chars','512');self.assertEqual(r.returncode,0,r.stderr)
   card=self.write(root,'card-answer.json',{'public_prompt':p.HEADER+'off; list questions; undecided','dispositions':d})
   r=self.command(root,'card-import','--ledger',ledger,'--audit',audit_file,'--budget-chars','512','--answer',card,'--out',str(root/'card.json'));self.assertEqual(r.returncode,0,r.stderr)
   self.assertEqual(json.loads(r.stdout)['model_calls'],0)
 def test_flagged_audit_and_duplicate_or_symlink_inputs_fail_without_output(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s,u,l,d=fixture();answer=clear_answer(l);answer['coverage'][0]['status']='uncertain'
   ledger=self.write(root,'ledger.json',l);audit_file=self.write(root,'audit.json',a.accept_audit(json.dumps(answer),l))
   r=self.command(root,'card-prepare','--ledger',ledger,'--audit',audit_file,'--budget-chars','512');self.assertEqual(r.returncode,2)
   duplicate=root/'duplicate.json';duplicate.write_text('{"schema_version":1,"schema_version":1,"sources":[]}')
   r=self.command(root,'inventory-prepare','--sources',str(duplicate));self.assertEqual(r.returncode,2)
   symlink=root/'link.json';symlink.symlink_to(duplicate)
   r=self.command(root,'inventory-prepare','--sources',str(symlink));self.assertEqual(r.returncode,2)

if __name__=='__main__':unittest.main()
