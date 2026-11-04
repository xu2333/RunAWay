# Source review of a fixed incomplete draft

## Measured outcome

The approved diagnostic closed after **5 actual calls**. The source-only review
returned a schema-valid graph but failed literal-source binding:
`Anchor is not an exact source quote`. No reviewed public card was compiled.
Its two readers were skipped, all **15 reviewed cases remain missing**, and
the two unused slots expired. This is not an observed 0% reader accuracy.
No retry, quote correction, alternative compilation or manual repair was run.

| View | Correct / planned | Known | Unknown | Missing |
| --- | --- | --- | --- | --- |
| Full source control | 15 / 15 | 7 / 7 | 8 / 8 | 0 |
| No-memory control | 8 / 15 | 0 / 7 | 8 / 8 | 0 |
| Unchanged original card, two reads | 11 / 15 | 3 / 7 | 8 / 8 | 0 |
| Reviewed candidate, no reader calls | unmeasured / 15 | unmeasured / 7 | unmeasured / 8 | 15 |

Original-card losses recur in both reads and both option orders:
`notes_complete_0`, `notes_complete_2`, `signup_complete_1`, and
`signup_complete_2`. Each known choice is answered `U` four times; the first is
source-entailed and the other three are explicit. The original card and the
previous 66-call/grid results are unchanged.

Offline inspection of the returned graph finds two objects, four nodes and
20 anchor occurrences. Exactly one is not a substring of its named source:
`nodes[0].contexts[1]`, source `m03`, appends ` 第` after
`完整内容会传到外部服务；任何改动都能一步完整恢复。`.
The other 19 occurrences pass literal matching. This identifies the first
rejection mechanism; it does **not** certify their semantic support, correct
condition inheritance, budget fit or the hypothetical repaired card's fidelity.
We preserve the rejected graph unchanged in the portable archive.

All five usage receipts are present: **61,268 reported tokens**
(58,535 input + 2,733 output). Cached input 5,888 is a subset of input;
reasoning 355 is a subset of output. Stage totals are no-memory 11,699,
full-source 13,330, review 12,332, and original-card reads 23,907. These are
reported CLI counters, not a bill or whole-project cost.

A source recheck did not produce an importable replacement in this attempt.
The next design question is whether evidence can be addressed by source spans
instead of generated quotation text, while retaining the same strict rejection
of unsupported claims. That would change the encoding contract and needs a
separate measured comparison; this run supplies no evidence of its benefit.

## Frozen design and replay

This seven-call diagnostic creates a separate reviewed candidate from the fixed
240-character f7s graph generated in the closed66-call scope. The old graph,
card,reference and scores remain unchanged. The draft is a posthoc selected
known failure,not a fresh initial extraction or independent holdout.

A generic review prefix asks the encoder to recover source-supported choices
and conditions,distinguish unencoded content from user uncertainty,and output
a complete graph rather than a patch. Its only inputs are the own22fictional
source messages,the existing draft graph with its original source anchors,and
fixed instructions/schema/budget. No question,reference,reader response/score,
author parameter or manually supplied case correction reaches this reviewer.
The prefix was developed after observing the failure;this is not blind validation.

One no-memory and one own full control precede the single review. Full15/15,
both option orders,no missing and personal-known gain are required. Original
and reviewed public cards are each read twice in a counterbalanced sequence;
each view keeps15cases (7known,8unknown),all four read/order answers required.
The same schema,wire,binder,compiler,reader and1536whole-character limit apply.
Realized lengths may differ. One reviewed candidate cannot establish generation
stability,population benefit,real-person fidelity or size efficiency.

A structurally/budget-invalid reviewed product skips only its own two readers;
its15cases remain missing,and original-card reads continue. A control,transport,
wire/schema/decode,unknown usage,model,input/runtime or owned-guard failure stops
the whole remainder. No retries,manual patching,resumption,slot replacement or
old-budget reuse occurs. The planned review creates another candidate;it never
edits the sealed original or retroactively changes its eligibility/denominator.

The unapproved intake is retained in `protocol.json`;it is not service authority.
The actual scope needs a separate grant and exact-head CI. The three portable
code files reconstruct input manifest
`cd5c7aa21640533e187476c7acf8fd3c02238bf21d274a6c3153d723f2408912`.

```sh
python scripts/replay_source_review_diagnostic.py
python -m unittest discover -s tests -p 'test_source_review_diagnostic*.py' -q
```

Replay injects archived values/categories into the frozen finite controller,
validates exact source/draft/own-parent requests,artifacts,usage,controls and
fixed denominators,and performs zero service calls. The raw draft is fictional;
private grants,host paths,runtime/activation data and transport envelopes stay
outside the portable archive. Literal anchors and structural import still do
not certify source completeness or semantic support. Production defaults and
the completed120-case source grid remain unchanged.
