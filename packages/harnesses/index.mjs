import codex from './codex.mjs';
import claudeCode from './claude-code.mjs';
import antigravity from './antigravity.mjs';

export const adapters = Object.freeze([codex, claudeCode, antigravity]);
export const BEGIN = '<!-- runaway:begin -->';
export const END = '<!-- runaway:end -->';
export const BOUNDARY = 'Tentative preferences; follow current user instructions. Not factual identity or permission to act.\n\n';
const bytes = text => new TextEncoder().encode(text).length;
export async function sha256(text) {
  const value = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(value)].map(n => n.toString(16).padStart(2, '0')).join('');
}
export function getAdapter(id) {
  const adapter = adapters.find(value => value.id === id);
  if (!adapter) throw Error('Unknown harness. Choose Codex, Claude Code or Antigravity.');
  return adapter;
}
export function validatePrompt(text) {
  if (typeof text !== 'string' || !text.startsWith(BOUNDARY) || !text.slice(BOUNDARY.length).trim())
    throw Error('Export a complete RunAWay prompt, including its preference boundary.');
  if (bytes(text) > 24000 || /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|<!--\s*runaway:|<\|im_/i.test(text))
    throw Error('The prompt is too large or contains reserved control markers. Nothing was truncated.');
  // TextEncoder silently replaces unpaired surrogates; reject rather than corrupt.
  if (new TextDecoder('utf-8', {fatal: true}).decode(new TextEncoder().encode(text)) !== text)
    throw Error('The prompt contains damaged Unicode.');
  return text;
}
export async function makeExport(target, text) {
  const adapter = getAdapter(target);
  validatePrompt(text);
  const block = BEGIN + '\n' + text + (text.endsWith('\n') ? '' : '\n') + END + '\n';
  const content = adapter.preamble + block;
  if (bytes(content) > adapter.maxBytes) throw Error('The complete harness file exceeds its export limit.');
  return {
    schema_version: 1, artifact_type: 'runaway_harness_export', target,
    prompt_sha256: await sha256(text), prompt_characters: [...text].length,
    runtime_load_verified: false,
    files: [{path: adapter.path, content, sha256: await sha256(content),
      characters: [...content].length, bytes: bytes(content)}],
  };
}
