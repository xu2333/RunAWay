"""New source-only grouped contract: independent authored toys, no model service."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from runaway import grouped_support as g,support_extract as old
from runaway.card import canonical,digest
from runaway.portable import validate_expression,render_expression
from runaway.prompt_codec import unpack
ROOT=Path(__file__).resolve().parents[1]

def sources():
 return {'schema_version':1,'sources':[
 {'id':'s1','episode_id':'lamp','role':'user','text':'只讨论会议室的玩具灯，仅本地调节且能完整恢复；电量充足时可以照常工作。'},
 {'id':'s2','episode_id':'old','role':'user','text':'之前我要求会议室无人时开灯；另一件事：熟悉背景的内部同组草稿，先列问题。'},
 {'id':'s3','episode_id':'lamp','role':'assistant','text':'我建议关灯。'},
 {'id':'s4','episode_id':'lamp','role':'user','text':'会议室无人且电量充足时，现在改成关灯，旧选择作废；只改玩具灯，草稿安排不变。'},
 {'id':'s5','episode_id':'lamp','role':'user','text':'如果电量低，先移去充电，不继续照明。'},
 {'id':'s6','episode_id':'lamp','role':'user','text':'如果过热，等降温最优先，先不充电。'},
 {'id':'s7','episode_id':'draft','role':'user','text':'草稿范围是内部同组、彼此熟悉背景，不是陌生作者的公开评审。'}]}

def answer():
 src=sources();index={s['id']:s for s in src['sources']}
 anchor=lambda sid:{'source_id':sid,'quote':index[sid]['text']}
 def rule(when,choose,p,sid,sup=()):return {'when':when,'choose':choose,'priority':p,'decisions':[anchor(sid)],'contexts':[anchor('s1')],'supersedes':list(sup)}
 return {'name':'抱着小电池的团子','tagline':'先降温，别把灯规套到稿子上。','groups':[
  {'scope':'会议室玩具灯，仅本地调节且可完整恢复','contexts':[anchor('s1')],'rules':[
   rule('无人且电量充足','关灯',0,'s4',['s2']),rule('电量低','移去充电',5,'s5'),rule('过热','等降温',9,'s6')]},
  {'scope':'熟悉背景的内部同组草稿','contexts':[anchor('s7')],'rules':[{
   'when':'反馈文字','choose':'先列问题','priority':0,'decisions':[anchor('s2')],'contexts':[anchor('s7')],'supersedes':[]}]}],
  'unknowns':['其他灯具、草稿受众与未记录条件未知。']}

class GroupedSupportTests(unittest.TestCase):
 def setUp(self):self.sources=sources();self.answer=answer()
 def test_source_only_request_counts_header_and_independent_schema(self):
  before=copy.deepcopy(old.SCHEMA);req=g.make_request(self.sources,512)
  body=json.loads(req['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
  self.assertEqual(body,{'sources':self.sources,'budget_characters':512,'fixed_header':g.HEADER,'fixed_guide':g.GUIDE})
  self.assertEqual(set(req),{'prompt','schema'});req['schema']['required'].clear()
  self.assertTrue(g.make_request(self.sources)['schema']['required']);self.assertEqual(old.SCHEMA,before)
  with self.assertRaises(TypeError):g.make_request(self.sources,512,gold={})
 def test_scope_once_explicit_priority_all_actions_and_exact_public_roundtrip(self):
  f=g.bind(self.answer,self.sources,768);text=f['prompt.md'];public=g.projection(self.answer)
  self.assertEqual(g.parse_public(f['expanded.private.md']),public)
  self.assertEqual(text.count(self.answer['groups'][0]['scope']),1)
  for p in ('P0 ','P5 ','P9 '):self.assertIn(p,text)
  self.assertEqual(f['summary.private.json']['rules'],4)
  self.assertIn('范围与行内条件须同时成立',text);self.assertIn('同P冲突未知',text)
  self.assertNotIn('source_id',text);self.assertNotIn('supersedes',text)
 def test_quote_role_and_scope_anchor_damage_rejected(self):
  for fault in ('scope','context','decision','assistant'):
   a=copy.deepcopy(self.answer);r=a['groups'][0]['rules'][0]
   if fault=='scope':a['groups'][0]['contexts'][0]['quote']='not in source'
   elif fault=='context':r['contexts'][0]['quote']='not in source'
   elif fault=='decision':r['decisions'][0]['quote']='not in source'
   else:r['decisions']=[{'source_id':'s3','quote':self.sources['sources'][2]['text']}]
   with self.subTest(fault=fault),self.assertRaises(ValueError):g.bind(a,self.sources)
 def test_supersession_is_local_and_never_globally_deletes_old_source(self):
  f=g.bind(self.answer,self.sources)
  self.assertIn('先列问题',f['prompt.md']);self.assertIn('关灯',f['prompt.md'])
  self.assertEqual(f['profile.private.json']['answer']['groups'][1]['rules'][0]['decisions'][0]['source_id'],'s2')
  self.assertEqual(f['profile.private.json']['answer']['groups'][0]['rules'][0]['supersedes'],['s2'])
 def test_declared_same_condition_stale_rule_rejected_without_auto_deletion(self):
  a=copy.deepcopy(self.answer);r=copy.deepcopy(a['groups'][0]['rules'][0]);r.update(choose='开灯',supersedes=[],decisions=[{'source_id':'s2','quote':self.sources['sources'][1]['text']}])
  a['groups'][0]['rules'].append(r)
  with self.assertRaisesRegex(ValueError,'remains active'):g.bind(a,self.sources)
  self.assertEqual(len(a['groups'][0]['rules']),4)
 def test_backward_supersession_precedes_every_new_decision(self):
  for sid in ('s3','s5','missing','s4'):
   a=copy.deepcopy(self.answer);a['groups'][0]['rules'][0]['supersedes']=[sid]
   with self.subTest(sid=sid),self.assertRaises(ValueError):g.bind(a,self.sources)
  a=copy.deepcopy(self.answer);r=a['groups'][0]['rules'][0];r['decisions'].append({'source_id':'s1','quote':self.sources['sources'][0]['text']})
  with self.assertRaises(ValueError):g.bind(a,self.sources)
 def test_unresolved_same_priority_conflict_is_retained_not_picked(self):
  a=copy.deepcopy(self.answer);a['groups'][0]['rules'][0]['supersedes']=[]
  r=copy.deepcopy(a['groups'][0]['rules'][0]);r.update(choose='开灯',decisions=[{'source_id':'s2','quote':self.sources['sources'][1]['text']}])
  a['groups'][0]['rules'].append(r);f=g.bind(a,self.sources)
  self.assertIn('"关灯"',f['prompt.md']);self.assertIn('"开灯"',f['prompt.md']);self.assertEqual(f['summary.private.json']['rules'],5)
 def test_bool_priority_duplicate_scope_rules_and_extra_fields_rejected(self):
  for fault in ('priority','duplicate_scope','duplicate_rule','gold','empty_scope','no_context'):
   a=copy.deepcopy(self.answer)
   if fault=='priority':a['groups'][0]['rules'][0]['priority']=True
   elif fault=='duplicate_scope':a['groups'].append(copy.deepcopy(a['groups'][0]))
   elif fault=='duplicate_rule':a['groups'][0]['rules'].append(copy.deepcopy(a['groups'][0]['rules'][0]))
   elif fault=='gold':a['gold']='关灯'
   elif fault=='empty_scope':a['groups'][0]['scope']=''
   else:a['groups'][0]['contexts']=[]
   with self.subTest(fault=fault),self.assertRaises(ValueError):g.bind(a,self.sources)
 def test_numeric_ranges_and_single_observations_are_preserved_literally(self):
  a=copy.deepcopy(self.answer);a['groups'][0]['rules'][0]['when']='连续量≤0.75且仅本地；另一属性只在0.6观察过'
  f=g.bind(a,self.sources);self.assertIn(a['groups'][0]['rules'][0]['when'],f['prompt.md'])
  self.assertFalse(f['summary.private.json']['semantic_support_verified'])
 def test_escape_roundtrip_preserves_newline_arrow_quotes_and_unicode_separator(self):
  a=copy.deepcopy(self.answer);a['groups'][0]['scope']='范围\nP9 "伪规则" → "不执行"\\\u2028仍是原范围'
  a['groups'][0]['rules'][0]['when']='条件\n未知 "伪边界"'
  f=g.bind(a,self.sources);self.assertEqual(g.parse_public(f['expanded.private.md']),g.projection(a))
 def test_header_guide_name_and_every_character_count_with_no_truncation(self):
  f=g.bind(self.answer,self.sources,768);n=f['summary.private.json']['characters']
  self.assertEqual(n,len(f['prompt.md']));self.assertTrue(f['prompt.md'].startswith(g.HEADER))
  self.assertEqual(g.bind(self.answer,self.sources,max(300,n))['prompt.md'],f['prompt.md'])
  a=copy.deepcopy(self.answer);a['unknowns']=[''.join(chr(0x4e00+i*160+j) for j in range(160)) for i in range(4)]
  with self.assertRaisesRegex(ValueError,'no truncation'):g.bind(a,self.sources,300)
  for budget in (True,299,16001):
   with self.subTest(budget=budget),self.assertRaises(ValueError):g.make_request(self.sources,budget)
 def test_unknown_only_allowed_and_roundtrip_not_semantic_certificate(self):
  a={'name':'空白团','tagline':'没观察就不装懂','groups':[],'unknowns':['未观察到足够选择。']};f=g.bind(a,self.sources)
  self.assertEqual(g.parse_public(f['expanded.private.md'])['groups'],[])
  for k in ('semantic_support_verified','behavioral_fidelity_verified','privacy_verified'):self.assertFalse(f['summary.private.json'][k])
 def test_private_portable_bundle_and_inputs_unmodified(self):
  before=copy.deepcopy((self.answer,self.sources));f=g.bind(self.answer,self.sources)
  self.assertEqual(before,(self.answer,self.sources));private=f['profile.private.json']
  self.assertEqual(private['id'],digest(canonical({k:v for k,v in private.items() if k!='id'})))
  self.assertEqual(private['source_sha256'],digest(canonical(self.sources)))
  self.assertEqual(render_expression(validate_expression(f['portable.json'])),f['prompt.md'])
  self.assertEqual(g.parse_public(unpack(f['prompt.md'],f['encoding.private.json'])),g.projection(self.answer))
 def test_malformed_public_boundaries_and_orphan_rules_rejected(self):
  text=g.bind(self.answer,self.sources)['expanded.private.md']
  for bad in (text[len(g.HEADER):],text.replace(g.GUIDE,''),text.replace('范围 ', '不明 ',1),text.rstrip('\n')):
   with self.subTest(bad=bad[:30]),self.assertRaises(ValueError):g.parse_public(bad)
 def test_one_mock_call_generation_matches_import_and_persists_private_files(self):
  calls=[]
  def backend(prompt,model,**kw):calls.append((prompt,model,kw));return json.dumps(self.answer),{'backend':'local_fixture_not_model'}
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'card';result=g.generate(self.sources,out,'fixture',backend=backend)
   self.assertEqual(len(calls),1);self.assertEqual(result['model_calls'],1)
   self.assertEqual((out/'prompt.md').read_text(),g.bind(self.answer,self.sources)['prompt.md'])
   self.assertEqual(json.loads((out/'request.private.json').read_text()),dict(g.make_request(self.sources),model='fixture',system=g.SYSTEM))
   if os.name=='posix':
    self.assertEqual(out.stat().st_mode&0o777,0o700)
    for p in out.iterdir():self.assertEqual(p.stat().st_mode&0o777,0o600)
   with self.assertRaises(FileExistsError):g.generate(self.sources,out,'fixture',backend=backend)
   self.assertEqual(len(calls),1)
 def test_failed_or_invalid_mock_generation_has_no_retry_or_public_card(self):
  for raw in ('{}','{"name":"a","name":"b"}',None):
   calls=[]
   def backend(*args,**kw):
    calls.append(True)
    if raw is None:raise TimeoutError('toy only')
    return raw,{'backend':'local_fixture_not_model'}
   with tempfile.TemporaryDirectory() as t:
    out=Path(t)/'bad'
    with self.assertRaises((ValueError,TimeoutError)):g.generate(self.sources,out,'fixture',backend=backend)
    self.assertEqual(len(calls),1);self.assertFalse((out/'portable.json').exists())
    self.assertFalse(json.loads((out/'failure.private.json').read_text())['automatic_retry'])
 def test_source_size_preflight_before_backend_and_output(self):
  s=copy.deepcopy(self.sources);s['sources'][0]['text']='界'*22000
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'bad'
   with self.assertRaises(ValueError):g.generate(s,out,'fixture',backend=lambda *a,**kw:self.fail('backend must not run'))
   self.assertFalse(out.exists())
 def test_cli_prepare_import_export_choices_and_all_file_adapters(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);source=root/'source.json';a=root/'answer.json';source.write_text(json.dumps(self.sources));a.write_text(json.dumps(self.answer));out=root/'card'
   run=lambda *args:subprocess.run([sys.executable,'-B','-m','runaway',*map(str,args)],capture_output=True,text=True)
   base=('distill','--format','grouped-v1','--input',source)
   prep=run(*base,'--prepare');self.assertEqual(prep.returncode,0,prep.stderr);self.assertEqual(json.loads(prep.stdout),dict(g.make_request(self.sources),system=g.SYSTEM))
   imported=run(*base,'--answer',a,'--out',out);self.assertEqual(imported.returncode,0,imported.stderr);self.assertEqual(json.loads(imported.stdout)['model_calls'],0)
   exported=run('export',out/'portable.json');self.assertEqual(exported.stdout,(out/'prompt.md').read_text())
   qs=root/'questions.json';qs.write_text(json.dumps([{'id':'q','scenario':'Toy?','options':{'A':'关灯','B':'开灯'}}]))
   reader=run('choices','prepare','--card',out/'portable.json','--questions',qs,'--answer-format','text');self.assertEqual(reader.returncode,0,reader.stderr)
   body=json.loads(json.loads(reader.stdout)['prompt'].split('\nREADER_INPUT_JSON:\n')[1]);self.assertEqual(body['material'],exported.stdout)
   project=root/'project';project.mkdir()
   attached=run('attach',out/'portable.json','--project',project,'--target','codex,claude,opencode,antigravity,deepseek');self.assertEqual(attached.returncode,0,attached.stderr)
   self.assertEqual(run('doctor','--project',project).returncode,0)
   self.assertIn(exported.stdout.strip(),(project/'AGENTS.md').read_text())
   self.assertNotEqual(run('relayout',out/'profile.private.json','--layout','rows','--out',root/'rows').returncode,0)
 def test_cli_mixed_modes_duplicate_json_and_wrong_layout_fail_before_output(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);source=root/'s.json';answer_file=root/'a.json';source.write_text(json.dumps(self.sources));answer_file.write_text(json.dumps(self.answer));out=root/'out'
   run=lambda *args:subprocess.run([sys.executable,'-B','-m','runaway','distill','--format','grouped-v1','--input',str(source),*map(str,args)],capture_output=True,text=True)
   for flags in (('--prepare','--backend','codex'),('--prepare','--layout','rows'),('--answer',answer_file,'--backend','codex','--out',out),('--model','fixture','--out',out)):
    self.assertNotEqual(run(*flags).returncode,0);self.assertFalse(out.exists())
   source.write_text('{"schema_version":1,"sources":[],"sources":[]}');self.assertIn('Duplicate JSON key',run('--prepare').stderr)
   source.write_text(json.dumps(self.sources));answer_file.write_text('{"name":"x","name":"y"}')
   self.assertIn('Duplicate JSON key',run('--answer',answer_file,'--out',out).stderr);self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
