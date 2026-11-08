"""One restricted symbolic damage counterexample, not model-reader performance."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('material_blindspot_existing_plan',REPO/'benchmarks/fresh-alias-generalization-v1/plan.py')
DEFAULT=REPO/'benchmarks/fresh-alias-generalization-v1/measured.synthetic.json'
def read_evidence(path=DEFAULT):
 path=Path(path)
 if hashlib.sha256(path.read_bytes()).hexdigest()!=path.with_suffix('.sha256').read_text().strip():raise ValueError('Original evidence checksum differs')
 return json.loads(path.read_text())
def diagnose(data):
    d=data
    assert d['all_sources_fictional']is True and d['scientific_source_ref']=='417313504e14ac2dbe18664a2b7844afd9aa89f1'
    parent=next(x for x in d['records']if x['slot']==10)
    original=json.loads(parent['raw']);damaged=copy.deepcopy(original)
    replacements={'准备时间充裕且材料齐备':'准备时间充裕','时间很紧且材料尚未齐全':'时间很紧','时间很紧、材料尚未齐全':'时间很紧'}
    changed=[]
    for node in damaged['nodes']:
     if node['kind']!='base':continue
     for condition in node['requires']:
      if condition['text']in replacements:
       changed.append(dict(node=node['id'],before=condition['text'],after=replacements[condition['text']]))
       condition['text']=replacements[condition['text']]
    sources=d['prepared_files']['sources.json']['otter']
    old_card=p.alias_candidate.bind(original,sources)['prompt.md'];new_card=p.alias_candidate.bind(damaged,sources)['prompt.md']
    assert old_card==parent['artifact']['prompt']and len(changed)==12
    # The following evaluator intentionally understands only this fixture's exact
    # predicates and base/action_revision graph. It is not a general NLP decoder.
    def predicate(text,state):
     g,t,m,f=state
     table={
      '已经明确允许可撤销模拟':g is True,
      '准备时间充裕且材料齐备':t=='ample'and m=='full',
      '时间很紧且材料尚未齐全':t=='tight'and m=='incomplete',
      '时间很紧、材料尚未齐全':t=='tight'and m=='incomplete',
      '负责人愿意先给反馈':f is True,
      '准备时间充裕':t=='ample','时间很紧':t=='tight'}
     if text not in table:raise ValueError('Unsupported fixture predicate:'+text)
     return table[text]
    def rules(graph):
     nodes={n['id']:n for n in graph['nodes']};replaced={n['parent_id']for n in graph['nodes']if n['kind']=='action_revision'}
     def one(node):
      if node['kind']=='base':
       assert node['target_kind']=='choice'
       return dict(oi=node['object_index'],requires=[r['text']for r in node['requires']],priority=node['priority'],action=node['action'])
      assert node['kind']=='action_revision'
      result=one(nodes[node['parent_id']]);result['action']=node['action'];return result
     return[one(n)for n in graph['nodes']if n['id']not in replaced]
    def evaluate(graph,label,state):
     owners=set()
     known=p.corpus.CHAIN_OLD+p.corpus.CHAIN_MID+p.corpus.CHAIN_CURRENT
     if label not in known:return'U'
     for i,obj in enumerate(graph['objects']):
      if label in obj:owners.add(i)
     for relation in graph['object_aliases']:
      if label in(relation['canonical'],relation['alias']):owners.add(relation['object_index'])
     if len(owners)!=1:return'U'
     matching=[r for r in rules(graph)if r['oi']==next(iter(owners))and all(predicate(c,state)for c in r['requires'])]
     if not matching:return'U'
     priority=max(r['priority']for r in matching);actions={r['action']for r in matching if r['priority']==priority}
     return next(iter(actions))if len(actions)==1 else'U'
    normal=(True,'ample','full',False);exception=(True,'tight','incomplete',False);narrow=(True,'tight','incomplete',True)
    def existing(row):
     i,kind=row['case'].split('_',1);i=int(i)
     label=p.corpus.CHAIN_CURRENT[i]
     if kind in('base_old_alias','revised_old_alias'):label=p.corpus.CHAIN_OLD[i]
     elif kind=='linked_name':label=p.corpus.CHAIN_MID[i]
     elif kind=='denied_name':label=p.corpus.denied_name('chain',i)
     if kind=='execution_fact':return None,[]
     contexts=[normal]
     if kind=='exception_current':contexts=[exception]
     elif kind in('revised_current','revised_old_alias','linked_name'):contexts=[narrow]
     elif kind=='scope_not_established':contexts=[(None,'ample','full',False)]
     elif kind=='ambiguity':contexts=[normal,exception]
     elif kind=='same_choice_contexts':contexts=[normal,narrow]
     return label,contexts
    def answer(graph,label,contexts):
     if label is None:return'U'
     values=[evaluate(graph,label,state)for state in contexts]
     return values[0]if values and values[0]!='U'and all(x==values[0]for x in values)else'U'
    checked=[]
    for row in p.inputs()['rows']:
     if row['person']!='otter':continue
     label,states=existing(row);a=answer(original,label,states);b=answer(damaged,label,states)
     assert a==row['gold']and b==row['gold'],(row['case'],a,b,row['gold'])
     checked.append(dict(case=row['case'],reference=row['gold'],original_symbolic=a,damaged_symbolic=b))
    probes=[]
    for label in p.corpus.CHAIN_CURRENT:
     for t,m in(('ample','incomplete'),('tight','full')):
      for f in(False,True):
       state=(True,t,m,f);a=evaluate(original,label,state);b=evaluate(damaged,label,state)
       assert a=='U'and b!='U'
       probes.append(dict(label=label,simulation_allowed=True,time=t,materials=m,feedback=f,original_symbolic=a,damaged_symbolic=b))
    result=dict(kind='restricted_symbolic_condition_damage_not_model_measurement',parent_scientific_source_ref=d['scientific_source_ref'],parent_from_closed_fresh_run=10,person='otter',original_characters=len(old_card),damaged_characters=len(new_card),changed_conditions=changed,old_guard_accepts_damaged_graph=True,existing_person_cases=44,original_existing_symbolic_correct=44,damaged_existing_symbolic_correct=44,orthogonal_unknown_probes=len(probes),damaged_false_certainty_probes=len(probes),new_model_calls=0,current28_inputs_or_cards_changed=False,original_evidence_modified=False,limited_exact_predicate_interpreter=True,automatic_model_reader_performance_established=False,checked_cases=checked,probes=probes)
    result.update(damaged_graph=damaged,damaged_prompt=new_card)
    return result

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path);args=parser.parse_args()
 result=diagnose(read_evidence())
 if args.out is not None:
  args.out.mkdir(exist_ok=False)
  (args.out/'diagnostic.synthetic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  (args.out/'damaged-prompt.synthetic.md').write_text(result['damaged_prompt'])
 print(json.dumps({k:v for k,v in result.items()if k not in('checked_cases','probes','changed_conditions','damaged_graph','damaged_prompt')},ensure_ascii=False,indent=2))
