# Per-rule conditions before shared scope

The previous [40-call study](../remaining-world-frontier-v1/MEASURED.md)
retains **62/69** cases at 1024 characters and **61/69** at 1536. Explicit local
exceptions sometimes become unknown even though their triggers and actions
survive. A plausible cause is ordinary-only prerequisites being placed in a
scope that also gates the exception. Increasing the ceiling did not repair it.

This **unmeasured candidate** changes the intermediate representation. A
source-only encoder lists each rule's own required conditions, each grounded
in exact source quotes. It distinguishes the object, decision question,
conditions and current action. It sees no card budget, evaluation questions,
old outputs, references or feedback. A local compiler then factors conditions
into shared scope only when the same condition and citations occur in every
row for that object and all rows ask the same question.

For each row, `shared conditions ∪ residual conditions = original conditions`,
with no overlap. Ordinary prerequisites cannot enter an exception through this
factoring step. Genuine global prerequisites remain on every affected row.
Different questions or citation grounding prevent sharing. The resulting card
uses the existing renderer, guide and lossless public codec. All public text,
including the guide and embedded dictionary when used, counts toward the cap.
No external decoder, truncation, repair or automatic retry is introduced.

The invariant concerns the **explicit predicate sets**, not the truth of the
model's natural-language annotation. Exact quotations do not establish
entailment or completeness. An encoder can still omit a rule, assign the wrong
condition, merge objects, misunderstand priorities or exceed the fixed card
budget. The compiler does not solve these semantic problems. Toy calibration
cannot establish real-person fidelity or transfer across models/harnesses.

## Offline calibration

Eight tests cover an ordinary route, an explicit promised-route exception and
a genuine global entry constraint. Exhaustive Boolean assignments preserve the
decisions before/after factoring; damaged union-hoisting blocks the exception,
while deleting the global constraint incorrectly permits it. Missing ordinary
facts do not block the known exception, but missing real global facts do. Other
tests preserve same-priority conflict, exact renderer output, quote/role checks,
separate questions and hard budget rejection. These are symbolic fixtures, not
successful LLM extractions.

```sh
python -m unittest discover -s tests -p 'test_owned_conditions*.py' -v
python benchmarks/owned-conditions-v1/plan.py --out /tmp/runaway-owned-review
```

Preparation creates frozen inputs only; this public package has no model
backend, grant issuer or executable service launcher.

## Proposed new 42-call comparison — not authorized or run

- **96 existing fictional messages**: h93 (48), j16 (34), authored development
  fixture (14). Three distinct banks contain 160 public question forms.
- **6 concurrent-study controls**, one no-memory and one full-source per bank.
  Each full must pass immediately: 40 / 23 / 16 primary cases in both orders,
  no missing values, and personal-known (h/j) or known (dev) above no-memory.
- **12 fresh extractions**: 3 sources × unchanged scope-v1 / owned-condition
  candidate × 2 generations. Every extraction precedes every card read.
- **24 reads**, two identical requests per valid card, each with both option
  orders. Both methods have the same **1536 whole-character ceiling** and use
  the same reader. The ledger encoder itself does not see that ceiling.

Each method has **79 fixed primary cases**: 50 known, 29 unknown; 25 are
author-tagged personal-known. The 16 development cases additionally distinguish
11 preferences and 5 execution decisions. All 80 legacy cases remain present;
only j16/w14, flagged before this proposal, is unscored. Its old annotation and
response vectors remain, without new reference acceptance or a majority vote.

The primary strict score requires both generations × both reads × both orders
to match each primary reference. Report all generations, lengths, missing cases,
strata, within-card read disagreement, between-card observed disagreement and
paired baseline-only/candidate-only wins. Failed generations remain in the
denominator; neither successful repeats nor later cards replace them. Rotations,
reads and related cases are not independent people. No case-level confidence
interval or claim of causal variance decomposition is planned. This comparison
tests bundled encoder/compiler designs; it cannot isolate a single component.

The sources were selected after inspecting prior losses and are consumed
development, not an independent holdout. Passing the local exception cases while
losing unknown/execution cases is a regression. A tie, longer card or invalid
product is reported directly; none establishes an advantage. Default promotion,
human-fidelity claims and cross-model generalization require separate evidence.

An invalid bound product skips only its own profile/method/generation's two
readers. A failed control, transport, wire schema, decoding, unknown usage,
model, runtime, frozen input or owned guard closes the remainder. No retry,
repair, resume, replenishment, feedback or scope reuse. All old service scopes
are closed. **42 is a new local attempt cap, with no token or money ceiling**;
it requires a new direct human approval. No production default changes.
