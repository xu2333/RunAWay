import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { makeExport } from '../../packages/harnesses/index.mjs';

const load = async (path) => JSON.parse(await readFile(new URL(path, import.meta.url), 'utf8'));
const protocol = await load('protocol.json');
const previous = await load('../object-action-waits-cross-harness-v1/protocol.json');
const oldReceipts = await load('../object-action-waits-cross-harness-v1/rule-receipts.json');
const receipts = await load('rule-receipts.json');
const bySlot = new Map(receipts.map(r => [r.slot, r]));
const previousHashes = new Map(oldReceipts.map(r => [r.slot, r.rule_sha256]));
const hash = s => createHash('sha256').update(s).digest('hex');
assert.deepEqual(protocol.cases, previous.cases);
assert.deepEqual(protocol.slots, previous.slots);
assert.deepEqual(protocol.clients, previous.clients);
assert.equal(protocol.reader.old, previous.reader.new);
assert.equal(protocol.reader.new, protocol.reader.old + '\n\n' + protocol.reader.delta);
assert.equal(bySlot.size, 54);
assert.equal(receipts.length, 54);
for (const c of protocol.cases) {
  assert.equal(hash(c.task), c.task_sha256);
  assert.equal(hash(c.card), c.card_sha256);
  for (const client of Object.keys(protocol.clients)) {
    const { files: [rule] } = await makeExport(client, c.card);
    for (const arm of ['old', 'new']) {
      const receipt = bySlot.get([client, c.id, arm].join('-'));
      assert.equal(rule.path, receipt.rule);
      assert.equal(receipt.card_sha256, c.card_sha256);
      assert.equal(hash(rule.content + '\n' + protocol.reader[arm] + '\n'), receipt.rule_sha256);
      if (arm === 'old') assert.equal(receipt.rule_sha256, previousHashes.get([client, c.id, 'new'].join('-')));
    }
  }
}
console.log('Verified 54 rule installations, original tasks, and byte-identical controls.');
