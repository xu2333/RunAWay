import {makeRequest} from '../../../web/dist/core.mjs';

const instructions = [
  '用户只改了上一句提议的一部分，且答复沿用了其中的具体值时，在同一条判断的 evidence 中逐字摘录两处：用上一句含具体值的提议交代指代来源（qualifies），用用户限定范围的答复说明接受了哪一部分（supports）。每处引文都标自己的 source_id；用户没有表态的部分留作未知。',
  '用户只改了提议的一部分时，把这句答复和上一句提议连起来读。把答复中沿用的内容补全，把改动的部分写成用户改定的样子；对方提过、但从用户答复看不出是否同意的部分，留作未知。',
  '遇到有条件的变更时，把触发条件、要改的对象和改成的具体值写在随身卡的同一句里，原文没给出的值留作未知。',
  '如果用户明确指定了一个会改变执行结果的非私密短值，在对应判断和随身 prompt 正文中原样保留它，并写清它适用于什么情境、条件变化时怎样处理。泛称不能代替这个值。只保留执行所需的最小片段；私人身份信息、凭证和原句仍应省去。材料没指定的值不要补。',
].join('\n\n');

export function pocketRequest(sources, budget) {
  return instructions + '\n\n' + makeRequest(sources, budget);
}
