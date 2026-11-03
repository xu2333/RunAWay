# Fixed252-character card:9/15, matched tail3/15

All six independently approved read-only attempts completed and closed, with
six local inference children, no missing usage/responses and no unused slots.
The original card, reader, questions and references were unchanged. No new
extraction, card repair or external decoder was used.

| Material | Known /12 | Unknown /3 | Joint /15 |
|---|---:|---:|---:|
| No memory |0|3|3|
| Own full source |12|3|15|
| Fixed252-character card, both reads/orders |6|3|9|
| Own252-character role-labelled transcript tail, both reads/orders |0|3|3|

The full control passes15/15 in both option orders and improves personal-known
recovery over no-memory. Each control has one invocation/two orders; each short
view has two invocations/two orders, and all four answers must match per case.
Card reads each score9/15 and tail reads each3/15. No repeat or option order was
selected away. The fixed denominator stays15 per view, not the old49 scope's120.

## The six losses are one omitted decision domain

| Domain | Card | Tail |
|---|---:|---:|
| Note organization:6 known choices plus1 outside-feature case |7/7|1/7|
| Registration grouping:6 known choices plus1 outside-feature case |1/7|1/7|
| A third unobserved domain |1/1|1/1|

Every card loss is a known registration-grouping choice returned as `U` in both
reads and both orders:24 wrong response entries across six dependent cases.
These include two directly observed decisions, two unseen complete combinations
and two partial-feature cases. True unknowns all remain correct. The failure is
known-choice retention, not a reason to force guesses for genuinely unknown
conditions. The shorter card beats this simple raw suffix but loses an entire
known domain relative to source; that is not adequate fidelity.

This is consistent with the [generation-time concern](../extraction-readiness-v1/README.md):
the raw graph names two objects but assigns a node only to notes; the compiled
card has no registration scope. The experiment does not isolate a causal field,
collect the reader's reasoning or establish that an incidence warning predicts
losses generally. One post-result selected synthetic card/person, shared
questions and repeated reads are consumed development, not independent human
fidelity, a holdout, new-person generalization or generation-stability evidence.

## A structural warning can be gamed without changing memory

The [offline counterexample](incidence-invariance.synthetic.json) deletes only
the unreferenced object entry from a copy of the raw graph. Existing structural
binding still accepts it. The incidence warning changes from one unused object
to none, while the compiled252-character prompt is **byte-identical**.

The variant was not sent to a model, written over the original or counted as a
new behavioral sample. It establishes no fidelity gain. It shows why object
incidence is an advisory diagnostic rather than a completeness endpoint: do not
optimize that flag by deleting metadata. The source-backed questions and fixed
denominators remain the behavioral endpoint.

```sh
python scripts/check_object_incidence_invariance.py
```

An [unmeasured source-only guidance candidate](../object-coverage-guidance-v1/README.md)
asks producers to retain decisions for every independently supported source
scope, without inventing choices for unknown domains or relying on names/taglines.
It changes a generic request prefix only. No model call has tested it, no current
card was repaired, and no production default changed.

## Usage and scope limits

| Stage | Attempts | Reported tokens |
|---|---:|---:|
| No-memory |1|11697|
| Own full source |1|13351|
| Fixed-card reads |2|23907|
| Equal-character tail reads |2|23790|
| Total |6|72745|

Receipts report71214 input/1531 output tokens. Cached input5888 is already part
of input; reasoning output129 is already part of output. Equal characters do
not equal tokens or monetary cost: card reads report117 more total tokens than
tail reads, with different cache receipts. The card's prior10552-token extraction
belongs to its separate closed scope. The original earlier timeout's usage is
still unknown. No complete combined bill or net product saving is established.

Requested gpt-6.1-sol is recorded; served identity and internal RPC/retry counts
are not independently observable. The same standard reader/system/common
contract is used in every arm. Only the full-source control carries source rule
definitions; readers receive no extra codebook or private graph. The tail is
exactly the last252 characters of the own complete role-labelled transcript.
It can start mid-message and is not optimal retrieval or a token-matched control.

## Reproduce offline

```sh
python scripts/replay_fixed_card_fidelity.py
python -m unittest discover -s tests -p test_fixed_card_fidelity.py -v
```

The [snapshot](measured.synthetic.json) preserves exact synthetic source,
questions/reference, original materials, requests, raw answers and safe counters.
Replay reconstructs every portable input file and the original input-manifest
hash before replaying the finite controller with archived responses. It checks
controls, primary endpoints, per-read/domain losses, missing/usage/attempt ledgers
and closed scope. It cannot independently accept the source semantics or verify
omitted private envelope bytes. Grants, machine paths, process IDs and private
runtime/activation files are excluded. Old49 and readiness1 observations remain
sealed and unchanged. Publishing this result grants no further model budget.
