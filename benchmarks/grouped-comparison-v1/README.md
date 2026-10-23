# Whole512 paired comparison: generation compliance and fidelity

This is a new one-shot comparison of the shipped default `support-v1` and opt-in `grouped-v1` on **consumed, developer-visible fictional data**. Both have a complete512 Unicode-character budget. Generation failures remain in all80 planned person/scene cells; they are not observed reader mistakes.

The grouped contract fit4/4 cards, but retained only **29/52 known choices** while preserving **28/28 U targets**. All23 own-card errors returned U for a known choice. This is not a successful fidelity result: entire source-supported choice families disappeared. Default produced no valid512 card, so it has **no observed reader accuracy** here.

| Format | Valid cards | Own correct / observed | Own successes / planned | Missing cells | Strict gate |
| --- | ---: | ---: | ---: | ---: | --- |
| `support-v1` | 0/4 | Not read | 0/80 | 80 | Fail |
| `grouped-v1` | 4/4 | 57/80 | 57/80 | 0 | Fail |

Contemporary full-history controls scored **80/80**; the single shared no-memory response scored **28/80**. The frozen gate required full80/80 in both option positions and a personal-known advantage before any extraction. It qualified in this execution. Historical controls or responses were not reused.

| Input / scoring owner | Correct / planned | Known | U targets | Missing |
| --- | ---: | ---: | ---: | ---: |
| `support-v1` / own | 0/80 | 0/52 | 0/28 | 80 |
| `support-v1` / tail | 0/80 | 0/52 | 0/28 | 80 |
| `support-v1` / wrong | 0/80 | 0/52 | 0/28 | 80 |
| `support-v1` / wrong_against_donor | 0/80 | 0/52 | 0/28 | 80 |
| `grouped-v1` / own | 57/80 | 29/52 | 28/28 | 0 |
| `grouped-v1` / tail | 32/80 | 4/52 | 28/28 | 0 |
| `grouped-v1` / wrong | 42/80 | 15/52 | 27/28 | 0 |
| `grouped-v1` / wrong_against_donor | 57/80 | 29/52 | 28/28 | 0 |

## What this measures

Four fictional profiles each contain48 chronological messages:29 user,10 assistant,9 tool. The same20 scenes each have two option positions, yielding80 person/scene cells:52 known choices,28 U targets,36 personal-specific known choices. U includes uncovered/missing/conflicting preferences and four known actions absent from the offered menu. Both positions must match the reference for a cell to count. These are four source profiles, not four models or real participants.

Five new control calls precede eight fresh independent encoders. Each encoder receives only its own full source plus its production schema, fixed guide and whole512 budget; no questions, reference labels, authoring parameters, previous responses or other cards. The two formats differ in prompt/schema, scope/priority grammar, validation and compiler. This is a **paired method comparison**, not an isolated causal effect of grouping. Each format is generated anew; no old768 answer is re-exported.

Name, tagline, guide, scopes, conditions, actions, explicit priorities, unknown statements and any glossary count in the public budget. Private anchors are not extra reader memory. Exact quotes, user roles, backward references and literal round trips establish structure, not semantic support, completeness, privacy or personal fidelity.

Own readers receive the structurally validated full public card. Raw tails include a role/truncation warning and match that actual card in complete Unicode characters, not tokens. Wrong-card donors are fixed cyclically at the same format; independently generated wrong-card responses are scored against both the target and actual donor. Donor rescoring costs no extra calls.

The strict per-format gate requires4/4 valid products, own80/80 and independent donor80/80, with contemporary controls qualified. [Original cards](CARDS.md) and [generation failures / observed losses](LOSSES.md) retain failed and missing cases. Default remains support-v1; passing this consumed development bank would not itself authorize promotion.

## Scope and cost

Approved maximum37 local inference CLI children:5controls,8encoders,24dependent readers. Actual attempts: **25**, all counted whether successful or not; 12 dependency slots skipped, 12 unused slots expired. There was no retry, repair, truncation, replacement, replenishment, resume or automatic next service stage. Scope closed.

Observed usage: **331,070 input + 35,109 output = 366,179 tokens**. Cached input 57,216 is included in input; reasoning output 13,744 is included in output. Input/output usage missing for 0 attempts. Optional absent components do not prove actual zero. These numbers are not an invoice, token-matched compression ratio or total agent-chat cost. GPU work:none.

Requested model:gpt-6.1-sol through the logged-in tool-free Codex adapter,180s local timeout. Actual server model identity and upstream RPC/retry counts were unavailable. The approved37 cap was a local-call cap with no token/money ceiling. A temporary owned idle-sleep guard was removed after execution.

The first unexecuted preparation reported15 passing protocol tests instead of the actual14. Audit caught the reporting error before approval. The superseding preparation corrected reporting/path binding while retaining identical code, source, queries, references, slot graph and requests. No model observations existed in that first package.

## Replay offline

```sh
python3 benchmarks/grouped-comparison-v1/check.py
```

Replay makes zero model calls. It reconstructs all25 actual requests, original response hashes, usage, products, failure reasons and skipped dependencies, then checks frozen expected scores. Production source fingerprints bind the measured contracts. Checksums detect drift; they do not authenticate authors or prove reference semantics.

The bank was jointly authored, shares source/scenario scaffolding and was already developer-visible. Code/source/evaluation hash ordering does not make it blind. There is no new independent holdout, real-person fidelity, population/significance result, sampling-variability estimate, model diversity or actual harness portability result.80 cells and two positions are dependent. The auxiliary normalized accuracy gain uses planned successes; it is **not likelihood RIG**, and missing readers are not inaccurate observed answers.

[Next source-coverage contract](NEXT-CONTRACT.md) · [Grouped format](../../docs/grouped-support.md) · [Earlier budget frontier](../heterogeneous-frontier-v1/README.md)
