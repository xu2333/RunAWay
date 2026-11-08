# Fresh-person alias transfer: closed measurement

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
