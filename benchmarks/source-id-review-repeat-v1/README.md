# Repeated review of paired complete/incomplete drafts

**Measured scope closed:31 actual attempts,4 skipped/expired reader slots.**

## Measured outcome

Full controls pass30/30 unique person/cases;shared no-memory17/30. All four
originals are reread twice. Both new reviews per parent are read twice when
valid;all four answers per card/case and all eight joint answers are required.

| Parent | Original chars / score | Review0 chars / score | Review1 chars / score | Joint reviews |
| --- | --- | --- | --- | --- |
| p0,c2v historically complete |585 /15/15|510 /15/15|503 /15/15|15/15 |
| p1,c2v historically incomplete |312 /12/15|505 /15/15|503 /15/15|15/15 |
| p2,f7s historically complete |434 /15/15|442 /15/15|434 /15/15|15/15 |
| p3,f7s historically incomplete |240 /11/15|invalid /15missing|invalid /15missing|15missing |

The strict joint endpoint is **45/60correct,15missing**, versus original53/60
with no missing. Each individual review round is also45/60 with15missing.
Known cells are19/26 with7missing;unknown26/34 with8missing. These are60parent/
case cells over only30unique person/cases and two fictional people. Both draws
of p3 share the same15cases;their two invalid products do not create30unique
joint missing cases.

Three c2v known choices recover in both reviews/all orders:two explicit grouping
choices and one source-entailed notes choice whose branch is determinate despite
an unresolved complete rule. Both historically complete parents retain30/30
jointly. No observed wrong-choice regression occurs in a successfully read
reviewed card. This does not erase p3's availability failure. Six valid reviewed
cards pass90/90 conditional card/cases;discarding the two invalid products would
hide the primary endpoint failure. The prespecified60/60 target is not met.

## Why p3 remains unavailable

Both reviews return strings outside the source table,whose IDs are exactly
`m01` through `m22`:

- Slot9:`nodes[0].decisions[1]` is `m05 handicapped`.
- Slot28:`nodes[0].contexts[1]` is `m02 tailored`;`nodes[1].contexts[1]` is `m03 gl`.

The binder rejects both with `Undefined source reference`;no reviewed public
artifact is compiled and each loses only its two planned readers. The first
raw graph contains one node,the second four;node counts are not fidelity scores.
No ID suffix is removed,no source guessed,and no hypothetical repaired card is
compiled/read. The raw outputs and all old observations remain unchanged.

The earlier single p3 review that passed15/15 at381characters remains a separate
selected-case witness. It does not establish reliable review generation:these
two fresh reviews of the same fixed draft both fail admission. Citation semantic
sufficiency also remains unverified. Defaults are not promoted.

A separate [source-ID enum candidate](../source-id-enum-v1/README.md) now expresses
actual allowed IDs in the request schema. Its offline rejection/compatibility
checks make no new generation or fidelity claim;it was not used in this run.

## Cost and scope closure

All31receipts report364414input +15249output = **379663tokens**. Cached16384 is
inside input;reasoning1863 inside output. Stage totals: no-memory11701,full26682,
reviews99445,original reads96346,reviewed reads145489. Counters are not a bill or
project-wide total. All35planned slots are accounted for;four skipped readers
expire and cannot be reused. There are no model retries,manual patches or
missing usage records. The owned guard exits and ten older observation seals
remain unchanged.

## Frozen design
The [preceding selected-card study](../source-id-review-v1/README.md) recovers
f7s11/15→15/15 at240→381characters, but one review is insufficient to establish
repeatability or harmlessness on a complete card. Its citation-subset gap also
remains; this protocol does not change the reviewer to address it.

## Fixed sample and question

| Parent | Source | Original method | Characters | Historical band |
| --- | --- | --- | ---: | --- |
| p0 | c2v | source-order-v3 | 585 | complete |
| p1 | c2v | source-order-v3 | 312 | incomplete |
| p2 | f7s | coverage guidance | 434 | complete |
| p3 | f7s | coverage guidance | 240 | incomplete |

