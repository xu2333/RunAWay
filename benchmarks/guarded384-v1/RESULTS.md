# Power-guarded 384-card results

New fixed proposal: **complete**; 13/13 physical executions, 13 completed, 0 failed, 0 unstarted.

Frozen implementation `d1e7c351a2345c57a5acb5aa72ea8354ba9139a4`; proposal `61e1fa73d2b5ff90b16f6423b4db07f907b899c27c9a35a6bdc77cb58fa57562`. Earlier interrupted 46-slot study remains closed, including its usage-unknown failed call. No old answer substitutes for a new draw.

**Contemporary full, first card draw and independent repeat: each 160/160,
including all 43 known and 117 unknown cases. Zero repeat disagreements.**
This finite two-draw result passes the frozen gate on consumed synthetic cases;
it does not establish a population stability rate, human fidelity or generalization.

## Environment intervention and all attempts this continuation

The guard wrapper was frozen before this new proposal. An owned macOS idle-sleep
assertion was verified immediately before all 13 attempted service
calls, with no deadline change or retry. Manual sleep/lid closure and service
stalls remain possible. This establishes the observed run condition, not a
provider-signed attestation or population reliability estimate.

| Separate proposal | Attempted | Completed | Failed | Unstarted | Usage unknown |
|---|---:|---:|---:|---:|---:|
| Unguarded, closed after host sleep | 3 | 2 | 1 | 10 | 1 |
| New guarded proposal | 13 | 13 | 0 | 0 | 0 |

Combined this human continuation: **16** attempts, ceiling 16. The previous
usage-unknown timeout is retained; it was not retried inside its original plan,
reclassified as zero, or completed with unused slots. Known combined tokens:
**654,416**, plus unknown failed usage. Initial 13-slot ceilings
were separate; the additional guarded 13-slot ceiling was explicitly announced
after the sleep fix. Neither interrupted proposal is presented as complete.

## Fixed qualification

```json
{
  "contemporaneous_full_qualified": true,
  "retention_interpretable": true,
  "stable384_pass": true
}
```

Full qualifies only at all 160 cases correct, no missing outputs, known (full-minus-none) / 43 >= .25. The strict 384-character gate additionally requires both card draws all 160 correct with no missing outputs. This is a finite two-draw gate for consumed synthetic cases, not a statistical stability or human-fidelity guarantee.

## Every arm and person

| Arm | Known / 43 | Unknown / 117 | All / 160 | Missing |
|---|---:|---:|---:|---:|
| none | 0 | 117 | 117 | 0 |
| full | 43 | 117 | 160 | 0 |
| card | 43 | 117 | 160 | 0 |
| repeat | 43 | 117 | 160 | 0 |

| Arm | t04a / 40 | t11b / 40 | t35c / 40 | t92d / 40 |
|---|---:|---:|---:|---:|
| none | 32 | 26 | 31 | 28 |
| full | 40 | 40 | 40 | 40 |
| card | 40 | 40 | 40 | 40 |
| repeat | 40 | 40 | 40 | 40 |

All option rotations must be right for a person/scene to pass. The shared no-memory answer is scored against all four people, not four independent calls. Every missing planned case remains in the denominator. Always-U gets 117 unknowns and zero of 43 knowns correct; 80 unknowns are entirely unobserved domains. Cases, people and repeated rotations are not independent population samples.

## Consumed cohorts and unknown reasons

| Arm | Old known / 40 | Old unknown / 88 | Derived known / 3 | Derived unknown / 29 |
|---|---:|---:|---:|---:|
| none | 0 | 88 | 0 | 29 |
| full | 40 | 88 | 3 | 29 |
| card | 40 | 88 | 3 | 29 |
| repeat | 40 | 88 | 3 | 29 |

Both cohorts are consumed in this revalidation. The eight derived scenes add exhaustive three-state alternatives and mixed supported/unobserved conditions; they are not external holdouts.

| Arm | Known | Unobserved domain | Outside conditions | Ambiguous | Known action absent |
|---|---:|---:|---:|---:|---:|
| none | 0/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| full | 43/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| card | 43/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| repeat | 43/43 | 80/80 | 24/24 | 9/9 | 4/4 |

## Every paired regression and repeated-answer change

| Contrast | Known lost | Known recovered | Unknown lost | Unknown recovered |
|---|---:|---:|---:|---:|
| full->card | 0 | 0 | 0 | 0 |
| full->repeat | 0 | 0 | 0 | 0 |
| card->repeat | 0 | 0 | 0 | 0 |

Actual card/repeat answer disagreements among mutually observed cases: **0**. Missing reads are never called observed disagreements. Every ID and rotated raw answer is in `observed.synthetic.json`.

[All actual errors and missing-read counts](LOSSES.md). A card-minus-full contrast is not identifiable as compression loss if contemporaneous full fails qualification. Paired losses retain missing cases; these are availability losses, not observed hallucinations. No favorable sample, extra extraction, manual repair, fallback or retry was selected.

## Original cards and source sizes

| Person | Complete card chars | Long plain text | Long role JSON | Original short plain text | Card / long plain | Card / short plain |
|---|---:|---:|---:|---:|---:|---:|
| t04a | 375 | 5376 | 10718 | 669 | 0.070 | 0.561 |
| t11b | 381 | 5376 | 10718 | 674 | 0.071 | 0.565 |
| t35c | 332 | 5189 | 10531 | 584 | 0.064 | 0.568 |
| t92d | 374 | 5188 | 10530 | 596 | 0.072 | 0.628 |

[Complete prompts and portable cards](../long-trajectory-v1/CARDS.md): use 384-budget entries. All four are byte-identical to earlier production products, selected as the complete budget pool. One had a successful prior read; none is a fresh test of card selection. No re-extraction ran.

Character ratios are not token or information ratios. The long histories have 90 messages / 18 dated decisions but only six explicit current condition/action pairs, with deliberately repeated rationale and obsolete decisions. This tests current-state reconstruction, not preservation of all episodic detail or an equivalent reduction in latent information. Reference validity alone does not prove semantic completeness.

## Calls, cost and original bindings

Actual calls **13**; unique input fingerprints **9**; usage missing **0**. Separate card/repeat calls intentionally share exact requests and have independent local execution IDs. Physical calls and unique inputs are not interchangeable.

Known input tokens 545,112, including 194,560 cached; output 20,668, including 1,349 reasoning; known total **565,780**. Subsets are not added twice. Missing usage is unknown, not zero. Local accounting is not an invoice or a net end-to-end savings measurement; extracting these cards incurred prior-study cost. Requested ID `gpt-6-sol`; resolved model unavailable.

```sh
python benchmarks/guarded384-v1/check.py
```

The offline checker reconstructs the unchanged cards, exact frozen plan/requests, original answer/checkpoint hashes, execution identities, repeat inputs, usage, every score, qualification, paired loss and disagreement. Original failed checkpoints are retained if present. Hashes detect inconsistency, not provider-signed attestation. Mock corruption fixtures are labelled and never counted as real models.

No human, PRISM or private user trajectory was sent. This is not real-person fidelity, latent-rule generalization, historical recall, cross-vendor or runtime-harness portability, humor validation, independent population accuracy or likelihood-based relative information gain.
