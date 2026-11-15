import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdtemp,rm,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {chromium} from 'playwright-core';

test('mobile viewport: local import, evidence review, three ZIP exports and archive restore without egress',{timeout:90000},async t=>{
  const root=fileURLToPath(new URL('../dist/',import.meta.url)),temp=await mkdtemp(path.join(os.tmpdir(),'runaway-mobile-ui-'));
  const server=createServer(async(req,res)=>{
    try{const url=new URL(req.url,'http://localhost'),name=url.pathname==='/'?'index.html':url.pathname.slice(1);
      if(!['index.html','app.js','style.css','icon.svg'].includes(name)) {res.writeHead(404);res.end();return;}
      res.setHeader('Content-Type',name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':name.endsWith('.svg')?'image/svg+xml':'text/html');res.end(await readFile(path.join(root,name)));
    }catch{res.writeHead(500);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  let browser=null;
  t.after(async()=>{server.closeAllConnections();if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));await rm(temp,{recursive:true,force:true});});
  browser=await chromium.launch({headless:true,...(process.env.RUNAWAY_CHROME?{executablePath:process.env.RUNAWAY_CHROME}:{})});
  const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,acceptDownloads:true});
  const page=await context.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push({url:r.url(),method:r.method()}));
  const origin='http://127.0.0.1:'+server.address().port;
  await page.goto(origin);await page.locator('#demo').click();await page.locator('#result-panel').waitFor({state:'visible'});
  assert.equal(await page.locator('[data-harness]').count(),3);
  assert.match(await page.locator('#result-status').textContent(),/虚构/);
  await page.locator('[data-harness="codex"]').click();assert.match(await page.locator('#notice').textContent(),/勾选确认/);
  async function download(selector,name){const pending=page.waitForEvent('download');await page.locator(selector).click();const value=await pending;const file=path.join(temp,name||value.suggestedFilename());await value.saveAs(file);return file;}
  const archive=await download('#save-private');const saved=JSON.parse(await readFile(archive,'utf8'));assert.ok(saved.prepared.sources.sources.length);assert.ok(saved.answer.claims.length);
  page.once('dialog',d=>d.accept());await page.locator('#clear').click();assert.equal(await page.locator('#source').inputValue(),'');
  await page.locator('#archive-file').setInputFiles(archive);await page.locator('#result-panel').waitFor({state:'visible'});
  assert.match(await page.locator('#name').textContent(),new RegExp(saved.answer.name));
  const newPrompt=(await page.locator('#prompt').inputValue())+' 条件不明时先核对。';await page.locator('#prompt').fill(newPrompt);
  assert.equal(await page.locator('#reviewed').isChecked(),false);await page.locator('#reviewed').check();
  for(const target of ['codex','claude-code','antigravity']){
    const zip=await download('[data-harness="'+target+'"]');
    const out=spawnSync('python3',['-c','import zipfile,json,sys\nz=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None\nm=json.loads(z.read("runaway-export.json")); assert m["target"]==sys.argv[2]\nassert "条件不明时先核对。" in m["files"][0]["content"]\nassert not any("private" in p or "sources" in p for p in z.namelist())',zip,target],{encoding:'utf8'});
    assert.equal(out.status,0,out.stderr);
  }
  const portable=await download('#save-portable');
  if(process.env.RUNAWAY_SCREENSHOTS){await page.locator('#prompt').evaluate(el=>{el.scrollTop=0;});await page.screenshot({path:path.join(process.env.RUNAWAY_SCREENSHOTS,'mobile-result.png'),fullPage:true});}
  page.once('dialog',d=>d.accept());await page.locator('#clear').click();await page.locator('#archive-file').setInputFiles(portable);await page.locator('#result-panel').waitFor({state:'visible'});
  assert.equal(await page.locator('#prompt').isEditable(),false);assert.equal(await page.locator('#save-private').isDisabled(),true);
  page.once('dialog',d=>d.accept());await page.locator('#clear').click();
  await page.locator('#kind').selectOption('experience');
  const source=path.join(temp,'experience.txt');await writeFile(source,'这次上线我先保留撤销入口，再默认自动选择。');await page.locator('#source-file').setInputFiles(source);await page.locator('#prepare').click();await page.locator('#model-panel').waitFor({state:'visible'});
  assert.match(await page.locator('#request').inputValue(),/保留撤销入口/);
  await page.locator('#answer').fill('{}');await page.locator('#import-answer').click();assert.match(await page.locator('#notice').textContent(),/字段不完整/);
  await page.locator('[data-step="source"]').click();
  const corrupt=path.join(temp,'damaged.txt');await writeFile(corrupt,Buffer.from([0xff,0xfe]));await page.locator('#source-file').setInputFiles(corrupt);await page.waitForFunction(()=>/encoded|encoding|UTF/i.test(document.getElementById('notice').textContent));
  assert.match(await page.locator('#source').inputValue(),/保留撤销入口/);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  // Deliberate external fetch must be blocked by the real CSP. It is separate
  // from the observed application-flow request log above.
  assert.deepEqual(errors,[]);assert.ok(requests.every(r=>r.method==='GET'&&r.url.startsWith(origin+'/')));
  const egress=await page.evaluate(async()=>{try{await fetch('https://example.com/never-send');return 'allowed';}catch{return 'blocked';}});assert.equal(egress,'blocked');
  if(process.env.RUNAWAY_SCREENSHOTS)await page.screenshot({path:path.join(process.env.RUNAWAY_SCREENSHOTS,'mobile-source.png'),fullPage:true});
});
