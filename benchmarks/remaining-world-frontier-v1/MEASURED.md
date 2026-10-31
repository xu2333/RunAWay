# Broader source-policy test: known local exceptions still become unknown

All40approved local CLI children completed on2026-10-30, requesting gpt-6.1-sol.
All12extractions produced valid cards; no reader was skipped and no retry,
repair, replacement, unknown usage or unused slot occurred. The scope is closed.

| Ceiling | Strict primary cases | Known | Unknown | Author-tagged personal-known | Missing |
|---|---:|---:|---:|---:|---:|
|1024characters|**62/69**|44/51|18/18|33/33|0|
|1536characters|**61/69**|43/51|18/18|33/33|0|

Strict requires both generations, both reads and both option orders to match
each frozen primary reference. The earlier1024result of96/96did not transfer
without losses to these three other sources. One case's difference does not
establish that1024is superior. Actual cards are679–793characters, below both
ceilings; the larger ceiling did not demonstrate a repair. Personal-known is
an author-tagged diagnostic subset, not a replacement for the69-case endpoint.

## Every output and read

Scores below each require both option orders. Each profile has23primary cases.

| Profile | Ceiling | Generation0: characters; read0/read1 | Generation1: characters; read0/read1 | Strict across generations |
|---|---:|---|---|---:|
|j16|1024|693;23/23,23/23|767;20/23,20/23|20/23|
|j62|1024|725;20/23,23/23|760;23/23,23/23|20/23|
|j85|1024|683;22/23,23/23|679;23/23,23/23|22/23|
|j16|1536|793;20/23,20/23|787;20/23,20/23|19/23|
|j62|1536|780;19/23,19/23|791;23/23,23/23|19/23|
|j85|1536|788;23/23,23/23|774;23/23,23/23|23/23|

At1024, the first j62card changes3cases on its identical second request; the
first j85card changes1. Stable reader abstentions and generation differences
also remain. Do not select the successful repeat or later perfect generation.
The data describe nested observations, not a causal variance decomposition.

## The losses are explicit local exceptions

All incorrect primary answers areUfor known choices. Losses span four case types:

| Case | Source policy | Frozen exception answer | Observed failure contexts |
|---|---|---|---|
|w07|m11borrows a commemorative medal under a specific promise|View the original behind glass|j16andj62|
|w11|m16gives a confirmed night-shift-week exception|Agree fixed quiet hours|All3profiles|
|w19|m26gives a confirmed meter-shutdown-week exception|Water on fixed dates|j16andj62|
|w23|m31gives an explicitly named gift and requested-purchase exception|Choose directly and send|j16andj62|

The exceptions and their actions are often present in the public card. For
example, j16's1536generation0puts both ordinary and exception exhibition rules
under a shared scope requiring both displays to be permitted, informative and
equally priced. Its roommate scope likewise requires similar schedules and
agreement that both coordination methods work. The exception-only questions
do not state those ordinary prerequisites. The fixed guide requires group scope
and row conditions together, so ordinary conditions can block an explicit P1
exception even when its own trigger is known.

j16's plant exception is also retained, but generation1adds a later return-to-
normal condition into the action text. Its fixed-date answer becomesUwhile
generation0's shorter action succeeds. This suggests action/condition separation
as another hypothesis, not a proven sole cause. No per-question reasoning trace
was collected; the card text and repeat patterns do not identify one mechanism
with certainty. The source-only scope-v1instructions already warn against
overrestricting scope; another instruction-only assertion is not a verified fix.

The next architecture should make condition ownership explicit for each rule
and allow shared scope only from conditions common to all affected rules.
Any such source annotation and compiler still need separate semantic and model
validation. No new encoder, decoder, renderer or production default was tested
or promoted in this scope; the when-wire candidate was excluded.

## Three disputed cases remain unscored

All72legacy cases and48question forms remain. The69primary rows exclude only
the3preexisting w14flags, before any new outputs. Both generations and both
budgets answer those flagged questions with the old author annotations in this
run: j16individual scoring, j62/j85cooperative play. These observations do not
accept a gold label or overrule the earlier two same-model opinions favoringU.
There is no w14pass/fail or majority-vote adjudication, and69/69would not mean
72/72. All old labels and93/96results remain unchanged.

## Controls, accounting and coverage

Full-source controls pass23/23primary cases per profile and exceed no-memory
on personal-known. No-memory scores18/69from correctUanswers, with no known
decisions retained. All12extractions preceded any card reading and saw only
their own source and budget, never questions, flags, references, old cards,
old experimental responses or feedback.

Reported usage is522,775input +50,719output = **573,494tokens**, with no missing
counters.66,048cached-input and10,553reasoning-output tokens are subsets.
This is recorded usage, not a bill.40was a local attempt cap without token or
money ceilings. Internal RPC/retries, actual served identity and upstream
cancellation remain unobservable. The owned temporary guard exited.

These are3existing34-message fictional worlds, not new people or an independent
holdout. References are developer-visible author judgments. Rotations, repeats,
related cases and shared source templates are not independent people. Real-
person fidelity, cross-model transfer and independent semantic acceptance remain
unverified. No default change is justified by these results.

A separate[source-binding inventory audit](../regression-inventory-v1/README.md)
registers the first chronological valid1536reading per profile and adds72
recorded cases. The original inventory now has **232/232measurements bound**,
zero unmeasured cells and3disputed cells retained. It does not pass all232cases,
accept their references or establish project completion. The old sealed master
and160-case snapshot remain unchanged; the new ledger is appended separately.

## Offline replay

```sh
python scripts/replay_remaining_world_frontier.py
python scripts/replay_regression_inventory.py
python -m unittest discover -s tests -p test_remaining_world_evidence.py -v
```

The portable snapshot retains40exact requests/raw response texts,12bound cards,
safe counters, all72legacy references and the prospective69/3mask. Replay
reconstructs the frozen package and runs its controller against an injected
archive with no backend, reproducing gates, scores and unscored vectors.
Shared archive helpers preserve the earlier37-call replay unchanged. Local
grants, paths, credentials, private error messages and transport envelopes are
excluded. Original envelope hashes provide provenance; public replay does not
reconstruct omitted bytes or independently prove server identity.
