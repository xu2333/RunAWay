# Long-history / whole-card budget pressure test

This study preserves the four consumed final policies from
[fresh-boundary-v1](../fresh-boundary-v1/README.md), using alternative, explicitly
edited synthetic histories. It is a controlled stress test, not four new users,
real agentic logs, an external holdout or a latent-trait induction benchmark.

Each history contains 90 role-labelled messages and 18 user decisions over three
dated phases. Assistant alternatives and tool observations are not user choices.
Six current condition/action pairs supersede earlier decisions. Plain source text
is 5,188–5,376 Unicode characters; JSON metadata is measured separately. Repeated
scopes, rationales and updates create intentional redundancy: a small current
state does not imply that the full biography has been preserved or that its
latent information content has been compressed by the same ratio.

There are 40 scenes and 116 cyclically reordered questions/person. The 32 old
scenes remain consumed regressions. Eight new, derived stress scenes test three
exhaustive supported possibilities and a supported possibility mixed with a
concrete condition gap. The latter uses actual changed values (7 people,
20 minutes, contact two days later, 1,200 currency units), without telling the
model which conditions were unobserved. The finite-table oracle is checked against
an independent hand table. All option positions must be correct for a case.

| Cohort | Person/scene cases | Known offered choice | Unknown |
|---|---:|---:|---:|
| Consumed regressions | 128 | 40 | 88 |
| New derived stress scenes | 32 | 3 | 29 |
| All planned | 160 | 43 | 117 |

Always returning U gets 117 unknowns right and all 43 knowns wrong. Unobserved
domains and other unknown reasons remain separate. New scenes belong to the same
authored finite family; they are not independent external validation.

## Fixed maximum: 46 service executions

- Sol long-history full4, short-history full4 and no-memory1; Luna long full4
  and no-memory1: 14 controls. All receive the exact same public questions.
- One actual Sol source-support extraction per person at each of 768, 512 and
  384 complete Unicode characters: 12. No hand-authored ideal cards are read.
- Sol reads all 12 cards. Luna reads only the 4 cards from the 768 budget.
- Sol independently repeats the 4 card reads at 384, in reverse person order.

The requested identities are `gpt-6-sol` and `gpt-6-luna`; resolved server model
identities are not assumed. Production `make_request` and `bind` are unchanged.
The reader is the standard production request builder with a shared instruction
for a known action absent from offered choices, plus a fixed text-only system.
There is no new scoped-reader intervention in this comparison.

Encoder budget order rotates across people; card reading reverses that person's
budget order. This reduces systematic ordering effects without eliminating
sampling or service drift. Budgets can change both extractor wording and lossless
glossary packing. One extraction per person/budget is not a causal isolation of
budget effects. Repeats reuse exact requests with new execution identities.

Full qualification requires every one of the 160 choice cases correct across all
positions, no missing answers, and known full-minus-no-memory accuracy >= .25.
Sol's short-history result diagnoses context length; it cannot replace a failing
long-history control. Retention is interpretable only with qualified long full.
The strict 384 transfer gate additionally requires both card draws to pass all
planned cases. Every invalid product and missing read stays in the denominator.

Transport, JSON/schema, unknown usage or binding failure stops all later calls.
A valid-schema extraction rejected for anchors, references or complete budget is
retained as an invalid product: skip only dependent reads/repeats, preserve all
planned denominators and finish independent slots. No truncation, retries,
repairs, fallback, replacement people, threshold changes or best-of selection.

```sh
python benchmarks/long-trajectory-v1/world.py
python benchmarks/long-trajectory-v1/study.py prepare --out NEW_DIRECTORY
python benchmarks/long-trajectory-v1/study.py preflight --out NEW_DIRECTORY
```

These are offline. A real execution also requires matching offline acceptance,
runtime agreement and existing human authorization. A durable exclusive intent
makes proposals single use. Mocks validate plumbing, not model quality. This is
neither a likelihood-based information gain measurement nor evidence of real
person fidelity, cross-vendor portability, runtime harness loading, population
accuracy or an invoice. The ceiling is executions, not a token/money cap.
