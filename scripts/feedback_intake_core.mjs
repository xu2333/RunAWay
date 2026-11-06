import {createHash} from 'node:crypto';
import {canonical} from '../web/dist/core.mjs';
import {requireIntact} from '../web/dist/text-integrity.mjs';
import {publicTrialSummary,publicTrialIssueUrl} from '../web/dist/choice-feedback.mjs';

export class IntakeError extends Error {
  constructor(code) {super(code);this.code=code;}
}
export const digest=value=>createHash('sha256').update(canonical(value)).digest('hex');

// Check decoded object keys at every level, before JSON.parse could replace one.
export function parseFeedbackJSON(raw) {
  if(typeof raw!=='string'||Buffer.byteLength(raw)>2000000)throw new IntakeError('input_too_large');
  let i=0;
  const fail=()=>{throw new IntakeError('invalid_json');};
  const space=()=>{while(/[\t\n\r ]/.test(raw[i]??'x'))i++;};
  function string() {
    space();const start=i;if(raw[i++]!=='"')return fail();
    while(i<raw.length) {
      const char=raw[i++];if(char==='\\'){i++;continue;}
      if(char==='"') {
        try {return requireIntact(JSON.parse(raw.slice(start,i)));} catch {return fail();}
      }
    }
    return fail();
  }
  function value(depth) {
    if(depth>64)return fail();space();
    if(raw[i]==='"')return string();
    if(raw[i]==='{') {
      i++;space();const out=Object.create(null),keys=new Set();
      if(raw[i]!=='}')while(true) {
        const key=string();if(keys.has(key))return fail();keys.add(key);space();
        if(raw[i++]!==':')return fail();out[key]=value(depth+1);space();
        if(raw[i]!==',')break;i++;
      }
      if(raw[i++]!=='}')return fail();return out;
    }
    if(raw[i]==='[') {
      i++;space();const out=[];
      if(raw[i]!==']')while(true) {
        out.push(value(depth+1));space();if(raw[i]!==',')break;i++;
      }
      if(raw[i++]!==']')return fail();return out;
    }
    for(const [token,result]of [['true',true],['false',false],['null',null]]) {
      if(raw.startsWith(token,i)){i+=token.length;return result;}
    }
    const match=raw.slice(i).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    if(!match)return fail();i+=match[0].length;
    const number=Number(match[0]);if(!Number.isFinite(number))return fail();return number;
  }
  const out=value(0);space();if(i!==raw.length)return fail();return out;
}

const errors=new Set(['invalid_json','invalid_record','unsupported_record','unreadable_input',
  'not_regular_file','input_too_large','byte_budget_exhausted']);
const bump=(value,key)=>{value[key]=(value[key]??0)+1;};

