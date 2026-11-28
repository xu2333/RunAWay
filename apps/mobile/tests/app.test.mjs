import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdtemp,rm,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {chromium} from 'playwright-core';

async function mobilePage(t){
  const root=fileURLToPath(new URL('../dist/',import.meta.url)),temp=await mkdtemp(path.join(os.tmpdir(),'runaway-mobile-ui-'));
  const server=createServer(async(req,res)=>{
    try{const url=new URL(req.url,'http://localhost'),name=url.pathname==='/'?'index.html':url.pathname.slice(1);
      if(!['index.html','app.js','style.css','icon.svg'].includes(name)) {res.writeHead(404);res.end();return;}
      res.setHeader('Content-Type',name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':name.endsWith('.svg')?'image/svg+xml':'text/html');res.end(await readFile(path.join(root,name)));
    }catch{res.writeHead(500);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(async()=>{await new Promise(resolve=>server.close(resolve));await rm(temp,{recursive:true,force:true});});
  const browser=await chromium.launch({headless:true,...(process.env.RUNAWAY_CHROME?{executablePath:process.env.RUNAWAY_CHROME}:{})});
  t.after(()=>browser.close());
  const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,acceptDownloads:true});
  const page=await context.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push({url:r.url(),method:r.method()}));
  const origin='http://127.0.0.1:'+server.address().port;
  await page.goto(origin);
  return {page,context,origin,temp,requests,errors};
}

test('mobile viewport: local import, evidence review, three ZIP exports and archive restore without egress',async t=>{
  const {page,origin,temp,requests,errors}=await mobilePage(t);
  await page.locator('#demo').click();await page.locator('#load-demo').click();await page.locator('#result-panel').waitFor({state:'visible'});
  assert.equal(await page.locator('#name').textContent(),'纸鹤排头员');
  assert.match(await page.locator('#prompt-size').textContent(),/267 字符/);
  assert.match(await page.locator('#prompt').inputValue(),/只保留“纸鹤”/);
  await page.locator('#own-dialogue').click();
  assert.equal(await page.locator('#source').inputValue(),'');
  assert.equal(await page.locator('#source').evaluate(el=>el===document.activeElement),true);
  await page.locator('#source').fill('用户：这是我想保留的原稿。');
  await page.locator('#demo').click();
  assert.match(await page.locator('#demo-source').textContent(),/用户：只写纸鹤/);
  assert.match(await page.locator('#demo-body').textContent(),/只保留“纸鹤”/);
  await page.getByRole('button',{name:'回去写我的对话'}).click();
  assert.equal(await page.locator('#source').inputValue(),'用户：这是我想保留的原稿。');
  await page.locator('#demo').click();
  page.once('dialog',d=>d.dismiss());
  await page.locator('#load-demo').click();
  assert.equal(await page.locator('#source').inputValue(),'用户：这是我想保留的原稿。');
  page.once('dialog',d=>d.accept());
  await page.locator('#load-demo').click();
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
    assert.equal(await page.locator('#install-guide').evaluate(el=>el.open),true);
    assert.ok((await page.locator('#zip-status').textContent()).includes('已请求下载 runaway-'+target+'.zip'));
    const out=spawnSync('python3',['-c','import zipfile,json,sys\nz=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None\nm=json.loads(z.read("runaway-export.json")); assert m["target"]==sys.argv[2]\nassert "条件不明时先核对。" in m["files"][0]["content"]\nassert not any("private" in p or "sources" in p for p in z.namelist())',zip,target],{encoding:'utf8'});
    assert.equal(out.status,0,out.stderr);
  }
  const portable=await download('#save-portable');
  if(process.env.RUNAWAY_SCREENSHOTS){await page.locator('#prompt').evaluate(el=>{el.scrollTop=0;});await page.screenshot({path:path.join(process.env.RUNAWAY_SCREENSHOTS,'mobile-result.png'),fullPage:true});}
  page.once('dialog',d=>d.accept());await page.locator('#clear').click();await page.locator('#archive-file').setInputFiles(portable);await page.locator('#result-panel').waitFor({state:'visible'});
  assert.equal(await page.locator('#prompt').isEditable(),false);assert.equal(await page.locator('#save-private').isDisabled(),true);
  page.once('dialog',d=>d.accept());await page.locator('#clear').click();
  await page.locator('#source-options summary').click();
  await page.locator('#kind').selectOption('experience');
  const source=path.join(temp,'experience.txt');await writeFile(source,'这次上线我先保留撤销入口，再默认自动选择。');await page.locator('#source-file').setInputFiles(source);await page.locator('#prepare').click();await page.locator('#model-panel').waitFor({state:'visible'});
  assert.match(await page.locator('#request').inputValue(),/保留撤销入口/);
  await page.locator('#answer').fill('{}');await page.locator('#import-answer').click();assert.match(await page.locator('#answer-error').textContent(),/字段不完整/);
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

test('own dialogue survives the copy, correction and return trip',async t=>{
  const {page,context,origin,requests,errors}=await mobilePage(t);
  const quote='试映时先放无配乐版。';
  const source='You said:\r\n'+quote+'\r\nChatGPT said:\r\n那正式放映呢？';
  const answer={name:'试映笔记',tagline:'先听现场',prompt:quote,unknowns:['正式放映的做法未知。'],
    claims:[{id:'screening',basis:'self_report',scope:'试映',statement:quote,conditions:[],exceptions:[],
      evidence:[{source_id:'message-1',quote,relation:'supports'}],related_claim_ids:[]}],covered_claim_ids:['screening']};
  await page.locator('#source').fill('未标明说话者的文字');
  await page.locator('#prepare').click();
  assert.match(await page.locator('#source-error').innerText(),/用户/);
  await page.locator('#source').fill(source);
  await page.locator('#prepare').click();
  assert.match(await page.locator('#source-summary').innerText(),/你的 1 段文字、助手的 1 段文字/);
  const request=await page.locator('#request').inputValue();
  await context.grantPermissions(['clipboard-read','clipboard-write'],{origin});
  await page.locator('#copy-request').click();
  assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),request);
  assert.equal(await page.locator('#send-request').evaluate(el=>el.open),false);
  assert.equal(await page.locator('#answer').isVisible(),true);
  await page.locator('#send-heading').click();
  assert.equal(await page.locator('#copy-request').isVisible(),true);
  assert.match(request,/那正式放映呢/);
  const wrong=structuredClone(answer);
  wrong.claims[0].evidence=[{source_id:'message-2',quote:'那正式放映呢？',relation:'supports'}];
  await page.locator('#answer').fill(JSON.stringify(wrong));
  await page.locator('#import-answer').click();
  assert.match(await page.locator('#answer-error').innerText(),/助手或工具/);
  await page.locator('#copy-repair').click();
  assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/助手或工具[\s\S]*完整 JSON/);
  await page.locator('[data-step="source"]').click();
  await page.locator('#prepare').click();
  assert.equal(await page.locator('#answer').inputValue(),JSON.stringify(wrong));
  await page.locator('#answer').fill('```json\n'+JSON.stringify(answer)+'\n```');
  await page.locator('#import-answer').click();
  assert.equal(await page.locator('#name').innerText(),answer.name);
  await page.locator('#prompt').fill('试映时保留现场声。');
  await page.locator('[data-step="source"]').click();
  await page.locator('#prepare').click();
  await page.locator('[data-step="result"]').click();
  assert.equal(await page.locator('#prompt').inputValue(),'试映时保留现场声。');
  await page.locator('[data-step="source"]').click();
  await page.locator('#source').fill('你说：\n'+quote+'\nChatGPT 说：\n收到。');
  await page.locator('#prepare').click();
  assert.equal(await page.locator('#answer').inputValue(),'');
  assert.equal(await page.locator('#answer-repair').isVisible(),false);
  await page.evaluate(()=>{
    Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(Error())}});
    document.execCommand=()=>false;
  });
  await page.locator('#copy-request').click();
  assert.equal(await page.locator('#request').isVisible(),true);
  assert.match(await page.locator('#copy-status').innerText(),/已选中/);
  assert.equal(await page.locator('#send-request').evaluate(el=>el.open),true);
  assert.ok(await page.locator('#request').evaluate(el=>el.selectionStart===0&&el.selectionEnd===el.value.length));
  assert.deepEqual(errors,[]);
  assert.ok(requests.every(r=>r.method==='GET'&&r.url.startsWith(origin+'/')));
});

