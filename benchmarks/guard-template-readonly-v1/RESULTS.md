# Same-graph template reading: measured, not new extraction

The six authorized local Codex CLI attempts completed and were sealed. Requested model: `gpt-6.1-sol`; no retries, card edits, extraction, decoder supplement or unused budget. All 25 prior observation sets and the frozen scientific source remained unchanged. Offline replay reproduces every original record, answer, control, counter and score with zero service calls.

| Counted whole public view | Fixed cases | Known choices | Reference-unknown | Missing |
|---|---:|---:|---:|---:|
| Original 997 characters | 82/82 | 36/36 | 46/46 | 0 |
| Template 768 characters | 82/82 | 36/36 | 46/46 | 0 |

Each retained case requires both independent reads and both option orders: four correct answers. There are 82 paired retained cases, zero observed recoveries and zero new observed losses. Full source first passed all 82 cases in both orders; no memory retained zero of the 36 known choices. The template saves 229 whole characters (23.0%), including its complete counted guide. This validates reading of this fixed template, not automatic generation of a new 768-character card.

Cost reported by the six local calls: **343,641 tokens** = 326,959 input + 16,682 output; 462 reasoning tokens are a subset of output. Cache counters are zero; missing usage records: zero. These are reported usage, not an independently verified invoice or model identity.

## What was preserved, and what remains untested

All measured cohorts passed in both views: current and old numeric boundaries, local exceptions, necessary gate/guard false or missing, removal of a guard from only the exception, old names versus independent copies, past status versus preference, and missing-detail cases where all compatible choices agree. Complete action labels and the unknown boundary survived the layout change. Case traces retain full user/assistant/tool episodes and all four answers; no loss case was removed from the denominator.

The preceding failed-budget graph remains invalid in its original experiment. This is a later, separately authorized reading of two fixed views of that same graph; old missing scores are not replaced. One posthoc development graph, one fictional person and same-author reference cannot establish generation stability, source completeness, independent semantic gold, human preference fidelity or cross-provider transfer. The separate `condition_revision` encoder was not used or tested. Production defaults are unchanged.

The source audit found an uncovered constraint: **all six user setup messages specify nonnegative integer quantities, while neither fixed public view explicitly retains that domain**. The 82-case set contains no negative or fractional-quantity challenge. Exact restoration of the model graph therefore does not certify restoration of the entire source. This is a visible source-to-card omission, not an observed wrong model answer; the six calls did not test it. See [the complete audit](SOURCE-DOMAIN-AUDIT.json) and [loss analysis](LOSS-ANALYSIS.md).

```sh
python3 -B scripts/replay_guard_template.py
python3 -B scripts/inspect_guard_template.py 0_old_boundary
python3 -B scripts/inspect_guard_template.py --domain-audit
python3 -B -m unittest discover -s tests -p test_guard_template_evidence.py -v
```

Portable fictional inputs, reference, exact requests, raw responses and usage are in `measured.synthetic.json`, protected by its adjacent checksum. Checksums and archive replay establish content consistency, not independent provider attestation. No local grants, machine paths, credentials or real-person data are exported.
