const $=id=>document.getElementById(id),esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=value=>value==null?'不适用':(100*value).toFixed(1)+'%',num=value=>value==null?'缺失':value.toLocaleString('zh-CN',{maximumFractionDigits:1});
const labels={none:'无记忆',full_history:'完整历史（实测）',current_reference_naive:'参考：只留最后记录',new_reference_codec:'参考：保留时序事件',random_delete:'随机删半',shuffled_person:'打乱相似人物',delete_exception:'删除关键例外',delete_hard:'删除硬约束',stale_updates:'丢失后续更新',timeout:'模拟超时 / 缺失'};
const layers={facts:'事实',strength:'偏好强弱',conditions:'条件',exceptions:'例外',hard_constraints:'硬约束',updates:'更新 / 清除',revocations:'撤销 / 恢复',distinctions:'人物差异',unknowns:'未知偏好'};
const colors={none:'#c4bba1',full_history:'#839a6d',current_reference_naive:'#ac8b69',new_reference_codec:'#285c49',random_delete:'#b6a56b',shuffled_person:'#a27e9b',delete_exception:'#bd775b',delete_hard:'#ad4c3a',stale_updates:'#7d8ca5',timeout:'#aaa'};
let board=null;
function current(){return board.report.rows.find(r=>r.split===$('split').value&&r.condition===$('condition').value&&r.budget===Number($('budget').value));}
async function refresh(){try{const response=await fetch('./metric-data.synthetic.json',{cache:'no-store'});if(!response.ok)throw Error('工件读取失败');const data=await response.json();if(!data.available)throw Error('校准工件尚未就绪。');const first=!board;board=data;if(first){$('budget').innerHTML=board.report.budgets.map(b=>`<option value="${b}">${b} ${esc(board.report.tokenizer.unit)}</option>`).join('');$('budget').value=String(Math.max(...board.report.budgets));$('condition').innerHTML=Object.keys(labels).map(k=>`<option value="${k}">${labels[k]}</option>`).join('');$('condition').value='delete_exception';}render(true);$('error').hidden=true;}catch(error){$('error').textContent=error.message;$('error').hidden=false;}}
function render(rebuild=false){
 const split=$('split').value,people=board.people.filter(p=>p.split===split),row=current(),q=row.quality,hard=q.hard_constraints,twins=q.matched_person_disagreements;
 $('scope').textContent=`${board.people.length} 个合成人物 · 开发 / 评测各 ${people.length} 人 · 每人 ${people[0]?.queries.length??0} 个查询 · 外部模型调用 0`;
 $('tokenizer').textContent=board.report.tokenizer.model_name??board.report.tokenizer.unit;
 const cards=[['端到端正确率',pct(q.accuracy),`${q.correct} / ${q.planned} · 缺失 ${q.missing}`],['最弱关键分层',pct(q.worst_critical_accuracy),'硬约束、例外、更新等分别验收'],['硬约束错误',`${hard.incorrect} / ${hard.planned}`,`实际违反 ${hard.observed_violations} · 弃答 ${hard.abstentions} · 缺失 ${hard.missing}`],['近似人物分歧',`${twins.correct} / ${twins.planned}`,`两人须同时正确 · 缺失 ${twins.missing}`]];
 $('kpis').innerHTML=cards.map(([label,value,note])=>`<article class="kpi">${esc(label)}<strong>${esc(value)}</strong><small>${esc(note)}</small></article>`).join('');
 $('layers').innerHTML=Object.entries(q.strata).map(([key,value])=>`<div class="layer"><span>${esc(layers[key]??key)}</span><meter min="0" max="1" value="${value.accuracy}"></meter><strong class="${value.accuracy<1?'bad':'good'}">${value.correct}/${value.planned}</strong></div>`).join('');
 $('cost').textContent=`实际记忆 ${num(row.mean_memory_units)} ${board.report.tokenizer.unit} / 人；完整历史的 ${pct(row.memory_ratio_to_full)}。${row.budget_applies?'预算 '+row.budget:'此基线不受预算截断'}。只计完整记忆，生成与使用成本另计。`;
 $('retention').textContent=`相对完整历史退化 ${pct(q.degradation_vs_history)}；相对无记忆归一化保留 ${pct(q.normalized_retention)}。分母过小不适用；负值保持负值。`;
 const rows=board.report.rows.filter(r=>r.split===split&&r.budget===row.budget);
 $('comparisons').innerHTML=rows.map(r=>{const a=r.quality,h=a.hard_constraints,t=a.matched_person_disagreements;return `<tr class="${r.condition===row.condition?'active':''}"><td><button data-condition="${r.condition}">${labels[r.condition]}</button></td><td>${a.correct}/${a.planned}<small>${pct(a.accuracy)} · 缺 ${a.missing}</small></td><td>${pct(a.worst_critical_accuracy)}</td><td>${h.incorrect} / ${h.observed_violations}<small>弃答 ${h.abstentions} · 缺 ${h.missing}</small></td><td>${t.correct}/${t.planned}</td><td>${num(r.mean_memory_units)}<small>${r.memory_people}/${r.planned_people} 人有记忆</small></td></tr>`;}).join('');
 const checks=Object.entries(board.report.discrimination_checks);$('checks').textContent=`${checks.filter(([,pass])=>pass).length}/${checks.length} 损坏检查通过`;
 $('check-details').innerHTML=checks.map(([name,pass])=>`<p class="${pass?'good':'bad'}">${pass?'✓':'×'} ${esc(name)}</p>`).join('');
 const saved=$('persona').value;if(rebuild||!people.some(p=>p.id===saved)){$('persona').innerHTML=people.map(p=>`<option value="${p.id}">${p.id}</option>`).join('');if(people.some(p=>p.id===saved))$('persona').value=saved;}
 curve();sample();$('footer').textContent=`冻结 ${board.snapshot.id.slice(0,12)} · ${board.source} · 参考校准 ${num(board.costs.reference_calibration_seconds)} 秒 · 仅词表分词，未执行语言模型推理。普通程序耗时不折算成模型 tokens。`;
}
function curve(){
 const W=760,H=290,L=50,R=20,T=18,B=42,max=Math.max(1,...board.report.budgets),x=v=>L+v/max*(W-L-R),y=v=>T+(1-v)*(H-T-B),selected=$('condition').value;
 const grid=[0,.25,.5,.75,1].map(v=>`<line x1="${L}" y1="${y(v)}" x2="${W-R}" y2="${y(v)}" stroke="#e5e9dc"/><text x="${L-8}" y="${y(v)+4}" fill="#7b8772" text-anchor="end" font-size="10">${Math.round(v*100)}%</text>`).join('');
 const paths=Object.keys(labels).map(condition=>{const rows=board.report.rows.filter(r=>r.split===$('split').value&&r.condition===condition).sort((a,b)=>a.budget-b.budget);return `<polyline fill="none" stroke="${colors[condition]}" opacity="${condition===selected||['full_history','new_reference_codec'].includes(condition)?1:.25}" stroke-width="${condition===selected?3:1.5}" points="${rows.map(r=>`${x(r.budget)},${y(r.quality.accuracy)}`).join(' ')}"><title>${esc(labels[condition])}</title></polyline>`;}).join('');
 const ticks=board.report.budgets.filter((b,i)=>i%2===0).map(b=>`<text x="${x(b)}" y="${H-15}" text-anchor="middle" font-size="10" fill="#7b8772">${b}</text>`).join('');
 $('curve').innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="预算与端到端质量曲线">${grid}${paths}${ticks}<line x1="${x(Number($('budget').value))}" x2="${x(Number($('budget').value))}" y1="${T}" y2="${H-B}" stroke="#556d4e" stroke-dasharray="3 5"/></svg>`;
 $('legend').innerHTML=Object.entries(labels).map(([k,name])=>`<button data-condition="${k}" class="legend-${k}">● ${esc(name)}</button>`).join('');
}
function sample(){
 const p=board.people.find(p=>p.id===$('persona').value);if(!p)return;
 const condition=$('condition').value,budget=Number($('budget').value),memory=board.memories.find(r=>r.persona_id===p.id&&r.condition===condition&&r.budget===budget),pred=board.predictions.find(r=>r.persona_id===p.id&&r.condition===condition&&r.budget===budget)?.answers??{};
 $('history').textContent=p.history;$('memory').textContent=memory?.memory??'模拟失败：未产生记忆，所有预定查询仍在分母中。';
 $('cases').innerHTML=p.queries.map(c=>{const value=pred[c.public.id],right=c.allowed_answers.includes(value);return `<article class="case"><small>${esc(layers[c.stratum])} · ${esc(c.public.id)}</small><div>${esc(c.public.question)}</div><strong class="${right?'good':'bad'}">真值 ${esc(c.allowed_answers.join(' / '))} · 恢复 ${esc(value??'缺失')}</strong></article>`;}).join('');
}
for(const id of ['split','condition','budget'])$(id).addEventListener('change',()=>render(id==='split'));$('persona').addEventListener('change',sample);$('refresh').addEventListener('click',refresh);document.addEventListener('click',e=>{const button=e.target.closest('[data-condition]');if(button){$('condition').value=button.dataset.condition;render();}});
await refresh();$('live').textContent='离线快照';
