# Prospective everyday-decision compression check

**Unapproved; no model results.** Reproduce the frozen preparation offline:

```sh
python3 -B benchmarks/fresh-decision-v1/check.py
python3 -B -m unittest discover -s tests -p test_fresh_decision.py -v
```

The previous [single-pass repeat](../single-pass-repeat-v1/README.md) measured
four consumed fictional people. This proposal changes the sources and tasks
while keeping its encoder, compiler, reader, 1,536-character ceiling and finite
controller run function. It adds cohort reporting without changing control or
failure handling. No installed default changes.

## New material

Four new fictional people form two opposite pairs. Each has 16 messages
(12 user, 4 assistant), over 2,200 source-text characters, across four ordinary
domains: collaborative drafts, volunteer work, responding to a friend and
research exploration. Assistant suggestions are explicitly unendorsed. User
messages state a normal choice, a changed-condition exception and a narrower
override. They do not certify an executed task.

Each domain supplies three source-licensed choice cases and one unrecorded
target. There are 64 unique person/cases: 48 known, 16 unknown. Sixteen known
cases combine the exception and overriding condition. They are reported as
`derived_known` for compatibility, meaning author-specified condition
composition, not independent reasoning gold. The unknowns ask about tool or
place preferences, or execution status, absent from the source. Opposite pairs
disagree on all known cases and share the unknowns.

Every person sees the same 32 public forms: two option orders for each of 16
cases. No persona name, reference, source IDs or author settings enters the
question form. The extractor sees only its own source and the unchanged guide,
schema and character budget. It never sees questions, reference, prior outputs,
scores or the other independent generation. Readers see only the own card or
its own equal-character, role-labelled source suffix plus public questions.

This is **procedurally authored fiction**, designed with knowledge of previous
failures. The author settings, explicit messages and separately typed hand table
are consistency checks within one design, not independent semantic acceptance.
Fresh after freezing a method does not make this an independently authored
holdout. It is neither real-person validation nor evidence that the scenarios
represent a user population. The inherited reader `as_of` is unchanged; the new
sources contain no dated events or claims requiring later information.

## Proposed 45-call scope

| Stage | Maximum attempts |
| --- | ---: |
| New no-memory/full-source controls | 5 |
| Two independent single-pass cards per person | 8 |
| Two reads per card | 16 |
| Two reads of each exact-character own-source tail | 16 |

Each full-source control must get all 16 own cases right in both orders, with
no missing response and an own-known gain over the new shared empty-material
control. Any failed control ends the scope before extraction. No-memory still
uses the source-constrained reader; it is not an unconstrained assistant.

For each view, keep all 64 person/cases in the denominator. All two generations
× two reads × two orders (eight answers) must agree with the reference for a
case to count as jointly retained. Report generations and four cohorts
separately: ordinary, changed condition, compositional override and unrecorded
target. Repeated reads are not independent participants.

An invalid product skips only its own four reads; its missing cells remain.
Transport, structural schema/decode, unknown usage, requested-model mismatch,
input/runtime/guard or control failure closes unused slots. No retry, repair,
resume or replacement is permitted. Output creation precedes the exclusive
single-use claim, and that claim precedes backend entry. A local child is still
limited to 180 seconds. The proposed model is `gpt-6.1-sol`; the attempt cap
does not cap tokens or money. No live transport or service authorization is
included in this public controller.

The equal-character suffix is neither token-matched nor an optimal raw-history
selection. A paired contrast reuses responses and does not add independent
evidence. Passing this limited design would not establish real fidelity,
population generation stability, cross-provider transfer or optimal compression.

## Integrity and software checks

`corpus.py`, `plan.py`, `engine.py`, `fixtures.py` and `check.py` reconstruct the
sources, reference, requests and schedule. `protocol.json` records the proposal;
`prepared-manifest.json` binds all prepared files and explicit scientific
dependencies. Existing sealed evidence and implementation hashes are unchanged.
Runtime reference/author-evidence files are private and excluded from service
requests; the public authoring code makes this fictional design reproducible.

Tests use a **reference-aware oracle mock** returning answers separately from a
deliberately incomplete card. A 64/64 mock result checks bookkeeping only. It
is not a model response or fidelity observation. Damage cases test one-order
failure, missing-product denominators, own-parent tails, foreign anchors,
control/fatal stops, guard/output ordering, rehashed input changes and symlinks.

Execution needs a new direct finite-scope grant and successful exact-head CI.
Publication, a generated manifest and passing mocks do not grant model calls;
all previous experimental scopes remain closed.
