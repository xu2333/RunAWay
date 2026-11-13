# Condition-only revision edges: unmeasured repair candidate

A later[source-only development comparison](../domain-revision-probe-v1/RESULTS.md)observed two valid generations with14parent retirements each and94/94cases retained. The current encoder also retained94/94,so there is no observed comparative recovery or default promotion. The original unmeasured design notes below remain historical;semantic certification and broader generalization are still unestablished.


The [guard-amendment observations](../heterogeneous-guard-pressure-v1/LOSS-ANALYSIS.md)
found two different failures. Rivet's original768extraction retained18current and
14superseded rules as32active base nodes; the unchanged30active-row guard rejected
it. Raising the character budget cannot fix that graph. Quince's other invalid
parent instead had18current rules and failed public character packing. This
module targets **historical condition retirement**, not the independent layout
problem. It does not raise the30active-row limit.

`candidate.py` adds a source-ID `condition_revision` node. It names an earlier
active choice parent, exact parent predicates to edit, replacement predicates
with evidence (or null to remove one predicate), current decision/context anchors
and user relation evidence. It inherits the parent's object, question, action,
priority, execution annotation and every untouched predicate. It retires only
that node; other choices citing the same source message stay active. Historical
observations remain private and source-accounted. Existing action-only revisions
retain their condition-inheritance behavior; past-status nodes cannot be revision
parents. Current narrow scope does not support pure condition insertion without
a named replacement/removal target.

The model still decides whether a condition changed and which parent it updates.
Evidence IDs, user roles and chronology **do not certify the semantic edit**.
Tests deliberately show that a wrong edit can cite a structurally valid update
message, and all semantic/fidelity flags remain false. No observed generation or
reader recovery is claimed. No model backend is provided or called.

Historical nodes are materialized and individually checked with the old source,
role, condition and annotation validators before selecting active nodes. The old
alias and complete source-accounting checks apply to the entire history. The old
whole-ledger validator, order decomposition and public renderer then apply to the
active rows. Public defaults, sealed observations and historical hashes remain
unchanged. A new exact finite grant is required for a real-model comparison.

The source-only request contains only the selected source, budget, generic edge
guidance and schema. It does not contain evaluation questions, reference labels,
the selected failed graph, author repair bindings or old reader responses.

```sh
python3 -B -m unittest discover -s tests -p test_condition_revision_encoder.py -v
```

Thirteen local tests cover threshold replacement, local guard removal, untouched
conditions and sibling choices, past-status preservation, chained action updates,
execution annotations, source/role/timing/alias/accounting checks, whole-budget
refusal and byte-identical legacy public rendering when no new edges are used.
These authored protocol fixtures are not evidence that a model will choose the
right edge or that new source-only generations are stable.
