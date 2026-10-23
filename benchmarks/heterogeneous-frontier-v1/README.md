# Budget frontier: valid 768-character cards read correctly, smaller cards do not fit

This new, developer-authored fictional bank exposes a **generation-budget
failure** in default `support-v1`. Twelve one-shot extractions produced nine
over-budget candidates. The three valid 768-character cards retained all **60
actually read** person/scene cells, but **no budget passed the predefined
four-profile end-to-end gate**. Missing cards remain in the planned denominator.

| Whole public budget | Valid cards / 4 | Own correct / planned 80 | Missing cells | Strict gate |
| --- | ---: | ---: | ---: | --- |
| 384 characters | 0 | Not read (0/80 end-to-end successes) | 80 | Fail |
| 512 characters | 0 | Not read (0/80 end-to-end successes) | 80 | Fail |
| 768 characters | 3 | 60/80 | 20 | Fail |

The 384/512 results are **not reader accuracy of zero**: no valid cards existed,
so no readers ran. At 768, observed own-card accuracy was 60/60: known 40/40,
`U` 20/20, and both option positions correct. The remaining 20 planned cells
(12 known, 8 `U`) belong to the invalid fourth card, not observed model mistakes.
Selecting only the three successful cards cannot establish four-profile retention.

## Contemporary controls and observed readers

| Input / scoring owner | Correct / planned | Known / 52 | `U` / 28 | Missing |
| --- | ---: | ---: | ---: | ---: |
| Full sources | **80/80** | **52** | **28** | 0 |
| No memory, shared response | 28/80 | 0 | 28 | 0 |
| Own 768-character cards | 60/80 | 40 | 20 | 20 |
| Equal-character raw tails | 23/80 | 3 | 20 | 20 |
| Fixed wrong-person 768 cards, scored against target | 37/80 | 19 | 18 | 20 |
| Same independent wrong-card responses, scored against actual donor | 60/80 | 40 | 20 | 20 |

The five full/none controls ran **in this same execution**, before extraction,
and qualified the frozen source/query set. Unlike the earlier staged study,
these controls were not historical reuse. One no-memory response is scored
against all four sources; it chose `U` throughout. The 28 `U` targets include
24 missing-condition/uncovered/conflict decisions and four **known actions not
in the menu**. `U` is an offered-answer contract, not always absent preference.

Wrong-card donors were fixed as the next profile cyclically, at the same budget.
Responses were not copied from own-card calls: three separate wrong-card calls
were scored against target and donor. Target-specific differences exist among
observed responses, but the **predefined strict identity-specificity gate fails**
because one card is missing. Donor rescoring is not three extra calls or a
sampling-variance estimate. Both options were rotated; full per-cell errors,
missing flags and position-instability metadata are retained in the evidence.

## What failed

[Exact candidate lengths and losses](LOSSES.md) distinguish over-budget generation
from absent readers and observed decisions. [Actual valid cards](CARDS.md) were
745,747,762 complete Unicode characters; the fourth 768-target candidate was
783 and was rejected, not shortened or silently accepted. Every 384-target
candidate needed 654–781 characters, every 512-target candidate 616–703.
All nine failures reached and passed quote/role/reference validation before the
whole-budget check. No rejected prompt was supplied to a reader.

The production literal phrase packer found no beneficial replacement in any of
these twelve answers. This says something about **this greedy packer on these
answers**, not the minimum possible representation length. Header and guidance
cost100 characters; name/tagline/separators cost14–28 and repeated branch glue
44–52. Even removing all those fields and trailing newlines would leave
494–603 characters in the four 384-target answers' unchanged condition/action/
unknown strings. That conditional accounting is **not an information-theoretic
lower bound**; shorter equivalent wording or factored scopes remains possible.
Deleting a cute name or punctuation alone does not bridge the observed gap.

