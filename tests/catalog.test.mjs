import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateCatalog,filterEntries,entryFromHash,pickEntry,fictionalPrompt} from '../web/dist/catalog-core.mjs';
import {validateCard,cardText,makeOutputSample,auditSamples} from '../web/dist/presentation.mjs';
const data=JSON.parse(await readFile(new URL('../web/dist/catalog.json',import.meta.url),'utf8'));
test('all 700 fictional cards satisfy presentation limits and survive catalogue validation',()=>{
  assert.equal(validateCatalog(data),data);
  for(const entry of data.entries){validateCard(entry.card);assert.ok(cardText(entry.card,'catalog').includes('原创合成角色'));}
  const altered=structuredClone(data);altered.entries[1].id=altered.entries[0].id;
  assert.throws(()=>validateCatalog(altered));
  altered.entries[1].id='RW-0002';altered.entries[1].origin='user_submitted';
  assert.throws(()=>validateCatalog(altered));
});
test('search combines name, anchor, ID, category and AND terms without treating input as HTML',()=>{
  assert.equal(filterEntries(data).length,700);
  assert.equal(filterEntries(data,'','deadline').length,25);
  assert.equal(filterEntries(data,'外包 未来')[0].card.name,'未来的我外包公司');
  assert.equal(filterEntries(data,'ｒｗ－０１０１')[0].id,'RW-0101');
  assert.equal(filterEntries(data,'后悔药','meeting').length,0);
  assert.equal(filterEntries(data,'<script>never</script>').length,0);
  assert.equal(filterEntries(data,'知识食堂').length,25);
});
test('stable deep links select exactly one resident and random browsing avoids an immediate repeat',()=>{
  assert.equal(entryFromHash(data,'#RW-0700').card.name,'未完成也开门');
  assert.equal(entryFromHash(data,'#no-such-id'),null);
  assert.equal(pickEntry(data.entries,'RW-0001',()=>0).id,'RW-0002');
  assert.equal(pickEntry([],''),null);
  assert.equal(pickEntry([data.entries[0]],'RW-0001').id,'RW-0001');
  assert.equal(pickEntry(data.entries,'',()=>.99999).id,'RW-0700');
});
test('fictional exports preserve provenance and cannot be counted as real user samples',async()=>{
  const entry=data.entries[100],prompt=fictionalPrompt(entry);
  assert.ok(prompt.includes('原创虚构角色'));assert.ok(prompt.includes('不是对我或任何真实人物的判断'));
  for(const value of Object.values(entry.card))assert.ok(prompt.includes(value));
  await assert.rejects(()=>makeOutputSample(entry.card,{recognizable:'yes',amusing:'yes',would_share:'yes'},'a'.repeat(64),entry.origin));
  const report=await auditSamples([]);assert.equal(report.target,null);assert.equal(report.remaining_to_target,null);
});
