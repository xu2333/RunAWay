import {canonical} from './core.mjs';
import {requireIntact, requireIntactTree} from './text-integrity.mjs';

function schemaFor(queries, format) {
  if (!['label', 'text'].includes(format) || !Array.isArray(queries) || !queries.length) throw Error('请提供问题和有效的答案格式。');
  const properties = Object.create(null), seen = new Set();
  for (const q of queries) {
    if (!q || Object.keys(q).sort().join(',') !== 'id,options,scenario' || typeof q.id !== 'string' || !q.id || seen.has(q.id)) throw Error('问题字段或编号无效。');
    if (typeof q.scenario !== 'string' || !q.scenario.trim() || !q.options || Array.isArray(q.options) || typeof q.options !== 'object') throw Error('请写下情境与选项。');
    const labels = Object.keys(q.options), texts = Object.values(q.options);
    if (labels.length < 2 || labels.length > 8 || labels.join('') !== 'ABCDEFGH'.slice(0, labels.length) || texts.some(t => typeof t !== 'string' || !t.trim())) throw Error('需要 2–8 个连续编号的非空选项。');
    if (format === 'text' && (new Set(texts).size !== texts.length || texts.includes('U'))) throw Error('选项原文不能重复，U 专用于未知。');
    seen.add(q.id);
    properties[q.id] = {type:'string', enum:[...(format === 'text' ? texts : labels), 'U']};
  }
  requireIntactTree(queries);
  return {type:'object', additionalProperties:false, required:[...seen], properties};
}

export function makeChoiceRequest(contract, material, queries, format = 'text', readerMode = 'standard') {
  if (!['standard','coverage'].includes(readerMode)) throw Error('读取方式无效。');
  const prefix = readerMode === 'standard' ? contract?.prefixes?.[format] : contract?.reader_modes?.coverage?.[format];
  if (typeof material !== 'string' || contract?.schema_version !== 1 || typeof contract.prefixes?.[format] !== 'string') throw Error('材料或读取协议无效。');
  requireIntact(material, '随身 prompt');
  if (typeof prefix !== 'string') throw Error('所选读取协议未载入。');
  const schema = schemaFor(queries, format);
  return {schema, prompt:prefix + '\nANSWER_SCHEMA_JSON:\n' + canonical(schema) + '\nREADER_INPUT_JSON:\n' + canonical({material, queries})};
}

// Only a flat string-valued object is accepted. Detect duplicate decoded keys
// before JSON.parse can silently replace them; never fix a model's choices.
export function parseChoiceAnswer(raw) {
  if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > 200000) throw Error('请粘贴不超过 200 KB 的完整 JSON。');
  let source = raw.trim();
  if (/^```(?:json)?\s*\n/i.test(source) && /\n```$/.test(source)) source = source.replace(/^```(?:json)?\s*\n/i, '').replace(/\n```$/, '');
  let i = 0;
  const skip = () => {while (/[\t\n\r ]/.test(source[i] || 'x')) i++;};
  const take = char => {skip(); if (source[i++] !== char) throw Error('需要完整的 JSON 字符串对象。');};
  const string = () => {
    skip(); const start = i;
    if (source[i++] !== '"') throw Error('问题编号和答案都必须是 JSON 字符串。');
    while (i < source.length) {
      const char = source[i++];
      if (char === '\\') {i++; continue;}
      if (char === '"') {try {return JSON.parse(source.slice(start, i));} catch {break;}}
    }
    throw Error('JSON 字符串无效。');
  };
  const result = Object.create(null);
  take('{'); skip();
  if (source[i] !== '}') while (true) {
    const key = string();
    if (Object.hasOwn(result, key)) throw Error('JSON 中的问题编号重复。');
    take(':'); result[key] = string(); skip();
    if (source[i] !== ',') break;
    i++; skip();
    if (source[i] === '}') throw Error('JSON 不能有末尾逗号。');
  }
  take('}'); skip();
  if (i !== source.length) throw Error('JSON 后还有额外内容。');
  requireIntactTree(result);
  return result;
}

export function decodeChoiceResponse(queries, raw, format = 'text') {
  const schema = schemaFor(queries, format), answer = parseChoiceAnswer(raw);
  if (Object.keys(answer).length !== schema.required.length || schema.required.some(id => !Object.hasOwn(answer, id))) throw Error('问题编号缺失或多余；不会把漏答改成未知。');
  const result = Object.create(null);
  for (const q of queries) {
    const value = answer[q.id];
    if (!schema.properties[q.id].enum.includes(value)) throw Error('答案必须是选项完整原文或 U；不自动修正近似回答。');
    const label = value === 'U' ? 'U' : format === 'label' ? value : Object.keys(q.options).find(k => q.options[k] === value);
    result[q.id] = {label, text:label === 'U' ? null : q.options[label], unknown:label === 'U', raw:value};
  }
  return result;
}
