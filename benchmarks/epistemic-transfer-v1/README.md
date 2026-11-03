# Source-licensed inference and uncertainty

The [closed actual result](MEASURED.md) is available:10 attempts, full-source
controls120/120, then the first extraction timed out with unknown usage.39slots
expired. No card or tail was read; both120-case denominators remain missing.
Known receipts sum118579tokens but do not include the timeout's unknown cost.

## Original preparation record

The following unapproved/unrun flags describe the frozen intake package. Later
authorization and actual observations are separate; the original inputs were
not rewritten after execution.

**Prepared offline; unapproved and unrun.** No new model calls or production
changes. The previous [long-source result](../long-task-probe-v1/MEASURED.md)
retained40/40 existing questions; it did not establish inference on new feature
combinations. This probe follows the earlier
[standalone-decoder findings](../standalone-latent-v1/NEXT-CONTRACT.md).

## What can the source actually determine?

Eight fictional profiles each discuss two separate software domains: automatic
organization of personal notes and automatic grouping of event registrations.
Two binary features describe whether all content stays local and whether every
change is fully reversible. Each domain has a stable binary choice function;
the two domains need not use the same function.

The source initially spells out four possible functions: always automate,
automate iff local, iff reversible, or iff both. Some profiles later **withdraw
the guarantee that these four exhaust their possibilities**, preserving their
confirmed decisions. The oracle then considers all16 binary functions on the
four feature combinations. It does not resolve unknowns using the author's
hidden generating rule. Some withdrawn profiles actually use functions outside
the illustrative four. Changing undisclosed generating values leaves source,
questions and reference unchanged; tests verify this separation.

For a question with omitted features, every possible feature completion and
every source-compatible function must select the same action. Otherwise the
reference is `U`. A partially identified function can still entail a choice.
Summary-only export, partial recovery and a third unobserved domain fall outside
the explicitly defined vocabulary. No monotonicity or common-sense personality
assumption fills these gaps. Assistant/tool suggestions are not user decisions.

Definitions exist only in the source. The reader receives its own card or raw
comparator, the public questions, and the unchanged standard reader contract.
**No external decoder, rule-family table or candidate-personality label is
appended.** A successful card must carry what its reader needs within its1536
Unicode characters, including the fixed header and guide. The unchanged
source-order-v3 encoder sees only its own sources and fixed budget/guidance.
It sees no questions, references, hidden tables, old cards or experiment scores.

## Fixed cases and instrument checks

There are176 messages,22 per profile. Message text alone is1990–2044 characters
per profile, exceeding the whole-card ceiling; role-labelled transcripts are
2163–2217 characters. The comparator takes exactly the last N characters of the
own role-labelled transcript, where N is the whole compiled card length. It can
start mid-message. No span selection, repair or hidden metadata is added.
Character matching does not match tokens, retrieval quality or cost.

Each profile has15 cases: four complete combinations, two partial-feature cases
and one outside-vocabulary case per domain, plus one outside-domain case.
The same30 question forms cover both option orders for all profiles. The fixed
denominator is120 person/cases per view:

| Slice | Cases |
|---|---:|
| Known / unknown |58 /62|
| Known directly observed / derived from source constraints |27 /31|
| Known requiring personal observations / already fixed by the family guarantee |48 /10|
| Unknown that becomes falsely known if a withdrawn guarantee is reused |20|

The cohort partition is27 observed decisions,5 undecided training conditions,
32 unseen combinations,32 partial-feature cases,16 outside-vocabulary cases,
and8 outside-domain cases. Slices can overlap; their denominators are explicit.
One producer, two reader invocations and both option orders give four answers
per case/view; all must match. Missing answers remain in the120-case denominator.

`calibration.synthetic.json` contains constructed instrument fixtures:

| Constructed response style | Correct /120 | Known correct /58 | Unknown correct /62 |
|---|---:|---:|---:|
| Reference vector |120|58|62|
| Always unknown |62|0|62|
| Retain only direct observations |89|27|62|
| Ignore guarantee withdrawal |100|58|42|

These are deterministic scorer calibration, **not model performance**. They
demonstrate why the known/derived and withdrawal slices must accompany totals.
The oracle is exhaustively enumerated and checked against a separately written
hand-reference table. This is not independent semantic acceptance of the
Chinese narratives or a blinded holdout. Preparation review corrected a
partial-feature question whose prose said local while its state set meant
external; explicit prose/state checks now cover all complete and partial cases.

## Proposed49-attempt schedule

| Stage | Maximum local CLI attempts |
|---|---:|
| One shared no-memory and eight own full-transcript controls |9|
| Source-only extraction, one per profile |8|
| Two card reads per profile |16|
| Two own equal-character transcript-tail reads per profile |16|
| Total |49|

All eight full controls must achieve15/15 in both orders without missing answers
and improve personal-known recovery over shared no-memory before extraction10.
The shared response is dependent across profiles. If this gate fails, the scope
closes: an encoder comparison cannot explain failure already present with full
source and the unchanged reader. No post-result prompt change is permitted.

An invalid parent skips only its own four card/tail reads, retaining its15 cases
as missing in both denominators. Control, transport, schema, decode, unknown
usage, requested-model, runtime, input-integrity or owned temporary-guard failure
closes the remainder. No retry, repair, resume, replacement or slot replenishment;
unused slots expire. The180-second local-child timeout is not an aggregate
duration, token, money or upstream-cancellation cap. Internal service retries
and served-model identity are not independently observable.

This is a deliberately small finite logical stress test, not natural language
personality recovery, real-person fidelity, arbitrary reasoning or cross-model
validation. Profiles are selected joint settings sharing templates and questions,
not independent authors. One card/person does not test generation stability.
No confidence interval, population inference, likelihood-based information gain,
product-cost saving or production-default promotion is claimed. Old results and
closed authorizations remain unchanged. Execution requires a fresh explicit
human scope grant and successful exact-head CI.

## Reproduce offline

```sh
python benchmarks/epistemic-transfer-v1/check.py
python -m unittest discover -s tests -p test_epistemic_transfer.py -v
```

`corpus.py` constructs sources, public questions, oracle and author parameters;
`plan.py` prepares17 exact static requests and32 dynamic slots in a new local
review directory. Public synthetic author parameters/reference files are for
audit, never encoder/reader input. `engine.py` has only injected backends; its
test fixtures are explicitly simulated and create no inference children.
