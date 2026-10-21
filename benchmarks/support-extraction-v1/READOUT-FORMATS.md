# Frozen memories, different answer formats

The same six existing synthetic people, their full histories and their once-generated 672–764-character cards were read using either option letters or the exact offered action text. The question/material JSON was byte-identical across formats. Output instructions and enum schemas changed together; text mode can cost more tokens. The decoder only matches a public option string to its current display position. It never reads memory or gold answers to correct a choice.

Each arm covers 24 semantic scenarios: 82 known and 62 unknown person/scenario cases, with 78 cyclically reordered queries per person. A case is correct only if every position is correct. These are six synthetic policies and development scenarios, not 144 independent people or an external holdout. The wording had already been tested with Sol.

| Requested model / format / arm | Known /82 | Unknown /62 | Position-consistent /144 |
|---|---:|---:|---:|
| Luna / letters / full |49|59|109|
| Luna / action text / full |75|59|138|
| Luna / letters / card |50|62|117|
| Luna / action text / card |77|59|141|
| Luna / action text / full, unconditional repeat |79|58|141|
| Luna / action text / card, unconditional repeat |75|60|138|
| Sol / action text / full |82|62|144|
| Sol / action text / card |82|62|144|
| Luna / letters / no memory |0|62|144|
| Luna / action text / no memory |0|62|144|
| Sol / action text / no memory |0|62|144|

Text mode reduced Luna's position errors and increased known-case accuracy, **while introducing unknown-case errors**. The first card comparison recovered 28 previously wrong cases and lost 4 previously correct cases; the later repeat lost 5 and recovered 4 versus the first text draw. Full and card comparisons use independent model executions, so this does not isolate the causal effect of representation from sampling or instruction/schema length.

The predeclared gate requires all 144 cases correct, all positions consistent, no missing answers, and full-history known accuracy at least 25 percentage points above no memory. **Luna fails the reader gate in both formats and on the text repeat.** Its card/full difference is therefore not an identified compression-retention estimate. Sol passes this particular text comparison; that does not establish human fidelity, cross-vendor transfer or unseen-user performance. Letter mode remains the CLI default. The browser's new single-choice trial uses text mode as an explicit experimental interface; the batch result is not a measurement of that single-choice UI.

The fixed study made **51 actual calls**, including 12 unconditional repeats, with 39 unique request fingerprints. All 51 completed with recorded usage: 1,575,103 input tokens (316,928 cached, already included) and 46,165 output tokens, totaling **1,621,268**. Requested identities were `gpt-6-luna` and `gpt-6-sol`; the service did not expose resolved model identities. These local counters are not an invoice. Luna card totals increased from 115,927 tokens for letters to 205,233 for action text; this is not a smaller memory or free compression gain. No retries, best-of selection, extra extractor calls or extra real-person disclosures were used in this study.

[`readout-formats.synthetic.json`](readout-formats.synthetic.json) includes all raw responses, frozen material, questions, request hashes, execution IDs, usage, qualification results and per-arm summaries. Reproduce the scores and exact request fingerprints offline:

```sh
python benchmarks/support-extraction-v1/run.py check-observed
```

To inspect individual errors without a model call, save one group's `answers` object as JSON and run:

```sh
python benchmarks/support-extraction-v1/run.py score --case-set fresh \
  --answer-format text --answers raw-group.json
```

The output includes per-person, per-axis and per-case gold/observed values, losses and consistency. Pass `--shared` for a no-memory group and `--answer-format label` for a letter group. Always-unknown fails the known controls. [Try the offline reader interface](../../docs/automatic-support.md#replay-a-choice-with-any-llm).
