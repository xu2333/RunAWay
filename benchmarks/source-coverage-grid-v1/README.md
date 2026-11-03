# One fixed development grid across three repeated-generation studies

The fixed grid covers all120planned cases with no missing cells. Both methods
retain62/62true unknowns,but both lose documented known choices:

| Method | Joint strict | Known | Unknown | Derived known |
|---|---:|---:|---:|---:|
| source-order-v3 |117/120|55/58|62/62|30/31|
| generic coverage guidance |116/120|54/58|62/62|30/31|

Full controls retain120/120;shared no-memory62/120. Baseline loses three c2v
knowns in one generated card;guidance loses four f7s knowns in one generated
card. Each method has15/16fully passing generated cards in these studies.
Neither is a reliable semantic-completeness solution,and the guidance does not
show consistent improvement across the fixed grid. No default is changed.

The three studies contain **107actual CLI attempts**:32extractions,64card reads
and11controls. Their known service counters total1211756input +84253output =
**1296009tokens**,with0missing receipts. Cached124928 and reasoning15099 are
subsets of input/output. This excludes older pilots,authoring and chat costs;
it is not a project bill or an efficiency claim. All three scopes are closed.


This report combines archived observations,without a new model call. The fixed
mapping uses one repeated study per fictional source world:

| Study | Worlds | Person/cases per method | Planned service attempts |
|---|---|---:|---:|
| source-coverage-repeat-v1 |a8r|15|14|
| ambiguous-source-repeat-v1 |c2v,d9n|30|27|
| remaining-source-repeat-v1 |b6t,e4q,f7s,g1w,h3k|75|66|

Both methods retain the same120planned person/cases:58known and62unknown.
Each endpoint requires two generations ×two reads ×two option orders to be
correct. Missing parents/readers retain their original known/unknown denominators.
Eight fictional worlds are not32people,and methods'overlapping cases do not
become240independent observations. No best-of card is selected from older studies.

```sh
python scripts/replay_source_coverage_grid.py --check
python -m unittest discover -s tests -p 'test_source_coverage_grid.py' -q
```

The replay verifies each original frozen scope,source/question/reference mapping,
shared encoder/compiler/reader hashes,raw requests/responses,artifact bindings
and control/cost ledgers. It then sums the predetermined endpoints. The saved
summary/checksum must agree with a fresh offline reconstruction. Snapshot-value
hashes in the summary are canonical JSON value digests;source-file checksums are
verified separately. No private runtime,grant,host path or real-person trajectory
is included. Any unknown usage remains unknown;cached/reasoning subsets are
not added a second time.

This is a descriptive,consumed development grid. Guidance was developed after
an earlier omission;the first two studies target those development questions.
Adding every remaining world completes the original set but does not create an
independent holdout or population stability estimate. Realized lengths differ
under a common1536ceiling,so instruction effects and size efficiency are not
isolated. The production default and all older observations remain unchanged.
The original stopped49-call study still has its original missing endpoints;
this grid neither fills nor replaces them.

These metrics concern documented synthetic-source retention and source-licensed
inference,not future human-choice prediction. The [real PRISM pilot](../../REAL-SCENARIO-PILOT.md)
remains a separate zero-personalization-gain result. Synthetic gains cannot be
used to relabel it,claim real-person fidelity,or call equal full/no-memory
accuracy100%retention. Provider/harness fidelity also remains unvalidated.

The [offline experimental memory bridge](../../docs/experimental-memory.md)
provides explicit-method request preparation and import into existing portable
artifacts. Successful structural import is not a behavioral fidelity certificate.
