# New-source contrast probe — prepared, unapproved and unrun

Freeze the unchanged source-order-v3 encoder from merged PR #38 before evaluating
new sources. `encoder-lock.json` pins its merged code and dependencies; this
protocol does not tune the encoder, reader, guide or 1536-character cap.

`corpus.py` creates four fictional source packs: two people in a shared workshop
and two in a reading club. Each has 12 role-labelled messages. Each family shares
12 questions in two option orders, giving 48 unique public forms, 96 person/form
combinations and **48 person/case endpoints**, not 96 independent cases.

There are 32 known and 16 unknown cases. Twenty personal-known cases have opposite
answers between paired people. Coverage includes action revision with inherited
conditions, two separate permission/presence guards, promise exceptions that do
not require the ordinary readiness condition, exception priority, a past fact
independent of future permissions, assistant-only proposals, meaningful execution
ordering, and method names whose leading `先` belongs to their full name.

These are new template-authored transfer sources, designed after prior development
failures. They are deliberately explicit boundary tests, not natural human logs,
independent authors, independent semantic gold acceptance or a population holdout.
The four fictional people form **two correlated template families**. Literal
support quotes establish provenance, not semantic entailment. Full-source controls
calibrate interpretability but cannot establish author/reference truth.

## Proposed scope

Request gpt-6.1-sol through logged-in OpenAI Codex, at most **46 new local CLI
attempts with no token or monetary ceiling**:

| Stage | Maximum calls |
|---|---:|
|One shared no-memory control and two full-source controls per family|6|
|Two independent source-only cards per fictional person|8|
|Two reads of each own card|16|
|Two reads of each own card's equal-character raw-source tail|16|

Each full control must immediately pass its 12 cases in both orders, no missing,
and personal-known must beat its own family's no-memory control. Any failure
closes before extraction slot 7. All eight extractions precede any reading.
Extractors see only their own source, budget, header/guide, instructions and schema;
no questions, references, old cards/responses/scores, manual bindings or case
feedback. Card/tail order alternates; the second read round reverses the first.

Each view has a fixed 48-case endpoint: two generated parents × two reads × two
option orders must all be correct. Report known, unknown, personal-known and
per-family/profile outcomes. A single failed order loses the case. An invalid
parent skips only its own four card/tail reads; those 12 cases remain missing in
both view denominators. No valid-only denominator, best-of or historical pooling.

The tail is the suffix of the complete canonical role-labelled source JSON,
exactly the character count of its own whole public card, including the card's
header/guide. It may begin inside a message or JSON structure and is not repaired.
This is a naive truncation comparator, not optimal source selection or a matched
model-token budget. Main card fidelity and the paired card/tail difference remain
separate endpoints; success against this tail alone is not a general compression
efficiency claim.

The same completed card answers are also rescored against the paired person's
20 divergent personal references. This needs **zero extra reader calls** and is
algebraically dependent on the main answers. It is a diagnostic, not an independent
wrong-card experiment or another successful statistical test.

Control, transport, wire/decode, unknown usage, model, runtime, input hash or owned
guard failure closes the remainder. Intent counts even if receipt is unknown.
No retry, repair, resume, truncation, replacement, replenishment or borrowing old
call scopes. Unused slots expire. Each child has 180 seconds; 8280 nominal summed
seconds are not a spending/total-duration cap or upstream cancellation guarantee.
Served identity, internal RPC/retries and cancellation remain unobservable.

## Offline checks and boundaries

```sh
python -m unittest discover -s tests -p test_fresh_source_contrast.py -v
python benchmarks/fresh-source-contrast-v1/plan.py --out /tmp/runaway-fresh-contrast-review
```

Seven fixture checks cover source/reference provenance, paired opposition, source
isolation, all 46 slots, own-length tails, repeat-request equality, every control
stop, invalid-parent missing denominators, one-order losses isolated by view,
fatal/final closure and exclusive freezing. Their oracle scores are not model
observations. Four local grant-refusal checks run separately. There are 14 static
requests and 32 frozen dynamic read rules; actual calls are **0**.

All earlier scopes remain closed. No production default change, real-person,
cross-model/harness claim, old 232-inventory coverage or asynchronous pooling.
New model execution requires a separate direct approval of this precise scope.
