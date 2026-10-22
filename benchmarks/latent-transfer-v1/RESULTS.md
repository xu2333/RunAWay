# New-person finite-family transfer results

Fixed result: **complete**. 31/31 physical executions; 31 responses completed; 0 dependent slots skipped.

Frozen implementation `4457e948e9e6fd4e72d81cdbeb88730a9a944b26`; proposal `6e44ba49faef73af58b9e0851ec9e34e0bd62ae4049099f804c97e24b37d7de4`. Six new fictional source histories; after these outcomes this corpus is consumed. No re-extraction, repair, sample removal or additional call was selected.

**Later standalone removal check: the same six cards fall to 80/102 while
contemporary full remains 102/102. The 102/102below is conditional on the shared
decoder, not standalone fidelity.** [Removal results](../standalone-latent-v1/RESULTS.md).

## Qualification before attribution

```json
{
  "contemporary_full_qualified": true,
  "retention_interpretable": true,
  "strict_transport_pass": true,
  "identity_specificity_verified": true
}
```

Full qualifies only at 102/102 with no missing answers and personal-known (full-minus-none) / 43 >= .25. Only a qualified full makes compression retention interpretable. Strict transport also requires both own and wrong-against-donor repeat at 102/102; identity specificity requires lower wrong-target personal-known accuracy. This is a finite gate, not a population stability estimate.

## Every planned arm

| Arm | Known / 55 | Unknown / 47 | Personal known / 43 | Structural known / 12 | All / 102 | Missing |
|---|---:|---:|---:|---:|---:|---:|
| none | 17 | 46 | 5 | 12 | 63 | 0 |
| full | 55 | 47 | 43 | 12 | 102 | 0 |
| own | 55 | 47 | 43 | 12 | 102 | 0 |
| tail | 27 | 47 | 15 | 12 | 74 | 0 |
| wrong | 26 | 35 | 14 | 12 | 61 | 0 |
| wrong_against_donor | 55 | 47 | 43 | 12 | 102 | 0 |

Every person/scene needs both option positions correct. All missing cases stay in planned denominators. The one no-memory response is scored against six people, not six independent calls. Always-U scores zero known and 47 unknown correct. The public family alone determines 12 known cases; those are never personal-memory gains. An ideal uninformed decoder scores 59/102. Thirty unknowns concern public scope/vocabulary boundaries, separately from the harder 17 policy/partial/absent-option unknowns.

## Held-out feature combinations and partial descriptions

| Arm | Cohort | Known | Unknown | Personal known | Missing |
|---|---|---:|---:|---:|---:|
| none | observed_paraphrase | 0/18 | 0/0 | 0/18 | 0 |
| none | heldout_combination | 17/26 | 3/4 | 5/14 | 0 |
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
| own | heldout_combination | 26/26 | 4/4 | 14/14 | 0 |
| own | partial_features | 9/9 | 9/9 | 9/9 | 0 |
| own | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| own | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| own | action_not_offered | 2/2 | 4/4 | 2/2 | 0 |
| tail | observed_paraphrase | 6/18 | 0/0 | 6/18 | 0 |
| tail | heldout_combination | 18/26 | 4/4 | 6/14 | 0 |
| tail | partial_features | 3/9 | 9/9 | 3/9 | 0 |
| tail | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| tail | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| tail | action_not_offered | 0/2 | 4/4 | 0/2 | 0 |
| wrong | observed_paraphrase | 4/18 | 0/0 | 4/18 | 0 |
| wrong | heldout_combination | 19/26 | 0/4 | 7/14 | 0 |
| wrong | partial_features | 3/9 | 3/9 | 3/9 | 0 |
| wrong | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| wrong | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| wrong | action_not_offered | 0/2 | 2/4 | 0/2 | 0 |
| wrong_against_donor | observed_paraphrase | 18/18 | 0/0 | 18/18 | 0 |
| wrong_against_donor | heldout_combination | 26/26 | 4/4 | 14/14 | 0 |
| wrong_against_donor | partial_features | 9/9 | 9/9 | 9/9 | 0 |
| wrong_against_donor | outside_feature_vocabulary | 0/0 | 18/18 | 0/0 | 0 |
| wrong_against_donor | unobserved_domain | 0/0 | 12/12 | 0/0 | 0 |
| wrong_against_donor | action_not_offered | 2/2 | 4/4 | 2/2 | 0 |

