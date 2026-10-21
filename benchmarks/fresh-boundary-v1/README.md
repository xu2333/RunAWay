# Fresh synthetic users: scope and end-to-end transfer

This pilot starts from four new authored synthetic users in two contrasting
pairs. Research disclosure, collaboration feedback, close-relationship contact
and travel booking are new domains relative to the earlier six-policy layout
study. Each user has two recorded domains; the other two are unobserved.

The natural histories include assistant suggestions, explicit user decisions and
later changes under the same conditions. Separate finite tables define current
choices, and an independently written hand table checks the oracle's outputs.
Held-out scenario prose is authored separately. This is new to the previous
runs, but is not an external dataset or an independent human-authored validation.

There are 32 scenes, 92 cyclically reordered questions and 128 person/scene
cases. A case passes only when every tested option position is correct:

| Target category | Cases |
|---|---:|
| Known offered choice | 40 |
| Unobserved domain | 64 |
| Changed necessary conditions | 16 |
| Exhaustive possibilities with different choices | 4 |
| Unique known action absent from offered choices | 4 |

The 64 unobserved-domain unknowns are reported separately. Always choosing `U`
gets all 88 unknowns correct and all 40 knowns wrong; it cannot pass.

## Fixed protocol

The 56-call ceiling consists of 4 actual source-support extractions with requested
`gpt-6-sol`, and 22 reader calls each with requested `gpt-6-luna` and `gpt-6-sol`:
standard full4/none1/own4/wrong4 plus scoped full4/none1/own4. Luna adds independent
standard-own4/scoped-own4 repeats. Reader order is balanced by person and reversed
on repeat. No model identities resolved by the server are assumed.

Both readers receive the same complete, automatically extracted paragraph card
with a 768 Unicode-character budget, including its header and guide. The scoped
contract reports `scope` and `choice` separately; it is a reader intervention,
not a change to memory content. `determinate` means a unique supported action,
`ambiguous` means exhaustive supported possibilities choose differently, and
`uncovered` means a necessary condition/domain is outside the records. A known
action absent from the choices still has determinate scope but choice `U`.
The decoder never changes a choice to make it agree with the reported scope.

Each model/contract gets contemporary full-history and no-memory controls. Full
qualification requires every choice correct across all positions, no missing
answers and a known accuracy advantage over no memory of at least 0.25. Scoped
qualification additionally requires scope-and-choice correct on all 128 cases.
Stable card transfer requires qualified full history, a perfect card arm and,
for Luna, a perfect independent repeat. All draws and per-case regressions are
retained; failed full history prevents interpreting card-minus-full as compression
retention. A wrong-person card is scored against both target and donor policies.

Any transport/wire/schema/usage/binding failure stops later calls. A structurally
valid extraction rejected by production evidence or budget validation remains an
invalid product: its dependent reads are skipped with planned denominators kept.
No repairs, fallback, truncation, retries or favorable-draw selection are allowed.

```sh
python benchmarks/fresh-boundary-v1/world.py
python benchmarks/fresh-boundary-v1/study.py prepare --out NEW_DIRECTORY
python benchmarks/fresh-boundary-v1/study.py preflight --out NEW_DIRECTORY
```

These commands make zero model calls. Real execution additionally requires a
matching offline acceptance record, local runtime agreement and existing human
authorization. The exclusive service intent makes a proposal single use. Mock
executions in tests exercise plumbing and failure accounting, not model quality.

[Results and all draws](RESULTS.md), [four generated cards](CARDS.md), execution
bindings and offline reproduction are saved alongside this protocol. Run
`python benchmarks/fresh-boundary-v1/check.py` to audit the recorded evidence
without service calls. No real-person data is used. These small synthetic
samples do not establish real-person fidelity, cross-vendor compatibility,
population confidence intervals or likelihood-based relative information gain.
