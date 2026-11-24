import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {makeExport} from '../../packages/harnesses/index.mjs';

const load = async name => JSON.parse(await readFile(new URL(name,import.meta.url), 'utf8'));
const protocol = await load('protocol.json');
const receipts = await load('rule-receipts.json');
const cards = new Map(protocol.cases.map(c => [c.id,c]));
const slots = new Map(receipts.map(r => [r.slot,r]));
assert.equal(slots.size,54);
assert.equal(receipts.length,slots.size);
const sha = text => createHash('sha256').update(text).digest('hex');
for (const item of protocol.slots) {
  const c = cards.get(item.case);
  const receipt = slots.get(item.slot);
  assert.equal(sha(c.task),c.task_sha256);
  assert.equal(sha(c.card),receipt.card_sha256);
  const native = await makeExport(item.client,c.card);
  const file = native.files[0];
  assert.equal(receipt.rule,file.path);
  const suffix = item.arm === 'new' ? '\n' + protocol.reader.new + '\n' : '';
  assert.equal(sha(file.content+suffix),receipt.rule_sha256);
  assert.equal(file.content.split(c.card).length,2);
}
console.log('Verified the original task, full card, and native rule in all 54 slots.');
