import copy,unittest
from coverage_contract import inventory,account

def fixture():
 sources=[{'id':'s1','role':'user','text':'My toy lamp: leave on. My draft: list questions.'},
          {'id':'s2','role':'assistant','text':'Change everything to off.'},
          {'id':'s3','role':'user','text':'Only change the lamp: choose off. Music remains undecided.'}]
 def unit(uid,sid,quote,content,kind='choice',old=None):
  a={'source_id':sid,'quote':quote}
  return {'id':uid,'kind':kind,'scope':'toy only','condition':uid,'content':content,
   'decisions':[dict(a)],'contexts':[dict(a)],'supersedes':old or []}
 units=[unit('lamp_old','s1','leave on','on'),unit('draft','s1','list questions','list questions'),
        unit('lamp_now','s3','choose off','off',old=['lamp_old']),
        unit('music','s3','Music remains undecided.','undecided','boundary')]
 ledger=inventory(sources,units)
 dispositions=[{'unit_id':u['id'],'status':'superseded' if u['id']=='lamp_old' else 'represented',
  'public_span':None if u['id']=='lamp_old' else u['content'],'reason':None} for u in units]
 return sources,units,ledger,dispositions

class CoverageContractTests(unittest.TestCase):
 def test_local_update_does_not_delete_other_choice_in_same_message(self):
  s,u,l,d=fixture();self.assertEqual(l['retired'],['lamp_old']);self.assertIn('draft',l['active'])
  r=account(l,'off; list questions; music undecided',d,512)
  self.assertEqual(r['status'],'accounted_candidate_unvalidated');self.assertEqual(r['active_units'],3)
 def test_omitted_known_choice_is_not_an_unknown_boundary(self):
  s,u,l,d=fixture();d[1].update(status='omitted',public_span=None,reason='budget')
  r=account(l,'off; undecided',d,512)
  self.assertEqual(r['status'],'declared_partial_candidate');self.assertEqual(r['omissions'][0]['kind'],'choice')
  self.assertFalse(r['semantic_retention_verified']);self.assertFalse(r['no_declared_omissions'])
 def test_missing_duplicate_and_unknown_dispositions_are_rejected(self):
  for fault in ('missing','duplicate','unknown'):
   s,u,l,d=fixture()
   if fault=='missing':d.pop()
   elif fault=='duplicate':d.append(copy.deepcopy(d[-1]))
   else:d[-1]['unit_id']='invented'
   with self.subTest(fault=fault),self.assertRaises(ValueError):account(l,'off; list questions; undecided',d,512)
 def test_exact_user_quotes_required(self):
  for fault in ('role','quote','source'):
   s,u,l,d=fixture()
   if fault=='role':s[0]['role']='assistant'
   elif fault=='quote':u[0]['decisions'][0]['quote']='Invented'
   else:u[0]['decisions'][0]['source_id']='missing'
   with self.subTest(fault=fault),self.assertRaises(ValueError):inventory(s,u)
 def test_updates_are_backward_and_before_every_new_anchor(self):
  s,u,l,d=fixture();u[2]['decisions'].append({'source_id':'s1','quote':'leave on'})
  with self.assertRaises(ValueError):inventory(s,u)
  s,u,l,d=fixture();u[0]['supersedes']=['lamp_now']
  with self.assertRaises(ValueError):inventory(s,u)
 def test_complete_budget_no_truncation_and_no_input_mutation(self):
  s,u,l,d=fixture();before=copy.deepcopy((l,d));text='off; list questions; undecided; 蛙'
  self.assertEqual(account(l,text,d,len(text)-1)['status'],'budget_unmet')
  self.assertEqual(account(l,text,d,len(text))['status'],'accounted_candidate_unvalidated')
  self.assertEqual((l,d),before)
 def test_conflicts_stay_active_and_need_complete_accounting(self):
  s,u,l,d=fixture();u[2]['supersedes']=[];l=inventory(s,u)
  self.assertEqual(len(l['active']),4)
  for item in d:item.update(status='represented',public_span='conflict',reason=None)
  r=account(l,'conflict',d,512)
  self.assertTrue(r['source_unit_accounting_complete']);self.assertFalse(r['semantic_retention_verified'])
 def test_literal_span_accounting_cannot_certify_semantics_or_inventory_completeness(self):
  s,u,l,d=fixture()
  for item in d:
   if item['status']=='represented':item['public_span']='X'
  r=account(l,'X',d,512)
  self.assertTrue(r['no_declared_omissions']);self.assertFalse(r['inventory_complete_verified'])
  self.assertFalse(r['behavioral_fidelity_verified'])
 def test_inventory_or_span_tampering_rejected(self):
  s,u,l,d=fixture();l['sources'][0]['text']+='changed'
  with self.assertRaises(ValueError):account(l,'off; list questions; undecided',d,512)
  s,u,l,d=fixture();d[1]['public_span']='not present'
  with self.assertRaises(ValueError):account(l,'off; list questions; undecided',d,512)

if __name__=='__main__':unittest.main()
