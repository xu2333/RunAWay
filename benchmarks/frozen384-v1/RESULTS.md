# Frozen 384-card revalidation results

New fixed proposal: **stopped**; 3/13 physical executions, 2 completed, 1 failed, 10 unstarted.

Frozen implementation `132b7d7197970121bd30fd03c36d5c62bc0b8b0e`; proposal `a21dbf78801ed54abda39f1beeda0f7517fda643e2013f71e7edbcf6a27c6052`. Earlier interrupted 46-slot study remains closed, including its usage-unknown failed call. No old answer substitutes for a new draw.

## Host sleep interrupted collection

The third call, `card:t35c`, raised `GenerationTimeout`. It completed no answer
and reported unknown usage. Invocation intent was 22:45:20.918637UTC; the host
entered Idle Sleep at 22:45:28UTC and woke at 23:00:21UTC (893 seconds). The failure
records 180.011 active seconds and 1,070.251 wall seconds. The sleep interval overlaps
the invocation and explains nearly all excess wall time; this does not rule out
an upstream stall. This is an environmental interruption, not evidence of card
quality. [Minimal local power evidence](host-sleep-observation.json).

Only shared no-memory and `full:t11b` completed. All card/repeat outputs and three
full controls are missing. Zero observed repeated-answer disagreements therefore
means **unmeasured**, not stable. All ten later slots remained unstarted.

`scripts/with_awake.py` now offers temporary macOS idle-sleep prevention for a new
accepted proposal. It was not applied to any recorded model invocation. This
proposal stays closed; no retry or automatic new study ran. A zero-model-call
[real macOS guard test](awake-guard-audit.json) verified a new idle-sleep assertion
during a controlled child process, release after exit, and preservation of exit
code 7. The offline checker binds this audit to the exact wrapper source hash.

## Fixed qualification

```json
{
  "contemporaneous_full_qualified": false,
  "retention_interpretable": false,
  "stable384_pass": false
}
```

Full qualifies only at all 160 cases correct, no missing outputs, known (full-minus-none) / 43 >= .25. The strict 384-character gate additionally requires both card draws all 160 correct with no missing outputs. This is a finite two-draw gate for consumed synthetic cases, not a statistical stability or human-fidelity guarantee.

## Every arm and person

| Arm | Known / 43 | Unknown / 117 | All / 160 | Missing |
|---|---:|---:|---:|---:|
| none | 0 | 117 | 117 | 0 |
| full | 14 | 26 | 40 | 120 |
| card | 0 | 0 | 0 | 160 |
| repeat | 0 | 0 | 0 | 160 |

| Arm | t04a / 40 | t11b / 40 | t35c / 40 | t92d / 40 |
|---|---:|---:|---:|---:|
| none | 32 | 26 | 31 | 28 |
| full | 0 | 40 | 0 | 0 |
| card | 0 | 0 | 0 | 0 |
| repeat | 0 | 0 | 0 | 0 |

All option rotations must be right for a person/scene to pass. The shared no-memory answer is scored against all four people, not four independent calls. Every missing planned case remains in the denominator. Always-U gets 117 unknowns and zero of 43 knowns correct; 80 unknowns are entirely unobserved domains. Cases, people and repeated rotations are not independent population samples.

## Consumed cohorts and unknown reasons

| Arm | Old known / 40 | Old unknown / 88 | Derived known / 3 | Derived unknown / 29 |
|---|---:|---:|---:|---:|
| none | 0 | 88 | 0 | 29 |
| full | 12 | 20 | 2 | 6 |
| card | 0 | 0 | 0 | 0 |
| repeat | 0 | 0 | 0 | 0 |

Both cohorts are consumed in this revalidation. The eight derived scenes add exhaustive three-state alternatives and mixed supported/unobserved conditions; they are not external holdouts.

| Arm | Known | Unobserved domain | Outside conditions | Ambiguous | Known action absent |
|---|---:|---:|---:|---:|---:|
| none | 0/43 | 80/80 | 24/24 | 9/9 | 4/4 |
| full | 14/43 | 20/80 | 6/24 | 0/9 | 0/4 |
| card | 0/43 | 0/80 | 0/24 | 0/9 | 0/4 |
| repeat | 0/43 | 0/80 | 0/24 | 0/9 | 0/4 |

## Every paired regression and repeated-answer change

| Contrast | Known lost | Known recovered | Unknown lost | Unknown recovered |
|---|---:|---:|---:|---:|
| full->card | 14 | 0 | 26 | 0 |
| full->repeat | 14 | 0 | 26 | 0 |
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

Actual calls **3**; unique input fingerprints **3**; usage missing **1**. Separate card/repeat calls intentionally share exact requests and have independent local execution IDs. Physical calls and unique inputs are not interchangeable.

Known input tokens 85,665, including 19,456 cached; output 2,971, including 171 reasoning; known total **88,636**. Subsets are not added twice. Missing usage is unknown, not zero. Local accounting is not an invoice or a net end-to-end savings measurement; extracting these cards incurred prior-study cost. Requested ID `gpt-6-sol`; resolved model unavailable.

Stopped on:
```json
{
  "group": "card",
  "person": "t35c",
  "reason": {
    "kind": "model_or_format_failure",
    "stage": "card"
  }
}
```
No later slot ran; this proposal is closed without replenishment.

```sh
python benchmarks/frozen384-v1/check.py
```

The offline checker reconstructs the unchanged cards, exact frozen plan/requests, original answer/checkpoint hashes, execution identities, repeat inputs, usage, every score, qualification, paired loss and disagreement. Original failed checkpoints are retained if present. Hashes detect inconsistency, not provider-signed attestation. Mock corruption fixtures are labelled and never counted as real models.

No human, PRISM or private user trajectory was sent. This is not real-person fidelity, latent-rule generalization, historical recall, cross-vendor or runtime-harness portability, humor validation, independent population accuracy or likelihood-based relative information gain.
