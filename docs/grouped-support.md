# Experimental shared-scope taste cards

`distill --format grouped-v1` extracts source-supported choices under shared
scopes. A scope is written once; every child condition must also hold. Public
`P0`–`P9` values give explicit precedence, with higher values first and equal-P
conflicts unknown. The complete guide, name, tagline, scopes, conditions,
actions, priorities, unknown statements and any literal glossary count inside
the whole Unicode-character budget. There is no external hidden decoder.

This is an **opt-in experimental contract**, not a measured fidelity improvement.
`support-v1` remains the default. The preceding [budget-frontier study](../benchmarks/heterogeneous-frontier-v1/README.md)
found nine over-budget default candidates, while all60actually read cells from
valid cards were right. Grouping is a candidate response to that bottleneck;
these offline integration tests do not establish that it generates512-character
cards or preserves real users' choices. A fresh generation can still fail its
budget, evidence or format checks; there is no retry or truncation.

## Try without a model service

The following answer is **developer-authored toy data**, not model output or a
new model accuracy result. It exercises scoped local updates, priorities and
more than two actions:

```sh
runaway distill --format grouped-v1 \
  --input examples/grouped-sources.synthetic.json \
  --answer examples/grouped-answer.synthetic.json \
  --budget-chars 512 --out grouped-demo
runaway export grouped-demo/portable.json
runaway attach grouped-demo/portable.json --project /path/to/project \
  --target codex,claude,opencode,antigravity,deepseek
runaway doctor --project /path/to/project
```

All these commands run offline. Attachment tests verify files and checksums;
they do not prove that each actual harness loads or interprets the memory.
`prompt.md` can also be pasted directly into a model. Use the ordinary
[`choices prepare/import` workflow](automatic-support.md#replay-a-choice-with-any-llm)
to inspect a prediction; it does not correct answers from references or grant
action authority.

For your explicitly selected role-labelled sources, prepare a source-only
request for any model or harness and import its JSON:

```sh
runaway distill --format grouped-v1 --input selected-sources.json \
  --budget-chars 512 --prepare > request.private.json
# Give only the request's system/prompt/schema to your chosen model.
runaway distill --format grouped-v1 --input selected-sources.json \
  --budget-chars 512 --answer answer.private.json --out my-groups
```

These CLI commands make zero model calls. If you explicitly want the installed
Codex backend to send that selected source to its configured service, supply
`--backend codex --model YOUR_MODEL --out my-groups` instead of prepare/import.
That path makes one attempt, preserves the request/raw response/failure privately
and makes no automatic retry. It does not inspect other chats or projects.
A text input is treated as a user-authored narrative; convert mixed-speaker logs
to role-labelled JSON first. JSON sources/answers with duplicate keys are refused.

## Scope and update contract

The model returns `name`, `tagline`, `groups`, `unknowns`. Each group has `scope`,
private `contexts` quote anchors and `rules`. Each rule has `when`, `choose`,
`priority`, private user `decisions`, private `contexts` and `supersedes` source
IDs. Conditions remain natural language; continuous ranges, single observations
and arbitrary numbers of action types are allowed. No fixed feature catalogue,
closed-world family or two-action restriction is required.

- Group scope AND child condition must hold. Sharing an action does not broaden
  the union of observed situations or turn a single number into a numeric range.
- Only user-role sources can support a choice. Scope/rule contexts must contain
  exact source quotes; assistant/tool text may provide context but cannot serve
  as a user's decision.
- A superseded source must be a user message preceding **every** new decision
  anchor. Supersession is private audit metadata, not a global delete operation.
  One old message may still support an unrelated choice in another scope.
- An explicitly superseded rule left active in the exact same declared scope
  and condition is rejected. Different or paraphrased conditions are not
  semantically normalized or proven equivalent. The model must extract current
  choices and preserve unresolved conflicts; the compiler does not silently
  prune them or pick a convenient winner.
- Priority is rendered explicitly inside the budget. Structural validation of
  a number is not proof that the source justifies that priority. Equal-priority
  conflicts remain represented so the reader can return unknown.

The public grammar quotes and escapes literal strings. Embedded newlines,
quotes, arrows and Unicode separators cannot create extra structural rows.
Round-trip parsing checks those components, not their logical truth. The private
record retains the entire selected sources, evidence, provenance and checksums;
review public prose for sensitive details before sharing it.

`profile.private.json` has type `grouped_source_support_profile`; the legacy
`relayout` command deliberately refuses it. Re-import the saved grouped answer
with the original selected sources into a **new directory** to apply another
budget. Do not treat retrospective re-exports or repaired candidates as an
independent prospective experiment. `--layout rows` belongs to `support-v1`;
the grouped format has its own fixed renderer.

Exact quotes, backward references, scope/P parsing and complete character counts
do not certify semantic support, same-condition updates, completeness, privacy,
readability, real-person fidelity or cross-model portability. Every output stays
`candidate_unvalidated`. Model-based generation yield and choice fidelity for
this new format remain to be measured separately.