test('a fresh visitor can open a log, pick one conversation from a ZIP or label individual messages',async t=>{
  const {page,origin,requests}=await mobilePage(t);
  const input=page.locator('#source-file');
  assert.equal(await input.isVisible(),true);
  await input.setInputFiles(fileURLToPath(new URL('fixtures/chat-import/rollout.jsonl',import.meta.url)));
  await page.locator('#model-panel').waitFor({state:'visible'});
  assert.match(await page.locator('#source-summary').textContent(),/你的 2 段文字、助手的 1 段文字/);
  await page.locator('[data-step="source"]').click();
  const {zipSync,strToU8}=await import('fflate');
  const chat=JSON.parse(await readFile(new URL('fixtures/chat-import/claude-conversations.json',import.meta.url),'utf8'))[0];
  const zip=zipSync({'conversations.json':strToU8(JSON.stringify([{name:'Other',chat_messages:[{sender:'human',text:'OTHER_CHAT'}]},chat]))});
  page.once('dialog',d=>d.accept());await input.setInputFiles({name:'export.zip',mimeType:'application/zip',buffer:Buffer.from(zip)});
  await page.locator('#conversation-picker').waitFor({state:'visible'});
  await page.locator('#chat-filter').fill('虚构展柜');await page.locator('#choose-chat').click();
  assert.match(await page.locator('#request').inputValue(),/不写库房号/);
  assert.doesNotMatch(await page.locator('#request').inputValue(),/OTHER_CHAT/);
  await page.locator('[data-step="source"]').click();
  await page.locator('#source').fill('');await page.locator('#single-turn summary').click();
  await page.locator('#turn-text').fill('我只选第一版');await page.locator('#append-user').click();
  await page.locator('#turn-text').fill('好的。\n用户：这是我引用的文本');await page.locator('#append-assistant').click();
  await page.locator('#prepare').click();
  assert.match(await page.locator('#source-summary').textContent(),/你的 1 段文字、助手的 1 段文字/);
  assert.ok(requests.every(r=>r.method==='GET'&&r.url.startsWith(origin+'/')));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
});