No observed own/donor choice or `U` regression occurred among valid cards.
The tail's 37 observed failures all returned `U` for known choices; original
information is absent from or cut by that suffix. That is a plausible evidence
availability explanation, not independently established causal attribution.
The next optimization should address the **budget-constrained representation
and generation contract**, preserving exceptions/unknowns. These results do
not justify changing the reader or repairing old candidates and relabelling
them as prospective successes. Product defaults were not changed here.

## Data and frozen design

Four new fictional histories each contain48 chronological messages (29 user,
10 assistant,9 tool; body2744–2757 characters). Twenty shared scenes have two
option positions each:80 person/scene cells,52 known and28 `U`;36 known choices
are personal-specific. Shared answers can score at most61/80 by reference-label
combinatorics; that is **not a model score**.

Sources mix public/internal code migrations, exploratory replication, document
deduplication thresholds, feedback revisions, research reports/runbooks,
work travel and a one-time notification choice. They include unendorsed assistant
and tool summaries, scoped updates, unresolved conflicts and an irreversible
sharing exception. Unscored workshop layout choices add memory-selection load;
the80 reference cells do not exhaust every preference in the histories.
These are longer than the earlier15-message sources, **not an extreme long-context
benchmark**. All four profiles share authored narrative/scenario scaffolding.

The default source-only encoder, paragraph compiler and standard/text reader
were copied byte-for-byte from the previously shipped code. Each budget uses a
fresh independent source-only extraction, not a repack of the768 answer.
Encoders receive no queries, gold, authoring parameters or other answers.
Readers receive one material and the same40 public questions. Header, guidance,
name, tagline, conditions, unknowns and any glossary all count toward the public
character budget. Private quotes are never extra reader memory. Tails include
their warning and match actual whole-card **characters**, not tokens; no claim
is made against optimized retrieval or a token-matched baseline.

Before any service call, an unexecuted preparation was superseded solely to
replace research-reproduction wording with remediation wording in the runbook
options and corresponding four labels. Sources, code and every other question/
reference were retained. The old preparation remains archived. Reference quotes
are literal user-role spans; those checks do not prove semantics, completeness,
privacy or human taste. Source and gold were jointly authored and developer-visible.

## Cost and exact scope

The approved cap was53 local inference CLI attempts:5 controls,12 extractions,
36 readers. Actual execution used **26** (5+12+9), all with completed wire/schema
responses. Nine products failed local whole-budget validation; their27 dependent
reader slots were skipped exactly. Skipped capacity expired and was not reused.
There was no retry, repair, replacement, truncation, resume or automatic next
service stage. The53-call scope is closed.

Observed usage: **328,399 input +43,166 output =371,565 tokens**. Cached input
38,912 is included in input; reasoning output8,727 is included in output.
Input/output usage was known for every attempt. Optional absent components
default to zero in accounting and do not prove actual zero. This is not an
invoice or a memory-token savings estimate. GPU work: none. Actual service
model identity and upstream RPC/retry counts were unavailable. Requested model:
`gpt-6.1-sol` through the logged-in Codex CLI, with a fixed tool-free setup.

## Replay offline

```sh
python3 benchmarks/heterogeneous-frontier-v1/check.py
```

Replay makes **zero model calls**, validates all26 actual request/response
bindings, source quotes, usage, original fingerprints, three exported products,
nine rejection reasons and27 skipped dependencies, then reproduces the fixed
controls/budget scores. Relevant production source fingerprints prevent a new
compiler from silently replacing the measured one. Checksums detect changes;
they do not authenticate the author. This consumed bank is regression evidence.

No budget passed on all four authored profiles. There is no minimum passing
budget among the three tested points, no independent blind holdout, no human
fidelity, population/significance estimate, model diversity, actual harness
portability or sampling-variability result. Four source profiles share a
scaffold;80 cells and two positions are dependent. Normalized accuracy gain in
the JSON is only an auxiliary accuracy scale, **not likelihood RIG**, and missing
responses must not be interpreted as observed inaccurate answers.

[Earlier bounded768 success](../natural-compression-v1/README.md)
· [Default workflow](../../docs/automatic-support.md)
