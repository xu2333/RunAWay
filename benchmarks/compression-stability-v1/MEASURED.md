# Lower-budget results: 1024 retains the tested decisions, 768 loses coverage

On2026-10-30, this frozen scope reserved at most41new Codex CLI attempts,
requesting gpt-6.1-sol. **37actual children completed**. Two invalid extraction
products skipped exactly their own four readers; those4unused slots expired.
No retries, repairs, replacement generations or usage gaps occurred. The scope
is closed and the production default is unchanged.

| Whole-card ceiling | Strict cases | Missing cases | Known decisions | Unknown cases | Valid generated cards |
|---|---:|---:|---:|---:|---:|
|768characters|**53/96**|40|30/54 (21missing)|23/42 (19missing)|4/6|
|1024characters|**96/96**|0|54/54|42/42|6/6|

Strict means both generated cards, both reads per card and both option orders
must all match the frozen reference:8answers per case. The768score includes
40missing h68 cases and3incorrect h93 cases. It is not53/56after deleting
failed products. Development preference11/11 and execution5/5 pass at both
budgets. Older80cases remain untyped, not extra execution or preference tests.

## Every generation and both reads

Each score below already requires both option orders. The character count is
the complete public card, including the fixed header and guide.

| Profile | Ceiling | Generation0: characters; read0/read1 | Generation1: characters; read0/read1 | Strict across both generations |
|---|---:|---|---|---:|
|h68|768|Invalid: empty when; both reads skipped|Invalid:806>768; both reads skipped|0/40, all40missing|
|h93|768|754;37/40,37/40|741;38/40,38/40|37/40|
|dev|768|550;16/16,16/16|534;16/16,16/16|16/16|
|h68|1024|993;40/40,40/40|1005;40/40,40/40|40/40|
|h93|1024|957;40/40,40/40|964;40/40,40/40|40/40|
|dev|1024|562;16/16,16/16|588;16/16,16/16|16/16|

All valid cards produced identical answers on their two reads in this run.
h93's two768cards differ on one case; their error sets are described below.
Fresh contexts and two samples do not establish independent generation samples
or a causal variance decomposition. The short14-message dev source previously
yielded a615-character card; it may fit these ceilings without compression
pressure and is not evidence for long-history compression.

## Source-linked loss analysis

The h68 generation0raw output has **nine empty when strings**. The exact local
error is `when must be nonempty text of at most 120 characters`. This error does
not mean the field exceeded120characters. The requested wire schema permitted
empty strings while the unchanged binder refused them. No invalid card was read
or repaired. Generation1instead passes field validation but renders806complete
characters and fails the768ceiling; it was not truncated.

The h93generation0card omits three recorded choices and returnsUfor all three
on both reads/both orders. Generation1retains the travel choice, but still omits
the two workshop choices:

| Case | Frozen source anchors | Reference | 768generation0 | 768generation1 |
|---|---|---|---|---|
|t15, work-trip departure|m18/m20|Depart during the previous day and leave slack|U|Correct|
|n15, workshop handout|m40/m42|Leave a blank column on the right|U|U|
|n16, workshop projection|m44|Use24-point type|U|U|

These are known decisions in the full source. Missing encoded episodes with
stable reader abstention point to source-content omission in these samples,
rather than observed within-card read instability. This does not prove a unique
causal mechanism, generalize the failure rate or justify weakening unknown
boundaries. Original source anchors, references and all previous failures stay
unchanged. No per-question chain-of-thought was collected or used.

A separate [unmeasured wire-contract candidate](../wire-contract-v1/README.md)
adds only minLength1/maxLength120to the extraction schema's when field, keeping
source, prompt, binder and renderer unchanged. Four offline checks accept all10
actually valid outputs and reject the observed empty field without altering it.
This does not fix the806-character product, omitted episodes, whitespace-only
strings or other schema/binder gaps, and has not been tested with a model/backend.
It was created after this scope closed and did not affect these37calls.

## Controls, accounting and limits

All full-source controls passed:40/40h68,40/40h93,16/16dev. No-memory scores
were19,16and7respectively:42/96, entirelyU. Full sources exceeded the frozen
personal-known/known control signal before any extraction. All12extractions
preceded any card reading; no reference, question, old card, old response,
author target or feedback was sent to an extractor. Reader inputs contained
only public material and natural-language questions/options.

Recorded usage is552,795input +60,819output = **613,614tokens**. Cached-input
40,192and reasoning-output15,404are subsets. Usage is known for all37attempts;
it is not a monetary bill or total project cost.41was only a local attempt cap,
with no token/money ceiling. Internal RPC/retries, actual served identity and
upstream cancellation remain unobservable. The original temporary guard exited.

This consumed development set has2long fictional profiles and1short authored
fixture, not96independent users. References are visible author judgments,
not independently accepted human truth. The80old cases are repeats and the16dev
cases are visible development material. Original coverage remains160/232 with
72unmeasured; w14, original93/96and118/120observations remain unchanged.
Neither testing nor publication grants new model budget or a default switch.

1024is a viable next development operating point for these samples, not an
established universal minimum.768reveals both product-validity failures and
lost source coverage. Further validation needs new source units, model diversity
and a separately approved service scope. Do not recover scores by dropping
invalid generations, using only generation1or guessing omitted known decisions.

## Replay without a model

```sh
python scripts/replay_compression_stability.py
python -m unittest discover -s tests -p test_compression_stability_evidence.py -v
python -m unittest discover -s tests -p test_grouped_wire_contract.py -v
```

`measured.synthetic.json` retains all37exact requests/raw response texts,
10bound artifacts, safe counters and fixed source/query/reference snapshots.
Replay reconstructs the frozen input package and invokes the same controller
against an injected archive in a temporary directory. It reproduces original
gates, product failures, skip policy, fixed denominators and scores without a
backend. This is reproducibility using the same controller, not an independent
semantic oracle. Returned original usage is archived evidence, not new replay cost.

`scripts/export_compression_stability.py --run <sealed-local-run>` verifies the
private input/observation seals and reproduces the portable export. Machine
paths, approval records, credentials, private error messages and transport
envelopes stay local. Original envelope hashes are provenance; public replay
does not reconstruct omitted envelope bytes or prove served model identity.