Five complete combinations never appeared in each source: 30 person/scene cases, 26 known and 4 unknown. Only 14 of those knowns require personal observations; 12 are family-wide invariants. Partial-feature cases contain nine known and nine unknown outcomes, so blindly abstaining on every missing field cannot pass. The source histories, public candidate family, held-out combinations and oracle were frozen before service calls. This is not an external naturalistic or human holdout.

## New people and evidence limits

| Person | Compatible rule IDs (author-side audit only) | Full / 17 | Own / 17 | Tail / 17 | Wrong target / 17 |
|---|---|---:|---:|---:|---:|
| u06k | 1,7 | 17 | 17 | 13 | 8 |
| u19m | 2 | 17 | 17 | 12 | 11 |
| u42r | 3,8 | 17 | 17 | 13 | 11 |
| u58s | 4 | 17 | 17 | 12 | 10 |
| u73v | 5 | 17 | 17 | 10 | 10 |
| u85w | 6 | 17 | 17 | 14 | 11 |

Four histories identify one rule. Two identify a pair of rules that agree on every observed choice but disagree on two unobserved combinations. Their gold is U on those combinations even when the author knows the generating rule. Guessing that author rule is overconfidence, not faithful recovery. Source-only extraction never receives these version IDs, author labels, queries or gold.

## Unknown reasons

| Arm | Reason | Correct / planned | Missing |
|---|---|---:|---:|
| none | personal_known | 5/43 | 0 |
| none | structural_known | 12/12 | 0 |
| none | policy_not_identifiable | 3/4 | 0 |
| none | partial_ambiguity | 9/9 | 0 |
| none | outside_feature_vocabulary | 18/18 | 0 |
| none | unobserved_domain | 12/12 | 0 |
| none | known_action_not_offered | 4/4 | 0 |
| full | personal_known | 43/43 | 0 |
| full | structural_known | 12/12 | 0 |
| full | policy_not_identifiable | 4/4 | 0 |
| full | partial_ambiguity | 9/9 | 0 |
| full | outside_feature_vocabulary | 18/18 | 0 |
| full | unobserved_domain | 12/12 | 0 |
| full | known_action_not_offered | 4/4 | 0 |
| own | personal_known | 43/43 | 0 |
| own | structural_known | 12/12 | 0 |
| own | policy_not_identifiable | 4/4 | 0 |
| own | partial_ambiguity | 9/9 | 0 |
| own | outside_feature_vocabulary | 18/18 | 0 |
| own | unobserved_domain | 12/12 | 0 |
| own | known_action_not_offered | 4/4 | 0 |
| tail | personal_known | 15/43 | 0 |
| tail | structural_known | 12/12 | 0 |
| tail | policy_not_identifiable | 4/4 | 0 |
| tail | partial_ambiguity | 9/9 | 0 |
| tail | outside_feature_vocabulary | 18/18 | 0 |
| tail | unobserved_domain | 12/12 | 0 |
| tail | known_action_not_offered | 4/4 | 0 |
| wrong | personal_known | 14/43 | 0 |
| wrong | structural_known | 12/12 | 0 |
| wrong | policy_not_identifiable | 0/4 | 0 |
| wrong | partial_ambiguity | 3/9 | 0 |
| wrong | outside_feature_vocabulary | 18/18 | 0 |
| wrong | unobserved_domain | 12/12 | 0 |
| wrong | known_action_not_offered | 2/4 | 0 |
| wrong_against_donor | personal_known | 43/43 | 0 |
| wrong_against_donor | structural_known | 12/12 | 0 |
| wrong_against_donor | policy_not_identifiable | 4/4 | 0 |
| wrong_against_donor | partial_ambiguity | 9/9 | 0 |
| wrong_against_donor | outside_feature_vocabulary | 18/18 | 0 |
| wrong_against_donor | unobserved_domain | 12/12 | 0 |
| wrong_against_donor | known_action_not_offered | 4/4 | 0 |

## Every loss and independent donor-card repeat

| Contrast | Known lost | Known recovered | Unknown lost | Unknown recovered |
|---|---:|---:|---:|---:|
| full->own | 0 | 0 | 0 | 0 |
| full->tail | 28 | 0 | 0 | 0 |
| tail->own | 0 | 28 | 0 | 0 |
| own->wrong | 29 | 0 | 12 | 0 |

