# Measured loss: project identities disappear while choices survive

The separately approved51-attempt scope is closed: **47actual local CLI inference
attempts,16extractions,28reads,3controls**. Four readers were skipped for two
invalid graphs;their slots expired. No retries,repairs,replacements or missing
usage. Both own full controls retained32/32;none retained12/32,all unknowns.
The17earlier observation seals and the entire scientific source remain intact.

## Fixed endpoints

Each cell retains64person/cases (40known,24unknown). A case needs both independent
generations ×both reads ×both option orders correct: eight answers. Missing
products stay missing,not U. These are the same64cases across cells,not256
independent observations. Methods: **coverage**=`object-coverage-guidance-v1`,
**accounted**=`source-accounted-graph-v1`.

| Method | Whole-card cap | Joint | Known | Unknown | Missing joint |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coverage | 768 | 24/64 | 12/40 | 12/24 | 32 |
| Accounted | 768 | 24/64 | 12/40 | 12/24 | 32 |
| Coverage | 1536 | 48/64 | 24/40 | 24/24 | 0 |
| Accounted | 1536 | 48/64 | 24/40 | 24/24 | 0 |

At1536,the16old-name cases all fail the eight-answer endpoint in both methods.
All48other cases pass,including ordinary/current-name choices,local exceptions,
current-name late revisions,missing prerequisites,conflicting contexts and
unconfirmed actual execution. All8cards are valid (744–800characters). The
16-case alias and16-case late-revision slices overlap in8;do not add them.

## A tie hides recoveries and new losses

Generation0 at1536 retains56/64 in each method,but the losses belong to different
people:accounted recovers8willow old-name choices and newly loses8kestrel old-name
choices relative to coverage. Generation1 retains48/64 in each,with both losing
the same16old-name choices. Thus the stricter combined comparison is48kept,
16both-fail,0recovered,0new-loss;that does **not** mean no individual generation
introduced new loss. The replayer preserves both levels.

At768,generation0 coverage retains24/64 with32missing;accounted36/64 with none
missing. On available matched cases there are12kept,8both-fail and12new observed
losses;the remaining32 are baseline-missing,not demonstrated recoveries.
Generation1 coverage retains48/64 with no missing;accounted24/64 with32missing.
Their combined strict endpoints each have32missing,but for opposite people.
Consequently there are32baseline-missing and32candidate-missing paired cases;
there is no fully observed joint-method intersection at that budget.

No identical-parent repeated-read differences or within-read option-order
differences were observed. All valid-card wrong answers are U on known choices,
rather than a different concrete choice. This does not establish general reader
stability or a uniquely proven causal explanation.

## What was lost, with original evidence

| Original parent | Concrete omission/failure | Observed consequence |
| --- | --- | --- |
| 7:accounted,kestrel,1536,g0 | m37–m40 rename relations survive in private accounting reasons;objects contain current names only | All8old-name choices return U in both reads/orders |
| 13:coverage,willow,1536,g0 | Public objects contain current names only | Same8old-name losses for the other person |
| 40/43/46/49:both methods,1536,g1 | Old-name links absent from public scopes | All16old-name cases lost in each method |
| 25:accounted,willow,768,g0 | Objects retain domain descriptions,but omit **both old and current labels** | All20known choices return U,including12additional current-label choices |
| 19:coverage,kestrel,768,g0 | Revision decisions include early m01–m04 candidate-definition messages | Chronology refusal;only its own two reads skipped |
| 37:accounted,willow,768,g1 | m45–m48 confirmations support nickname revisions,then are reused as later full-name revisions | Same-position evidence violates strict revision chronology;only its two reads skipped |

For parent7,the four rename messages are correctly labelled `no_choice`:they do
not introduce another action choice. Their reasons nevertheless explicitly state
the old/current mapping. Neither these private reasons nor raw evidence quotes
reach readers. Public-bearing object fields discard the link. This is an
encoding/projection-contract omission,not evidence the user had not decided and
not a renderer silently deleting a relation already represented in a public field.
The ordinary actions,conditions and latest choices are present in the graph.

For parent25,the raw objects are only the four domain descriptions. The public
wire also lacks all eight labels;this is stronger than a raw-text substring
counter alone. Private reasons still know the new labels. Source links therefore
need preservation even when a message carries no new decision.

The invalid graphs are distinct availability failures. Parent19 mistakes action
definitions for decisions;parent37 mistakes a nickname-to-full-name
representation change for a later preference change. The chronology guard stays
in force. These failures do not demonstrate that768characters cannot hold the
information,and this milestone does not claim to repair either graph.

## Targeted implementation, with its limit

The new [scope-alias candidate](../scope-alias-encoding-v1/README.md) requires typed
source-bound aliases and per-user alias references independently of decision
classification. The binder projects declared names into the public object while
leaving existing nodes,conditions,actions,priorities and unknown boundaries intact.
It does not scrape names out of free-form private reasons.

A **developer-annotated,post-hoc** diagnostic on original parent7 adds four rename
relations from m37–m40. Its card grows768→793characters,within1536,with all
non-object ledger fields unchanged. This demonstrates a representation path and
that the selected omission need not be forced by the1536cap. It makes zero
reader calls:automatic extraction and choice recovery remain **unmeasured**.
The793-character diagnostic exceeds768;the smaller budget is not fixed here.
The canonical current name must also be present in the generated object,so
domain-only objects such as parent25 require correct regeneration,not a claimed
automatic patch. Semantic alias truth/completeness remain unchecked by literals.

The [next frozen27-call comparison](../scope-alias-comparison-v1/README.md) tests
source-only generation at1536 against the original accounted method,including
all48non-old-name cases to detect new losses. It needs a fresh direct grant and
exact-head three-platform CI. The closed51scope funds no additional call.
No installed default changes and no new accuracy benefit is claimed.

## Reproduce and inspect

```sh
python3 -B scripts/replay_scope_binding.py
python3 -B scripts/inspect_scope_binding.py --person kestrel --case 0_base_old_alias \
  --method source-accounted-graph-v1 --budget 1536 --generation 0
python3 -B benchmarks/scope-alias-encoding-v1/diagnostic.py
```

The [portable archive](measured.synthetic.json) and [checksum](measured.synthetic.sha256)
contain reviewed fiction,exact requests,raw structured values,cards and usage;
no grants,host paths,credentials or provider envelopes. Archive callbacks rebuild
every original attempt,skip,artifact,score and denominator without service calls.
Checksums verify consistency,not independent service attestation or semantic gold.
Scientific source:`175729045fd638ca5b5103f0ce8197807c26ff5f` (the tested PR81 head).
Input manifest:`1f157eb361ea31735cfaaf14531dd14499f886062fc7521e08b433159ac8f39e`.
Portable SHA256:`94ce32ceaca9f2c57724bb4158bd703de4f32a87732c289a591d9ac578cf22c5`.

Reported usage:848,966tokens=747,241input+101,725output. Cached input80,128 and
reasoning output6,995 are subsets,not extra totals. Controls use57,981tokens.
At1536,coverage/accounted extraction uses62,849/81,639tokens and reading
142,667/143,283. At768,extraction uses64,718/82,872 and reading106,519/106,438,
with unequal read availability. No price,net savings or real-person fidelity is
measured. Model requested:gpt-6.1-sol;resolved identity is not independently
reported. Two procedurally authored fictional people,dependent templates and
author-written references do not establish naturalistic or cross-provider fidelity.
