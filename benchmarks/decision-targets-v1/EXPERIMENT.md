# Proposed next test: at most21new calls, not executed

Old consumed h68/h93 sources test the actual observed losses; the new openly
authored development source tests whether a repair drops execution constraints.
No independent holdout, human, cross-model or causal method claim is intended.

| Proposed stage | New call cap |
|---|---:|
| Shared no-memory on80old t/n questions |1|
| Full h68 and h93,80questions each |2|
| No-memory and full on32rotated development questions |2|
| Cached scope-v1 h68/h93 cards, twice each |4|
| Fresh target-v2 extraction for h68/h93 |2|
| Fresh scope-v1 and target-v2 extraction for development source |2|
| Each of the4fresh cards read twice |8|
| Total |**21**|

The h baselines are the previously measured **1118/1219character scope-v1
cards**, not the older grouped cards. The development baseline has no previous
card, so both v1/v2 must generate one. Both methods share the original schema,
source binder, reader and1536whole-character cap, with no length padding.
Each new artifact has two identical reader request objects; sampling is not
controlled, and one extraction per method/source cannot measure generation
variance. Cached h baselines remain a confound.

The distinct sources are two48message fictional histories and one14message
authored development history:110messages. Old h cases are40per person and new
development cases16, all with two option orders:96cases, not extra independent
people. The old80cases are repeated regression, not new232case coverage. The
authored16cases are development and do not resolve reference custody or w14.

The first five slots are controls, checked immediately after each full result:
all40old or16development cases must match both orders, with no missing values;
h full personal-known must exceed shared h no-memory, and development full known
must exceed its no-memory. Any failure closes the remainder before cards or
extraction. All control references are existing/developer-visible judgments.

An invalid bound card skips exactly its own two readers, retaining missing
cases; no replacement, repair or truncation. Any transport/schema/decode/usage/
requested-model/runtime/input-hash/owned-guard failure stops the remainder.
Intent reservations count as attempts, including unknown whether upstream
received the request. No retry, resume, budget replenishment or reuse of closed
scopes. Schema-valid behavioral errors stay recorded; no best-of selection.

Requests target gpt-6.1-sol, fresh tool-free contexts, fixed as_of2026-10-30.
**21is a call cap with no token or money ceiling.**180seconds per local child
is not a spend cap or guaranteed upstream cancellation. Internal RPC/retries,
actual served identity and already-sent request costs cannot be independently
controlled. Unknown usage stays unknown and stops execution, not zero cost.

Extractors receive only their own source and generic instruction/schema, never
questions, old cards, scores, prior responses, targets, predicates or references.
Readers receive only a public card and natural-language questions/options.
Local reference data are separate; “private” here means model-input isolation,
not a secret holdout. No real-person data are included.

Prepare13exact static jobs and8conditional jobs without invoking a service:

```sh
python benchmarks/decision-targets-v1/experiment.py --out /path/to/new-proposal
```

`static-requests.json`, `dynamic-rules.json`, `slots.json`, source/query/reference
snapshots and implementation hashes make the finite scope reviewable. Preparation
is not authorization; a newly verified human grant and local activation checks
are required before an actual runner sends requests. No service runner, approval
receipt or background task is created by this command.

Report each profile/method/read with preference, execution, unknown, known and
missing denominators; also require both reads/both orders per case. Passing old
preference questions while losing execution constraints is a failure. Keep old
93/96,118/120and all original records. Neither publication nor this plan grants
calls for the remaining72j cases, B37 or any production-default switch.
