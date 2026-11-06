import {canonical} from './core.mjs';
import {makeChoiceRequest, decodeChoiceResponse} from './choice-core.mjs';
import {requireIntact} from './text-integrity.mjs';

const ratings = ['unrated','fits','misses','uncertain'];
const phases = ['not_recorded','before_prediction_in_session','after_prediction_in_session'];
const origins = ['demo_or_edited_demo','user_supplied_unverified'];
const snapshotKeys = ['schema_version','kind','created_at','synthetic','source_origin','material',
  'queries','answer_format','reader_mode','request','reference'];
function same(a,b) {return canonical(a) === canonical(b);}
function exact(value, keys) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).sort().join(',') !== [...keys].sort().join(',')) throw Error('反馈字段不完整或包含未审核内容。');
}
function timestamp(value) {
  if (typeof value !== 'string' || !Number.isFinite(Date.parse(value)) ||
      new Date(value).toISOString() !== value) throw Error('本地记录时间无效。');
  return value;
}

export function makeTrialSnapshot(contract, material, queries, options={}) {
  const {readerMode='standard', synthetic=false, referenceLabel='',
    referenceAfterPrediction=false, referenceAt=null, createdAt=new Date().toISOString()} = options;
  if (typeof synthetic !== 'boolean' || typeof referenceAfterPrediction !== 'boolean' ||
      typeof referenceLabel !== 'string') throw Error('反馈来源或记录时点无效。');
  const request = makeChoiceRequest(contract, material, queries, 'text', readerMode);
  if (queries.length !== 1 || queries[0].id !== 'q1') throw Error('本页每次记录一道选择题。');
  if (referenceLabel && !Object.hasOwn(queries[0].options, referenceLabel)) throw Error('请选择当前题目的选项。');
  timestamp(createdAt);
  const reference = referenceLabel ? {
    label:referenceLabel, text:queries[0].options[referenceLabel],
    timing:referenceAfterPrediction ? phases[2] : phases[1], recorded_at:timestamp(referenceAt ?? createdAt)
  } : {label:null, text:null, timing:phases[0], recorded_at:null};
  // The reference stays beside the request and never enters model material.
  return {schema_version:2, kind:'runaway_choice_trial', created_at:createdAt, synthetic,
    source_origin:synthetic ? origins[0] : origins[1], material, queries:structuredClone(queries),
    answer_format:'text', reader_mode:readerMode, request, reference};
}

function validateSnapshot(contract, snapshot) {
  exact(snapshot, snapshotKeys);
  exact(snapshot.reference, ['label','text','timing','recorded_at']);
  if (!phases.includes(snapshot.reference.timing)) throw Error('本人选择的记录时点无效。');
  const rebuilt = makeTrialSnapshot(contract, snapshot.material, snapshot.queries, {
    readerMode:snapshot.reader_mode, synthetic:snapshot.synthetic,
    referenceLabel:snapshot.reference.label ?? '',
    referenceAfterPrediction:snapshot.reference.timing === phases[2],
    referenceAt:snapshot.reference.recorded_at, createdAt:snapshot.created_at});
  if (!same(snapshot, rebuilt)) throw Error('请求、题目或本人选择记录已改变。');
  return rebuilt;
}

export function makeTrialRecord(contract, snapshot, raw, feedback, importedAt=new Date().toISOString()) {
  validateSnapshot(contract, snapshot);
  exact(feedback, ['rating','correction']);
  if (!ratings.includes(feedback.rating) || typeof feedback.correction !== 'string' ||
      [...feedback.correction].length > 12000) throw Error('评分或纠正内容无效。');
  requireIntact(feedback.correction, '纠正内容');
  const decoded = decodeChoiceResponse(snapshot.queries, raw);
  const hasReference = snapshot.reference.label !== null;
  return {...structuredClone(snapshot),
    prediction:{raw_response:raw, decoded, imported_at:timestamp(importedAt)},
    feedback:structuredClone(feedback), metrics:{
      declared_choice_match:hasReference ? decoded.q1.text === snapshot.reference.text : null,
      model_returned_unknown:decoded.q1.unknown},
    model_service:'user_selected_unverified', model_calls_by_app:0, independent_fidelity_verified:false};
}

export function publicTrialSummary(contract, record) {
  exact(record, [...snapshotKeys,'prediction','feedback','metrics','model_service',
    'model_calls_by_app','independent_fidelity_verified']);
  exact(record.prediction, ['raw_response','decoded','imported_at']);
  const snapshot = Object.fromEntries(snapshotKeys.map(key => [key,record[key]]));
  const rebuilt = makeTrialRecord(contract, snapshot, record.prediction.raw_response,
    record.feedback, record.prediction.imported_at);
  if (!same(record, rebuilt)) throw Error('预测、评分或导出记录已改变。');
  return {schema_version:1, kind:'runaway_choice_summary', origin:record.source_origin,
    reader_mode:record.reader_mode, reference_recorded:record.reference.label !== null,
    reference_timing:record.reference.timing,
    declared_choice_match:record.metrics.declared_choice_match,
    model_returned_unknown:record.metrics.model_returned_unknown,
    rating:record.feedback.rating, correction_provided:Boolean(record.feedback.correction.trim()),
    includes_prompt_or_task_text:false, includes_free_text:false,
    model_calls_by_app:0, model_identity_verified:false, independent_fidelity_verified:false};
}

export function publicTrialIssueUrl(summary) {
  exact(summary, ['schema_version','kind','origin','reader_mode','reference_recorded',
    'reference_timing','declared_choice_match','model_returned_unknown','rating',
    'correction_provided','includes_prompt_or_task_text','includes_free_text',
    'model_calls_by_app','model_identity_verified','independent_fidelity_verified']);
  if (summary.schema_version !== 1 || summary.kind !== 'runaway_choice_summary' ||
      !origins.includes(summary.origin) || !['standard','coverage'].includes(summary.reader_mode) ||
      !phases.includes(summary.reference_timing) || !ratings.includes(summary.rating) ||
      ['reference_recorded','model_returned_unknown','correction_provided'].some(k => typeof summary[k] !== 'boolean') ||
      ![true,false,null].includes(summary.declared_choice_match) ||
      ['includes_prompt_or_task_text','includes_free_text','model_identity_verified','independent_fidelity_verified'].some(k => summary[k] !== false) ||
      summary.model_calls_by_app !== 0 ||
      (summary.reference_recorded ? summary.reference_timing === phases[0] || summary.declared_choice_match === null
        : summary.reference_timing !== phases[0] || summary.declared_choice_match !== null) ||
      (summary.model_returned_unknown && summary.declared_choice_match === true)) throw Error('公开摘要包含无效或未审核字段。');
  const body = 'Voluntary single-choice feedback; model and personal fidelity are unverified.\n' +
    'Prompt, question, reference text, response text and corrections are omitted.\n\n```json\n' +
    JSON.stringify(summary,null,2) + '\n```\n';
  return 'https://github.com/xu2333/RunAWay/issues/new?title=' +
    encodeURIComponent('[choice feedback] One local trial') + '&body=' + encodeURIComponent(body);
}
