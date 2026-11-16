import {canonical,hash} from './core.mjs';
import {publicTrialSummary} from './choice-feedback.mjs';

// Every imported entry is revalidated. Files are local owner assertions, not signatures.
export function createLedger(engine, contract) {
  async function entry({artifact,portable,trial,preference_id,outcome,attributed}) {
    await engine.validate(artifact);
    const {id,...body}=portable;
    if(id!==await hash(canonical(body)) || body.artifact_type!=='portable_expression' ||
       body.profile_id!==artifact.id || typeof body.text!=='string' || body.text!==trial.material)
      throw Error('反馈的 prompt 与事件档案／导出版本不一致。');
    publicTrialSummary(contract,trial); // Validates the full private trial, not a public summary.
    if(attributed!==true) throw Error('请明确确认这次反馈归因于所选偏好。');
    if(!['adopted','corrected','unresolved'].includes(outcome)) throw Error('反馈结果无效。');
    const active=Object.values(await engine.effective(artifact)).flatMap(g=>[...g.regular,...g.exception,...g.constraint]);
    const preference=active.find(e=>e.id===preference_id);
    if(!preference) throw Error('所选偏好已撤回、被替换或不在当前有效事件中。');
    const event_id=await hash(canonical({created_at:trial.created_at,request:trial.request,
      imported_at:trial.prediction.imported_at,raw_response:trial.prediction.raw_response}));
    const value={artifact,portable,trial,preference_id,outcome,attributed:true,
      preference_version:await hash(canonical(preference)),event_id};
    return {...value,id:await hash(canonical(value))};
  }
  async function validate(ledger) {
    if(ledger?.schema_version!==1 || ledger.kind!=='runaway_preference_ledger' ||
       Object.keys(ledger).sort().join(',')!=='entries,kind,schema_version' ||
       !Array.isArray(ledger.entries) || ledger.entries.length>1000) throw Error('账本格式无效或超过1000条。');
    for(const old of ledger.entries) {
      const rebuilt=await entry(old);
      if(canonical(old)!==canonical(rebuilt)) throw Error('账本条目或绑定已改变。');
    }
    return ledger;
  }
  const empty=()=>({schema_version:1,kind:'runaway_preference_ledger',entries:[]});
  async function merge(left,right) {
    await validate(left);await validate(right);
    const entries=[...new Map([...left.entries,...right.entries].map(e=>[e.id,e])).values()];
    return validate({...empty(),entries});
  }
  async function add(ledger,input) {return merge(ledger,{...empty(),entries:[await entry(input)]});}
  async function summarize(ledger,artifact) {
    await validate(ledger);await engine.validate(artifact);
    const active=Object.values(await engine.effective(artifact)).flatMap(g=>[...g.regular,...g.exception,...g.constraint]);
    const rows=[];
    for(const p of active) {
      const version=await hash(canonical(p));
      for(const origin of ['demo_or_edited_demo','user_supplied_unverified']) {
        const found=ledger.entries.filter(e=>e.artifact.id===artifact.id&&e.preference_id===p.id&&e.preference_version===version&&e.trial.source_origin===origin);
        const groups=new Map();
        for(const e of found){const group=groups.get(e.event_id)||[];group.push(e);groups.set(e.event_id,group);}
        const counts={adopted:0,corrected:0,unresolved:0};const contexts=[];
        for(const [event_id,es] of groups){
          // Variants of one trial never become multiple successes; conflicts stay unresolved.
          const decisions=new Set(es.map(e=>canonical([e.outcome,e.trial.feedback,e.trial.reference])));
          const crossOrigin=ledger.entries.some(e=>e.event_id===event_id&&e.trial.source_origin!==origin);
          const outcome=decisions.size===1&&!crossOrigin?es[0].outcome:'unresolved';
          counts[outcome]++;contexts.push({event_id,situation:es[0].trial.queries[0].scenario,outcome});
        }
        rows.push({preference_id:p.id,preference_version:version,action:p.action,conditions:p.when_all,origin,...counts,contexts,
          review_priority:counts.corrected?'review':counts.unresolved?'uncertain':counts.adopted?'used_successfully':'untried'});
      }
    }
    return rows;
  }
  return {empty,entry,validate,merge,add,summarize};
}
