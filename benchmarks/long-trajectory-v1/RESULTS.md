# Long-history / whole-card budget results

Fixed service result: **stopped**. Four previously consumed synthetic policies, alternative long histories, three complete-card budgets. This is not four new people or real-person fidelity.

Frozen code commit `ef966d9ffb35801aa30c431b5ad510e14e996fef`; proposal `bcce37b487af880c4e9499f8e43a4e6b372290154c09a200581baff9fd8d656a`. Maximum 46 executions. No repairs, retries, truncation, fallback, favorable selection or replenishment.

## Interrupted run: no whole-budget pass

Execution 29 (`sol_768`, `t04a`) raised `GenerationTimeout`. The original failure
checkpoint is included in `observed.synthetic.json`; it records an active deadline
of 180 seconds, measured active elapsed 180.008 seconds and wall elapsed
1,210.75 seconds. These clocks differ; the cause is not established. Cleanup
killed the local process group. Usage for this attempt is **unknown**, not zero.

Of 46 planned executions, 28 completed, one failed and 17 never started. All 12
extractions succeeded. Of the 20 planned card reads, only two completed: `t04a`
at 384 (375 characters) and 512 (433 characters), each **40/40** of that person's
cases (8 known, 32 unknown, all option positions). No other card was read;
no 384 repeat or Luna card read ran. These are partial observations, not a
four-person budget curve or a passed 384 stability gate. The all-planned table
below retains every missing case.

## Every planned reader arm

| Arm | Known / 43 | Unknown / 117 | All / 160 | Missing cases |
|---|---:|---:|---:|---:|
| luna_768 | 0 | 0 | 0 | 160 |
| luna_full | 31 | 115 | 146 | 0 |
| luna_none | 0 | 117 | 117 | 0 |
| sol_384 | 8 | 32 | 40 | 120 |
| sol_384_repeat | 0 | 0 | 0 | 160 |
| sol_512 | 8 | 32 | 40 | 120 |
| sol_768 | 0 | 0 | 0 | 160 |
| sol_full | 43 | 117 | 160 | 0 |
| sol_none | 0 | 117 | 117 | 0 |
| sol_short | 43 | 117 | 160 | 0 |

All tested option positions must be correct for a person/scene. Missing reads stay in all planned denominators. Always choosing U scores 117/117 unknown and 0/43 known; 80 unknowns concern entirely unobserved domains. All generated cards reference the six latest user decisions (`s063`, `s068`, `s073`, `s078`, `s083`, `s088`), sometimes merged into fewer branches. Reference validation alone does not prove semantic completeness. Scope diagnostics were not requested in this standard-reader study.

## Contemporaneous controls

```json
{
  "sol": {
    "long_full_qualified": true,
    "retention_interpretable": true,
    "short_full_strict_pass": true,
    "stable_384_transfer_pass": false
  },
  "luna": {
    "long_full_qualified": false,
    "retention_interpretable": false
  }
}
```

A long-full control qualifies only at 160/160 with no missing answers and known full-minus-none accuracy >= .25. Short histories are a diagnostic, not a replacement for a failing long-full control. Card-minus-full cannot isolate compression loss for an unqualified model. The strict 384 gate requires qualified Sol long full and both independent 384 card draws to be perfect, with all four planned profiles present. No confidence interval or population-stability claim is made.

## Old and new scenes kept separate

| Arm | Consumed known / 40 | Consumed unknown / 88 | New known / 3 | New unknown / 29 |
|---|---:|---:|---:|---:|
| luna_768 | 0 | 0 | 0 | 0 |
| luna_full | 29 | 87 | 2 | 28 |
| luna_none | 0 | 88 | 0 | 29 |
| sol_384 | 8 | 24 | 0 | 8 |
| sol_384_repeat | 0 | 0 | 0 | 0 |
| sol_512 | 8 | 24 | 0 | 8 |
| sol_768 | 0 | 0 | 0 | 0 |
| sol_full | 40 | 88 | 3 | 29 |
| sol_none | 0 | 88 | 0 | 29 |
| sol_short | 40 | 88 | 3 | 29 |

The eight new derived scenes contribute 32 person/scene cases, only three known choices. They test exhaustive three-state alternatives and a concrete condition gap mixed with a supported state. They are within the same authored family, not independent external holdout. The 32 old scenes are consumed regressions.

## Unknown reasons

