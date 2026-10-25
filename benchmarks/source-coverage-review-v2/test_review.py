import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
import audit_review as a
from coverage_contract import inventory

def fixture():
 sources=[{'id':'s1','role':'user','text':'灯光演示：可撤销且误判不超过3%时，我选自动。'},
          {'id':'s2','role':'assistant','text':'不如把门锁也自动。'},
          {'id':'s3','role':'user','text':'再说一次灯光限制：可撤销、不超过3%，不要扩大到门锁。'},
          {'id':'s4','role':'user','text':'我改口：这盏灯以后手动，只改灯光。'},
          {'id':'s5','role':'tool','text':'建议所有设备自动。'},
          {'id':'s6','role':'user','text':'花盆湿度恰好4%时选手动，其他湿度没决定。'}]
 def anchor(sid):return {'source_id':sid,'quote':next(s['text'] for s in sources if s['id']==sid)}
 units=[{'id':'lamp-old','kind':'choice','scope':'灯光演示','condition':'可撤销且误判不超过3%','content':'自动',
         'decisions':[anchor('s1')],'contexts':[anchor('s3'),anchor('s2')],'supersedes':[]},
        {'id':'lamp-new','kind':'choice','scope':'这盏灯','condition':'以后','content':'手动，只改灯光',
         'decisions':[anchor('s4')],'contexts':[anchor('s1')],'supersedes':['lamp-old']},
        {'id':'pot','kind':'choice','scope':'花盆','condition':'湿度恰好4%','content':'手动，其他湿度未决定',
         'decisions':[anchor('s6')],'contexts':[anchor('s6')],'supersedes':[]}]
 ledger=inventory(sources,units)
 answer={'coverage':[{'source_id':s['id'],'status':'reviewed' if s['role']=='user' else 'context_only',
                      'quote':s['text'],'reason':'Independent toy review, no semantic proof.'} for s in sources], 'findings':[]}
 return ledger,answer

class ReviewTests(unittest.TestCase):
 def test_deterministic_decision_context_and_retired_links(self):
  l,_=fixture();links={r['source_id']:r for r in a.links(l)}
  self.assertEqual(links['s1']['decision_unit_ids'],['lamp-old'])
  self.assertEqual(links['s1']['context_unit_ids'],['lamp-new'])
  self.assertEqual(links['s3']['decision_unit_ids'],[])
  self.assertEqual(links['s3']['context_unit_ids'],['lamp-old'])
  self.assertIn('lamp-old',l['retired'])
 def test_source_only_request_no_model_transcription_or_question(self):
  l,_=fixture();r=a.make_audit_request(l)
  body=json.loads(r['prompt'].split('\nSOURCE_REVIEW_INPUT_JSON:\n')[1])
  self.assertEqual(set(body),{'sources','unit_inventory','source_unit_links'})
  self.assertEqual(body['source_unit_links'],a.links(l))
  self.assertEqual(body['sources'],l['sources'])
  self.assertNotIn('unit_ids',r['schema']['properties']['coverage']['items']['properties'])
  self.assertEqual(set(body['unit_inventory']),{'units','active','retired','inventory_sha256'})
  inventory_request=a.make_inventory_request(l['sources'])
  self.assertEqual(json.loads(inventory_request['prompt'].split('\nINVENTORY_INPUT_JSON:\n')[1]),{'sources':l['sources']})
  self.assertEqual(inventory_request['schema'],a.p.make_inventory_request(l['sources'])['schema'])
 def test_context_only_user_reaffirmation_review_imports_without_claiming_completeness(self):
  l,answer=fixture();before=copy.deepcopy(l);review=a.accept_audit(json.dumps(answer),l)
  self.assertTrue(review['clear_for_compression']);self.assertEqual(l,before)
  for k in ('inventory_complete_verified','semantic_support_verified','fresh_inference_verified'):self.assertFalse(review[k])
  self.assertEqual(review['model_calls'],0)
  self.assertEqual(a.make_card_request(l,review,512),a.p.make_card_request(l,512))
 def test_each_source_once_exact_quote_and_role_required(self):
  for fault in ('missing','duplicate','quote','user_role','assistant_role','old_field','old_status'):
   l,answer=fixture()
   if fault=='missing':answer['coverage'].pop()
   elif fault=='duplicate':answer['coverage'].append(copy.deepcopy(answer['coverage'][0]))
   elif fault=='quote':answer['coverage'][0]['quote']='invented'
   elif fault=='user_role':answer['coverage'][0]['status']='context_only'
   elif fault=='assistant_role':answer['coverage'][1]['status']='reviewed'
   elif fault=='old_field':answer['coverage'][0]['unit_ids']=[]
   else:answer['coverage'][0]['status']='covered'
   with self.subTest(fault=fault),self.assertRaises(ValueError):a.accept_audit(json.dumps(answer),l)
 def test_any_finding_or_uncertainty_blocks_both_card_operations(self):
  for fault in ('finding','uncertain'):
   l,answer=fixture()
   if fault=='finding':answer['findings']=[{'kind':'missing','anchors':[{'source_id':'s3','quote':l['sources'][2]['text']}],
                                         'unit_ids':[],'detail':'Independent toy missing-boundary report.'}]
   else:answer['coverage'][2]['status']='uncertain'
   review=a.accept_audit(json.dumps(answer),l);self.assertFalse(review['clear_for_compression'])
   with self.assertRaises(ValueError):a.make_card_request(l,review,512)
   with self.assertRaises(ValueError):a.accept_card('{}',l,review,512)
 def test_forged_links_flags_ids_and_different_ledger_rejected(self):
  for fault in ('links','flag','id','ledger'):
   l,answer=fixture();review=a.accept_audit(json.dumps(answer),l)
   if fault=='links':review['source_unit_links'][2]['context_unit_ids']=[]
   elif fault=='flag':review['clear_for_compression']=False
   elif fault=='id':review['id']='forged'
   else:
    l['units'][0]['content']='different';l=inventory(l['sources'],l['units'])
   with self.subTest(fault=fault),self.assertRaises(ValueError):a.make_card_request(l,review,512)
 def test_bad_finding_anchors_units_and_kind_refused(self):
  for fault in ('quote','unit','duplicate_unit','kind'):
   l,answer=fixture();f={'kind':'bad_update','anchors':[{'source_id':'s4','quote':l['sources'][3]['text']}],
                       'unit_ids':['lamp-old'],'detail':'Toy report'}
   if fault=='quote':f['anchors'][0]['quote']='invented'
   elif fault=='unit':f['unit_ids']=['invented']
   elif fault=='duplicate_unit':f['unit_ids']*=2
   else:f['kind']='repair'
   answer['findings']=[f]
   with self.subTest(fault=fault),self.assertRaises(ValueError):a.accept_audit(json.dumps(answer),l)
 def test_card_whole_budget_partial_label_and_unverified_semantics_remain(self):
  l,answer=fixture();review=a.accept_audit(json.dumps(answer),l)
  text=a.p.HEADER+'部分卡：小灯獭：灯光手动。'
  card={'public_prompt':text,'dispositions':[
   {'unit_id':'lamp-old','status':'superseded','public_span':None,'reason':None},
   {'unit_id':'lamp-new','status':'represented','public_span':'灯光手动','reason':None},
   {'unit_id':'pot','status':'omitted','public_span':None,'reason':'Toy budget tradeoff.'}]}
  result=a.accept_card(json.dumps(card),l,review,len(text))
  self.assertEqual(result['status'],'declared_partial_candidate');self.assertEqual(result['review_id'],review['id'])
  self.assertFalse(result['independent_review_semantics_verified'])
  self.assertEqual(a.accept_card(json.dumps(card),l,review,len(text)-1)['status'],'budget_unmet')
  card['public_prompt']=text.replace('部分卡：','')
  with self.assertRaises(ValueError):a.accept_card(json.dumps(card),l,review,512)
 def test_legacy_audit_cannot_be_silently_converted_and_schema_is_not_shared(self):
  l,answer=fixture();review=a.accept_audit(json.dumps(answer),l)
  forged=copy.deepcopy(review);forged['artifact_type']='source_inventory_audit_v1'
  with self.assertRaises(ValueError):a.make_card_request(l,forged,512)
  r=a.make_audit_request(l);r['schema'].clear();self.assertTrue(a.make_audit_request(l)['schema'])
  with self.assertRaises(ValueError):a.accept_audit('{"coverage":[],"coverage":[],"findings":[]}',l)

