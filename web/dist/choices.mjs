import {makeChoiceRequest, decodeChoiceResponse} from './choice-core.mjs';
const $ = id => document.getElementById(id);
let contract, snapshot = null, prediction = null, synthetic = false;
function notice(message) { $('notice').textContent = message; $('notice').hidden = !message; }
function invalidate() {
  snapshot = null; prediction = null;
  $('request-panel').hidden = true; $('result').hidden = true; $('waiting').hidden = false;
  for (const id of ['answer','request','correction']) $(id).value = '';
  $('rating').value = 'unrated'; notice('');
}
// Editing the fictional demo must not relabel its derivatives as real user data.
for (const id of ['memory','scenario','options']) $(id).addEventListener('input', invalidate);
$('reader-mode').addEventListener('change', invalidate);
$('answer').addEventListener('input', () => {prediction = null; $('result').hidden = true; $('rating').value = 'unrated'; $('correction').value = '';});
$('memory-file').addEventListener('change', async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    if (file.size > 400000 || !/\.(txt|md)$/i.test(file.name)) throw Error('请选择不超过 400 KB 的 .txt 或 .md 随身 prompt。');
    const text = await file.text();
    if ([...text].length > 100000) throw Error('随身 prompt 超过 100,000 字符。');
    $('memory').value = text; synthetic = false; invalidate();
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
    const request = makeChoiceRequest(contract, material, queries, 'text', readerMode);
    snapshot = {schema_version:1, created_at:new Date().toISOString(), synthetic, source_origin:synthetic ? 'demo_or_edited_demo' : 'user_supplied_unverified', material, queries, answer_format:'text', reader_mode:readerMode, request};
    $('request').value = request.prompt; $('request-panel').hidden = false; $('waiting').hidden = true;
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
    prediction = {raw_response:raw, decoded, imported_at:new Date().toISOString()};
    const answer = decoded.q1;
    $('outcome').textContent = answer.unknown ? '这一次，暂时无法确定。' : answer.text;
    $('result-note').textContent = answer.unknown ? '模型选择了 U。它可能缺少必要信息，也可能没有读懂已有条件。' : '这是模型给出的选择，还需要你核对条件与例外。一次命中不能证明它了解完整的你。';
    $('result').hidden = false; notice('');
  } catch (error) {notice(error.message);}
});
$('download').addEventListener('click', () => {
  if (!snapshot || !prediction) return;
  const record = {...snapshot, ...prediction, feedback:{rating:$('rating').value, correction:$('correction').value}, model_service:'user_selected_unverified', model_calls_by_app:0, independent_fidelity_verified:false};
  const url = URL.createObjectURL(new Blob([JSON.stringify(record,null,2)+'\n'], {type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = 'runaway-choice.private.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$('demo').addEventListener('click', async () => {
  try {
    const response = await fetch('./choice-demo.json'); if (!response.ok) throw Error('示例没有载入，请刷新后重试。');
    const demo = await response.json(); invalidate(); synthetic = true;
    $('memory').value = demo.material; $('scenario').value = demo.queries[0].scenario; $('options').value = Object.values(demo.queries[0].options).join('\n');
    notice('这是合成人物的演示材料。点击装好这一题，可到你常用的 AI 试试。');
  } catch (error) {notice(error.message);}
});
$('clear').addEventListener('click', () => {for (const id of ['memory','scenario','options']) $(id).value = ''; $('reader-mode').value = 'standard'; synthetic = false; invalidate();});
try {
  const response = await fetch('./choice-contract.json'); if (!response.ok) throw Error('读取协议未载入，请刷新重试。');
  contract = await response.json(); $('prepare').disabled = false; $('demo').disabled = false;
} catch (error) {notice(error.message);}
