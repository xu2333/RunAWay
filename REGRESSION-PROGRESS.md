# Compression regression progress

The latest [lower-budget repeated-extraction study](benchmarks/compression-stability-v1/MEASURED.md)
uses37of at most41attempts.1024whole characters retains **96/96** across two
generations, two reads and both option orders;768scores **53/96**, including
40missing cases from two invalid h68products and3omitted h93decisions. The
remaining4reader slots expired. This is consumed development, not a new holdout
or a production-default change.

The preceding [decision-target comparison](benchmarks/decision-targets-v1/MEASURED.md)
completed 21 calls: both methods score **96/96** on two consumed profiles and
one new authored development fixture, with the candidate adding 99 characters
in aggregate. This shows no observed advantage; the default remains unchanged.

The preceding consumed synthetic regression still records fidelity losses. Under the
strict rule that both reads and both option orders must match the frozen
reference, revised cards retain **118/120** cases and existing cards **119/120**.
This does not establish a causal method difference. The production default is
unchanged.

The revised-method inventory has **160/232 cases measured**, with 72 j-profile
cases unmeasured. Coverage means actual source-bound extraction/reading records
exist, not that the cases passed. Three disputed w14 cells remain in the
unmeasured inventory. Original labels and the old 93/96 result are retained.

## Published observations

| Closed scope | Actual CLI children | Cases in that phase | Observed result |
|---|---:|---:|---|
| Forward source-derived probes |17|80|Full 80, no-memory 42, own 80, equal-character source tail 54; wrong-card reads match actual donor 80|
| New fictional worlds |29|96|Full 96, no-memory 24, own 93; all 3 own losses belong to j39. Fixed attacked full/card reads each 96; the clean-dependent overall gate still fails|
| Source-policy revision, j39 |7|24|Old/new card each 24/24 twice; 797→720 characters, no observed accuracy advantage|
| Revised-method h17 pilot |7|40|Old/new card each 40/40 twice; 1167→1200 characters|
| Remaining h42/h68/h93 |19|120|Old strict 119/120, revised strict 118/120; no missing cells|
| Decision-target comparison |21|96|Both strict 96/96; 80 repeated old cases plus 16 authored development cases; no accuracy or compression advantage|
| Lower-budget repeated extraction |37|96per ceiling|1024strict96/96;768strict53/96including40missing;2invalid cards,4readers skipped|

Phases overlap: do not sum case denominators or treat option rotations,
repeated reads or shared templates as independent samples. References are
developer-visible author judgments, not independently accepted accounts of real
people. New-world text was unseen by the locked producer when authored; this
does not establish independent author blindness or external holdout status.

The original regression snapshot archives 79 choice/extraction request objects and raw JSON response
texts, safe usage counters, sources, references and public cards. Two additional
neutral-opinion calls are separate. Recorded tokens are 1,381,282 for the five
choice scopes and 21,210 for those opinions: 1,402,492 in this snapshot. This is not a
bill or the total project cost. Cached/reasoning tokens are subsets, not extra
tokens. Server model identity, internal RPC/retry count and cancellation are not
independently observable. Export and replay perform no new inference.

## Remaining loss

| Profile | Old card, first/second read | Revised, first/second read | Characters, old→new |
|---|---|---|---:|
|h42|40/40,40/40|40/40,40/40|1316→1217|
|h68|39/40,40/40|40/40,40/40|1218→1118|
|h93|40/40,40/40|38/40,40/40|1200→1219|

h68's old-card loss is t01; h93's revised-card losses are t01/t02. Both option
orders returned `U` instead of the recorded interface-plan choice. The identical
request recovered the choices on repeat. The correct action text remained in
each card; keep both reads rather than selecting the successful one.

The shared boundary is plan choice versus permission to execute. In h93, m29
chooses switching interfaces and marking a new version; m22 chooses the same
for the temporary script. m45 separately keeps the plan in a document pending
a client-list check and says style memory is not permission to publish. The new
card puts these rows in one group. A reader may conflate them into competing
choices, but this is a source-linked hypothesis, not a proven cause. No
per-question reasoning trace was collected, and the same request also succeeded.

The three revised cards total 3,554 characters versus 3,734, about 4.8% less. The
losing h93 card is 19 characters longer. Single-card samples establish neither a
stable length advantage nor that shortening caused the losses. The published
target-specific logical contract is a development aid, not a language parser or
an experimentally verified fix.

## Disputed reference and validator repair

In w14, “equal fees” may not establish the rule's “no extra charge” condition.
Whether the question inherits the earlier free setting remains unresolved for
all four j profiles. Two fresh same-model opinions say insufficient/`U`;
agreement does not accept a new gold label.

The first opinion's original controller failed because it omitted the supplied
question ID from the citation namespace. Its 12 user quotes and 4 question quotes are
literal. The second passed the repaired dual-domain check. Replay reproduces
the original failure without reclassifying it as a successful original scope,
and verifies question citations separately from user evidence.

## Reproduce without a model service

```sh
python benchmarks/regression-progress-v1/check.py
python -m unittest discover -s tests -p test_regression_progress_evidence.py -v
```

The [benchmark pack](benchmarks/regression-progress-v1/README.md) includes exact
public cards and deterministic binding/scoring checks. CI runs this replay.
Local approval records, credentials, absolute paths and private transport
envelopes are excluded. Original envelope hashes are provenance only; public
checks verify the retained requests, raw text, counters and artifacts, not
omitted envelope bytes.

Next, distinguish producer variation from reader variation and add harder
decision-boundary cases. The remaining 72 cases, independent
source/reference custody, real-person fidelity and cross-harness behavior remain
open. All scopes here are closed; publication grants no new experiment budget
or production-default change.

The [decision-target candidate and local calibration](benchmarks/decision-targets-v1/README.md)
implement that hypothesis without changing the schema or renderer. Calibration
detects execution-limit erasure even when preference scores stay perfect.
The new [21-call observation](benchmarks/decision-targets-v1/MEASURED.md) adds
375,216 recorded tokens and a separate portable evidence pack; its 96/96 tie
does not establish that the instructions repair prior losses. The original
snapshot remains byte-for-byte unchanged.

The [compression/stability plan](benchmarks/compression-stability-v1/README.md)
and its15offline fault tests are preserved. Its new41-call scope is now closed
with37actual children and613,614recorded tokens. A portable archive and9damage
tests reproduce validity failures, missing denominators and observed losses.
Four additional offline checks cover an[unmeasured when-field contract candidate](benchmarks/wire-contract-v1/README.md).
Neither the candidate nor publication grants another service scope. All original
source-policy and target-v2 records remain unchanged.

The next [unexecuted breadth/frontier plan](benchmarks/remaining-world-frontier-v1/README.md)
freezes three other existing fictional worlds at1024/1536whole characters,
two generations and two reads per card. It proposes40new attempts and requires
a new exact grant. The69previously unflagged author cases form the prospective
primary denominator;3preflagged w14cases retain original labels and response
observations without pass/fail or acceptance. Preparation does not fill the
remaining72inventory cases. Ten offline adapter/mask/failure tests pass.
