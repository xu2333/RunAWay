# Actual collateral regression: h93/dev preserved at56/56

All28 new local Codex CLI attempts completed while requesting gpt-6.1-sol:
4 own-bank controls,8 independent source-only extractions and16 own-card reads.
No invalid products,skips,missing responses,retries,repairs or unused slots.
Both full controls immediately qualified:h93full40/40versus none16/40;
devfull16/16versus none7/16. Their required personal-known/known signal gates
also passed before any extraction.

## Fixed endpoint

Every case must pass2 new cards × 2 reads × 2 option orders,8answers per method.
These repetitions are not independent people or additional test cases.

| Source | Cases | policy-v2 card chars | source-order-v3 card chars | Strict baseline | Strict candidate |
|---|---:|---|---|---:|---:|
|h93|40|1084 / 1144|1090 / 1258|40/40|40/40|
|dev|16|619 / 636|578 / 564|16/16|16/16|
|Same-batch total|56|||56/56|56/56|

Both methods preserve33/33known,23/23unknown,14/14personal-known,
11/11preference-typed and5/5execution-typed outcomes. The remaining40cases
retain their existing untyped stratum. Paired outcomes:56both correct,
0baseline-only,0candidate-only,0neither,no missing. No measured regression
appeared in this fixed development endpoint.

All4 source-order-v3parents had0active order-split annotations. No developer
supplied a binding and no null annotation was filled in by the compiler. This
observes behavior on these sources;it does not establish globally correct
semantic detection of when a split is needed. All cards fit1536whole characters.

## What this does and does not establish

The encoder,reader,codec,budget,62fictional source messages and112public forms
were frozen unchanged. Extractions saw only their own source,budget,header/guide,
instructions and schema;no questions,references,old cards/responses/scores,
developer-selected bindings or case feedback. All8extractions preceded reading.
The second read round reversed the first;each parent used identical own-bank
requests in both reads. No best-of selection or historical card reuse.

This checks collateral behavior after the separate
[j16source-only result](../source-order-probe-v1/MEASURED.md). j16and its
post-hoc ordering auxiliary are absent here. The old23and this56are separate
batches,not a new contemporaneous79-case result. No new ordering deletion
endpoint,disputed w14relabeling or source-preference gold change occurred.

These two sources were already used for development. Perfect outcomes are not
independent generalization,independent semantic acceptance,real-person or
cross-model/harness fidelity. There is0new original inventory coverage and no
production-default switch. The next empirical uncertainty is behavior on newly
frozen sources,not further selection from these successful cards.

## Reproduction and cost

```sh
python scripts/replay_source_order_regression.py
python -m unittest discover -s tests -p test_source_order_regression_evidence.py -v
```

The public archive preserves exact fictional sources/questions,raw response
values,method/generation ownership,artifacts,usage,control gates and all56case
denominators. Replay has no service capability. Eight mutation checks reject
source/reference/legacy drift,foreign parent bindings,request/raw/artifact
tampering,altered gates/missing denominators,removed or duplicate attempts,
usage/runtime drift and false independent/default/pooled claims. Six controller
fixtures separately protect both full-control stops and invalid-parent2-read
skips;fixtures are not measured fidelity.

Recorded usage:405053input+48981output=454034tokens. Cached input79104and
reasoning output3746are subsets,not extra charges;cache-write input0. There
was no token or monetary ceiling,and these counters do not establish a bill.
Requested model metadata does not independently verify served identity,internal
RPC/retries or upstream cancellation. Local grants,paths,credentials and private
transport envelopes are excluded from the public snapshot.

Input manifest SHA256:
`8abefb03c357c940208e6d07dbd65797016280586faa5bae0e45d22266bb53ae`.
