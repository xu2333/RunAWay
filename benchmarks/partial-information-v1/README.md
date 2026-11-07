# Partial information: when to answer and when to stop

The [separately authorized, closed results](RESULTS.md) retain 48/48 primary
cases with cards and 36/48 with tails. The preparation below keeps its original
unapproved metadata and grants no calls.

This is a fixed-card mechanism
diagnostic after the [fresh everyday-decision result](../fresh-decision-v1/RESULTS.md).
It keeps all eight existing cards verbatim and changes only the questions.
No extraction, repair, prompt change or new default is proposed.

```sh
python3 -B benchmarks/partial-information-v1/check.py
python3 -B -m unittest discover -s tests -p test_partial_information.py -v
```

## The gap

The previous unknown targets asked for preferences or execution facts never
provided. They do not establish that a reader handles missing conditions. A
reader that always says U can look cautious while losing supported choices.
This design asks for a unique choice under an explicitly exhaustive set of
possible situations. It is the same task for full source, card, tail and no
memory; the new task instruction is not a source-specific decoder.

For each of four domains, the prior frozen reference has three known complete
cases: ordinary conditions (0), an exception without its override (1), and the
exception with its narrower override (2). This diagnostic does **not** invent
an unobserved truth table. It joins those already licensed choices:

| Question cohort | Possible prior complete cases | Role |
| --- | --- | --- |
| Context missing | 0 or 1 | Partial; consequences differ, so U |
| Override missing | 1 or 2 | Partial; consequences differ, so U |
| Choice agrees | 0 or 2 | Partial; consequences agree, so return that choice |
| Complete anchor | 2 only | Repeated known anchor; not a new partial case |

The two conflicting cohorts must abstain. The agreement cohort must answer
despite missing context. Four people × four domains give **48 primary partial
person/cases** (16 known, 32 unknown), plus 16 separately reported complete
anchors. The combined 64 contain 32 known and 32 unknown. Each case has two
option orders, for 32 shared public forms. Opaque IDs and a fixed ordering do
not encode cohort or reference labels.

Each question states all its possible complete contexts, but supplies no
personal action-to-condition mapping. Source, card or tail must provide that.
The opposite person pairs share questions and disagree on known choices. If a
candidate branch has no previously licensed choice, construction fails: it is
never silently treated as agreement. `reference-derivation.private.json` links
every new reference to its prior cases and consequences; it is not sent.

## Proposed read-only 37-attempt scope

| Stage | Maximum local attempts |
| --- | ---: |
| New no-memory / four full-source controls | 5 |
| Two reads of each of eight fixed cards | 16 |
| Two reads of each own character-matched source suffix | 16 |

All 37 requests are fixed before authorization. No dynamic generation output,
raw graph, old reader response, old score, reference, author parameter or manual
correction is sent. The cards are the **entire eight-card cohort**, not a
selection of good or bad parents. Their text and the 64 original fictional
messages stay unchanged. All cards remain within the inherited 1,536-character
ceiling. Tail selection still follows each fixed card's exact character length.

Before any fixed-view read, every full-source control must get all its 16
cases correct in both orders, without missing answers, and outperform the new
no-memory control on **primary known cases**. Anchor success cannot substitute
for that gain. Source-control failure stops the scope rather than being called
compression loss.

Primary reporting keeps all 48 partial cases per view; anchors retain their
separate 16-case denominator. Also report the combined 64, known/unknown slices,
each parent generation, and all four cohorts. All two parent versions × two
reads × two orders (eight answers) must match for joint retention. The two
parents are old fixed cards, **not new independent extractions**. Missing and
invalid answers stay missing, not U.

Any control, transport, schema/decode, unknown-usage, requested-model,
input/runtime or owned-guard failure closes the remainder. No retry, repair,
resume, replacement or budget replenishment. Fixed inputs are validated before
entry; there is no invalid-new-product skip because no new product is generated.
Output creation must succeed before the exclusive single-use claim, and the
claim precedes backend entry. Each local child remains limited to 180 seconds.
The proposed model is `gpt-6.1-sol`. The 37-attempt cap is not a token or money
cap; execution requires a new direct grant and exact-head three-platform CI.

## Interpretation and integrity

This is a **post-hoc fixed-parent diagnostic on consumed fictional sources**.
Reference joins are deterministic, conditional on the old author reference;
they are not independent semantic adjudication. Exhaustive possibilities are a
question premise, not a verified model of a real person's missing context.
Results would not prove initial-generation stability, real-person fidelity,
cross-provider transfer, RIG, optimal compression or a production default.
Character-matched tails are not token-matched or optimally selected histories.

The original result file is pinned by its whole-file checksum. Existing source,
cards, raw observations and references are not edited. A cached derived packet
is serialized and copied on use, and parent bytes are rechecked each time.
`protocol.json` and `prepared-manifest.json` bind this preparation and its code;
they grant no service authority. The public authoring program exposes the
fictional reference construction for reproducibility, but requests exclude it.

Twelve offline checks use reference-aware mocks only. They explicitly show that
always-U fails the known partial endpoint, overconfident guesses fail unknowns,
one wrong order cannot be averaged away, and anchors cannot hide a failing
primary control. Further checks cover unchanged parents, own-tail lengths,
input mutation/symlinks, guards, failed calls and fixed denominators. Mock
perfect scores are bookkeeping tests, not measured fidelity. All prior call
scopes remain closed; publishing or merging this proposal grants no new calls.
