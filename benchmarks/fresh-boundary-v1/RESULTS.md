# Fresh-user end-to-end results

Fixed service result: **complete**. This is a four-user authored synthetic pilot; it does not establish real-person fidelity.

The data, oracle, contracts, code and 56-slot plan were frozen before service execution (code commit `4319246`, proposal `c15726444c7112fcd8079784d2a2ae90de221d84792e0eaa8b0cebe426d294ba`). No favorable draw, case deletion, extractor repair or additional call was selected.

Both Sol readers retain all 40 known and 88 unknown cases in this draw. Luna remains unqualified and unstable. In its scoped repeat, unknown improves to 88/88 while known drops to 32/40; this is not an unknown-judgment fix. Standard remains the default. The experiment validates a small automatic pipeline, not aggressive semantic compression.

## Every reader arm

| Requested model / arm | Known / 40 | Unknown / 88 | Scope / 128 | Scope + choice / 128 | Missing choice cases |
|---|---:|---:|---:|---:|---:|
| luna_scoped_full | 37 | 86 | 125 | 122 | 0 |
| luna_scoped_none | 0 | 88 | 80 | 80 | 0 |
| luna_scoped_own | 34 | 85 | 120 | 116 | 0 |
| luna_scoped_own_repeat | 32 | 88 | 117 | 117 | 0 |
| luna_standard_full | 35 | 81 | — | — | 0 |
| luna_standard_none | 0 | 88 | — | — | 0 |
| luna_standard_own | 35 | 85 | — | — | 0 |
| luna_standard_own_repeat | 34 | 87 | — | — | 0 |
| luna_standard_wrong | 6 | 80 | — | — | 0 |
| sol_scoped_full | 40 | 88 | 128 | 128 | 0 |
| sol_scoped_none | 0 | 88 | 80 | 80 | 0 |
| sol_scoped_own | 40 | 88 | 128 | 128 | 0 |
| sol_standard_full | 40 | 88 | — | — | 0 |
| sol_standard_none | 0 | 88 | — | — | 0 |
| sol_standard_own | 40 | 88 | — | — | 0 |
| sol_standard_wrong | 4 | 80 | — | — | 0 |

Each person/scene is correct only when all tested option positions are correct. The 88 unknowns include 64 unobserved-domain cases. That easy subset is reported separately; always choosing U scores 88/88 unknown and 0/40 known. Scope is scored against the target history, including for the no-memory controls. Scope reports are not used to repair choices.

## Qualification and repeated draws

| Requested model / reader | Full qualifies | Own strict choice pass | Own scope + choice pass | Stable transfer gate |
|---|---|---|---|---|
| luna_standard | False | False | False | False |
| luna_scoped | False | False | False | False |
| sol_standard | True | True | False | True |
| sol_scoped | True | True | True | True |

Full qualification is model/contract specific. It requires all 128 choice cases correct, no missing outputs and a known full-minus-none gap of at least .25; scoped also requires all scope+choice cases correct. The stable transfer gate requires qualified full history, perfect own-card results and both independent Luna own draws. A failed full control means card-minus-full cannot isolate compression loss. Sol has one card draw per reader, so a pass there remains finite pilot evidence, not a stability estimate.

## Unknown reasons and known controls

| Arm | Known / 40 | Unobserved domain / 64 | Outside conditions / 16 | Ambiguous possibilities / 4 | Known action absent / 4 |
|---|---:|---:|---:|---:|---:|
| luna_scoped_full | 37 | 62 | 16 | 4 | 4 |
| luna_scoped_none | 0 | 64 | 16 | 4 | 4 |
| luna_scoped_own | 34 | 62 | 16 | 4 | 3 |
| luna_scoped_own_repeat | 32 | 64 | 16 | 4 | 4 |
| luna_standard_full | 35 | 60 | 15 | 4 | 2 |
| luna_standard_none | 0 | 64 | 16 | 4 | 4 |
| luna_standard_own | 35 | 62 | 16 | 4 | 3 |
| luna_standard_own_repeat | 34 | 64 | 16 | 4 | 3 |
| luna_standard_wrong | 6 | 64 | 16 | 0 | 0 |
| sol_scoped_full | 40 | 64 | 16 | 4 | 4 |
| sol_scoped_none | 0 | 64 | 16 | 4 | 4 |
| sol_scoped_own | 40 | 64 | 16 | 4 | 4 |
| sol_standard_full | 40 | 64 | 16 | 4 | 4 |
| sol_standard_none | 0 | 64 | 16 | 4 | 4 |
| sol_standard_own | 40 | 64 | 16 | 4 | 4 |
| sol_standard_wrong | 4 | 64 | 16 | 0 | 0 |

