# Source inventory, omission audit and whole512 compression

**The added stages did not produce a usable512-character card in this run.**
Four inventories passed local checks; only one audit admitted compression, and
that card was1161characters. Its reader fidelity was **not measured**. Fresh
direct grouped baselines produced3/4valid cards and retained43/60observed cells,
with20more planned cells missing. Neither method passes the strict gate.

## Frozen comparison and results

Same4consumed fictional profiles,48messages each;20scenes with two option
orders,80dependent person/scene cells,52known and28U targets. Public questions
went only to controls/readers. Producers saw source-only material. References,
old answers/cards and author parameters were never sent. Requested model was
`gpt-6.1-sol`; actual server identity is unavailable.

| Stage | Direct grouped | Inventory → audit → compression |
| --- | --- | --- |
| Valid inventories | — | 4/4;42,35,34,36units |
| Audits | — | 3valid imports:1clear,2flagged;1invalid import |
| Valid complete-budget cards | 3/4 | 0/4;1attempted,3blocked before compression |
| Own-card fidelity on observed cells | 43/60 | Unmeasured;no readers admitted |
| Correct / all80planned cells | 43/80;20missing | 0/80;80missing |
| Known choices on observed cells | 23/40 | Unmeasured |
| U targets on observed cells | 20/20 | Unmeasured |

Contemporary complete-source controls passed80/80;no memory scored28/80.
The three valid direct cards were476/500/490characters;h68was rejected at555.
Direct equal-character raw tails scored23/60observed;fixed wrong-person cards
scored31/60against targets and43/60against their actual donors. The latter is an
independent response, not reused own-card output. Missing donors/targets differ
in some subgroups;use the exact per-person/cohort counts in the fixture.

All17observed own-card errors returnedU for an originally known choice. Five
families failed for all three observed profiles:temporary internal scripts,
exploratory research,public research reports,on-call runbooks and work-report
travel. Two more errors were partial-context interface questions. No option-order
instability was observed. Missing cells are not observed wrong answers;0/80for
the inventory method is an end-to-end planned yield, **not0%reader accuracy**.

## What blocked the inventory path

- **h17:** audit clear;compression claimed40represented/2superseded units but
  emitted1161public characters against512. No truncation,repair or reader call.
- **h42:** two user reaffirmations were marked`covered` with no decision-unit
  IDs because the inventory linked them only as context. Frozen v1 rejects this
  with`Covered user needs units`. This is an interface/annotation failure.
- **h68:** the auditor reported a missing explicit prohibition on merging two
  projects into a global personality trait. The original quote was in private
  context;the auditor said the unit's scope/condition/content did not express it.
- **h93:** the auditor reported two wrong successor IDs in retired-unit prose,
  despite the structured supersession links naming the actual successors.

Those are model reports plus local validation, not independently adjudicated
semantic truth. A clear audit does not prove completeness. Literal represented
spans do not prove equivalent meaning. [Producer diagnostics](producer-diagnostics.synthetic.json)
and [message-incidence loss traces](loss-traces.synthetic.json) preserve details;
shared source IDs in a trace do not establish semantic coverage or causation.

The unmeasured [review-v2 prototype](../source-coverage-review-v2/README.md) derives
decision/context links in code and removes their model retranscription. It does
not relabel this run,repair inventories,fix budget overflow or establish better
fidelity.10independent toy tests exercise that narrower interface change.

## Cost and offline replay

27actual local CLI inferences of45maximum;18dependent slots skipped and expired.
All27returned wire-valid responses and known usage. Input361133+output75992=
**437125tokens**;15104cached input and11817reasoning output are subsets, not extra
totals. No aggregate token/money cap,no retry/repair/resume. This is not a bill;
upstream RPC retries are unobservable and optional zero usage is not proof of zero.
The temporary idle-sleep guard was removed. No local GPU work.

Inventories consumed67698tokens;audits82896;the one attempted inventory-card
compression16756. Four direct extractions consumed53173. These include failed
and flagged outputs;they do not estimate the cost of a successful deployment.
Exact stage costs and all27requests/responses are in[observed.synthetic.json](observed.synthetic.json).

```sh
python3 -B benchmarks/source-coverage-comparison-v1/check.py
python3 -B -m unittest discover -s tests -p 'test_source_coverage_comparison_evidence.py' -v
```

Replay makes zero service calls,rebuilds stage requests and artifacts,checks
runtime fingerprints,budgets,audit/partial gates,skips,original response hashes,
usage and fixed scoring. The fixture checksum is in`observed.sha256`.

This is developer-visible consumed data with shared authored scaffolding,
one requested model and one draw per slot. No fresh holdout,real-person,
cross-model/harness,population or significance claim. The methods change prompts,
schemas,headers,representation and gates together;this is not an isolated audit
effect or likelihoodRIG. Neither product default nor root README changed.
