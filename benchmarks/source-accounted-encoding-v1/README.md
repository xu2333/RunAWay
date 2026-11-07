# Source-accounted encoding: targeted omission repair candidate

**The separately approved comparison is now closed:** both methods retain30/30,
including all seven historical-loss targets, with no observed new loss. Candidate
cards are slightly shorter on average but extraction reports more tokens; there
is no observed accuracy advantage. See [measured results](RESULTS.md). The
originally unapproved preparation below remains frozen and grants no authority.
This changes the encoder request/schema and checks its output, rather than adding
another accuracy score. The existing graph compiler, public wire, reader and
1,536-character whole-card cap are unchanged. Installed defaults are unchanged.

## What was lost

The [remaining-source repeat](../remaining-source-repeat-v1/README.md) contains an
f7s generation-1 card of 240 characters. Four known choices become U in both
reads and both option orders: three explicit manual choices and one source-entailed
manual-notes choice. Its sole automatic-notes node cites both m05's automatic
choice and m09's manual choice; the registration object has no decision node.
The public unknown text admits that confirmed choices were not fully encoded.
That is encoder incompletion, not evidence that the user was undecided.

The [ambiguous-source repeat](../ambiguous-source-repeat-v1/README.md) contains a
c2v generation-1 card of 312 characters. It loses two explicit registration
choices and one source-entailed automatic-notes choice. Both failing cards name
two objects but have only one decision node. Object incidence cannot establish
decision coverage. Their other same-request generations pass all15cases at
434/585characters respectively, so the observed omissions are not a demonstrated
necessity of the1,536-character cap.

| Lost information | f7s source | c2v source | Why it matters |
| --- | --- | --- | --- |
| Confirmed first registration choice | m13 conditions + m15 choice | m13 + m15 | A withdrawn complete rule does not erase this observation |
| Confirmed second registration choice | m17 conditions + m19 choice | m17 + m19 | A named object with no action cannot reproduce the choice |
| Manual notes under the observed second condition | m07 + m09 | Not a known choice there | Opposite choices cannot jointly endorse one automatic observation |
| Source-entailed unseen notes choice | m02, m05, m09, m11 | m02, m05, m11 | Candidate definitions, observations and the active completeness guarantee must be combined |

These are developer-visible, post-hoc failure analyses on public fiction. The
source IDs, conditions and references are not supplied as manual annotations to
the new encoder. Original cards, raw graphs, answers and scores remain intact.

## Changed encoding contract

Before compiling a card, the model must classify **every user source message**
in `source_accounting` as `direct_choice`, `contextual_choice` or `no_choice` and
give a source-only reason. A choice entry lists its observation node IDs. Each
direct entry must have a decision quotation containing that node's full action;
the original binder still checks that the quotation exists in that exact user
message. Contextual confirmations retain their own decision evidence and source
context without pretending the omitted action was literally repeated.

Every decision source on an observation node must be accounted for. Multiple
messages may reaffirm the same complete-condition/action node; conflicting
direct actions fail the per-source literal witness check. Every node belongs
either to these observations or to `derived_node_ids`, never both. Inferred
rules do not substitute for preserving the confirmed observations. No new source
text, hidden decoder or bookkeeping is appended to the public reader material.

This directly addresses observations being skipped or prematurely folded into
one inferred rule. It does **not** prove message classification, condition
equivalence, inference correctness or semantic completeness. An explicit
counterexample test shows that a model could still misclassify real decisions
as background. All semantic/fidelity flags remain false until tested. Matching
an action substring alone does not understand negation or endorse its meaning.

## Frozen next comparison: 27 calls maximum, not authorized here

Use c2v/f7s's44existing fictional messages and the original30public forms.
Current generic-coverage encoding and the new candidate each get two independent
source-only extractions/person; each card gets two reads with both option orders.
Three fresh controls qualify first: shared none, then each own full source must
pass all15cases/bothorders with personal-known gain and no missing answers.

| Stage | Maximum new local inference attempts |
| --- | ---: |
| No-memory / own full controls | 3 |
| Two methods × two people × two generations | 8 |
| Each new card × two reads | 16 |
| Total | 27 |

Each method keeps30unique person/cases (13known,17unknown). All eight answers
must match for a case to count. Report known/unknown, derived-known,
withdrawal-sensitive and per-generation slices separately. Missing stays in the
denominator. Source-accounting incidence is not the behavioral endpoint.

Extraction sees only its own source, budget and fixed instructions/schema: no
questions, references, old cards/graphs, outputs/scores, manual dispositions,
author parameters or another generation. Reader prompts contain only their own
compiled public card and the original public forms. This is a bundled encoding
contract change on selected consumed development sources, not a single-factor
causal ablation, independent holdout or general stability estimate.

Binding/accounting/witness/budget-invalid parents skip only their own two reads,
leaving15missing in their method's30case endpoint. Control, transport, structural
schema/decode, unknown usage, model, input/runtime or owned-guard failure closes
all remainder. No retry, repair, resume, best-of, replacement or budget reuse.
The prospective scope has no token/money cap; it needs a separate direct finite
grant and all three CI jobs at the exact published implementation head.

```sh
python3 -B -m unittest discover -s tests -p 'test_source_accounted*.py' -v
python3 -B benchmarks/source-accounted-encoding-v1/plan.py --out my-frozen-proposal
```

The14offline checks cover opposite observations, contextual reaffirmation,
missing/orphaned nodes, forged quotes, original compiler/budget conservation,
semantic counterexamples, source-only input routing and fixed-denominator finite
lifecycle failures. Oracle responses test controller wiring, not model quality.
`plan.py` only prepares files; it has no model backend. The new protocol pins an
explicit current dependency list; historical experiments retain their original
locks and continue replaying under their original verified executor snapshot.
