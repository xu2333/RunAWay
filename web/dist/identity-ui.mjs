import {validateManual,manualText,renderManual,MANUAL_LABELS} from './manual-core.mjs';
import {lockCase,makeTrial,prediction,assess,puzzleText,revealText} from './holdout-core.mjs';
const $=id=>document.getElementById(id);
export function createIdentity({copy,notify,guard,currentBundle,record,invalidate}){
  let context=null,manual=null,trial=null,result=null;
  const revealed=new Set(),history=[];
  const add=(parent,tag,text,cls='')=>{const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;parent.append(el);return el;};
  function clearTrial(){trial=null;result=null;$('trial-requests').hidden=true;$('trial-reveal').hidden=true;$('trial-lock').disabled=false;for(const mode of ['baseline','personalized']){$(mode+'-prediction').value='';$(mode+'-prediction').disabled=false;}reviewReset();}
  function reviewReset(){$('puzzle-reviewed').checked=false;$('reveal-reviewed').checked=false;}
  function reset(){context=null;manual=null;clearTrial();}
  function clearInput(){$('holdout-enabled').checked=false;for(const el of $('holdout-fields').querySelectorAll('input,textarea,select')){if(el.type==='checkbox')el.checked=false;else el.value=el.tagName==='SELECT'?'A':'';}revealed.clear();history.length=0;reset();}
  async function lockInput(sources){if(!$('holdout-enabled').checked)return null;const input={};for(const key of ['source','quote','question','a','b','actual','reason'])input[key]=$('holdout-'+key).value;input.confirmed=$('holdout-confirmed').checked;return lockCase(input,sources);}
  for(const el of $('holdout-input').querySelectorAll('input,textarea,select'))el.addEventListener('input',invalidate);
  function paintManual(){
    $('manual-reviewed').checked=false;
    try{validateManual(manual,context.answer.claims);renderManual($('manual-canvas'),context.answer.name,manual,context.answer.claims,context.demo);$('download-manual').href=$('manual-canvas').toDataURL('image/png');$('manual-canvas').hidden=false;$('manual-error').textContent='';}
    catch(e){$('download-manual').removeAttribute('href');$('manual-canvas').hidden=true;$('manual-error').textContent=e.message;}
  }
  function checkedManual(){if(!manual)throw Error('这份结果还没有使用说明书。');validateManual(manual,context.answer.claims);if(!$('manual-reviewed').checked)throw Error('请先核对说明书，并确认其中的文字可以分享。');return manual;}
  $('manual-headline').addEventListener('input',()=>{if(manual){manual.headline=$('manual-headline').value;paintManual();}});
  $('copy-manual').addEventListener('click',guard(async()=>{await copy(manualText(context.answer.name,checkedManual(),context.answer.claims,context.demo));record('manual_copied');notify('使用说明书已复制，原始材料与引文未包含在内。');}));
  $('download-manual').addEventListener('click',event=>{try{checkedManual();record('manual_download_requested');notify('已请求下载预览中的说明书。');}catch(e){event.preventDefault();notify(e.message,true);}});
  function render(answer,sources,heldout,demo){
    reset();context={answer,sources,heldout,demo};manual=answer.manual?structuredClone(answer.manual):null;
    $('manual-content').hidden=!manual;$('manual-missing').hidden=!!manual;
    if(manual){
      $('manual-headline').value=manual.headline;$('manual-items').replaceChildren();
      for(const item of manual.items){
        const box=add($('manual-items'),'div','');const label=add(box,'label',MANUAL_LABELS[item.kind]);label.htmlFor='manual-'+item.kind;
        const field=add(box,'textarea','');field.id='manual-'+item.kind;field.rows=3;field.maxLength=120;field.value=item.text;field.addEventListener('input',()=>{item.text=field.value;paintManual();});
        const detail=add(box,'details','');add(detail,'summary','对照这句话的依据（仅在本页）');
        for(const id of item.claim_ids){const c=answer.claims.find(c=>c.id===id);add(detail,'p',c.statement,'small');for(const s of [...c.conditions.map(s=>'条件：'+s),...c.exceptions.map(s=>'例外：'+s)])add(detail,'p',s,'small');for(const e of c.evidence)add(detail,'blockquote',e.quote);}
      }
      paintManual();
    }
    $('trial-ready').hidden=!heldout;$('trial-missing').hidden=!!heldout;
    $('trial-origin').textContent=demo?'虚构演示：情境、经历均为编写，不计真实验证。':'已在提炼之前留出一段经历。网站只检查原句重复；你仍需核对语义泄漏与题面中立性。';
    if(heldout){$('puzzle-preview').value=puzzleText(heldout);$('trial-question').textContent=heldout.public_case.question+'\nA：'+heldout.public_case.a+'\nB：'+heldout.public_case.b;}
  }
  $('trial-start').addEventListener('click',guard(async()=>{
    if(!context?.heldout)throw Error('请先在第 1 步留出独立经历。');
    if(trial&&!result)throw Error('这轮请求已经锁定。请粘贴对应结果；如需改 prompt，会清空本轮。');
    clearTrial();const bundle=await currentBundle();trial=await makeTrial(context.heldout,bundle.portable,revealed.has(context.heldout.id));
    for(const mode of ['baseline','personalized'])$(mode+'-request').value=trial.modes[mode].request;
    $('trial-version').textContent=`锁定 prompt ${trial.portable_id.slice(0,12)} · ${trial.retest?'揭晓后的复测，不计首次':'尚未揭晓'}`;
    $('trial-requests').hidden=false;$('trial-demo-predictions').hidden=!context.demo;record('holdout_trial_prepared');notify('已锁定当前 prompt。分别在两个全新对话里运行，使用同一模型与设置；不要把真实答案发给它。');
  }));
  for(const mode of ['baseline','personalized'])$('copy-'+mode).addEventListener('click',guard(async()=>{if(!trial)throw Error('请先锁定当前 prompt。');await copy(trial.modes[mode].request);notify('已复制该组请求。请在独立的新对话中运行。');}));
  $('trial-demo-predictions').addEventListener('click',()=>{if(!context?.demo||!trial||result)return;for(const mode of ['baseline','personalized'])$(mode+'-prediction').value=JSON.stringify({request_id:trial.modes[mode].id,choice:mode==='baseline'?'unknown':'A',reason:mode==='baseline'?'预写演示：没有个人偏好，暂不能判断。':'预写演示：低成本且不涉及隐私时，倾向先观察现场反馈。'},null,2);notify('载入的是预写演示结果，没有调用模型，也不计真实验证。');});
  $('trial-lock').addEventListener('click',guard(()=>{
    if(!trial||result)throw Error('本轮结果已锁定，或尚未生成请求。');
    const baseline=prediction($('baseline-prediction').value,trial.modes.baseline.id),personalized=prediction($('personalized-prediction').value,trial.modes.personalized.id);
    result=assess(context.heldout,trial,baseline,personalized);revealed.add(context.heldout.id);history.push(structuredClone({heldout:context.heldout,trial,result}));
    for(const mode of ['baseline','personalized'])$(mode+'-prediction').disabled=true;$('trial-lock').disabled=true;
    const label=c=>c==='unknown'?'无法判断':c;
    $('trial-outcome').textContent=`你实际选了 ${result.actual}。普通 AI：${label(baseline.choice)}；带着你的 prompt：${label(personalized.choice)}。`;
    $('trial-note').textContent=result.note;$('trial-proof').textContent='你事先留出的原句：'+context.heldout.private_answer.quote;
    $('reveal-preview').value=revealText(context.heldout,result);$('trial-reveal').hidden=false;record('holdout_revealed');notify('两份判断已锁定并揭晓。这一次的命中或失误只代表这个案例。');
  }));
  $('copy-puzzle').addEventListener('click',guard(async()=>{if(!context?.heldout||!$('puzzle-reviewed').checked)throw Error('请核对题面预览并确认可分享。');await copy(puzzleText(context.heldout));record('holdout_puzzle_copied');notify('已复制题面，不包含真实答案或原始经历。');}));
  $('copy-reveal').addEventListener('click',guard(async()=>{if(!result||!$('reveal-reviewed').checked)throw Error('请先揭晓，并核对揭晓预览是否可以分享。');await copy(revealText(context.heldout,result));record('holdout_reveal_copied');notify('已复制揭晓文字，没有附上原始经历或引文。');}));
  return {render,reset,clearInput,lockInput,clearTrial,snapshot:()=>({edited_manual:manual,trial,result,history})};
}
