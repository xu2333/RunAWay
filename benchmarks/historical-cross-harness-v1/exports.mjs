import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import {makeBundle, SOURCE_FILES} from '../../packages/harnesses/bundle.mjs';

const data = name => readFile(new URL(name, import.meta.url), 'utf8');
const protocol = JSON.parse(await data('protocol.json'));
const receipts = JSON.parse(await data('web-exports.json'));
const sha256 = data => createHash('sha256').update(data).digest('hex');
const sources = Object.fromEntries(await Promise.all(SOURCE_FILES.map(async name =>
  [name, await data('../../packages/harnesses/' + name)])));
const args = process.argv.slice(2);
if (args.length && (args.length !== 3 || !protocol.cases.some(c => c.id === args[0]) ||
    !Object.hasOwn(protocol.clients, args[1]))) {
  throw Error('Usage: node exports.mjs [CASE CLIENT NEW_ZIP_PATH]');
}
assert.equal(receipts.length, protocol.cases.length * Object.keys(protocol.clients).length);
for (const item of protocol.cases) {
  assert.equal(sha256(item.card), item.card_sha256);
  assert.equal(sha256(item.task), item.task_sha256);
  for (const client of Object.keys(protocol.clients)) {
    const receipt = receipts.find(r => r.case === item.id && r.client === client);
    assert.ok(receipt);
    const bundle = await makeBundle(client, item.card, sources);
    assert.equal(bundle.manifest.prompt_sha256, receipt.card_sha256);
    assert.equal(bundle.manifest.files[0].path, receipt.rule);
    assert.equal(bundle.manifest.files[0].sha256, receipt.rule_sha256);
    assert.equal(sha256(bundle.bytes), receipt.zip_sha256);
    if (args[0] === item.id && args[1] === client)
      await writeFile(args[2], bundle.bytes, {flag:'wx'});
  }
}
console.log('Verified all ' + receipts.length + ' archived web exports.');