test('review native Claude Code dots and keep only the chosen turns',async t=>{
  const {page}=await mobilePage(t);
  await page.locator('#source-file').setInputFiles(fileURLToPath(new URL('fixtures/chat-import/claude-export.txt',import.meta.url)));
  const panel=page.locator('#chat-review');
  await panel.waitFor({state:'visible'});
  assert.equal(await panel.locator('input:checked').count(),2);
  await panel.getByText(/那也写库房号吗/).click();
  await page.locator('#choose-chat').click();
  assert.match(await page.locator('#source-summary').textContent(),/你的 2 段文字、助手的 1 段文字/);
  assert.doesNotMatch(await page.locator('#request').inputValue(),/model synthetic could not/);
});

test('Claude desktop selection keeps both texts in order after explicit role confirmation',async t=>{
  const {page}=await mobilePage(t);
  const raw=await readFile(new URL('fixtures/chat-import/claude-desktop-pair.txt',import.meta.url),'utf8');
  const source=page.locator('#source'),confirm=page.locator('#confirm-pair');
  for(const other of ['one turn','one\n\ntwo\n\nthree','用户：第一段\n\n第二段','第一段\n\nAssistant: second','one\ncontinued\n\ntwo']){
    await source.fill(other);
    assert.equal(await confirm.isVisible(),false);
    assert.equal(await page.locator('#prepare').isVisible(),true);
  }
  await source.fill(raw);
  assert.equal(await page.locator('#model-panel').isVisible(),false);
  await confirm.click();
  const [question,reply]=raw.split('\n\n');
  const transcript=await source.inputValue();
  assert.equal(transcript,'用户：'+question+'\n助手：'+reply);
  const request=await page.locator('#request').inputValue();
  assert.ok(request.includes(question) && request.indexOf(reply)>request.indexOf(question));
  assert.match(await page.locator('#source-summary').innerText(),/你的 1 段文字、助手的 1 段文字/);
});