## Paired regressions

| Contrast | Known lost | Known recovered | Unknown lost | Unknown recovered |
|---|---:|---:|---:|---:|
| luna_standard_full->luna_standard_own | 4 | 4 | 0 | 4 |
| luna_scoped_full->luna_scoped_own | 4 | 1 | 3 | 2 |
| luna_standard_own->luna_scoped_own | 3 | 2 | 1 | 1 |
| luna_standard_own_repeat->luna_scoped_own_repeat | 6 | 4 | 0 | 1 |
| sol_standard_full->sol_standard_own | 0 | 0 | 0 | 0 |
| sol_scoped_full->sol_scoped_own | 0 | 0 | 0 | 0 |
| sol_standard_own->sol_scoped_own | 0 | 0 | 0 | 0 |

Every affected person/case ID, exact rotated answers and scope reports are retained in `observed.synthetic.json`. Paired counts describe these finite draws; cases, option rotations and the two contrasting pairs are not independent population samples.

## Wrong-person controls

| Requested model | Correct for target / 128 | Correct for donor / 128 |
|---|---:|---:|
| luna | 86 | 119 |
| sol | 84 | 128 |

All people receive the same public questions, so a standard wrong-person request is byte-identical to an own-person request for the donor. These are additional independent executions with different target scoring, not new unique inputs or evidence that a hidden person identifier was transmitted. The Luna card repeats also reuse exact requests.

## Automatically extracted cards

| Synthetic user | Name | Complete card characters | Role-labelled history characters | Plain source-text characters | Card/history character ratio |
|---|---|---:|---:|---:|---:|
| t04a | 小绒尺 | 442 | 1832 | 669 | 0.241 |
| t11b | 小核桃 | 489 | 1837 | 674 | 0.266 |
| t35c | 团团小路灯 | 458 | 1747 | 584 | 0.262 |
| t92d | 分岔糯米团 | 455 | 1759 | 596 | 0.259 |

[Read/copy the cards or use their portable JSON files](CARDS.md). Character ratios include role/source JSON metadata in the history denominator; plain source-text sizes are also shown to avoid attributing metadata removal to preference compression. These are not token ratios, end-to-end service savings or proofs of semantic completeness. Imports use the actual production `bind` path; backend execution provenance is recorded separately in the original service ledger.

## Cost and reproduction

Actual service executions: **56**; unique request fingerprints: **40**; usage missing: **0**.

Known input tokens: 1,837,016 (including 325,376 cached); output: 98,772 (including 14,967 reasoning); total: **1,935,788**. Subsets are not added twice. These are local records, not an invoice. Requested identities only; resolved server models are unavailable.

```sh
python benchmarks/fresh-boundary-v1/check.py
```

This reproduces every recorded score/gate, source-bound product and request/answer/checkpoint binding without model calls. It checks execution identities, repeated inputs, usage provenance and fixed ordering. Hashes detect inconsistency; they are not provider-signed attestations. Mocks used in corruption tests are explicitly marked and never counted as real calls.

This measures reconstruction of source-supported choices under a finite authored world. It does not measure useful analogy to unrecorded domains, real-person fidelity, romantic compatibility, runtime harness portability, cross-vendor generalization, humor quality, population confidence intervals or likelihood-based relative information gain. No actual user history, PRISM data or user feedback was sent in this run.

## Post-hoc offline packing probe

After the fixed study finished, the same generated answers were re-exported at
768, 512, 400, 384, 320 and 300 characters, with zero additional model calls.
The current lossless renderer fits two of four at 400 (397 and 398 characters);
none fit at 384 or below without rejection. This is a result for this renderer
and these answers, not a proof of an optimal minimum description length. The
smaller glossary variants were **not tested for behavioral fidelity** and are
not substituted into any scored arm. The tested cards remain 442–489 characters.
See `packing-frontier.synthetic.json` for exact outputs and rejection reasons.

The role-labelled JSON histories are 1,747–1,837 characters, but their plain
source text is only 584–674. The tested cards retain approximately 66–78% of that
plain-text length. This pilot establishes end-to-end operation and scope tests;
it does not yet establish large semantic compression ratios on long trajectories.
