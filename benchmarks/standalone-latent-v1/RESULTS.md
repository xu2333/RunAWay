# Standalone ablation: the conditional pass does not carry through

Fixed result **complete**: 19/19 physical calls. Full history **102/102**, unchanged own cards **80/102**. Strict standalone gate: **False**.

Frozen implementation `58fa30064571c131fa519c67e239f9d323cb3d11`; proposal `f4779e637c176a89d7a8138d2db8b927dd9044b9719a111b17681ab31867f63c`. Exactly619shared-prefix characters were removed; no card, source, question, gold, model request, timeout or other request field changed. Full histories still contain the user's original candidate-family definitions. No re-extraction, manual repair, sample selection or retry occurred.

## Main result and all arms

| Arm | Known / 55 | Unknown / 47 | Person-discriminating known / 43 | Family invariants / 12 | Total / 102 | Missing |
|---|---:|---:|---:|---:|---:|---:|
| none | 0 | 47 | 0 | 0 | 47 | 0 |
| full | 55 | 47 | 43 | 12 | 102 | 0 |
| own | 33 | 47 | 29 | 4 | 80 | 0 |
| wrong | 12 | 41 | 8 | 4 | 53 | 0 |
| wrong_against_donor | 33 | 47 | 29 | 4 | 80 | 0 |

The 12 family-invariant cases were free public-decoder knowledge only in the earlier condition. Here their definitions are absent unless the supplied material preserves them. They are not independent personal preference wins. All option rotations must match; missing cases remain planned. The one none call is scored against six people, not six independent trials.

## Gate and qualified control

```json
{
  "contemporary_full_qualified": true,
  "retention_interpretable": true,
  "identity_specificity_verified": false,
  "standalone_gate": false
}
```

Contemporary full must be 102/102 with no missing output and personal-known(full-minus-none)/43>=.25. If it qualifies, this controlled reader can derive the original source-supported conclusions without the added decoder. A failing own card then shows loss in the exported representation under this contract. This is still a sequential exploratory removal study on consumed synthetic cases, not randomized causal inference or a population estimate. The removed prefix contained both candidate definitions and reasoning guidance; this does not isolate each component.

## Per-person losses

| Person | Chars | Earlier own + decoder / 17 | Standalone full / 17 | Standalone own / 17 | Known lost from full | Unknown lost from full |
|---|---:|---:|---:|---:|---:|---:|
| u06k | 378 | 17 | 17 | 13 | 4 | 0 |
| u19m | 387 | 17 | 17 | 17 | 0 | 0 |
| u42r | 371 | 17 | 17 | 13 | 4 | 0 |
| u58s | 336 | 17 | 17 | 9 | 8 | 0 |
| u73v | 296 | 17 | 17 | 17 | 0 | 0 |
| u85w | 314 | 17 | 17 | 11 | 6 | 0 |

## Unseen combinations and other cohorts

| Arm | Cohort | Known | Unknown | Person-discriminating known | Missing |
|---|---|---:|---:|---:|---:|
| none | observed_paraphrase | 0/18 | 0/0 | 0/18 | 0 |
| none | heldout_combination | 0/26 | 4/4 | 0/14 | 0 |
| none | partial_features | 0/9 | 9/9 | 0/9 | 0 |
| none | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| none | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| none | action_not_offered | 0/2 | 4/4 | 0/2 | 0 |
| full | observed_paraphrase | 18/18 | 0/0 | 18/18 | 0 |
| full | heldout_combination | 26/26 | 4/4 | 14/14 | 0 |
| full | partial_features | 9/9 | 9/9 | 9/9 | 0 |
| full | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| full | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| full | action_not_offered | 2/2 | 4/4 | 2/2 | 0 |
| own | observed_paraphrase | 18/18 | 0/0 | 18/18 | 0 |
| own | heldout_combination | 10/26 | 4/4 | 6/14 | 0 |
| own | partial_features | 3/9 | 9/9 | 3/9 | 0 |
| own | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| own | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| own | action_not_offered | 2/2 | 4/4 | 2/2 | 0 |
| wrong | observed_paraphrase | 4/18 | 0/0 | 4/18 | 0 |
| wrong | heldout_combination | 7/26 | 2/4 | 3/14 | 0 |
| wrong | partial_features | 1/9 | 7/9 | 1/9 | 0 |
| wrong | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| wrong | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| wrong | action_not_offered | 0/2 | 2/4 | 0/2 | 0 |
| wrong_against_donor | observed_paraphrase | 18/18 | 0/0 | 18/18 | 0 |
| wrong_against_donor | heldout_combination | 10/26 | 4/4 | 6/14 | 0 |
| wrong_against_donor | partial_features | 3/9 | 9/9 | 3/9 | 0 |
| wrong_against_donor | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| wrong_against_donor | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| wrong_against_donor | action_not_offered | 2/2 | 4/4 | 2/2 | 0 |