| Arm | known | unobserved_domain | outside_observed_conditions | ambiguous | known_action_not_offered |
|---|---:|---:|---:|---:|---:|
| luna_768 | 0/43 | 0/80 | 0/24 | 0/9 | 0/4 |
| luna_full | 31/43 | 80/80 | 23/24 | 9/9 | 3/4 |
| luna_none | 0/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| sol_384 | 8/43 | 20/80 | 6/24 | 4/9 | 2/4 |
| sol_384_repeat | 0/43 | 0/80 | 0/24 | 0/9 | 0/4 |
| sol_512 | 8/43 | 20/80 | 6/24 | 4/9 | 2/4 |
| sol_768 | 0/43 | 0/80 | 0/24 | 0/9 | 0/4 |
| sol_full | 43/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| sol_none | 0/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| sol_short | 43/43 | 80/80 | 24/24 | 9/9 | 4/4 |

## Paired losses and recoveries

| Contrast | Known lost | Known recovered | Unknown lost | Unknown recovered |
|---|---:|---:|---:|---:|
| sol_full->sol_768 | 43 | 0 | 117 | 0 |
| sol_full->sol_512 | 35 | 0 | 85 | 0 |
| sol_full->sol_384 | 35 | 0 | 85 | 0 |
| sol_768->sol_512 | 0 | 8 | 0 | 32 |
| sol_512->sol_384 | 0 | 0 | 0 | 0 |
| sol_384->sol_384_repeat | 8 | 0 | 32 | 0 |
| luna_full->luna_768 | 31 | 0 | 115 | 0 |

Every affected person/case ID, exact answer at every option rotation, and unknown reason is retained in `observed.synthetic.json`. Missing executions count as lost cases against a successful full control; they are not evidence that an unexecuted reader guessed incorrectly. Budget contrasts use independent encoder draws, so wording, source selection and glossary packing vary together. The 384 repeat uses the same request and a new execution, not a second extraction.

## Product validity and measured size

| Budget | Valid products / 4 | Invalid products |
|---|---:|---:|
| 768 | 4 | 0 |
| 512 | 4 | 0 |
| 384 | 4 | 0 |

No invalid products; the run stopped on transport timeout, not extraction validation.

| Person | Budget | Card chars | Long plain text | Long role JSON | Original short plain text | Card / long plain | Card / short plain |
|---|---:|---:|---:|---:|---:|---:|---:|
| t04a | 768 | 491 | 5376 | 10718 | 669 | 0.091 | 0.734 |
| t11b | 768 | 552 | 5376 | 10718 | 674 | 0.103 | 0.819 |
| t35c | 768 | 549 | 5189 | 10531 | 584 | 0.106 | 0.940 |
| t92d | 768 | 518 | 5188 | 10530 | 596 | 0.100 | 0.869 |
| t04a | 512 | 433 | 5376 | 10718 | 669 | 0.081 | 0.647 |
| t11b | 512 | 494 | 5376 | 10718 | 674 | 0.092 | 0.733 |
| t35c | 512 | 484 | 5189 | 10531 | 584 | 0.093 | 0.829 |
| t92d | 512 | 459 | 5188 | 10530 | 596 | 0.088 | 0.770 |
| t04a | 384 | 375 | 5376 | 10718 | 669 | 0.070 | 0.561 |
| t11b | 384 | 381 | 5376 | 10718 | 674 | 0.071 | 0.565 |
| t35c | 384 | 332 | 5189 | 10531 | 584 | 0.064 | 0.568 |
| t92d | 384 | 374 | 5188 | 10530 | 596 | 0.072 | 0.628 |

[Copy complete cards and portable JSON](CARDS.md). These are Unicode-character ratios, not token ratios. Long histories contain 90 role-labelled messages and 18 explicit user decisions across three dates, but only six current condition/action pairs. Old decisions, repeated rationale and repeated uncertainty limits are deliberately redundant. This tests reconstruction of the current state; it does not preserve every earlier event or establish an equivalent reduction in latent information. Metadata removal is shown separately from plain text.

## Cost and offline reproduction

Actual executions: **29**; unique request fingerprints: **29**; usage missing: **1**.

Known usage from the 28 completed executions only: input tokens **833,849**, including 127,744 cached; output **49,877**, including 13,048 reasoning; known total **883,726**; the failed attempt adds unknown usage. Subsets are not added twice. This is incomplete local usage accounting, not an invoice or a total money cap. Requested model IDs only (`gpt-6-sol`, `gpt-6-luna`); resolved identities unavailable.

```sh
python benchmarks/long-trajectory-v1/check.py
```

The offline checker reconstructs products, budgets, all scores, gates, losses, exact requests, original answer/checkpoint hashes, execution identities, usage provenance, skip order and exported portable cards. Hashes catch inconsistency, not maliciously rewritten provider attestations. Mock corruption tests never count as real-model evidence.

No human trajectories, PRISM records or user feedback were transmitted. This study does not establish real-person fidelity, generalization to new people or unobserved domains, historical recall, runtime harness loading, cross-vendor portability, humor quality, population accuracy, likelihood-based relative information gain, or net end-to-end cost savings.
