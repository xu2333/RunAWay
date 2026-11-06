import {canonical} from '../web/dist/core.mjs';
import {requireIntact} from '../web/dist/text-integrity.mjs';
import {makeChoiceRequest,decodeChoiceResponse} from '../web/dist/choice-core.mjs';
import {digest,IntakeError} from './feedback_intake_core.mjs';

export const ARMS=['full','card','none'];
const CASE_KEYS=['schema_version','kind','source_text','memory_text','queries','reference','reader_mode'];
function exact(value,keys) {
  if(!value||typeof value!=='object'||Array.isArray(value)||
    Object.keys(value).sort().join('|')!==[...keys].sort().join('|'))throw new IntakeError('invalid_fields');
}
function selectedText(value) {
  if(typeof value!=='string'||!value.trim()||Buffer.byteLength(value)>64000)throw new IntakeError('invalid_material');
  requireIntact(value);return value;
}
export function buildCheck(contract,value) {
  exact(value,CASE_KEYS);
  if(value.schema_version!==1||value.kind!=='runaway_memory_check'||
    !Array.isArray(value.queries)||!value.queries.length||value.queries.length>32)throw new IntakeError('invalid_case');
  const source=selectedText(value.source_text),memory=selectedText(value.memory_text);
  const materials={full:source,card:memory,none:''};
  const requests=Object.fromEntries(ARMS.map(arm=>[arm,makeChoiceRequest(contract,materials[arm],value.queries,'text',value.reader_mode)]));
  if(value.reference!==null)decodeChoiceResponse(value.queries,JSON.stringify(value.reference),'label');
  return {case:structuredClone(value),case_sha256:digest(value),requests};
}
export function verifyCheck(contract,packet) {
  exact(packet,['case','case_sha256','requests','dependencies']);
  const rebuilt=buildCheck(contract,packet.case);
  if(packet.case_sha256!==rebuilt.case_sha256||canonical(packet.requests)!==canonical(rebuilt.requests))
    throw new IntakeError('packet_changed');
  return rebuilt;
}

export function evaluateCheck(contract,packet,responses) {
  const checked=verifyCheck(contract,packet),c=checked.case;
  if(!responses||typeof responses!=='object'||Array.isArray(responses)||
    Object.keys(responses).some(key=>!ARMS.includes(key)))throw new IntakeError('invalid_responses');
  const arms={};
  for(const arm of ARMS) {
    if(!Object.hasOwn(responses,arm))arms[arm]={status:'not_provided',reason:'answer_not_provided'};
    else {
      const response=responses[arm];
      exact(response,Object.hasOwn(response,'read_error')?['read_error']:['raw']);
      if(Object.hasOwn(response,'read_error')) {
        if(!['unreadable_input','not_regular_file','input_too_large','invalid_utf8'].includes(response.read_error))
          throw new IntakeError('invalid_responses');
        arms[arm]={status:'invalid',reason:response.read_error};
      }else {
        try {arms[arm]={status:'valid',raw:response.raw,decoded:decodeChoiceResponse(c.queries,response.raw)};}
        catch {arms[arm]={status:'invalid',reason:'invalid_answer',raw:typeof response.raw==='string'?response.raw:null};}
      }
    }
  }
  const partition={incomplete_response_set:0,unscored_no_reference:0,source_control_disagrees_with_reference:0,
    unknown_retained:0,choice_retained_no_increment_over_no_memory:0,choice_retained_with_no_memory_difference:0,
    card_choice_where_reference_and_source_unknown:0,card_unknown_where_source_matches_choice:0,
    card_different_choice_where_source_matches:0};
  const byArm=Object.fromEntries(ARMS.map(arm=>[arm,{status:arms[arm].status,
    valid_answers:0,missing_or_invalid_answers:0,unknown_answers:0,declared_matches:0,
    declared_disagreements:0,unscored_answers:0}]));
  const cases=[];
  for(const query of c.queries) {
    const reference=c.reference===null?null:c.reference[query.id],labels={};
    for(const arm of ARMS) {
      const a=arms[arm],counts=byArm[arm];
      if(a.status!=='valid'){counts.missing_or_invalid_answers++;labels[arm]=null;continue;}
      const decoded=a.decoded[query.id];labels[arm]=decoded.label;counts.valid_answers++;
      if(decoded.unknown)counts.unknown_answers++;
      if(reference===null)counts.unscored_answers++;
      else if(decoded.label===reference)counts.declared_matches++;
      else counts.declared_disagreements++;
    }
    let disposition;
    if(ARMS.some(arm=>labels[arm]===null))disposition='incomplete_response_set';
    else if(reference===null)disposition='unscored_no_reference';
    else if(labels.full!==reference)disposition='source_control_disagrees_with_reference';
    else if(labels.card===reference)disposition=reference==='U'?'unknown_retained':
      labels.none===reference?'choice_retained_no_increment_over_no_memory':'choice_retained_with_no_memory_difference';
    else if(reference==='U')disposition='card_choice_where_reference_and_source_unknown';
    else if(labels.card==='U')disposition='card_unknown_where_source_matches_choice';
    else disposition='card_different_choice_where_source_matches';
    partition[disposition]++;cases.push({id:query.id,reference,answers:labels,disposition});
  }
  if(Object.values(partition).reduce((a,b)=>a+b,0)!==c.queries.length)throw new IntakeError('internal_count_error');
  const summary={schema_version:1,kind:'runaway_memory_check_summary',cases:c.queries.length,
    reference_provided:c.reference!==null,reader_mode:c.reader_mode,
    material_characters:{full:[...c.source_text].length,card:[...c.memory_text].length,none:0},
    partition,by_arm:byArm,
    counts_are_questions_not_independent_people:true,reference_timing_verified:false,
    source_sufficiency_verified:false,heldout_independence_verified:false,model_identity_verified:false,
    response_request_binding_verified:false,independent_fidelity_verified:false,
    includes_private_text_or_identifiers:false,model_calls_by_check:0,network_requests_by_check:0};
  return {summary,review:{schema_version:1,kind:'runaway_memory_check_private_result',
    case_sha256:checked.case_sha256,cases,arms,independent_fidelity_verified:false}};
}