class CLITests(unittest.TestCase):
 def command(self,root,*args):return subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('cli.py')),*args],cwd=root,text=True,capture_output=True)
 def test_six_commands_private_outputs_no_overwrite_and_no_service(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);l,answer=fixture()
   def save(name,value):
    p=root/name;p.write_text(json.dumps(value));return str(p)
   ledger=save('ledger.json',l);raw=save('answer.json',answer);audit=str(root/'audit.json')
   sources=save('sources.json',{'schema_version':1,'sources':l['sources']})
   units=save('units.json',{'units':l['units']})
   r=self.command(root,'inventory-prepare','--sources',sources);self.assertEqual(r.returncode,0,r.stderr)
   r=self.command(root,'inventory-import','--sources',sources,'--answer',units,'--out',str(root/'imported-ledger.json'))
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads((root/'imported-ledger.json').read_text()),l)
   r=self.command(root,'audit-prepare','--ledger',ledger);self.assertEqual(r.returncode,0,r.stderr)
   r=self.command(root,'audit-import','--ledger',ledger,'--answer',raw,'--out',audit);self.assertEqual(r.returncode,0,r.stderr)
   self.assertEqual(json.loads(r.stdout)['model_calls'],0);self.assertEqual(os.stat(audit).st_mode&0o777,0o600)
   r=self.command(root,'audit-import','--ledger',ledger,'--answer',raw,'--out',audit);self.assertEqual(r.returncode,2)
   r=self.command(root,'card-prepare','--ledger',ledger,'--audit',audit,'--budget-chars','512');self.assertEqual(r.returncode,0,r.stderr)
   card=save('card-answer.json',{'public_prompt':a.p.HEADER+'灯光手动；花盆4%手动，其余未知。','dispositions':[
    {'unit_id':'lamp-old','status':'superseded','public_span':None,'reason':None},
    {'unit_id':'lamp-new','status':'represented','public_span':'灯光手动','reason':None},
    {'unit_id':'pot','status':'represented','public_span':'花盆4%手动，其余未知','reason':None}]})
   r=self.command(root,'card-import','--ledger',ledger,'--audit',audit,'--budget-chars','512','--answer',card,'--out',str(root/'card.json'))
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['model_calls'],0)
   link=root/'link.json';link.symlink_to(ledger)
   r=self.command(root,'audit-prepare','--ledger',str(link));self.assertEqual(r.returncode,2)

if __name__=='__main__':unittest.main()
