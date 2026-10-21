# Applicability before choosing: unknown-judgment follow-up

**This did not produce a stable repair of Luna’s short-card unknown judgments.** The original reader remains the default. An explicit experimental `coverage` mode is available in the CLI and browser.

## Fixed comparison

Six existing synthetic people and their once-generated 672–764-character cards were held fixed. Each request included 24 previously observed development scenes and 24 prospectively frozen scenes: 164 known and 124 unknown person/scenario cases, with 156 cyclically reordered queries per person. The new scenes include equivalent wording/numeric spellings, unsupported condition changes, exhaustive alternatives and two unobserved domains. They are not new independent people or latent policies.

Only a generic instruction prefix changes between `standard` and `coverage`. It checks applicability before choosing, rejects unlicensed numeric/monotonic extrapolation and preserves a known choice when all exhaustive recorded alternatives agree. Material, questions, option positions, schemas and exact action-text decoding are identical. No gold or preference rule is used by the decoder; no predicted choice is programmatically changed to U.

| Requested reader / arm | Old known /82 | Old unknown /62 | New known /82 | New unknown /62 | Position-consistent /288 |
|---|---:|---:|---:|---:|---:|
|luna_standard_full|67|61|67|61|278|
|luna_standard_none|0|62|0|62|288|
|luna_standard_card|77|61|78|59|285|
|luna_coverage_full|78|62|78|62|286|
|luna_coverage_none|0|62|0|62|288|
|luna_coverage_card|76|60|78|61|281|
|sol_coverage_full|82|62|82|62|288|
|sol_coverage_none|0|62|0|62|288|
|sol_coverage_card|82|62|82|62|288|
|luna_coverage_full_repeat|80|61|81|62|285|
|luna_coverage_card_repeat|76|60|78|60|283|

## What improved, and what did not

Luna full-history coverage improved known cases from 134/164 to 156/164 and unknown cases from 122/124 to 124/124. Its fixed independent repeat scored 161/164 known and 123/124 unknown. Aggregate gains still include 4 previously correct known cases lost and 26 recovered in the first protocol contrast.

The short-card result is much less favorable: standard scored 155/164 known and 120/124 unknown; coverage scored 154/164 and 121/124; its fixed repeat scored 154/164 and 120/124. The first card contrast lost 7 and recovered 6 known cases, while losing 2 and recovering 3 unknown cases. Keeping only the initially improved aggregate would hide these regressions.

The strict gate requires every known and unknown case correct at every position, no missing answers, and a full-history known gain over no memory of at least 25 percentage points. Stable adoption additionally requires both first and repeat full/card runs to pass separately on old and new suites. **Luna fails.** Its full/card difference is not an identified compression-retention estimate. Sol coverage full/card both scored 164/164 known and 124/124 unknown; that shows readability in this controlled setting, not human fidelity. There is no Sol-standard control on the new scenes, so it cannot establish a Sol-specific gain from this prefix.

## Residual examples and incomplete singleton diagnostic

The fictional p 38 card retains two different learning choices: a familiar concept without a specified teaching order chooses a concrete example first; an explicit request for definitions/derivations chooses formal material first. When the question says it is one of these two contexts without saying which, the answer should be U. Luna still selected the formal action on some/all positions in both wordings. These two branches are present in the short card, and Sol reads this case correctly. That particular failure is not evidence that the branches were omitted. The p 38 card uses no glossary references, so a glossary-only explanation is insufficient.

Selected singleton tests also still extrapolated an observed 4%classification decision to 0.2%, using both full history and the short card. The selected learning-conflict singletons answered U correctly. These are posthoc-selected examples, one orientation each, with fresh sampling; they do not identify a randomized causal batch-size effect.

The original 63-call unit stopped at invocation 11 after a nonzero CLI exit with error/turn.failed events. Ten responses completed; the failed call has unknown usage and no answer. The original error text was not retained by the transport, so its exact cause is unknown. No retry was made, and the diagnostic unit remains incomplete. Before any further call, a separate 51-call main comparison was sealed using only requests already frozen before those diagnostic results and never previously attempted. The candidate prefix, scenes, cards and main requests were unchanged. The failure and operational amendment are preserved publicly; this is not a completed original 63-call study.

## Cost and reproduction

Main comparison:51 completed calls,39 unique request fingerprints, including 12 unconditional repeats. Whole turn:62 actual attempts,61 completed responses,1 failed invocation;61 usage records known and 1 unknown. Known recorded total: **3322653 tokens**, including 3229524 input and 93129 output. 931712 cached input tokens are already included. The failed call is not charged as zero. These counters are not an invoice; resolved model identities were not exposed. The 63-call announced ceiling was not exceeded; the spare call was not used.

[`coverage-observed.synthetic.json`](coverage-observed.synthetic.json) contains all main raw answers, material, questions, request/answer hashes, execution identities, old/new summaries and costs, plus all available diagnostic answers and the failed-call record. Reproduce both scores and negative qualification without a model service:

```sh
python benchmarks/support-extraction-v 1/check_coverage.py
```

The checker rejects swapped outputs, duplicate execution IDs, reuse of an attempted diagnostic request, invented failed-call answers and mismatched request fingerprints. The actual service audit separately binds local raw wire responses and usage to every invocation. No population confidence intervals, likelihood RIG, true-person fidelity, external-vendor transfer or harness-runtime success is claimed. Larger batch size differs from the earlier format study; compare only the contemporaneous identical-input arms here.

## Try the explicit experimental mode

```sh
runaway choices prepare --card tiny-demo/portable.json \
  --questions examples/choice-questions.synthetic.json \
  --answer-format text --reader-mode coverage
```

The browser exposes the same explicit mode at `/choices.html`. Switching it clears the old trial; downloaded records include the mode and source origin. Modified fictional demos remain marked synthetic, and user-supplied text is marked unverified. This UI uses a single question; the large-batch study is not a direct evaluation of the UI. [Usage and limits](../../docs/automatic-support.md).
