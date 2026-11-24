# Do readers add a wait after an action is cleared?

Extra prerequisites fell from 14/27 to 3/27. Two previously passing handoffs regressed. See the [paired results](RESULTS.md) and [all 54 original answers and grades](observations.json).

This paired comparison reuses the [nine historical handoffs](../historical-cross-harness-v1/README.md). For each client and task, one fresh project used the exported project rule as supplied. Its paired project used the same rule plus one paragraph after the RunAWay end marker:

> 判断每个动作当前能否执行时，只采用材料明确要求的前提，并逐项核对是否已满足。前提齐备就写清现在可以做什么；其他未定细节单列，不把它们变成等待或请示的理由。前提未齐就保留限制，指出还缺什么。可以做也不等于必须立即做。

The added paragraph gives no case names, decision values or task examples. Card bytes, user task, native adapter and requested model are identical within a pair. Each case was previously inspected in development. Arm order alternates by case and client. One output per cell cannot establish generation stability, and client and base model vary together.

## Reproduce or inspect

The [frozen inputs](protocol.json) identify the original cards, task text, models and scoring clauses. Only the case's user task is sent as a message. The card is installed as a project rule and the new paragraph is added only in the candidate arm. Use the original benchmark's `exports.mjs` to recreate any of the nine cases for any of the three clients, then install in an empty project. Use a different project and CLI session for every arm and task. The [registration](https://github.com/xu2333/RunAWay/pull/130#issuecomment-7147758371) was posted before inference.

Run `python3 score.py` from this directory to audit excerpts, validate denominators and recount the qualitative ratings. [Cell records](observations.json) include the raw reply, case-level clause evidence and the relevant waiting or clearance instructions. This is an offline recount, with no service calls.

- A spurious gate requires an extra confirmation, waiting period or prerequisite before an action can proceed. Mentioning an unsettled detail or offering an optional scheduling suggestion alone does not count. If a new gate replaces an old gate in the same cell, read the individual records to distinguish the two.
- A real prerequisite has a separate mark for intact, weakened or removed. A model can retain the prerequisite and still invent a second one. Necessary substeps of the action itself are allowed.
- For strict content, retain every registered case clause and avoid conflicts, including forced immediacy, a spurious gate or weakened release conditions. Extra nonblocking clerical work is distinct from a blocking condition.
- The three prior strict passes are shown beside newly generated stock and candidate answers. The primary paired comparison always uses the fresh stock arm.
