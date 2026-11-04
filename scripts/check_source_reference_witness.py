"""Posthoc case-specific citation-sufficiency witness; no generic semantic parser."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_reference_witness_replay',ROOT/'scripts/replay_source_id_review.py')
replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)

def cited_ids(value):
 if isinstance(value,list):return set().union(*(cited_ids(v)for v in value))if value else set()
 if not isinstance(value,dict):return set()
 own={value['source_id']}if set(value)=={'source_id'}else set()
 return own|set().union(*(cited_ids(v)for v in value.values()))if value else own

def witness(data):
 result=replay.replay(data)
 record=next(r for r in data['records']if r['kind']=='review')
 answer=replay.parse_answer(record['raw'])
 node=next(n for n in answer['nodes']if n['id']=='notes_no_restore')
 selected=cited_ids(node)
 if selected!={'m01','m02','m03','m05','m07'}:raise ValueError('Measured citation selection differs')
 sources={s['id']:s['text']for s in data['sources']['f7s']['sources']}
 # These manually supplied case interpretations are explicit, posthoc annotations.
 # We verify their quoted text, not pretend to parse arbitrary language semantically.
 for sid,text in(('m02','我先保证自己在这个范围固定采用其中一条'),
  ('m03','完整内容会传到外部服务；任何改动都能一步完整恢复。'),
  ('m05','我明确选“启用自动整理”'),
  ('m07','全部内容只留在本机，完全不外发；任何改动都不能撤销'),
  ('m09','我明确选“保持手动整理”')):
  if text not in sources[sid]:raise ValueError('Case interpretation text differs')
 functions={'always_auto':'1111','local_only':'0011','undo_only':'0101','both':'0001'}
 # Order00,01,10,11; coordinates are(local,undo). m03+m05 supply01=auto.
 consistent=lambda obs:[name for name,table in functions.items()if all(int(table[state])==value for state,value in obs)]
 selected_consistent=consistent([(1,1)])
 full_consistent=consistent([(1,1),(2,0)]) # m07+m09 add10=manual.
 outputs=sorted({int(functions[f][0])for f in selected_consistent})
 if node['action']!='保持手动整理'or selected_consistent!=['always_auto','undo_only']or full_consistent!=['undo_only']or outputs!=[0,1]:
  raise ValueError('Case witness differs')
 return {'kind':'posthoc_author_annotated_citation_subset_witness',
  'profile':'f7s','node':'notes_no_restore','selected_source_ids':sorted(selected),
  'unselected_resolving_source':'m09','source_not_referenced_anywhere_in_graph':'m09'not in cited_ids(answer),
  'truth_tables_state_order':['00','01','10','11'],'truth_tables':functions,
  'selected_confirmed_observations':[{'context_source':'m03','decision_source':'m05','state':'01','auto':True}],
  'full_additional_observation':{'context_source':'m07','decision_source':'m09','state':'10','auto':False},
  'consistent_with_selected_evidence':selected_consistent,'consistent_with_full_source':full_consistent,
  'selected_evidence_allows_both_actions_at_00':outputs==[0,1],
  'new_card_observed_score':result['scores']['views']['reviewed']['joint'],
  'measured_import_eligibility_or_scores_changed':False,'old_graph_corrected':False,
  'general_semantic_validator':False,'independent_semantic_acceptance':False,'new_model_calls':0,
  'limit':'A posthoc case-specific interpretation of already public fictional text,not a new primary endpoint. The full-source-derived public action is correct in the fixed reader test,while the node citation subset leaves a competing function possible. No reference,card,eligibility or score is changed.'}

def check():
 path=replay.DEFAULT
 replay.require(replay.p.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
 return witness(replay.p.read(path))
if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False,indent=2))
