"""Generic source-only prompt revision;unchanged schema/binder/public renderer.

No observed test question,answer,label,person,card or review finding is loaded.
The revision is a hypothesis,not a demonstrated semantic repair.
"""
from runaway import grouped_support as grouped
REVISION='policy-scope-instructions-v1'
RULES='''\nSCOPE_REVISION_V1\n
先区分三种来源语义：仅一次的选择、用户明确界定范围的今后政策、由用户说明优先的局部例外。不要把观察次数多或动作相同当作通用政策。
对可独立适用的明确今后政策，以用户给出的当前适用范围和必要条件表述规则；早期单次事件的叙述性背景不能自动成为该政策的新门槛。每个公开条件都要有当前必要性依据，而不只是能在旧记录中找到同一句话。
用户明确持续适用的限制不能因较晚消息没再提及就丢掉。若较晚消息只是在原情境中改选动作，或仍指向原有条件，保留原必要条件；仅有省略、时间更晚或“以后”字样不足以证明所有旧限制已解除。适用范围是否已完整独立给出仍不清楚时，不自行扩大。
明确政策允许同范围内未逐项列举的新实例；仅一次观察仍限于其已记录条件，不把它外推成同类场景的必然选择。共享scope只承载组内每条规则真正共有的必要条件；条件不同就分组，不把旧条件移进共享范围使新政策额外收窄。
只把用户的明确选择和认可作为证据。例外仅在用户给出的例外条件成立时优先，不因看起来更稳妥就造例外；一个局部改口不改动别的情境。同级有效冲突未被解决时仍未知，不按先后、常识或当前题目裁决。
缺少影响选择的必要条件、超出范围或没有唯一已知动作仍未知；不能为了提高覆盖率整体放宽未知。只有所有可能且有记录支持的适用分支都同选时才合并作答；未覆盖的可能分支不能忽略。
只输出现有schema；decisions/contexts使用当前用户政策及限制的逐字锚点，旧决定仍用supersedes私有追溯。渲染器、公共边界声明、指南与整卡字符预算不变。无题目、目标答案或行为评分可供你优化。\nEND_SCOPE_REVISION_V1\n'''

def make_request(sources,budget=1536):
 req=grouped.make_request(sources,budget)
 marker='\nEXTRACTION_INPUT_JSON:\n'
 prefix,body=req['prompt'].split(marker,1)
 return {'schema':req['schema'],'prompt':prefix+RULES+marker+body}

def bind(answer,sources,budget=1536):
 return grouped.bind(answer,sources,budget)
