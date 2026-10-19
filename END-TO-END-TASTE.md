# From histories to an actual portable prompt

This pilot tests the browser product, rather than a hand-written memory. Two fictional people have similar surface preferences but differ on reversible automation, disposable prototypes, learning order, and when to share a sanitized draft. Their natural, role-labelled histories contain noise, unendorsed assistant suggestions, exceptions, and a later change of mind.

The encoder sees only that person's histories. It uses the unchanged browser `makeRequest → validateAnswer → makeBundle` path. The **768 Unicode character ceiling includes the complete exported boundary and final newline**. Readers receive only the untouched exported text; the entertaining name, private claims and evidence are not supplied as extra memory.

Each person is tested under four inputs: complete role-labelled history, no personal information, their own exported prompt, and the other person's exported prompt. Each read contains 12 new scenes in both option orders. There are **48 planned answers per condition, 192 in total**, but only **one authored pair**, not 192 independent people.

## Real pilot results

All **10 planned calls completed**, with no retries or missing usage, using the logged-in Codex service and requested model `gpt-6.1-sol`. Resolved model identity was not reported.

| Reader input | Correct | Matched distinctions | Option consistency |
|---|---:|---:|---:|
| Complete histories |48/48|4/4|24/24|
| No personal material |10/48|0/4|24/24|
| Own compressed prompt |48/48|4/4|24/24|
| Other person's compressed prompt |28/48|0/4|24/24|

Against the **donor's** policy, the swapped-prompt answers score **48/48**. Thus the loss against the target is the intended switch of personal tradeoffs, rather than random failure. Own memory preserves every tested exception, update and unknown, with zero full-history-correct → own-memory-wrong answers. Choice retention on this pair is **1.0**, not a population estimate.

The product produced **“试跑也带刹车”** and **“手动挡试映员”**. Their complete portable prompts are **584 / 607 characters**, under the 768 ceiling. They occupy **47.1%** of the role-labelled JSON histories, but **72.8%** of the original source text with structure removed (1,191 / 1,637 characters). The latter is only a **27.2% text reduction**: this validates the path at a moderate budget, not extreme compression. Relative to user messages alone, the respective ratios are 76.8% and 85.3%.

Actual service usage was **84,004 input + 9,003 output = 93,007 tokens**. Cached input was 0; 1,175 reasoning tokens are already inside output. These are experiment-service records, not an invoice or total research/chat usage. The ten-call allowance is exhausted and closed.

[Exact results and the two prompts](examples/end-to-end-taste-results.synthetic.json) · [Length audit](examples/end-to-end-taste/length-audit.synthetic.json) · [106-file frozen evidence](examples/end-to-end-taste-evidence.synthetic.zip).

```sh
python3 -B scripts/replay_end_to_end_taste.py --archive examples/end-to-end-taste-evidence.synthetic.zip
```

Replay reconstructs the actual product outputs and all ten exact requests, recomputes scores and usage, and detects changed choices: **0 new model calls / 0 tokenization**. Python 3.9+ and Node 22+ are needed for the unchanged browser bridge. Existing 18 evidence archives remain unchanged.

## Predeclared measurements

- Choices use an author-defined policy interpreter and a separately written semantic answer table. Neither parses the generated prompt; neither is sent to the encoder or reader. All questions ask about the latest preference at a stated cutoff, avoiding ambiguity between current choices and historical reconstruction.
- Report ordinary accuracy alongside four matched personal distinctions, exceptions, changed sharing habits, unknown domains, partial context, and option-order consistency. Swapped prompts are scored against both the intended person and the donor policy, so random damage cannot masquerade as successful persona transfer.
- Choice retention is `(own − none) / (full − none)` using correct counts. It is undefined when any condition is incomplete or `full ≤ none`, and is never clipped. It is **not likelihood-based relative information gain**: this transport supplies no choice log-probabilities.
- Record complete export characters and UTF-8 bytes separately from actual service tokens. Export/history ratios use the role-labelled history delivered to the full-history reader. Removing JSON structure also saves characters; these ratios alone do not establish semantic compression efficiency.

## Integrity and scope

The fixed maximum is **10 new service generations**: two product extractions and eight blind reads. Each is single-use, with a 180 second deadline and the existing bounded cleanup. There are no retries, repair calls, fallback models, quality-based sample filters, or resume balances. Invalid products and uncertain usage stop later calls while every planned denominator stays in the report. No GPU instance is needed.

Offline controls include all-unknown and all-A predictions, an empty result, a missing answer, a changed choice, flipped option letters, unobserved overconfidence, stale public-sharing behavior, missing exceptions, and another person's policy. For example, all-unknown achieves perfect order consistency but only **10/48 correct**; the ideal donor policy achieves **28/48** against its recipient and loses all four matched distinctions. Consistency alone cannot pass for fidelity.

The scenarios, histories and gold were written by the same research agent, albeit through separate representations and a checked hand table. That can leave author and task bias. This is a small diagnostic of the full product path, not validation of real personal taste, population accuracy, cross-vendor transfer, or an optimal compression budget. Once run, this pair is consumed and should not become a tuning target.

Prepare a new offline proposal without contacting a model:

```sh
python3 -B -m runaway.end_to_end_runner --prepare --proposal /tmp/runaway-review
```

Real execution requires independently verified authorization for that exact proposed scope. A local JSON approval receipt is bookkeeping, not a way to grant oneself permission. Previously sealed calls remain excluded; old budgets are not carried forward.
