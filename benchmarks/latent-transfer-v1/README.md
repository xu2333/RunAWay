# New people and identifiable rule transfer

[Recorded results](RESULTS.md) · [Complete cards](CARDS.md) ·
[Exact shared decoder](CODEBOOK.md) · [Every actual error](LOSSES.md)

**31/31 calls completed. Full history, own cards and independent donor-card
reads each score 102/102. Equal-character raw tails score 74/102; wrong-person
cards score 61/102 against the target. All 14 person-dependent known cases in
unseen combinations pass. These results require the shared decoder below.**

This moves beyond recovery of six explicitly recorded latest choices. Six new
fictional people each provide three effective decisions, with obsolete user
choices, unendorsed assistant alternatives and tool records kept distinct. Five
complete feature combinations never appear in those histories. Two people remain
compatible with two different rules; the oracle preserves that uncertainty even
though the experiment author knows the hidden generating rule.

This is a **controlled shared-codebook inference task**, not unconstrained
personality inference or default-reader behavior without the codebook. Eight
public candidate rules trade off external transmission, setup effort and full
undo for low-risk personal note processing. Their binary vocabulary and domain
scope are explicit. Every reader gets the same 619-character decoder contract,
including no-memory and wrong-person controls. Its overhead is reported separately
from each 512-character maximum personal card; it is not free compression.

The truth oracle enumerates every rule compatible with effective observations,
then every possible feature state in a query. It returns an action only if all
possibilities agree and the action is offered. Independent fixed hand tables
check all 64 rule/state results, six version spaces and 102 person/scene labels.
For the two ambiguous people, held-out states can have a definite hidden author
answer while the evidence-based gold is U. Guessing that hidden answer is wrong.

| Cohort | Cases | Known | Unknown | Personal known | Structural known |
|---|---:|---:|---:|---:|---:|
| Observed feature states, paraphrased | 18 | 18 | 0 | 18 | 0 |
| Five unseen complete combinations | 30 | 26 | 4 | 14 | 12 |
| Partial feature descriptions | 18 | 9 | 9 | 9 | 0 |
| Feature values outside the binary vocabulary | 18 | 0 | 18 | 0 | 0 |
| Unobserved domains | 12 | 0 | 12 | 0 | 0 |
| Known action absent from offered choices | 6 | 2 | 4 | 2 | 0 |
| All planned | 102 | 55 | 47 | 43 | 12 |

There are 17 scenes, each tested in both option orders: 34 questions/person.
Rotations and related scenes are correlated checks, not independent population
samples. Always-U gets 47 unknowns and zero knowns right. Even without personal
history the public family determines 12 known cases; those are never credited as
personal-memory gains. An ideal uninformed decoder gets 59/102 overall.

## Fixed maximum: 31 physical service calls

- Shared no-memory1 and contemporary full-history6.
- One unchanged production source-support extraction/person at **512 complete
  Unicode characters**, including header, guide, name and unknown limits: six.
- Own-card6, character-matched raw-history tail6, and wrong-person6.

All request `gpt-6-sol`; resolved server identity is unavailable. Extractors see
only that person's source history, with common rule definitions and actual
observations. They never see evaluation questions, gold, version-space labels or
the author's hidden generating rule. Reader requests use the standard production
builder plus the fixed shared decoder contract and absent-option instruction.

Raw-tail controls use exactly as many Unicode characters as that person's actual
card, including a fixed warning about incomplete leading text and user roles.
They are **character-matched, not token-matched**. This is a prespecified recency
baseline, not a model-generated ideal summary. If a card is invalid, dependent
own, tail and wrong-person reads are skipped but stay in all planned denominators.
There is no fallback or extraction repair.

All people share the same public queries. A wrong-person request is identical to
an own request for the donor, but is a new execution. Both target-gold and
donor-gold results are retained; donor-gold acts as an independent read of each
card. Calls and unique request fingerprints are reported separately.

Contemporary full qualifies only at 102/102, missing0, and a personal-known
full-minus-none accuracy gap >= .25. Retention is interpretable only with this
qualified control. The strict transport gate also requires own and donor-repeat
reads at 102/102 with no missing cases. Identity specificity additionally requires
wrong-person personal-known accuracy below own. Each case requires both option
orders correct. All actual wrong answers, missing cases, paired losses and
repeated-answer changes remain public. A gate failure never deletes a sample.

The plan is single-use. Guard ownership, source/request binding, schema/decode,
transport or unknown-usage failure stops all later calls. Valid-schema extraction
rejected by evidence/budget validation is an invalid product: skip only its
three dependent reads, keep the independent slots. No retry, resume, truncation,
deadline extension, sample replacement, best-of selection or replenishment.

```sh
python benchmarks/latent-transfer-v1/world.py
python benchmarks/latent-transfer-v1/study.py prepare --out NEW_DIRECTORY
python benchmarks/latent-transfer-v1/study.py preflight --out NEW_DIRECTORY
python scripts/with_awake.py -- python benchmarks/latent-transfer-v1/study.py run --out NEW_ACCEPTED_DIRECTORY
```

Preparation and preflight are offline. Real execution additionally needs matching
offline acceptance, runtime agreement, existing human authorization and an owned
macOS idle-sleep assertion before every call. Manual sleep/lid closure and service
stalls remain possible. The 31-call cap is not a token/money cap. Mock tests verify
plumbing only. After outcomes this corpus is consumed: it does not establish human
fidelity, population generalization, cross-vendor/runtime-harness portability,
likelihood information gain, open-ended taste induction or net end-to-end savings.

The observed no-memory response scored 63/102, above the 59/102 contract-conforming
reference, by guessing one underdetermined case and matching five profiles. That
reference is not an accuracy ceiling. See the labelled posthoc, zero-call
protocol diagnostic in RESULTS.md; primary gates use the actual response.

The next unmeasured question is standalone portability without the 619-character
family decoder. The family is an experimental assumption, not a product trait
taxonomy or a claim that all people belong to eight types.

**The removal ablation is now complete:** without the shared decoder, the same
cards score 80/102 against full 102/102, losing 22 known conclusions as abstentions.
The conditional 102/102must not be presented as standalone fidelity.
[Standalone results and diagnosis](../standalone-latent-v1/RESULTS.md).
