# Fresh-person alias transfer: closed measurement

**The comparison stopped early. Alias preservation is promising on two new chain-family cards, but stable transfer and qualified-name behavior remain unverified.**

The two observed first-generation alias cards retain **88/88 unique person/cases**
across two reads and both option orders (four answers per case):

| Person | Public characters | Known choices | Unknown boundaries | Cases correct |
| --- | ---: | ---: | ---: | ---: |
| otter | 831 | 28/28 | 16/16 | 44/44 |
| marten | 805 | 28/28 | 16/16 | 44/44 |

This observed subset includes 24/24 original/intermediate-name cases and 64/64
other cases. It is not a replacement denominator or a completed paired recovery:
no baseline card was readable and no second generation was attempted. The fixed
primary endpoint below is therefore **0 retained with 176 missing under each
method**, not 176 observed wrong choices. Qualified-person full controls passed,
but their card generation/reads were never reached.

## What was actually lost

1. **A usable original-method card was lost to quote corruption.** Parent 7
   adds `整体` after a source quotation ending `条件、选择与历史归属不变。`.
   Source s33 contains no such suffix. The original literal-quote validator
   rejects it; reads 8/9 are skipped and all44cases remain in the denominator.
   This is an availability failure, not an observed semantic wrong answer.
2. **The original-method parent 16 produced no accepted card before its
   180-second child deadline.** It is recorded as `GenerationTimeout` and the
   remaining40attempts expire. Sanitized progress contains a `turn.completed`
   event and known usage; that is not a usable card or a diagnosis of the timeout
   cause. No partial result is recovered, scored or used to continue the run.
3. **No observed choice loss on the two valid alias cards.** Each uses explicit
   original→middle and middle→current edges, with current/middle names in the
   object and old names projected into the public scope. The cards also retain
   the permission gate, narrow revision and independent-copy boundary. Their
   observed answers are all correct. This covers one generation and two people
   in one family; it does not establish generation stability, namespace transfer,
   population fidelity or a causal advantage over missing baseline cards.

A separate unmeasured source-ID extraction prototype targets freehand quote
corruption. It reconstructs original text from selected IDs and keeps old guards;
matching old public cards offline is not proof of new-generation fidelity or a
fix for the child timeout. Original cards, scores and observations stay unchanged.

## Planned primary endpoint (incomplete)

Closed 14/54 local attempts; 40 unused slots expired. Reported tokens: 313791; missing usage records: 0. No retry, repair, resume, replenishment or old-budget reuse. Original inputs and observations remain sealed.

All four full-history controls qualified: **True**.

| Method | Joint /176 | Known /112 | Unknown /64 | Missing /176 |
| --- | ---: | ---: | ---: | ---: |
| source-accounted-graph-v1 | 0 | 0 | 0 | 176 |
| scope-alias-encoding-v1 | 0 | 0 | 0 | 176 |

Each joint case requires two independent generations × two reads × both orders (eight answers). Missing answers are never filled with unknown or dropped. The same 176 person/cases appear under both methods; they are not 352 independent samples.

## Paired case transitions

| Transition | Cases |
| --- | ---: |
| kept | 0 |
| recovered | 0 |
| new_observed_loss | 0 |
| both_observed_fail | 0 |
| baseline_missing | 0 |
| candidate_missing | 0 |
| both_missing | 176 |

Missing-product transitions are separate from observed regressions and recoveries. Each generation is also reported in the derived replay; equal joint scores may conceal opposite changes.

## Case groups

| Cohort | Original correct | Alias correct |
| --- | ---: | ---: |
| base_current | 0 | 0 |
| exception_current | 0 | 0 |
| revised_current | 0 | 0 |
| base_old_alias | 0 | 0 |
| revised_old_alias | 0 | 0 |
| linked_name | 0 | 0 |
| denied_name | 0 | 0 |
| scope_not_established | 0 | 0 |
| ambiguity | 0 | 0 |
| same_choice_contexts | 0 | 0 |
| execution_fact | 0 | 0 |

These strata locate observed answers, not their proven causal mechanism. Use the original source → raw graph → public card → observed read trace; literal name presence, declared edges and accounting incidence are not semantic coverage.

## Full-control failures

```json
[]
```

## Reproduce and inspect

```sh
python3 -B scripts/replay_fresh_alias.py
python3 -B scripts/inspect_fresh_alias.py --person otter --case 0_base_old_alias --method scope-alias-encoding-v1 --budget 1536 --generation 0
```

The trace retains complete related source episodes with all roles, original raw graph and public card, and both reads/orders. A missing parent stays missing. Qualified ambiguous/context-pair questions retain both source owners.

## CI qualification

A green aggregate initially arrived before the macOS required-step metadata settled. The pre-start guard rejected that snapshot before any explicit grant receipt, single-use claim, finite-controller entry or backend child. The original failure records remain intact. Qualification continued only after all71pinned steps were completed successfully, under the same unconsumed54-attempt grant; no model request was repeated. The pure readiness guard adds six offline regression tests for this race, missing metadata, failures and foreign heads.

## Limits

Four newly authored fictional people test two adversarial scenario families, with author knowledge of prior failures. This is not an independent holdout, human-fidelity result, cross-provider verification or population-generation-stability estimate. The author table is a constructor consistency check, not independent semantic adjudication. Checksums and archive replay establish internal consistency, not independent service attestation or model identity. No production default changes; the smaller 768-character problem is not tested here. The original preparation metadata remain unapproved historical preparation; this later measurement used a separate direct finite grant.