The original latent study has 30 unseen-combination person/scene cases: 26 known, 4 unknown; only 14 of those knowns discriminate people rather than follow family-wide invariants. Every cohort, including partial fields, outside values/domains and absent actions, remains separate.

## Every paired loss and donor-repeat change

| Contrast | Known lost | Known recovered | Unknown lost | Unknown recovered |
|---|---:|---:|---:|---:|
| full->own | 22 | 0 | 0 | 0 |
| own->wrong | 29 | 8 | 6 | 0 |

Observed own/donor-repeat answer changes: **0**. Wrong-person inputs are exact donor-own inputs with new execution identities, scored both for target and donor. [Every actual error and rotated answer](LOSSES.md). Missing is not called an observed disagreement.

## What the loss suggests (manual interpretation, not a new causal test)

The two cards for `u19m` and `u73v` explicitly state their full conditional decision rules and retain 17/17 in this ablation. The other four mostly preserve the three observed choices and broad abstention limits. `u06k` and `u42r` also refer to candidate numbers without their definitions. Read the [unchanged complete cards](../latent-transfer-v1/CARDS.md) alongside the full source evidence.

The observed own losses are abstentions on known conclusions, not false certainty on the 47 unknown gold cases. This is consistent with losing source-supported constraint closure, plus overly broad "unobserved is unknown" limits. The card comparisons differ in person/rule complexity and were not randomized style interventions, so this is a diagnosis to test, not proof of a universal mechanism.

The next correction should preserve self-contained rule meanings and the full set of still-compatible alternatives, not just opaque IDs or observations. It must allow only conclusions entailed by explicit source constraints, keep genuine uncertainty, and avoid relaxing abstention globally. A repair would need fresh source-only extraction and independent validation; none was applied to these recorded cards.

## Both independently frozen phases and all cost

| Phase | Cap | Actual | Unique inputs | Known tokens | Missing usage |
|---|---:|---:|---:|---:|---:|
| Shared decoder | 31 | 31 | 25 | 407601 | 0 |
| Prefix removed | 19 | 19 | 13 | 255118 | 0 |

Combined this human continuation: **50** calls, announced ceiling 50; known total **662,719** tokens. Earlier31slots stayed closed and no old response was reused as a new draw. The additional 19-call question was explicitly announced and frozen before its first call.

This phase input242,633, including112,896cached; output12,485, including4,216reasoning. Subsets are not added twice. Local usage is not an invoice, token/money ceiling or end-to-end savings claim. Requestedgpt-6-sol; resolved model unavailable.

## Reproduction and limits

```sh
python benchmarks/standalone-latent-v1/check.py
```

The offline checker binds the exact 619-character removal for every request, unchanged production cards, original answer/checkpoint hashes, physical executions, repeated inputs, usage, guard observations, all scores, paired losses and disagreements. The prior 31-call ledger remains bound and public. Mock tests are not model evidence; hashes are not provider-signed attestations.

No human/PRISM/private trajectory was sent. The corpus and family are authored, small and consumed; no real-person fidelity, unconstrained personality inference, population confidence interval, cross-vendor/runtime-harness loading, humor, likelihoodRIG or net economic-savings claim. The production library defaults were not changed to fit this experiment.
