# Carry-on taste and historical reconstruction are separate promises

The D-0015 result remains **4/48 in every cell, 192 valid U answers, no winner**.
This follow-up makes **zero external model calls**. It does not replace that
score with a better-looking number or establish that a new reader prompt works.

## The product contract

The original goal was a tiny, readable carry-on of how a person chooses and
judges, portable across harnesses. “Reproduce taste/choices/judgments” and “as
accurate and detailed as possible” require more than a plausible current-style
description. An effective exception, hard limit or changed preference must
survive; uncertainty must not erase a choice that remains supported.

| Requirement | Prospective task | Required challenge |
| --- | --- | --- |
| Choose like the represented person | New same-scope decision at an explicit source cutoff | Similar people differing in one exception; balanced option orders |
| Preserve conditions and boundaries | Current choice with changed context | Public/private feedback, reversible/irreversible operation, repeated help |
| Apply the latest effective preference | Current choice after updates | Strong versus later weak evidence, replacement, revocation and revoking a revocation |
| Preserve uncertainty and current user control | Unknown domain and explicit current instruction | U only when unsupported; current instruction overrides memory |
| Readable prose across harnesses | Format-independent reader interface | No requirement for literal record IDs when semantic support exists |
| Reconstruct earlier states | Separate historical diagnostic | Past choice/fact at a particular time, including withdrawn records |

Changing the primary task **does not excuse current-state errors**. Historical
losses remain a separate score and an all-24 joint score. D-0015's original
questions, answers, denominator and negative result stay unchanged. The new
contract was frozen before its future comparison cohort and before any new
inference. Public fixtures are development examples, not a fresh heldout win.

## What the saved evidence actually shows

The offline audit reconstructs all four extraction/bound-compression pairs
through the actual product functions and verifies all eight portable texts.
Every one of the 192 observed answers is linked to its source, profile, memory
and query. A U alone is **not** assigned a cause. Six representative cases have
explicit source spans and executable witnesses:

| Case | Evidence chain | Supported conclusion |
| --- | --- | --- |
| Old marker omitted | Original first-day marker → absent from the claim projection and 128-budget portable prompt → past marker query | A date wrapper cannot supply an omitted value. The full private source still survives. |
| Revocation interval omitted | Automatic base + irreversible limit + later revocation → “limit revoked, still automatic” without timing | Two different revocation dates yield the same current policy but different day-14 choices. Past timing information is genuinely lost. |
| Action retained, reader still U | Bound prompt explicitly says “仍自动处理” → day-16 reader U, no source-cutoff envelope | Current action content survives. Framing/cutoff sensitivity is unresolved, not proved to be the cause. |
| Invented second-order revocation | Source revokes a replacement, but never revokes that revocation → extraction claims it was restored → bound prose repeats the claim | A wrong **current** default already exists in extraction. The actual source defaults to a minimal entry; repeated-help alone selects the prominent entry. |
| Known base choice changed to unknown | Revocation says other records continue → base automatic choice remains → extracted exception says current choice unknown | A semantic loss in claim bounds, copied by compression; more permissive reading cannot repair the false bound. |
| Genuine unknown | No film preference in source → U | Correct abstention; U is not always an error. |

“Lost from the profile” would be too broad: the private profile archives the
original sources. These losses concern the claim projection and portable
surface. Reference coverage and copied quotes cannot prove semantic fidelity.
The prior explanation focused on dates was incomplete: content loss, wrong
current-state inference and reader compatibility all need separate tests.

## Executable prospective specification

```sh
python3 -m runaway.taste_contract freeze --out task-contract
python3 -m runaway.taste_audit \
  --evidence examples/pilot-evidence.synthetic.zip --out traces.json
python3 -m unittest tests.test_taste_contract
```

All commands are offline; the source replay also needs Node22+. There are two
representative development pairs. Each evaluation person has16 current-choice
queries and8 historical queries. Current questions have new scenario wording,
explicit cutoff metadata and no hidden rule fields. They still require resolving
active limits, exception scope, evidence strength, replacement and recursive
revocation. Missing outputs remain in every planned denominator. Source coverage
is explicitly complete through the cutoff **within this synthetic fixture**;
that assumption is not silently applied to a real person's incomplete history.

The16 current queries are8 scenarios in two option orders. The two matched
distinction items are the two orders of one conditional difference, not two
independent preferences. These dependent items do not support population-level
confidence intervals or a claim of broad transfer.

To score a `{persona_id: {query_id: option_id}}` answer map:

```sh
python3 -m runaway.taste_contract score --run task-contract \
  --answers answers.json --out scored.json
```

The output always includes current, historical and joint results, critical
layers, hard errors versus observed violations, matched distinctions and option
order pairs. An all-U reader may be order-consistent while still failing almost
all choices. A real no-memory baseline can follow explicit current instructions;
it is measured separately from an artificial always-U control.

## What the deterministic controls establish

These are code-oracle checks, **not model performance**:

| Deliberate semantic damage | Current correct /32 | Critical signal |
| --- | ---: | --- |
| Full structured truth | 32/32 | 0 hard errors |
| Delete exceptions | 26/32 | Both person distinctions lost |
| Delete hard limits | 28/32 | 4 observed hard violations |
| Ignore revocations | 24/32 | Updates remain a core challenge |

A finite family of64 histories per person preserves exactly the same effective
current policy while varying old facts and transient timing. All16 current
answers agree; each of the8 historical questions has disagreeing compatible
histories. This demonstrates information loss **under that declared semantic
projection**, not automatic interpretation of the actual model's prose.
Renaming record IDs while preserving the event graph leaves all reference
answers unchanged. Syntax is therefore not logically necessary; whether an LLM
rejects otherwise sufficient prose requires a model ablation.

## Proposed next comparison, not executed

One new proposal has an upper bound of24 calls, separately requiring approval:

| Stage | Calls | Purpose |
| --- | ---: | --- |
| Existing D-0015 bodies: reader only, cutoff only, both, and source-complete prose | 8 | Diagnose content versus framing; consumed-data development only |
| Fresh contract: full history, no memory, wrong person, current-policy oracle | 8 | Validate actual reader and sensitivity; oracle never enters compression |
| Actual browser extraction, two new people | 2 | Shared old prompt/profile |
| Actual bound compression | 2 | Additional new-method cost |
| Old/new memories under the new contract | 4 | Frozen current + historical + joint readout |

The original body/reader cells are reused **offline**, never sent again. The
reader-only condition leaves memory unchanged; cutoff-only adds metadata, not
preference facts. The source-complete prose is an unbudgeted reader control,
not a successful compressed candidate. The fresh cohort changes parameter
combinations and task wording, not just IDs, but remains a small finite-family
test. The plan retains every historical result and disallows promotion that
hides critical regressions or hard errors.

Generation requests only receive source history, public event semantics and
budget. They receive no queries, seeds, oracle state, gold or diagnostic tags.
The proposed generator/reader remain `gpt-6-luna` / `gpt-6.1-sol`, one384-token
memory budget, maximum180seconds per generation, zero retries/repairs. The old
24-call allowance is closed. No additional service call occurred in this work.

The [dedicated executor and numeric reader gates](TASK-EXECUTOR.md) are now
prepared and tested offline. A matching new human approval is still required.

[Frozen specification](examples/taste-contract/contract.json) ·
[Representative fixtures](examples/taste-contract/fixtures.synthetic.json) ·
[Code-only controls](examples/taste-contract/calibration.synthetic.json) ·
[192-answer trace audit](examples/taste-contract/D0015-trace-audit.synthetic.json)