Actual own/donor-repeat answer changes among mutually observed cases: **0**. Missing reads are not called observed changes. The wrong-person request is byte-identical to the donor's own request, with a new local execution identity and different target scoring. It is an independent read, not an extra unique input or a hidden target identifier.

[All actual errors, missed cases and rotated choices](LOSSES.md). Original IDs and labels are retained in `observed.synthetic.json`. Paired loss counts include missing outputs as availability losses, not observed semantic hallucinations. Relative full/card comparisons cannot isolate compression loss when full fails qualification.

## Validity, complete-card size and shared cost

| Person | Card chars | Source plain text | Source role JSON | Shared decoder chars | Card + decoder chars | Matched raw-tail chars |
|---|---:|---:|---:|---:|---:|---:|
| u06k | 378 | 1234 | 2305 | 619 | 997 | 378 |
| u19m | 387 | 1234 | 2305 | 619 | 1006 | 387 |
| u42r | 371 | 1234 | 2305 | 619 | 990 | 371 |
| u58s | 336 | 1234 | 2305 | 619 | 955 | 336 |
| u73v | 296 | 1234 | 2305 | 619 | 915 | 296 |
| u85w | 314 | 1234 | 2305 | 619 | 933 | 314 |

Valid products **6/6**; invalid products **0**. A card failing exact source/role/chronological-reference or whole-budget validation is never repaired or substituted.

[Complete cards and portable JSON](CARDS.md). The raw baseline is a prespecified suffix of role-labelled source text with a fixed incomplete-fragment warning, exactly matched to actual card characters. It is not token-matched or an ideal LLM summary. It uses more or fewer tokens depending on text; input usage remains public.

The 619-character public decoder is common to every reader arm, including no-memory and raw-tail controls. It supplies a finite rule family and explicit inference/scope assumptions; this is not stock-reader behavior without it. Decoder + card size is shown to avoid hiding the shared-codebook cost. Other fixed request/system/schema text also exists, so that sum is not total service input. Source history itself includes rule definitions, and metadata removal must not be called equivalent semantic compression.

## Calls, cost and reproduction

Actual physical executions **31**; unique request fingerprints **25**; usage missing **0**.

Known input tokens **376,329**, including 85,888 cached; output **31,272**, including 15,340 reasoning; known total **407,601**. Subsets are not added twice. Unknown usage is not zero. These are local records, not an invoice, token/money cap or end-to-end savings claim. Requested `gpt-6-sol`; resolved identity unavailable.

```sh
python benchmarks/latent-transfer-v1/check.py
```

The offline checker reconstructs source-bound products, equal-character raw tails, rule/version/scenario hand-oracles, exact requests, original answer/checkpoint hashes, execution identities, usage, guard observations, all scores, gates, losses and independent repeated-answer changes. Hashes detect inconsistency, not provider-signed attestation. Mock corruption tests never count as actual model evidence.

Owned temporary macOS idle-sleep assertions are verified before every invocation. No permanent power setting, deadline or retry changes. Manual sleep/lid closure and service stalls remain possible.

No human trajectories, PRISM data or private user feedback were sent. This controlled finite-family result cannot establish unconstrained latent personality, real-person fidelity, population generalization, cross-vendor/runtime-harness loading, humor quality, likelihood-based relative information gain or net economic savings.

## No-memory protocol diagnostic (posthoc, offline only)

A decoder that obeys the no-history uncertainty rule scores 59/102 on this pool;
this is a **contract-conforming reference, not an accuracy upper bound**. The
frozen proposal's phrase "expected ceiling" was imprecise; data and gates were
not changed to repair that wording. Lucky source-free guesses can score higher
against person-conditioned gold while violating the public uncertainty contract.

Actual none scores 63/102 and gets
5/43 personal-known cases
right. An offline diagnostic added after observing the baseline checks that shared
response against all-eight-rule gold: 16/17 scenes
conform. It is descriptive, not a replacement gate or new model call. Every
mismatch is retained in `none_decoder_diagnostic` in the original-response export.
Full qualification and gains use the actual none response, not a forced-zero or
idealized baseline.
