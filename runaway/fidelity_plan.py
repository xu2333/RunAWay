"""Freeze a synthetic stress-comparison proposal offline. Preparation never runs it."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import zipfile

from . import fidelity_stress as fs
from .card import canonical, digest
from .pipeline import write_once
from .production_adapters import FILES
from .selfplay import browser, BROWSER_SCHEMA
from .bound_memory import SCHEMA
from .taste_plan import reader_job

ROOT = Path(__file__).resolve().parents[1]
STAGES = {'full_history':4,'wrong_person_history':4,'current_policy_oracle':4,'none':4,
          'shared_extraction':8,'new_compression':8,'actual_memory_reader':16}
BUDGETS = (128,384)
CODE = tuple(dict.fromkeys(FILES + ('runaway/synthetic_metric_world.py','runaway/taste_executor.py',
    'runaway/taste_contract.py','runaway/taste_plan.py','runaway/synthetic_metric.py',
    'runaway/fidelity_stress.py','runaway/fidelity_plan.py','runaway/fidelity_runner.py',
    'tests/test_fidelity_stress.py','tests/test_fidelity_runner.py')))
GATES = {'current_accuracy_min':.9,'collapsed_scenario_accuracy_min':.9,'each_critical_layer_min':.9,'hard_errors_max':0,
         'matched_domains_required_fraction':1.0,'option_consistency_min':.9,
         'full_historical_accuracy_min':.9,'wrong_matched_domains_max':1,
         'full_minus_none_current_accuracy_min':.25,
         'on_failure':'Stop every later call. Retain all planned current/history/joint denominators.'}


def history_sources(person):
    # The old adapter helper adds a legacy tie-breaking protocol. This input
    # instead uses only the new narrated history, whose explicit semantics agree
    # with this version's conflict/unknown contract. Browser product code is unchanged.
    return {'schema_version':1,'sources':[{'id':'history','episode_id':'synthetic',
                                          'role':'user','text':person['history']}]}


def current_oracle(person):
    lines = ['仅描述截止第12天的有效选择，不提供完整历史。未列出的领域不推断。']
    for d in fs.DOMAINS:
        parts = []
        for c0,c1 in ((False,False),(True,False),(False,True),(True,True)):
            value = fs.resolve(person['events'],d[0],12,{'c0':c0,'c1':c1})[0]
            condition = '；'.join(f'{word}：{"是" if flag else "否"}' for word,flag in zip(d[3],(c0,c1)))
            parts.append(f'当{condition}，选「{fs.label(d[0],value)}」')
        lines.append(d[1]+'：'+'；'.join(parts)+'。')
    lines.append('文件标记偏好已清除；影片偏好没有记录；讨论形式两条有效记录等强相反，无法判断。当前明确要求优先。')
    return '\n'.join(lines)


def gates(name, scores, full=None):
    current = scores['current_choice'];checks = {}
    if name == 'wrong_person_history':
        checks = {'same_positive_matched_denominator':current['matched_domain_contrasts']['planned'] > 0 and
                  current['matched_domain_contrasts']['planned'] == full['current_choice']['matched_domain_contrasts']['planned'],
                  'wrong_loses_at_least_five_domains':current['matched_domain_contrasts']['correct'] <= GATES['wrong_matched_domains_max']}
    elif name == 'none':
        checks = {'memory_information_needed':full['current_choice']['accuracy']-current['accuracy'] >= GATES['full_minus_none_current_accuracy_min']}
    else:
        counts = current['current_scenarios_option_orders_collapsed'];matched=current['matched_domain_contrasts']
        checks = {'current_accuracy':current['accuracy'] >= GATES['current_accuracy_min'],
                  'collapsed_scenario_accuracy':counts['planned'] > 0 and counts['correct']/counts['planned'] >= GATES['collapsed_scenario_accuracy_min'],
                  'hard_errors':current['hard_constraints']['errors'] == 0,
                  'matched_domains':matched['planned'] > 0 and matched['correct'] == matched['planned'],
                  'option_consistency':counts['planned'] > 0 and counts['consistent']/counts['planned'] >= GATES['option_consistency_min']}
        for layer in fs.CRITICAL:
            x=current['layers'].get(layer,{'correct':0,'planned':0})
            checks[layer]=x['planned'] > 0 and x['correct']/x['planned'] >= GATES['each_critical_layer_min']
        if name == 'full_history':checks['historical_accuracy']=scores['historical_reconstruction']['accuracy'] >= GATES['full_historical_accuracy_min']
    return {'passed':all(checks.values()),'checks':checks}


def prepare(out, seed=None, runtime_template=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    # Protocol is committed before the unknown future parameters are sampled.
    contract={'version':1,'domains':[d[0] for d in fs.DOMAINS],'reader':fs.READER,
              'primary':'Current scenarios require both option orders correct; also retain raw accuracy, worst layer, matched domains and per-paired-cluster rows.',
              'historical':'Independent diagnostic and full joint score, never silently dropped.',
              'units':'4 people, 2 paired clusters; 6 targeted domain contrasts. Not 224 independent preferences.',
              'semantics':'Strongest active regular evidence; equal opposing strength is U; explicit replacements, clears, conjunctions and nested revocations follow narrated history.',
              'budgets':list(BUDGETS),'stage_caps':STAGES,'gates':GATES,'external_model_calls_this_preparation':0}
    write_once(out/'contract.json',contract)
    world=fs.build_world(secrets.randbelow(2**31) if seed is None else seed,'future')
    write_once(out/'fixtures.private.json',world)
    jobs=[];generation=[];dynamic=[];lookup={p['id']:p for p in world['people']}
    for person in world['people']:
        public=[c['public'] for c in person['cases']]
        for condition,memory in [('full_history',person['history']),('wrong_person_history',lookup[person['twin']]['history']),
                                 ('current_policy_oracle',current_oracle(person)),('none','')]:
            job=reader_job(condition,person['id'],memory,public,fs.READER,12,'stress_controls')
            jobs.append(job)
        for budget in BUDGETS:
            limit=budget*2
            request={'prompt':browser('request',history_sources(person),limit)['request'],
                     'schema':BROWSER_SCHEMA,'model':'gpt-6-luna','system':jobs[-1]['request']['system']}
            generation.append({'stage':'shared_extraction','persona_id':person['id'],'budget':budget,
                               'character_limit':limit,'request':request,'request_id':digest(canonical(request))})
            dynamic.append({'stage':'new_compression','persona_id':person['id'],'budget':budget,
                            'character_limit':limit,'schema':SCHEMA,'model':'gpt-6-luna'})
            for condition in ('current_browser','new_bound'):
                dynamic.append({'stage':'actual_memory_reader','persona_id':person['id'],'budget':budget,
                                'condition':condition,'queries':public,'reader':fs.READER,'source_cutoff':12})
    write_once(out/'reader-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in jobs))
    write_once(out/'generation-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in generation))
    write_once(out/'dynamic-jobs.json',dynamic)
    legacy=runtime_template or ROOT/'runs/task-contract-offline-v1/proposed-comparison/executor-config.json'
    runtime=json.loads(Path(legacy).read_text())
    inputs=('contract.json','fixtures.private.json','reader-jobs.jsonl','generation-jobs.jsonl','dynamic-jobs.json')
    body={'status':'offline_prepared_not_approved_not_executed','runner':'runaway.fidelity_runner.execute',
          'proposal_directory':str(out.resolve()),'world_id':world['id'],'models':{'generator':'gpt-6-luna','reader':'gpt-6.1-sol'},
          'python_executable':runtime['python_executable'],'tokenizer':runtime['tokenizer'],'tokenizer_path':runtime['tokenizer_path'],
          'calls_max':48,'stage_caps':STAGES,'timeout_seconds':180,'cleanup_waits_seconds':[2,2],
          'budgets':list(BUDGETS),'character_limits':{'128':256,'384':768},'gates':GATES,
          'retries':0,'format_repairs':0,'resources':'Existing official Codex CLI login/service only, no purchases.',
          'cost_boundary':'48 experiment generations; no hard aggregate HTTP/token/money/time ceiling. Every generation has180seconds plus2+2cleanup.',
          'matrix':'16control reads +8shared extractions +8additional bound compressions +16actual memory reads =48.',
          'methodology':'Old/new share the same extracted profile within each person/budget. Standalone new cost includes extraction plus compression. Extraction request limits differ by budget, so cross-budget differences concern the end-to-end pipeline, not an isolated compression transform.',
          'data_scope':{'synthetic_people':4,'history_characters':sum(len(p['history']) for p in world['people']),
              'public_queries_per_person':75,'current_per_person':56,'historical_per_person':19,
              'included':'Only fully synthetic histories, source-derived current oracle for reader-only controls, derived profiles/memories, public queries and necessary CLI system/schema/environment metadata.',
              'excluded':'Real user data, workspace/central messages, credentials in payload, seed, parameters, event objects, gold/options mappings and tags.',
              'oracle_disclosure':'Intentionally answer-bearing, unbudgeted, never encoder/compressor input.'},
          'selection':'One newly sampled future cohort; no filtering by model output. Two paired clusters with three changed conditional domains each. Same six-domain ontology, new parameter vectors and question wording; not domain-generalization.',
          'identical_requests':'Identical planned requests reuse a single verified completed checkpoint offline. No new invocation, independent-sample claim or refilling unused slots. Reuse is reported.',
          'stopping':['Source/runtime/payload drift: no invocation.','Any failed numeric control gate stops all later calls.',
              'Timeout, transport/format failure, uncertain prior intent or checkpoint corruption stops all later calls.',
              'Missing usage stops all further calls; unknown cost is never zero.',
              'No retry, repair, replacement subjects or old budget. Single-use proposal intent across output paths.',
              'Local product or actual-token budget rejection retains failed method rows; no truncation or repair.'],
          'reporting':'Always retain each budget/method224current +76historical =300joint planned queries. Missing differs from U. Show112collapsed current scenarios, 6matched domain contrasts, 2paired clusters. No significance/real-person/cross-provider claim.',
          'source_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in CODE},
          'input_hashes':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in inputs},
          'forbidden_request_ids':sorted({Path(name).name.removesuffix('.request.json')
                  for archive in ('pilot-evidence.synthetic.zip','comparison-evidence.synthetic.zip')
                  for name in zipfile.ZipFile(ROOT/'examples'/archive).namelist() if name.endswith('.request.json')}),
          'sealed_prior_archives':{name:hashlib.sha256((ROOT/'examples'/name).read_bytes()).hexdigest()
                                   for name in ('pilot-evidence.synthetic.zip','comparison-evidence.synthetic.zip')}}
    proposal={**body,'id':digest(canonical(body))};write_once(out/'proposal.json',proposal)
    for name in CODE:
        dest=out/'frozen-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    return proposal


def preflight(root):
    root=Path(root);p=json.loads((root/'proposal.json').read_text())
    if p['id'] != digest(canonical({k:v for k,v in p.items() if k!='id'})):raise ValueError('Proposal changed')
    if p['proposal_directory'] != str(root.resolve()):raise ValueError('Moved/copied proposal')
    if p['stage_caps'] != STAGES or p['calls_max'] != sum(STAGES.values()) or p['budgets'] != list(BUDGETS) or p['gates'] != GATES:
        raise ValueError('Frozen policy differs')
    if p['timeout_seconds'] != 180 or p['cleanup_waits_seconds'] != [2,2]:raise ValueError('Deadline policy differs')
    for name,want in p['source_hashes'].items():
        for source in (ROOT/name,root/'frozen-source'/name):
            if hashlib.sha256(source.read_bytes()).hexdigest()!=want:raise ValueError('Source changed: '+name)
    for name,want in p['input_hashes'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=want:raise ValueError('Input changed: '+name)
    for name,want in p['sealed_prior_archives'].items():
        if hashlib.sha256((ROOT/'examples'/name).read_bytes()).hexdigest()!=want:raise ValueError('Prior evidence changed')
    return p


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True);a=parser.parse_args()
    result=prepare(a.out);print(json.dumps({'proposal_id':result['id'],'calls_max_if_separately_approved':48,'external_model_calls':0}))
