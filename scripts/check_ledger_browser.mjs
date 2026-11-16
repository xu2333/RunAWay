import fs from 'node:fs/promises';import path from 'node:path';import {createServer} from 'node:http';import assert from 'node:assert/strict';
import {chromium} from '../apps/mobile/node_modules/playwright-core/index.mjs';
const root=new URL('../web/dist',import.meta.url).pathname;
const server=createServer(async(req,res)=>{try{const name=new URL(req.url,'http://127.0.0.1').pathname;const file=path.resolve(root,'.'+decodeURIComponent(name==='/'?'/index.html':name));if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}res.setHeader('Content-Type',file.endsWith('.mjs')?'text/javascript':file.endsWith('.json')?'application/json':file.endsWith('.css')?'text/css':'text/html');res.end(await fs.readFile(file));}catch{res.writeHead(404).end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;try{browser=await chromium.launch({headless:true,executablePath:process.env.RUNAWAY_BROWSER_EXECUTABLE || undefined});const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:'+server.address().port+'/ledger.html');
const fixtures=await page.evaluate(async()=>{
 const {createTemporal}=await import('/temporal-core.mjs');const {canonical,hash}=await import('/core.mjs');
 const {makeTrialSnapshot,makeTrialRecord}=await import('/choice-feedback.mjs');
 const protocol=await (await fetch('/temporal-protocol.json')).json(),demo=(await (await fetch('/temporal-demo.json')).json()).cases[0],contract=await(await fetch('/choice-contract.json')).json();
 const engine=createTemporal(protocol),artifact=await engine.bind(demo.answer,demo.sources);
 const body={schema_version:1,artifact_type:'portable_expression',profile_id:artifact.id,text:(await engine.render(artifact,1600)).text};
 const portable={...body,id:await hash(canonical(body))};
 const snap=makeTrialSnapshot(contract,portable.text,[{id:'q1',scenario:'私有条件必须保留',options:{A:'甲',B:'乙'}}],{synthetic:true});
 const trial=makeTrialRecord(contract,snap,'{"q1":"甲"}',{rating:'fits',correction:''});return {artifact,portable,trial};
});
for(const key of ['artifact','portable','trial'])await page.locator('#'+key).setInputFiles({name:key+'.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(fixtures[key]))});
await page.locator('#attributed').check();await page.locator('#outcome').selectOption('adopted');await page.locator('#add').click();
await page.waitForFunction(()=>document.querySelector('#rows').textContent.includes('采纳 1'));
await page.locator('#add').click();await page.waitForTimeout(100);assert.equal((await page.locator('#rows').innerText()).includes('采纳 2'),false);
const saved=page.waitForEvent('download');await page.locator('#download').click();const downloaded=await saved;const bytes=await fs.readFile(await downloaded.path());
await page.reload();await page.locator('#restore').setInputFiles({name:'ledger.json',mimeType:'application/json',buffer:bytes});
await page.locator('#artifact').setInputFiles({name:'artifact.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(fixtures.artifact))});
await page.waitForFunction(()=>document.querySelector('#rows').textContent.includes('采纳 1'));
assert.ok((await page.locator('#rows').innerText()).includes('私有条件必须保留'));assert.deepEqual(errors,[]);
console.log(JSON.stringify({status:'passed',scope:'timeline + portable + private choice -> attribution -> dedup -> download -> reload -> restore',model_calls:0}));}finally{if(browser)await browser.close();server.closeAllConnections();await new Promise(r=>server.close(r));}