Within each person, the two cards came from the **same exact original producer
request**. Both pairs were selected after observing their old outcomes. They
are consumed fictional development data, not four people or a fresh holdout.
Historical bands stay fixed even if the new original-card reads differ.

c2v contains ambiguity in its entire notes rule while some individual branches
are still uniquely determined; its incomplete card lost one such inferred
choice and two explicit grouping choices. f7s has a uniquely inferable notes
rule and separately withdrawn grouping completeness; its incomplete card lost
one inferred and three explicit choices. The paired complete cards test whether
review introduces loss or false certainty into content previously preserved.

## 35-slot protocol

Three new controls run first: one shared no-memory, one own full source/person.
Each full control must pass15/15 in both orders, without missing, and improve
personal-known retention over no-memory. All controls must qualify before any
original-card read or review.

Each unchanged original graph receives **two independent review invocations**.
The second always receives the same original graph, not the first review's
output. Each new public card is read twice, with AB/BA in each response.
Original cards are also read twice. Parent order reverses between rounds;
original reads bracket the reviewed reads. Total:3controls +8reviews +8original
reads +16reviewed reads = **35 local CLI attempts maximum**.

The primary ledger retains **60 parent/case cells**, representing only
**30 unique person/cases** (13known,17unknown) and two people. Each parent has
15cases. Original and each single review use4answers/case; the joint result
across both reviews requires8/8. Report per-review endpoints alongside the
stricter joint endpoint; the unequal repetition count is not a matched-precision
causal comparison. The acceptance target is joint60/60 without loss of unknowns;
no production-default change follows from this finite development result.

Report recovery, observed regression and missing cells separately, with known,
unknown, derived-known and historical complete/incomplete bands. Repeated reads,
option swaps, parent views and the shared no-memory response are not independent
participants. Realized characters and costs may differ under the shared1536
whole-public-character ceiling.

## Unchanged method and failure rules

The published source-ID reviewer, schema, whole-message resolver, compiler and
reader stay unchanged. Review sees only its own22fictional messages and original
quoted graph. No questions, references, old reader responses/scores, previous
reviewed graph, manual binding/correction or author parameter enters review.
Readers get only the own public card and original30public forms; no decoder,
source table or private graph is supplied.

A binding/budget-invalid review skips only its own2readers; its15cases stay
missing in its repeat and joint endpoints. The other repeat and original reads
continue. A control, transport, wire/schema/decode, unknown usage, model,
input/runtime or owned-guard failure closes the whole remainder. No retries,
manual patches, resumption, replacement, best-of or expired-slot reuse.
There are zero new initial extractions. The sample does not establish fresh
initial-generation stability, independent generalization, real-user fidelity,
cross-provider transfer or semantic citation sufficiency.

## Reproduce preparation without a service

```sh
python -m unittest discover -s tests -p 'test_source_id_review_repeat_protocol.py' -q
```

Seven offline fixtures check exact own-source/parent requests,35slot accounting,
selective invalid-product skips, fatal closure, a single wrong option order,
own-parent/review-repeat routing, guarded live refusal and immutable inputs.
Oracle choices only verify accounting; they are not measured recovery results.
Cached preparation rechecks archive/implementation fingerprints and returns
copies, so cache reuse cannot hide changed files or caller mutations.

The unchanged two-file implementation reconstructs input manifest
`87e51a7306fd35c3b0dd05f0fc3a9c5ea679e9e3fc96786060fd984c24a3ae69`.
It freezes19static requests and16own-review reader rules. `protocol.json` retains
the unapproved intake;actual execution used a separate local35-call grant after
all three CI checks passed at the published implementation commit. The scope is
now closed. Replay reconstructs exact requests,own-parent/repeat routing,raw
values,invalid products,skips,usage,artifacts and fixed denominators offline:

```sh
python scripts/replay_source_id_review_repeat.py
python -m unittest discover -s tests -p 'test_source_id_review_repeat*.py' -q
```

Private grants,host/process/runtime records and transport envelopes stay outside
the portable archive. Replay is not independent semantic acceptance,new model
inference or a bill. Old scopes and observations remain closed.
