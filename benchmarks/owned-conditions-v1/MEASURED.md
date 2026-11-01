# Condition ownership helps three exceptions, but capacity prevents replacement

The approved 42-attempt scope closed on2026-11-01 with **38 actual CLI children**.
Both h93candidate products are invalid; their 4 readers were skipped and expired.
No retry, repair, replacement, unknown usage or scope replenishment occurred.
The production default stays unchanged.

| Method | Strict primary cases | Missing | Known | Unknown |
|---|---:|---:|---:|---:|
|Unchanged scope-v1|**75/79**|0|46/50|29/29|
|Owned-condition candidate|**38/79**|40|25/50,24missing|13/29,16missing|

Each strict case requires both independently requested generations, both reads
and both option orders to match its frozen reference. Missing is not an observed
wrong choice or an abstention, and it remains in the 79-case denominator.
The candidate is **not suitable to replace scope-v1**.

## Every generation and read

All cards have the same 1536 whole-character ceiling, renderer and reader.

| Source/method | Generation0: characters; read0/read1 | Generation1: characters; read0/read1 | Strict |
|---|---|---|---:|
|h93/scope-v1|1118;40/40,40/40|1128;40/40,40/40|40/40|
|h93/owned-v1|Invalid;two readers skipped|Invalid;two readers skipped|0/40,40missing|
|j16/scope-v1|783;19/23,19/23|791;20/23,20/23|19/23|
|j16/owned-v1|1409;22/23,22/23|1379;22/23,22/23|22/23|
|dev/scope-v1|675;16/16,16/16|608;16/16,16/16|16/16|
|dev/owned-v1|910;16/16,16/16|957;16/16,16/16|16/16|

The 39 cases whose sources have valid products under **both** methods score
35/39baseline versus38/39candidate. This diagnostic subset does not replace
the 79-case primary endpoint. Paired strict outcomes across all 79 are 35 both
correct, 40 baseline-only correct, 3 candidate-only correct and 1 neither correct.
The 40 baseline-only cases are the candidate's missing h93 cases.

The candidate's two j16cards total 2788 characters versus 1574 for baseline,
**1214 more**, approximately 77% longer. The development cards total 1867 versus
1283, 584 more, with no score gain. These are observed paired lengths, not a
general compression estimate. The bundled encoder/schema/compiler design
differs; this study does not isolate a single component or length effect.

## Invalid products are a structural capacity failure

Both h93 extractions contain 24 rows across 14 distinct object labels. Their raw
wire format passes, but compilation creates 14 groups and the unchanged public
binder accepts at most 12. Both fail with `Provide0–12 groups` before character
packing. No valid prompt length exists for them; **this is not a measured
1536-character overflow**. They were not merged, shortened or recompiled into
replacement experiment products.

The flat ledger schema constrains row count but not distinct object count.
This exposes an intermediate-to-public capacity mismatch. An
[unmeasured private object-table candidate](../owned-object-table-v1/README.md)
now constrains at most 12 objects and 30 total rows in the wire schema, expanding
all object names before public rendering. Six symbolic tests cover its bounds,
references, exact original binding and failures. It has no model observations
and does not repair or replace either failed original h93 product. Other text
limits, budget and semantic annotation can still fail.

## Three known exceptions recover; night-shift remains unknown

All scored baseline losses are known j16 exceptions answeredU:

| Case | Frozen answer | Baseline strict | Candidate strict |
|---|---|---|---|
|w07,borrowed medal promise|View the original behind glass|Fails both generations|Passes both generations and reads|
|w11,confirmed night-shift week|Agree fixed quiet hours|Fails both generations|Fails both generations|
|w19,confirmed meter shutdown week|Water on fixed dates|Fails both generations|Passes both generations and reads|
|w23,explicitly named gift/requested purchase|Choose directly and send|Generation0fails,generation1passes|Passes both generations and reads|

Both candidate night-shift rows retain the explicit trigger and P1 priority,
without the ordinary branch's same-schedule/agreement prerequisites. They still
returnUin all 8 nested observations. Both use the action `先约定固定安静时段`
while the offered option is `约定固定安静时段`. Action wording or reader alignment
is a hypothesis, not a proven cause: no controlled wording ablation or
per-question reasoning trace was collected. Removing `先` universally would
also risk erasing real sequencing preferences. The current scorer, reader,
source and reference are preserved.

The remaining valid products retain all 6 j16 unknown cases, all 16 development
cases (11 preference/5 execution), and 11 j16 personal-known cases. Baseline retains
all 25 personal-known; candidate has 11 correct and 14 missing h93personal-known.
Unknown and execution diagnostics cannot erase the invalid-source failures.
The 3 recovered exceptions are not in the author-tagged personal-known subset;
they do not establish improved discrimination of individual taste.

## Dispute, controls and costs

All 80 legacy rows and 160 public forms remain. Only preflagged j16/w14is excluded
prospectively, leaving 79 primary cases (50 known,29 unknown). Baseline answers the
old `各自计分` annotation throughout. Candidate generation0 answers U throughout;
generation1 answers`各自计分`throughout. Both vectors remain unscored. No label
acceptance, pass/fail or majority-vote adjudication occurs.

All 6 new controls complete. Each full-source control passes its 40/23/16 primary
cases and the required signal exceeds its own no-memory control. No-memory's
29/79 correct cases are all unknown. All 12 extractions precede all 20 actual reads;
extractions see only their own source (and baseline's budget), never questions,
references, old outputs, cards, disputes, scores or feedback. No real people or
new original-inventory cells are involved.

Recorded usage is495,509 input +62,886 output = **558,395 tokens**, with no missing
counters.10,496 cached-input and 7142 reasoning-output tokens are subsets. This is
recorded usage, not a bill.42was a local attempt cap without token/money caps;
the four unused reader slots expired. Internal RPC/retries, served identity and
upstream cancellation remain unobservable. The temporary owned guard exited.

These are 3 consumed fictional sources selected after prior losses. Cases,
rotations, reads, shared templates and generations are not independent people.
No population significance, causal variance decomposition, independent semantic
acceptance, real-person fidelity or cross-model/harness generalization follows.
The original 232 measurement inventory and all historical snapshots stay intact.

## Replay without a service

```sh
python scripts/replay_owned_conditions.py
python -m unittest discover -s tests -p test_owned_conditions_evidence.py -v
```

The portable archive retains exact requests, raw response values, safe counters,
source/parent/method/generation binding,10 valid cards,2 failed products,4 skips,
all 80 references and the prospective 79/1 mask. Replay injects the archive into the
frozen finite controller and reconstructs gates, artifacts, usage and scores.
Eight adversarial archive tests check method/generation swaps, raw/request/card
drift, removed attempts, masked references, paired outcomes and usage. Shared
helpers preserve the previous 37/40 scope replays; local grants, credentials,
machine paths and private transport/error messages are excluded. Envelope hashes
are provenance, not reconstruction of omitted bytes or proof of server identity.
