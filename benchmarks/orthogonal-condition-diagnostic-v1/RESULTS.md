# Fixed-card time/material boundary: closed measurement

Closed 24/24 local attempts; 0 unused slots expired. Reported tokens: 658694; missing usage: 0.
No extraction, card repair, retry, resume, replenishment or reuse of a closed scope. Original sources, cards, questions and observations remain sealed.

Both full-history controls qualified: **True**.

| Automatic encoder of inherited card | Joint /120 | Known /56 | Unknown /64 | Missing /120 |
| --- | ---: | ---: | ---: | ---: |
| scope-alias-encoding-v1 | 120 | 56 | 64 | 0 |
| source-id-initial-encoding-v1 | 120 | 56 | 64 | 0 |

Each primary case requires both inherited generations × two new reads × both orders (eight answers). The same120person/cases appear under both methods, not240independent samples. Missing never becomes U and never leaves the denominator. All88old anchors are retained alongside32new crossed unknown cases.

| Subset | Method | Correct | Planned | Missing |
| --- | --- | ---: | ---: | ---: |
| old_anchors | scope-alias-encoding-v1 | 88 | 88 | 0 |
| old_anchors | source-id-initial-encoding-v1 | 88 | 88 | 0 |
| crossed_unknown | scope-alias-encoding-v1 | 32 | 32 | 0 |
| crossed_unknown | source-id-initial-encoding-v1 | 32 | 32 | 0 |

## Paired observed transitions

```json
{
  "kept": 120,
  "recovered": 0,
  "new_observed_loss": 0,
  "both_observed_fail": 0,
  "baseline_missing": 0,
  "candidate_missing": 0,
  "both_missing": 0
}
```

Missing products are separate from observed recoveries and new losses. Per-generation transitions and each original answer/order remain in the replay to expose opposite changes hidden by joint scores.

## Separate historical original/damage diagnostic

| Fixed historical view | Joint /60 | Known /28 | Unknown /32 | Missing /60 | Crossed unknown /16 |
| --- | ---: | ---: | ---: | ---: | ---: |
| historical_original | 60 | 28 | 32 | 0 | 16 |
| constructed_material_damage | 44 | 28 | 16 | 0 | 0 |

These rows each require two new reads and both orders (four answers). This is a posthoc, manually constructed rule-condition omission from one historical parent, not a newly generated compression loss or an encoder result. Actions, priorities, aliases, evidence and unknown notes are preserved. Retained unknown notes may rescue a real reader despite damaged rule predicates; failure to discriminate is a finding, not grounds for editing, suppressing or rerunning. The earlier symbolic errors were never empirical model-reader scores.

## Full-control failures

```json
[]
```

## Reproduce and inspect

```sh
python3 -B scripts/replay_orthogonal_condition.py
python3 -B scripts/inspect_orthogonal_condition.py --person otter --case 0_cross_0_0 --method scope-alias-encoding-v1 --generation 0
```

The trace includes complete related source episodes and all roles, the inherited raw graph (or the explicit constructed damage), deterministic source-ID expansion when applicable, the unchanged public card, both questions and both reads/orders. Source links are author navigation, not independent semantic acceptance.

## Limits

Only two consumed fictional development people and a posthoc diagnostic. No new extraction or population-generation-stability test; no independent holdout, human-fidelity result, cross-provider test or independent semantic gold. New unknown references reflect unsupported conjunctions under the recorded rules, not general advice. Checksums and reconstruction establish internal consistency, not independent service attestation or model identity. No production default change. Publication and archive replay add zero model calls or future budget.
