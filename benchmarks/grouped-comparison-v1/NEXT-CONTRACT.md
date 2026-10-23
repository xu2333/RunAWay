# Next contract: make omission accountable before claiming compression

The paired whole512 result is a failure of known-choice retention: grouped cards
fit4/4 but own/donor readers score57/80, with all23 errors returning U for known
choices. U28/28 alone would conceal the loss. Source quote and byte/character
checks do not detect missing source-supported choices.

Inspection finds five absent families in all four original grouped answers:
temporary internal-script exceptions (t03), exploratory research tradeoffs
(t04), public research-report style (t12), incident-runbook exceptions (t13)
and work-report travel (t15). These account for20 observed errors. Two additional
known partial-context cases (t02,h42/h93) depend on the omitted script branch;
h42 also omits its one-point notification choice (t16). This is a descriptive,
developer review of original cards and references, not independent causal proof.
No wrong-choice own answer or option instability was observed: the23 answers
became U. That does not establish what a repaired card or different reader would do.

## Proposed source-only stages

1. Before compression, inventory atomic **user-endorsed choice observations**
   from sources, with literal decision/context anchors, scopes, numeric bounds,
   update links, unresolved conflicts and single-point restrictions. Split
   multiple decisions in one message; do not equate one source ID with one fact.
   Do not send public evaluation questions or reference labels to this stage.
2. Require an explicit disposition for every inventory unit: retained with a
   literal public span, or omitted with a stated reason. Current live choices,
   exceptions, unresolved alternatives and observed unknown boundaries cannot
   silently disappear because a generic “others unknown” sentence was added.
3. If the complete budget cannot be met while retaining the inventory, return a
   clearly labelled **partial candidate / budget unmet**, with its omissions.
   A structurally valid short card is not a full-coverage result. Do not silently
   enlarge its budget, repair old outputs or reuse skipped inference slots.
4. Validate IDs, exact source quotes, local update references, literal public
   spans, public budget and **complete accounting** locally. A span mapping does
   not prove semantic equivalence; an inventory can itself omit a decision.
   Keep separate flags for accounting, semantic completeness and behavioral
   fidelity. Use source-derived held-back probes and an independently authored
   scenario bank for later behavior tests; no reference-aware packing.

This proposal is not implemented or measured by the grouped format. The
[offline accounting prototype](prototype/coverage_contract.py) has9 independent
[toy tests](prototype/test_coverage_contract.py) covering omitted-unit detection,
multi-decision messages, local supersession, conflicts, unsupported spans, exact
budget refusal and unknown-vs-omitted distinctions. They passed with zero model
calls and no changes to measured cards. Tests also demonstrate that mapping all
units to the literal span `X` can pass accounting: inventory completeness, semantic
retention and behavioral fidelity therefore remain unverified. The prototype has
no extractor, backend or portable export. Such tests certify bookkeeping only. A new
service experiment must freeze that inventory/extraction/compression boundary,
baseline, denominator and input scope before requesting approval.

The current37-call scope is closed after25 actual attempts. Its12 skipped
dependencies expired. This document grants no further calls and does not change
the production default.
