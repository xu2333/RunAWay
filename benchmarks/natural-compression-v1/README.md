# Naturalistic synthetic compression: 624–675 characters retain 56/56 cells

Sixteen explicitly approved `gpt-6.1-sol` CLI inference attempts completed with
**four one-shot default `support-v1` cards** and twelve independent reader calls.
All four cards fit the whole-public-card limit of 768 Unicode characters. No
retry, repair, truncation, replacement, prompt change or dictionary packing was
used. Actual server model identity was unavailable.

| Material | Both positions correct / 56 | Known / 38 | Unknown / 18 | Personal-specific known / 32 |
| --- | ---: | ---: | ---: | ---: |
| Own short card | **56** | **38** | **18** | **32** |
| Same-character raw source tail | 38 | 20 | 18 | 16 |
| Fixed wrong-person card, scored against target | 30 | 14 | 16 | 10 |
| Same independent wrong-card responses, scored against actual donor | **56** | **38** | **18** | **32** |
| Historical full history, reused | 56 | 38 | 18 | 32 |
| Historical no memory, reused | 18 | 0 | 18 | 0 |

The predefined strict retention gate passed: four valid cards, all own-card
cells correct and all independent donor-card cells correct against their actual
owners. The identity-specificity gate also passed: personal-specific known
choices dropped from 32/32 to 10/32 when the same fixed cards were assigned to
other profiles. Donor rescoring uses the **same four wrong-card calls**, not four
additional service calls. Each card was read independently once in its own slot
and once as a donor; this is not a sampling-variability estimate.

| Fictional source profile | Whole card characters | Own / 14 | Equal-character tail / 14 | Wrong target / 14 |
| --- | ---: | ---: | ---: | ---: |
| n31 | 624 | 14 | 10 | 6 |
| n72 | 675 | 14 | 9 | 9 |
| n46 | 636 | 14 | 10 | 5 |
| n85 | 627 | 14 | 9 | 10 |

The [complete actual cards](CARDS.md) include their header, scope guidance,
name, tagline, conditions, exceptions and unknown statements in those counts.
Private source quotes are not counted as public memory and are never reader
input. Each tail consists of a fixed warning plus the role-labelled raw source
suffix, matched to its owner's actual complete card **character** count. This
is one truncation baseline, not a token-matched or optimized retrieval baseline.

## What was preserved and what was lost

Own-card losses were **0 known choices and 0 unknown boundaries** in this bank.
The equal-character tail lost 18 known choices, answering `U` in both option
orders every time. For every profile these were c01–c04 (early product choices
and classification thresholds); n72 and n85 additionally lost c11 (a missing
condition still admits the same manual action under their recorded threshold).
The older source material is absent from, or cut at the boundary of, that tail.
This is consistent with loss of available evidence; it is not an independent
causal diagnosis of every reader decision.

The wrong-target condition changed 26 cells, including two target-unknown c11
cells that are known for the donor. Those same responses match their donors
exactly. They are evidence of preserved differences on these four sources,
not an unknown-boundary regression of the correctly assigned own-card condition.
No option-position instability was observed in any of the twelve new reader
responses. Full per-person/case errors and the unchanged references are included
in the replay fixtures.

Each fictional history has 15 role-labelled user/assistant/tool messages.
Sources contain continuous numeric thresholds, scoped chronological updates,
mathematical-writing exceptions, research tradeoffs, collaboration arrangements,
and unendorsed assistant suggestions. A source-only encoder received only its
own history, fixed request/schema and whole-card budget. It received no queries,
reference answers or previous responses. Readers received only one material
and the same 28 public queries (14 scenes × 2 option rotations). Production
extractor, paragraph renderer and standard text reader stayed unchanged.
Literal quote, role, chronological-reference and budget checks do **not** verify
semantic completeness, privacy or real-person fidelity.

## Cost and scope

Observed new usage: **175,795 input + 13,270 output = 189,065 tokens**.
The 12,800 cached input tokens are a subset of input; reported reasoning tokens
are a subset of output. These are CLI usage reports, not an invoice or memory
inference token-savings estimate. Optional absent usage components default to
zero in accounting and are not proof of actual zero. All sixteen local inference
CLI children completed with known input/output usage. Upstream RPC attempts and
hidden retries are unobservable. The sixteen-call scope is closed; no automatic
next service stage is authorized. No GPU work was involved.

The earlier five full/no-memory calls (63,457 tokens) were **reused, not rerun**.
They use the same sources, public queries, as-of date, reader and requested model,
but unknown server identity/drift and sampling variation limit causal comparison.
New cards were produced after those qualified controls. The combined two-stage
cost is 252,522 reported tokens across 21 local inference CLI children.

The auxiliary normalized accuracy gain is `(56−18)/(56−18) = 1`. This is a
normalized **accuracy** difference, not likelihood relative information gain,
Shannon information gain or a universal compression/fidelity score.

## Replay offline

```sh
python3 benchmarks/natural-compression-v1/check.py
```

The replay makes **zero model calls**. It verifies the linked five-call control
snapshot, reconstructs all sixteen source/card/tail/donor requests, checks
original response fingerprints and usage, rebinds the actual four one-shot
products with whole-card budgets, decodes exact offered text and reproduces
all scores. Relevant production source fingerprints are checked so a changed
extractor/renderer cannot silently replace the measured one. Do not update a
checksum to conceal an intended implementation change; retain the original
observations and evaluate the changed method separately. Checksums detect
changes; they do not authenticate the author or prove semantic support.

This is **developer-authored, developer-visible synthetic evidence on a consumed
bank**, not an independent new holdout or real humans. Four fictional profiles
are the dependence units; 56 person/scene cells and their two option positions
are not 112 independent users. There is no population inference, significance,
real-user taste fidelity, cross-model or actual-harness guarantee. The result
supports this default extraction path on this bounded set. Next useful evidence
is a separately frozen broader/longer bank or consented real traces with withheld
future choices, smaller-budget stress and different readers; none was measured
here. Product defaults were not changed from these outcomes.

[Historical controls](../natural-controls-v1/README.md)
· [Default extraction workflow](../../docs/automatic-support.md)
· [Different, finite-schema v2 study](../source-constraints-v2/README.md)
