# Budget guidance is insufficient; both complete table cards still overflow

The new14-slot budget-aware scope closed on2026-11-01 with **10actual CLI
children**,4skipped/expired readers and **203,574recorded tokens**. Both
candidate generations pass object-count/structural binding but fail the unchanged
1536whole-character cap after lossless packing. No valid candidate was read.

| Method | Strict cases | Missing | Known | Unknown | Personal-known |
|---|---:|---:|---:|---:|---:|
|Fresh unchanged scope-v1|**40/40**|0|24/24|16/16|14/14|
|Budget-aware object table|**0/40**|40|0/24,24missing|0/16,16missing|0/14,14missing|

This candidate has no observed card-reading accuracy. Missing is not a wrong
answer orU. The previous baseline38/40remains unchanged; the new40/40does not
establish a method improvement over a different previous card/read sample.
The production default stays unchanged.

## Every generation

| Method/generation | Objects/rules | Complete prompt result | Read0/read1 |
|---|---:|---|---|
|Scope-v1,generation0|Existing grouped representation|1129characters,valid|40/40;40/40|
|Scope-v1,generation1|Existing grouped representation|1173characters,valid|40/40;40/40|
|Budgeted table,generation0|12/24|1889after lossless packing,exceeds1536|Both skipped|
|Budgeted table,generation1|12/22|1687after lossless packing,exceeds1536|Both skipped|

The unsuccessful packed sizes exceed the cap by353and151characters. These are
failed diagnostics, not accepted prompt artifacts. No truncation, repair,
replacement, retry, resume, replenishment or over-budget model reading occurs.
All40candidate cases remain missing, regardless of the relative size decrease
from the preceding study's1999/2170. Generations are fresh and instructions
change together with budget information; that historical comparison is not a
causal estimate of budget disclosure or stable compression improvement.

## A separate offline renderer reaches the cap without dropping fields

After this scope closes, an [experimental dense renderer](../owned-dense-v1/README.md)
reuses these same two generated ledgers, preserving every literal public scope,
question, condition, action, priority, rule order, name/tagline and unknown.
It replaces repeated field wording/quotes/parentheses with counted compact
syntax and a self-contained public JSON dictionary. Program decoding recovers
the original grouped semantic projection exactly.

The two **new offline counterfactual layouts** are1536and1413characters,
including the guide and any dictionary. Their353/274character savings concern
these fixed semantic projections, not a new model sample or behavioral result.
The original1889/1687failures, four skips and0/40with40missing are unchanged.
No new service calls or reader-fidelity observations are obtained by reformatting.

A separately [proposed14-call read-only comparison](../dense-layout-probe-v1/README.md)
will compare the fixed baseline cards, uncapped complete projection diagnostics
and in-budget dense views. It is unapproved and unrun. Two inherited producer
outputs do not constitute new generation-stability samples. Expanded diagnostic
views are not compressed candidates and are explicitly exempt from the1536cap.

## Controls, costs and scope limits

The full-source control passes all40cases/bothorders; personal-known exceeds
no-memory. No-memory's16correct cases are all unknown. All4fresh extractions
precede all4actual baseline reads. Both encoders see only their own48fictional
messages,budget and fixed public prefix, never questions,references,old cards,
old experimental responses or feedback. All40author references and80public
forms are unchanged. No real-person data or new original-inventory coverage.

Reported usage is176,105input +27,469output = **203,574tokens**, with no missing
counters. Reported cached input is0;3160reasoning-output tokens are an output
subset. Usage is not a bill.14was a local attempt cap without token/money caps;
4unused slots expired. The owned temporary guard exited. Internal RPC/retries,
served identity and upstream cancellation remain unobservable.

This is one consumed fictional source,not an independent holdout or population
sample. Cases,orders,reads and generations are not independent people. No
reference acceptance,j16/night-shift/development validation,cross-harness/model
claim,combined79-case endpoint or production-default switch follows.

## Replay without a service

```sh
python scripts/replay_budgeted_table_probe.py
python -m unittest discover -s tests -p test_budgeted_table_probe_evidence.py -v
python benchmarks/owned-dense-v1/evidence.py
```

The archive retains exact10requests/raw values,safe counters,2baseline artifacts,
2failed products,4skips,all40references and source/method/generation lineage.
Replay injects the archive into the frozen controller and recomputes requests,
schemas,gates,failures,usage and scores. Eight mutation controls preserve these
bindings and reject unsupported endpoint claims. Local grants,paths,credentials
and private transport/error metadata are excluded; envelope hashes are
provenance,not omitted-byte reconstruction or proof of served identity.
