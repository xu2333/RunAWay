import {decodeChoiceResponse} from './choice-core.mjs';
import {makeTrialSnapshot, makeTrialRecord, publicTrialSummary, publicTrialIssueUrl} from './choice-feedback.mjs';
const $ = id => document.getElementById(id);
let contract, snapshot = null, prediction = null, synthetic = false;
let predictionSeen = false, referenceAfterPrediction = false, referenceAt = null, publicDraft = null;
function notice(message) { $('notice').textContent = message; $('notice').hidden = !message; }
function invalidateSummary() {
  publicDraft = null; $('public-feedback-panel').hidden = true;
  $('public-feedback-preview').value = ''; $('public-reviewed').checked = false;
  $('download-summary').disabled = true; $('github-summary').disabled = true;
}
function resetReference() { $('reference-choice').value = ''; referenceAfterPrediction = false; referenceAt = null; }
function refreshReferenceOptions() {
  const labels = $('options').value.split(/\r?\n/).map(x => x.trim()).filter(Boolean).slice(0,8);
  $('reference-choice').replaceChildren(new Option('还没决定／暂不提供',''),
    ...labels.map((text,i) => new Option('ABCDEFGH'[i] + ' · ' + text,'ABCDEFGH'[i])));
}
function invalidate() {
  snapshot = null; prediction = null;
  $('request-panel').hidden = true; $('result').hidden = true; $('waiting').hidden = false;
  for (const id of ['answer','request','correction']) $(id).value = '';
  $('rating').value = 'unrated'; notice('');
  invalidateSummary();
}
// Editing the fictional demo must not relabel its derivatives as real user data.
for (const id of ['memory','scenario','options']) $(id).addEventListener('input', () => {
  if (id === 'options') refreshReferenceOptions();
  resetReference(); invalidate();
});
$('reader-mode').addEventListener('change', invalidate);
$('reference-choice').addEventListener('change', () => {
  referenceAfterPrediction = predictionSeen;
  referenceAt = $('reference-choice').value ? new Date().toISOString() : null;
  invalidate();
});
$('answer').addEventListener('input', () => {
  if ($('answer').value.trim()) predictionSeen = true;
  prediction = null; $('result').hidden = true; $('rating').value = 'unrated'; $('correction').value = '';
  invalidateSummary();
});
for (const id of ['rating','correction']) $(id).addEventListener('input', invalidateSummary);
$('memory-file').addEventListener('change', async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    if (file.size > 400000 || !/\.(txt|md)$/i.test(file.name)) throw Error('请选择不超过 400 KB 的 .txt 或 .md 随身 prompt。');
    const text = await file.text();
    if ([...text].length > 100000) throw Error('随身 prompt 超过 100,000 字符。');
    $('memory').value = text; synthetic = false; resetReference(); invalidate();
  } catch (error) {notice(error.message);} finally {event.target.value = '';}
});
$('prepare').addEventListener('click', () => {
  invalidate();
  try {
    const material = $('memory').value;
    if (!material.trim()) throw Error('请先带上你的完整随身 prompt。');
    const texts = $('options').value.split(/\r?\n/).map(t => t.trim()).filter(Boolean);
    const queries = [{id:'q1', scenario:$('scenario').value, options:Object.fromEntries(texts.map((t,i) => ['ABCDEFGH'[i],t]))}];
    const readerMode = $('reader-mode').value;
    snapshot = makeTrialSnapshot(contract, material, queries, {readerMode, synthetic,
      referenceLabel:$('reference-choice').value, referenceAfterPrediction, referenceAt});
    $('request').value = snapshot.request.prompt; $('request-panel').hidden = false; $('waiting').hidden = true;
    notice(synthetic ? '这是虚构示例或其修改版；没有调用模型，也不代表你的偏好。' : '请求已准备。请发送到一个全新对话，再把回答带回来。');
  } catch (error) {notice(error.message);}
});
$('copy').addEventListener('click', async () => {
  try {if (!snapshot) throw Error('请先准备请求。'); await navigator.clipboard.writeText(snapshot.request.prompt); notice('已复制。请求含你的随身 prompt 与题目，请发到你选择的服务。');}
  catch (error) {notice('复制未完成；可展开完整请求并手动复制。');}
});
$('import').addEventListener('click', () => {
  prediction = null; $('result').hidden = true;
  try {
    if (!snapshot) throw Error('请先准备当前题目的请求。');
    const raw = $('answer').value;
    const decoded = decodeChoiceResponse(snapshot.queries, raw);
    predictionSeen = true;
    prediction = {raw_response:raw, decoded, imported_at:new Date().toISOString()};
    const answer = decoded.q1;
    $('outcome').textContent = answer.unknown ? '这一次，暂时无法确定。' : answer.text;
    $('result-note').textContent = answer.unknown ? '模型选择了 U。它可能缺少必要信息，也可能没有读懂已有条件。' : '这是模型给出的选择，还需要你核对条件与例外。一次命中不能证明它了解完整的你。';
    const reference = snapshot.reference;
    $('reference-note').textContent = reference.label === null ? '本题未记录本人选择，暂不做答案对照。' :
      (answer.text === reference.text ? '与本页记录的本人选择一致。' : '与本页记录的本人选择不同。') +
      (reference.timing === 'before_prediction_in_session' ? ' 本人选择记录于本次页面会话的预测之前。' : ' 本人选择是在本次页面会话看到预测后记录或修改的。') +
      ' 是否具备足够来源依据仍需另行核对。';
    $('result').hidden = false; notice('');
  } catch (error) {notice(error.message);}
});
function currentRecord() {
  if (!snapshot || !prediction) throw Error('请先完成本次预测。');
  return makeTrialRecord(contract, snapshot, prediction.raw_response,
    {rating:$('rating').value, correction:$('correction').value}, prediction.imported_at);
}
function download(filename, record) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(record,null,2)+'\n'], {type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('download').addEventListener('click', () => {
  try { download('runaway-choice.private.json',currentRecord()); } catch (error) {notice(error.message);}
});
$('preview-summary').addEventListener('click', () => {
  try {
    invalidateSummary(); publicDraft = publicTrialSummary(contract,currentRecord());
    $('public-feedback-preview').value = JSON.stringify(publicDraft,null,2); $('public-feedback-panel').hidden = false;
    const timing = publicDraft.reference_timing === 'not_recorded' ? '未记录本人选择' :
      publicDraft.reference_timing === 'before_prediction_in_session' ? '本人选择在预测前记录' : '本人选择在预测后记录或修改';
    const match = publicDraft.declared_choice_match === null ? '暂不做答案对照' :
      publicDraft.declared_choice_match ? '与本人选择一致' : '与本人选择不同';
    $('public-summary-note').textContent = (publicDraft.origin === 'demo_or_edited_demo' ? '虚构示例或其修改版' : '用户提供、尚未验证的材料') +
      '；' + timing + '；' + match + '；模型' + (publicDraft.model_returned_unknown ? '答了未知' : '给出一个选项') +
      '；你的评分：' + ({unrated:'暂未评分',fits:'这次像我',misses:'这次没理解我',uncertain:'我也不确定'})[publicDraft.rating] + '。';
  } catch (error) {notice(error.message);}
});
$('public-reviewed').addEventListener('change', () => {
  const enabled = publicDraft !== null && $('public-reviewed').checked;
  $('download-summary').disabled = !enabled; $('github-summary').disabled = !enabled;
});
function reviewedSummary() {
  if (!publicDraft || !$('public-reviewed').checked) throw Error('请先核对摘要并勾选确认。');
  if (JSON.stringify(publicTrialSummary(contract,currentRecord())) !== JSON.stringify(publicDraft)) {
    invalidateSummary(); throw Error('反馈已改变，请重新预览并确认。');
  }
  return publicDraft;
}
$('download-summary').addEventListener('click', () => {
  try {download('runaway-choice-summary.json',reviewedSummary());} catch (error) {notice(error.message);}
});
$('github-summary').addEventListener('click', () => {
  try {
    window.open(publicTrialIssueUrl(reviewedSummary()),'_blank','noopener,noreferrer');
    notice('已请求打开 GitHub 公开草稿，请检查后手动提交。打开草稿不计作成功提交。');
  } catch (error) {notice(error.message);}
});
$('demo').addEventListener('click', async () => {
  try {
    const response = await fetch('./choice-demo.json'); if (!response.ok) throw Error('示例没有载入，请刷新后重试。');
    const demo = await response.json(); invalidate(); synthetic = true;
    $('memory').value = demo.material; $('scenario').value = demo.queries[0].scenario; $('options').value = Object.values(demo.queries[0].options).join('\n');
    refreshReferenceOptions(); resetReference();
    notice('这是合成人物的演示材料。点击装好这一题，可到你常用的 AI 试试。');
  } catch (error) {notice(error.message);}
});
$('clear').addEventListener('click', () => {
  for (const id of ['memory','scenario','options']) $(id).value = '';
  $('reader-mode').value = 'standard'; synthetic = false; predictionSeen = false;
  refreshReferenceOptions(); resetReference(); invalidate();
});
try {
  const response = await fetch('./choice-contract.json'); if (!response.ok) throw Error('读取协议未载入，请刷新重试。');
  contract = await response.json(); $('prepare').disabled = false; $('demo').disabled = false;
} catch (error) {notice(error.message);}
