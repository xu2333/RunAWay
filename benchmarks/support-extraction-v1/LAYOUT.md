# Paragraph versus condition/action rows

**Rows remain an explicit experimental option. The default stays paragraph.**
One Luna row draw was perfect; the other still lost known and unknown judgments.
Both layouts passed with Sol in this finite synthetic comparison. These results
do not establish fidelity to a real person.

## Fixed comparison

We reused six synthetic policies and 48 previously consumed development scenes.
The inherited `development` and `prospective` labels in the fixture both refer
to consumed scenes; neither is a fresh holdout here. Reordering the scenes'
choices produces 156 queries per policy and 288 person/scene cases: 164 known
and 124 unknown. A case is correct only if every tested choice ordering is
correct. Position consistency alone does not imply correctness.

The facts, branch priorities, original standard reader, answer schema and
2026-04-01 cutoff were fixed. Paragraph cards contain 672–764 characters; rows
contain 671–762. Only display delimiters/whitespace and the resulting literal
glossary packing changed. The production renderer reproduces all six frozen
row candidates. Exact field round trips demonstrate preservation of the
extracted representation, not completeness of the original extraction.

Requested models were `gpt-6-luna` and `gpt-6-sol`; resolved server model identities
were unavailable. Each received full-history, no-memory, paragraph and rows
controls (19 calls each). Luna received an independent paragraph/rows repeat
(12 calls). Within each policy, paragraph/row execution order was balanced;
the repeat reversed that order. There were no retries, new extractor calls,
program choice overrides or gold/memory access by the output decoder.

## All draws

| Requested model / arm | Known / 164 | Unknown / 124 | Known false abstentions | Position-consistent / 288 |
|---|---:|---:|---:|---:|
| Luna full history | 159 | 119 | 4 | 284 |
| Luna no memory | 0 | 124 | 164 | 288 |
| Luna paragraph | 158 | 123 | 4 | 285 |
| Luna rows | 161 | 122 | 2 | 286 |
| Sol full history | 164 | 124 | 0 | 288 |
| Sol no memory | 0 | 124 | 164 | 288 |
| Sol paragraph | 164 | 124 | 0 | 288 |
| Sol rows | 164 | 124 | 0 | 288 |
| Luna paragraph repeat | 156 | 119 | 7 | 285 |
| Luna rows repeat | 164 | 124 | 0 | 288 |

In the first Luna paragraph-to-rows comparison, rows recovered six known cases
and lost three; they recovered one unknown case and lost two. In the repeat,
rows recovered eight known and five unknown cases with no losses. Both draws,
including every loss, remain in the public fixture. Choosing only the perfect
repeat would hide instability.

The contemporaneous full-history qualification requires all cases correct at
every ordering, no missing outputs, and a known full-minus-no-memory accuracy
gap of at least 0.25. Sol qualifies and both cards pass. Luna does not qualify,
so its full/card difference cannot identify compression retention. The stable
rows gate requires both Luna row draws and the Sol row arm to be perfect on
each consumed scene set. **It fails.** No default change is justified.

## Reproduce without model calls

```sh
python benchmarks/support-extraction-v1/check_layout.py
```

The checker reconstructs the cards from the public synthetic extraction fixture,
checks fact/priority and character-budget preservation, binds 50 execution records
to 38 distinct requests and their exact answers, verifies the counterbalanced
plan, and recomputes all ten arms and qualification gates. Tests also reject
changed facts, changed ordering, duplicate executions and substitution of the
better repeat into the first draw. This rechecks recorded evidence; it does not
rerun the models.

Existing source-support profiles can be reformatted locally:

```sh
runaway relayout my-card/profile.private.json --layout rows --out my-rows
runaway relayout my-rows/profile.private.json --layout paragraph --out my-restored
```

This uses zero service calls and writes a new directory. It verifies the private
profile checksum, source references and evidence constraints; checksums do not
authenticate an author. It neither adds missing preferences nor improves a
profile's fidelity status. See [the usage guide](../../docs/automatic-support.md).

## Cost and limits

All 50 attempted service calls completed, with usage recorded for every call:
3,033,628 input tokens (including 995,968 cached), 95,903 output tokens
(including 17,617 reasoning), **3,129,531 total tokens**. Cache/reasoning are
subsets, not additional charges to add. These local usage records are not an
invoice. The repeat reuses requests but is counted as 12 additional executions.

Before any backend invocation, a local preflight rejected tuple/list inequality
after a JSON round trip. The repair normalized the runtime plan to lists and
added a regression test. Serialized requests and the call plan were unchanged;
the original seal and failed preflight were retained locally. This consumed zero
service calls and is not a model retry.

Counterbalancing reduces systematic order asymmetry but cannot eliminate service
drift or sampling noise. This is six synthetic policies, consumed scenes and a
small number of draws. It does not support population confidence intervals,
likelihood-based relative information gain, a single-glyph causal explanation,
cross-vendor portability, harness runtime compatibility or real-user fidelity.
The installed CLI and Codex file adapter were checked offline; that is separate
from executing a real harness session.
