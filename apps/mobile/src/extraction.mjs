import {makeRequest} from '../../../web/dist/core.mjs';

export function pocketRequest(sources, budget) {
  const instruction = '如果用户明确指定了一个会改变执行结果的非私密短值，在对应判断和随身 prompt 正文中原样保留它，并写清它适用于什么情境、条件变化时怎样处理。泛称不能代替这个值。只保留执行所需的最小片段；私人身份信息、凭证和原句仍应省去。材料没指定的值不要补。';
  return instruction + '\n\n' + makeRequest(sources, budget);
}