export function analyzeFeedback(entries,contract) {
  if(!Array.isArray(entries)||!entries.length||entries.length>256)throw new IntakeError('invalid_inputs');
  const totals={input_files:entries.length,valid_private_files:0,valid_public_summary_files:0,rejected_files:0};
  const rejections={},privateGroups=new Map(),privateVersions=new Set(),publicGroups=new Map(),files=[];
  const publicCounts={origin:{},reference_timing:{},rating:{},declared_choice_match:{},model_returned_unknown:0};
  for(const [index,entry]of entries.entries()) {
    if(!entry||typeof entry!=='object'||entry.file_index!==index)throw new IntakeError('invalid_inputs');
    let reason=entry.read_error;
    if(reason&&!errors.has(reason))throw new IntakeError('invalid_inputs');
    if(!reason) {
      try {
        const value=entry.value;
        if(value?.kind==='runaway_choice_trial'&&value.schema_version===2) {
          const summary=publicTrialSummary(contract,value),version=digest(value);
          const event=digest({created_at:value.created_at,request:value.request,
            imported_at:value.prediction.imported_at,raw_response:value.prediction.raw_response});
          const reference=digest({origin:value.source_origin,reference:value.reference});
          if(!privateGroups.has(event))privateGroups.set(event,{event,files:[],references:new Set(),
            versions:new Set(),ratings:new Set(),summaries:[],correctionProvided:false});
          const group=privateGroups.get(event);group.files.push(index);group.references.add(reference);
          group.versions.add(version);group.ratings.add(value.feedback.rating);group.summaries.push(summary);
          group.correctionProvided ||= summary.correction_provided;privateVersions.add(version);
          totals.valid_private_files++;files.push({file_index:index,status:'accepted_private',event_id:event,record_sha256:version});
          continue;
        }
        if(value?.kind==='runaway_choice_summary'&&value.schema_version===1) {
          publicTrialIssueUrl(value); // Validation only;never navigate or send.
          const version=digest(value);
          // Identical content is not evidence of participant identity.
          publicGroups.set(version,(publicGroups.get(version)??0)+1);
          bump(publicCounts.origin,value.origin);bump(publicCounts.reference_timing,value.reference_timing);
          bump(publicCounts.rating,value.rating);bump(publicCounts.declared_choice_match,String(value.declared_choice_match));
          if(value.model_returned_unknown)publicCounts.model_returned_unknown++;
          totals.valid_public_summary_files++;files.push({file_index:index,status:'accepted_public_summary'});
          continue;
        }
        reason='unsupported_record';
      }catch {reason='invalid_record';}
    }
    totals.rejected_files++;bump(rejections,reason);files.push({file_index:index,status:'rejected',reason});
  }
  const partitions={ready_for_manual_review:0,excluded_conflicting_versions:0,excluded_demo:0,
    excluded_no_reference:0,excluded_post_prediction:0};
  const outcomes={matched_declared_choice:0,choice_disagreement:0,returned_unknown_requires_source_review:0};
  const events=[];let feedbackRevisions=0;
  for(const group of privateGroups.values()) {
    let disposition,reviewReason=null;
    if(group.references.size>1)disposition='excluded_conflicting_versions';
    else {
      const summary=group.summaries[0];
      if(summary.origin==='demo_or_edited_demo')disposition='excluded_demo';
      else if(!summary.reference_recorded)disposition='excluded_no_reference';
      else if(summary.reference_timing!=='before_prediction_in_session')disposition='excluded_post_prediction';
      else {
        disposition='ready_for_manual_review';
        reviewReason=summary.model_returned_unknown ? 'returned_unknown_requires_source_review' :
          summary.declared_choice_match ? 'matched_declared_choice' : 'choice_disagreement';
        bump(outcomes,reviewReason);
      }
      if(group.versions.size>1)feedbackRevisions++;
    }
    bump(partitions,disposition);
    events.push({event_id:group.event,file_indexes:group.files,disposition,review_reason:reviewReason,
      unique_record_versions:group.versions.size,reference_or_origin_variants:group.references.size,
      rating:group.ratings.size===1?[...group.ratings][0]:'multiple_versions',
      correction_provided:group.correctionProvided,requires_source_and_consent_review:true});
  }
  if(Object.values(partitions).reduce((a,b)=>a+b,0)!==privateGroups.size||
     Object.values(outcomes).reduce((a,b)=>a+b,0)!==partitions.ready_for_manual_review)throw new IntakeError('internal_count_error');
  const summary={schema_version:1,kind:'runaway_choice_intake_summary',totals,
    private_local_events:{distinct:privateGroups.size,exact_duplicate_extra_files:totals.valid_private_files-privateVersions.size,
      feedback_revision_events:feedbackRevisions,partitions,manual_review_outcomes:outcomes},
    public_summary_files:{content_groups:publicGroups.size,
      identical_content_extra_files:totals.valid_public_summary_files-publicGroups.size,
      not_deduplicated_as_people_or_cases:true,counts:publicCounts},
    rejections,counts_are_files_and_local_events_not_people:true,unique_participants_verified:false,
    independent_fidelity_verified:false,model_identity_verified:false,model_calls_by_intake:0,
    network_requests_by_intake:0,inputs_modified:false,includes_private_text_or_identifiers:false};
  return {summary,review:{schema_version:1,kind:'runaway_choice_intake_private_review',files,events,
    independent_fidelity_verified:false,new_service_authority:false}};
}
