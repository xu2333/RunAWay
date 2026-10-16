import test from 'node:test';
import assert from 'node:assert/strict';
import {Readable} from 'node:stream';
import {readJsonUtf8} from '../scripts/read-stdin-json.mjs';

test('stdin JSON survives every single-byte boundary including Chinese and emoji',async()=>{
 const value={scope:'材料中的四次入口位置选择，不代表所有设计取舍。🐸𠮷',nested:['修改建议','5%']};
 const bytes=Buffer.from(JSON.stringify(value),'utf8'),chunks=[...bytes].map(byte=>Buffer.from([byte]));
 assert.deepEqual(await readJsonUtf8(Readable.from(chunks)),value);
 const broken=JSON.parse(chunks.map(chunk=>chunk.toString()).join(''));
 assert.notEqual(broken.scope,value.scope);assert.ok(broken.scope.includes('\ufffd'));
});
test('malformed UTF-8 is rejected instead of silently replaced',async()=>{
 await assert.rejects(readJsonUtf8(Readable.from([Buffer.from([0x7b,0x22,0x78,0x22,0x3a,0x22,0xe5,0xff,0x22,0x7d])])),/encoded data|encoding/i);
});
