import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {Session} from '../apps/mobile/src/session.mjs';
import {makeRequest} from '../web/dist/core.mjs';

test('pocket preview adds one source-independent instruction to the archived phone request', async () => {
  const raw = await readFile(new URL('../benchmarks/designated-value-v1/source.txt', import.meta.url), 'utf8');
  function prepare(text) {
    const session = new Session();
    const request = session.prepare(text, 'trajectory', 768);
    assert.equal(request, session.request());
    const stock = makeRequest(session.prepared.sources, 768);
    assert.ok(request.endsWith(stock));
    return {stock, delta: request.slice(0, -stock.length)};
  }
  const {stock, delta} = prepare(raw);
  assert.equal(createHash('sha256').update(stock).digest('hex'), '961624a8c48e4cdf6cb1e76f2c6fb3e9afcab894b0817d5ae0eee107f08b20cf');
  assert.equal(prepare('用户：请在导出时保留单位。').delta, delta);
  assert.match(delta, /非私密短值/);
  assert.doesNotMatch(delta, /纸鹤|档案|盒名|日期|文字标签/);
});
