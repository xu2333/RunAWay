"""Offline authoring contracts;structure/provenance checks are not semantic gold."""
import copy

VERSION='task_contract_v1'
KINDS={
 'preferred_option':('future_policy','existing_option_label','本人会选择哪个既有方案？请返回方案完整名称。'),
 'execution_order':('explicit_sequence','execution_order_label','记录明确写出的执行先后是哪一个？不要从方案名补推。'),
 'past_observation':('recorded_past','observed_status_label','只问已经记录的上一次实际状态，不推测下一次。'),
 'decision_polarity':('recorded_commitment','decision_polarity_label','本人明确接受还是明确拒绝该安排？没有明确决定则回答U。')}
UNKNOWN_REASONS={'missing_condition','uncovered_policy','conflicting_sources','not_decided'}
FIELDS={'version','id','target_object','intent','temporal_role','answer_kind','facts','options','reference',
        'unknown_reason','support','contrasts'}


def string(value,label):
 if type(value) is not str or not value.strip():raise ValueError(label+' must be nonempty text')
 return value


def validate(contract,sources):
 if type(contract) is not dict or set(contract)!=FIELDS or contract['version']!=VERSION:raise ValueError('Version/contract fields differ')
 for key in ('id','target_object','facts'):string(contract[key],key)
 intent=string(contract['intent'],'intent')
 if intent not in KINDS:raise ValueError('Unsupported intent;creating a new name is not choosing an existing option')
 temporal,kind,_=KINDS[intent]
 if (contract['temporal_role'],contract['answer_kind'])!=(temporal,kind):raise ValueError('Task/answer/temporal role mismatch')
 options=contract['options']
 if type(options) is not list or len(options)!=2 or any(type(x) is not str or not x.strip() or x!=x.strip() or x=='U' for x in options) or len(set(options))!=2:raise ValueError('Two distinct known option labels required;U is separate')
 reference=contract['reference']
 if reference not in options+['U']:raise ValueError('Reference outside answer space')
 if reference=='U' and contract['unknown_reason'] not in UNKNOWN_REASONS:raise ValueError('Unknown reference needs an explicit author reason')
 if reference!='U' and contract['unknown_reason'] is not None:raise ValueError('Known status/choice is not an unknown reason')
 if type(sources) is not dict or type(sources.get('schema_version')) is not int or sources.get('schema_version')!=1 or type(sources.get('sources')) is not list:raise ValueError('Source pack required')
 index={}
 for source in sources['sources']:
  if type(source) is not dict:raise ValueError('Source entry must be an object')
  sid=string(source.get('id'),'source id')
  if sid in index:raise ValueError('Duplicate source id')
  string(source.get('text'),'source text');index[sid]=source
 support=contract['support']
 if type(support) is not list or not support:raise ValueError('Literal supporting anchors required')
 for anchor in support:
  if type(anchor) is not dict or set(anchor)!={'source_id','quote'}:raise ValueError('Anchor fields differ')
  source=index.get(string(anchor['source_id'],'anchor source id'));quote=string(anchor['quote'],'quote')
  if source is None or source.get('role')!='user' or quote not in source['text']:raise ValueError('User-source quote not grounded')
 if reference!='U' and not any(reference in anchor['quote'] for anchor in support):raise ValueError('Known literal label absent from supporting quotes')
 contrasts=contract['contrasts']
 if type(contrasts) is not list or not contrasts:raise ValueError('Declare at least one discriminating counterfactual witness')
 for witness in contrasts:
  if type(witness) is not dict or set(witness)!={'fault','predicted_answer'}:raise ValueError('Witness fields differ')
  string(witness['fault'],'fault');value=witness['predicted_answer']
  if value not in options+['U']:raise ValueError('Counterfactual is outside options:it cannot demonstrate the intended choice error')
  if value==reference:raise ValueError('Counterfactual does not change the scored answer')
 return {'structural_contract_valid':True,'literal_user_anchors_valid':True,
  'semantic_entailment_verified':False,'question_source_equivalence_independently_accepted':False,
  'contrast_behaviour_observed':False,'reference_independently_accepted':False}


def prepare(contract,sources):
 """Return public questions separately from private author reference/audit."""
 audit=validate(contract,sources)
 target=KINDS[contract['intent']][2]
 scenario=contract['target_object']+'。'+contract['facts']+'。'+target+' 没有唯一有依据的选项则回答U。'
 first,second=contract['options']
 questions=[{'id':contract['id']+'_ab','scenario':scenario,'options':{'A':first,'B':second}},
            {'id':contract['id']+'_ba','scenario':scenario,'options':{'A':second,'B':first}}]
 return {'questions.public':questions,'contract.private':copy.deepcopy(contract),'audit.private':audit,
         'new_model_calls':0,'old_benchmark_metrics_changed':False}
