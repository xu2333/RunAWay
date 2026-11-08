# New-source whole768: closed observations

Closed 54/54 local attempts; 0 unused slots expired. Reported total tokens: 1884730; missing usage: 0.
No retry, card repair, resume, replacement or replenishment. Original inputs, cards, raw responses and reference are unchanged.

All four full-history controls qualified: **True**.

| Method | All8correct /384 | Known /168 | Unknown /216 | Missing /384 |
| --- | ---: | ---: | ---: | ---: |
| source-id-flat | 384 | 168 | 216 | 0 |
| source-id-factor | 384 | 168 | 216 | 0 |

Every case requires two independent source-only extractions × two reads × two option orders, all eight answers correct. Both methods have the same whole768character ceiling. The same384cases are paired across methods; four fictional people are the person-level units. No best-generation selection or missing-to-U conversion.

## Per-family and per-cohort fidelity

| Family | Method | Correct | Planned | Missing |
| --- | --- | ---: | ---: | ---: |
| strict | source-id-flat | 192 | 192 | 0 |
| strict | source-id-factor | 192 | 192 | 0 |
| released | source-id-flat | 192 | 192 | 0 |
| released | source-id-factor | 192 | 192 | 0 |

| Cohort | Method | Correct | Planned | Missing |
| --- | --- | ---: | ---: | ---: |
| boundary | source-id-flat | 24 | 24 | 0 |
| boundary | source-id-factor | 24 | 24 | 0 |
| ordinary | source-id-flat | 24 | 24 | 0 |
| ordinary | source-id-factor | 24 | 24 | 0 |
| revised | source-id-flat | 24 | 24 | 0 |
| revised | source-id-factor | 24 | 24 | 0 |
| old_alias | source-id-flat | 24 | 24 | 0 |
| old_alias | source-id-factor | 24 | 24 | 0 |
| missing_material_narrow | source-id-flat | 24 | 24 | 0 |
| missing_material_narrow | source-id-factor | 24 | 24 | 0 |
| failed_material_narrow | source-id-flat | 24 | 24 | 0 |
| failed_material_narrow | source-id-factor | 24 | 24 | 0 |
| failed_material_ordinary | source-id-flat | 24 | 24 | 0 |
| failed_material_ordinary | source-id-factor | 24 | 24 | 0 |
| crossed_conditions | source-id-flat | 24 | 24 | 0 |
| crossed_conditions | source-id-factor | 24 | 24 | 0 |
| missing_gate | source-id-flat | 24 | 24 | 0 |
| missing_gate | source-id-factor | 24 | 24 | 0 |
| missing_review | source-id-flat | 24 | 24 | 0 |
| missing_review | source-id-factor | 24 | 24 | 0 |
| paired_same_choice | source-id-flat | 24 | 24 | 0 |
| paired_same_choice | source-id-factor | 24 | 24 | 0 |
| lookalike | source-id-flat | 24 | 24 | 0 |
| lookalike | source-id-factor | 24 | 24 | 0 |
| actual_status | source-id-flat | 24 | 24 | 0 |
| actual_status | source-id-factor | 24 | 24 | 0 |
| missing_time_same_choice | source-id-flat | 24 | 24 | 0 |
| missing_time_same_choice | source-id-factor | 24 | 24 | 0 |
| missing_material_ordinary | source-id-flat | 24 | 24 | 0 |
| missing_material_ordinary | source-id-factor | 24 | 24 | 0 |
| ambiguous_owner | source-id-flat | 24 | 24 | 0 |
| ambiguous_owner | source-id-factor | 24 | 24 | 0 |

## What was lost

[Source/card/answer review and remaining limits](LOSS-ANALYSIS.md).

Observed transitions are separate from missing products. All generation-level changes and reader/order differences remain in archive replay; a recovered case and a new loss in different generations cannot cancel invisibly.

```json
{
  "kept": 384,
  "recovered": 0,
  "new_observed_loss": 0,
  "both_observed_fail": 0,
  "baseline_missing": 0,
  "candidate_missing": 0,
  "both_missing": 0
}
```

## Generated parent cards

| Person | Method | Generation | Valid | Characters | Active public rows |
| --- | --- | ---: | --- | ---: | ---: |
| puffin | source-id-flat | 0 | True | 700 | 18 |
| puffin | source-id-factor | 0 | True | 555 | 18 |
| stoat | source-id-factor | 0 | True | 570 | 18 |
| stoat | source-id-flat | 0 | True | 734 | 18 |
| mallow | source-id-flat | 0 | True | 727 | 18 |
| mallow | source-id-factor | 0 | True | 658 | 18 |
| sorrel | source-id-factor | 0 | True | 661 | 18 |
| sorrel | source-id-flat | 0 | True | 720 | 18 |
| puffin | source-id-factor | 1 | True | 568 | 18 |
| puffin | source-id-flat | 1 | True | 727 | 18 |
| stoat | source-id-flat | 1 | True | 751 | 18 |
| stoat | source-id-factor | 1 | True | 568 | 18 |
| mallow | source-id-factor | 1 | True | 654 | 18 |
| mallow | source-id-flat | 1 | True | 711 | 18 |
| sorrel | source-id-flat | 1 | True | 716 | 18 |
| sorrel | source-id-factor | 1 | True | 665 | 18 |

Counts of declared objects, rows, aliases or literal labels do not establish semantic coverage. Invalid and unattempted generations remain in fixed case denominators. Private16000-character diagnostic structures are not delivered reader memory.

## Reproduce and inspect

```sh
python3 -B scripts/replay_fresh_direct768.py
python3 -B scripts/inspect_fresh_direct768.py --person mallow --case 0_missing_material_narrow --method source-id-factor --budget 768 --generation 0
```

The trace retains complete source episodes and all roles, original raw and resolved graph, active rows, exact public card and both answer orders/read repeats. Author links and literal witnesses are navigation, not automatic semantic acceptance or a proven error cause.

## Limits

Four newly authored fictional development people,216messages,384unique public forms; the author knew prior failures and wrote the reference. Not an independently accepted semantic gold set or human fidelity result. One requested model/provider; no population or cross-provider claim. The candidate changes request guidance and rendering together, not a pure-layout causal estimate. No original source supplement, private graph or program decoder is supplied to card readers. Checksums and replay establish internal consistency, not independent service or model-identity attestation. Preparation metadata remain historical preparation; later real execution used a separate direct finite grant. Replay/publication add zero calls or future budget. Production defaults remain unchanged.
