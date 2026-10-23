# Naturalistic source controls: full history qualifies, compression untested

Five explicitly approved `gpt-6.1-sol` CLI inference attempts completed without
retry or repair. The actual server model identity was unavailable. This study
uses **four developer-authored fictional work trajectories**, not real people
or four different models. Source documents, public questions, reader and scoring
gate were frozen before inference; the developer could inspect all references.

| Material | Both positions correct / 56 | Known / 38 | Unknown / 18 | Personal-specific known / 32 |
| --- | ---: | ---: | ---: | ---: |
| No memory | 18 | 0 | 18 | 0 |
| Full history | 56 | 38 | 18 | 32 |

The full-history control passed its predefined gate: correct on all 56 planned
person/scene cells, **both option orders** per cell, and more personal-specific
known choices than the shared no-memory response. The no-memory response chose
`U` throughout. This preserves uncertainty but cannot recover the 38 choices
that the sources explicitly determine. It is **not a compact-card result**.

Each source contains 15 user/assistant/tool messages. Four profiles share 14
scenes, each presented twice with rotated options: 28 queries in each of five
requests. All conditions use identical queries, schema and reader prefix; only
material changes. There is no exhaustive finite rule-family promise or explicit
feature-bin catalogue. The sources contain ordinary continuous thresholds,
scoped updates, mathematical-writing exceptions, research tradeoffs,
collaboration arrangements and unendorsed assistant suggestions. Uncovered
social/coffee preferences and missing known actions must remain unknown.

| Fictional profile | Full / 14 | No memory / 14 |
| --- | ---: | ---: |
| n31 | 14 | 5 |
| n72 | 14 | 4 |
| n46 | 14 | 5 |
| n85 | 14 | 4 |

The reference labels make any single shared answer set score at most 39/56
across the four profiles; that is a pre-execution combinatorial check, not a
model score. Sources and reference interpretations were jointly authored by
the developer, not independent human gold. Before any service call, two public
questions were revised to remove answer-revealing hints; the previous unexecuted
preparation remains archived. The approved final inputs were not changed.

Observed usage was **62,098 input + 1,359 output = 63,457 tokens**. The 6,400
cached input tokens are included in input. This is not an invoice or a token
savings claim. Five is the count of local inference CLI children; upstream RPC
attempts are unobservable. No missing usage, retries, extraction, compression,
sample replacement or automatic next stage occurred. The five-call scope is
closed. Qualification does not grant another model-call budget.

## Replay offline

```sh
python3 benchmarks/natural-controls-v1/check.py
```

The fixture contains the actual five requests, raw JSON responses, usage,
fictional source histories, source-supported references and expected results.
Replay checks source/query request bindings, original response fingerprints,
strict offered-text decoding, usage totals and the unchanged scoring result.
It makes **zero model calls** and must not be reported as a fresh validation.
Checksums detect edits; they do not authenticate the author or prove semantic
support. This consumed bank is available for regression, not a new holdout.

Four source profiles are the dependence units. The 56 cells and 112 option
positions are not independent users. No population inference, significance,
likelihood RIG, real-person fidelity, cross-model or actual-harness guarantee is
reported. The next compression comparison needs its own fixed scope; these
results alone do not establish that either v1 or v2 cards preserve this history.

[Earlier bounded v2 extraction study](../source-constraints-v2/README.md)
· [Default trajectory workflow](../../docs/automatic-support.md)
· [Explicit finite v2 limits](../../docs/source-constraints.md)
