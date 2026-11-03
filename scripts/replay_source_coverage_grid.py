"""Fixed three-study development grid; reuse archives, never infer or select best-of."""
import argparse,copy,importlib.util,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
STUDIES={
 'a8r_repeat':('scripts/replay_source_coverage_repeat.py',('a8r',)),
 'ambiguous_repeat':('scripts/replay_ambiguous_source_repeat.py',('c2v','d9n')),
 'remaining_repeat':('scripts/replay_remaining_source_repeat.py',('b6t','e4q','f7s','g1w','h3k'))}
MODULES={key:load('grid_'+key,ROOT/path)for key,(path,_)in STUDIES.items()}
canonical=MODULES['a8r_repeat'].engine.plan.base
METHODS=MODULES['a8r_repeat'].engine.plan.METHODS
EXPECTED={
 'a8r_repeat':'6c4f02cbf69ecd88a494d5f89036a3cfe55caa8a137cc2e9a2ff366b243ac582',
 'ambiguous_repeat':'2d7cdd05e84e6601d152a427f71f552eb2b94450f2c41ce1a25a6a76d8874557',
 'remaining_repeat':'965bf7345866b672502d1d500c92df5eb7887f0eedcbec8bb432599869664d66'}
def require(value,message):
 if not value:raise ValueError(message)

def combine_reports(reports):
 """Pure arithmetic; callers must validate archives before measured publication."""
 require(set(reports)==set(STUDIES),'All three fixed studies required')
 totals={m:{}for m in METHODS};profiles=[];cost=Counter();missing_usage=0;attempts=0;controls={}
 for study,(_,people)in STUDIES.items():
  report=reports[study]
  for pid in people:
   own={}
   for method in METHODS:
    counts=report['scores']['profiles'][pid+':'+method+':card']['strict_both_generations']
    own[method]=copy.deepcopy(counts)
    for cohort,value in counts.items():totals[method].setdefault(cohort,Counter()).update(value)
   profiles.append({'profile':pid,'fixed_study':study,'methods':own})
  cost.update(report['known_original_usage']);missing_usage+=report['missing_original_usage'];attempts+=report['actual_original_attempts']
  for name in('full_control_strict','no_memory_strict_reused'):
   for cohort,value in report[name].items():controls.setdefault(name,{}).setdefault(cohort,Counter()).update(value)
 require(len(profiles)==len({p['profile']for p in profiles})==8,'Duplicate/missing source world')
 return {'kind':'consumed_source_coverage_grid_v1','fictional_source_worlds':8,'primary_cases_per_method':120,
  'answers_per_primary_case':8,'methods':{m:{k:dict(v)for k,v in cohorts.items()}for m,cohorts in totals.items()},
  'profiles':profiles,'controls':{n:{k:dict(v)for k,v in c.items()}for n,c in controls.items()},
  'actual_original_attempts':attempts,'known_original_usage':dict(cost),'missing_original_usage':missing_usage,
  'study_call_caps':{'a8r_repeat':14,'ambiguous_repeat':27,'remaining_repeat':66},
  'new_model_calls':0,'new_service_authority':False,'old49_missing_cases_filled':False,
  'old_observations_replaced':False,'production_default_changed':False,'independent_holdout':False,
  'independent_semantic_acceptance':False,'population_stability_estimated':False,
  'real_person_fidelity_verified':False,'new_choice_personalization_gain_verified':False,
  'documented_synthetic_source_retention_only':True,
  'no_memory_reuse_is_independent':False,'methods_cases_are_independent':False,
  'selection':'One fixed repeated-generation study per world: a8r14,c2v/d9n27,remaining five66. No best-of across older studies. This descriptive mapping is not a new independent validation.'}

def summarize(archives):
 require(set(archives)==set(STUDIES),'Missing/foreign study')
 reference=canonical.inputs();profiles=set();reports={};core=canonical.implementation()
 core['benchmarks/object-coverage-guidance-v1/candidate.py']=canonical.sha(ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py')
 for study,(_,people)in STUDIES.items():
  data=archives[study]
  require(data['source_input_manifest_sha256']==EXPECTED[study],'Fixed study substituted')
  require(set(data['sources'])==set(people),'Source selection differs')
  require(data['queries']==reference['queries'],'Public questions differ')
  require(all(data['implementation_sha256'].get(k)==v for k,v in core.items()),'Common frozen implementation differs')
  for pid in people:
   require(pid not in profiles and data['sources'][pid]==reference['sources'][pid],'Duplicate/foreign profile')
   own=[r for r in data['reference_rows']if r['person']==pid]
   require(own==[r for r in reference['rows']if r['person']==pid],'Reference mapping differs')
   profiles.add(pid)
  reports[study]=MODULES[study].replay(data)
 require(profiles==set(canonical.PROFILES),'Incomplete source grid')
 result=combine_reports(reports)
 for method in METHODS:
  require(result['methods'][method]['joint']['planned']==120,'Case denominator differs')
  require(result['methods'][method]['known']['planned']==58 and result['methods'][method]['unknown']['planned']==62,'Known/unknown strata differ')
 result['input_manifest_sha256']=dict(EXPECTED)
 result['source_snapshot_value_sha256']={s:MODULES[s].engine.plan.digest(data)for s,data in archives.items()}
 return result

def archives():
 values={}
 for study,module in MODULES.items():
  path=module.DEFAULT
  require(module.engine.plan.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Source archive checksum differs')
  values[study]=module.engine.plan.read(path)
 return values

def check():return summarize(archives())
DEFAULT=ROOT/'benchmarks/source-coverage-grid-v1/summary.synthetic.json'
def check_saved(path=DEFAULT):
 path=Path(path)
 require(canonical.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Grid summary checksum differs')
 expected=check();require(canonical.read(path)==expected,'Saved summary differs from frozen studies')
 return expected
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path);parser.add_argument('--check',action='store_true')
 args=parser.parse_args()
 if args.out and args.check:parser.error('--out and --check are separate operations')
 text=json.dumps(check_saved()if args.check else check(),ensure_ascii=False,indent=2)+'\n'
 if args.out:
  with args.out.open('x',encoding='utf8')as f:f.write(text)
  with args.out.with_suffix('.sha256').open('x')as f:f.write(canonical.sha(args.out)+'\n')
 else:print(text,end='')
