# Fresh everyday-decision results

The separately authorized scope is **closed**: 45 actual local inference attempts,
45recorded inference children, no invalid products, skipped readers,expired slots
or missing usage. Four new full-source controls passed 16/16 own cases in both
orders, with a known-choice gain over the same new no-memory control,before any
extraction. No repair or retry was made. The [original prospective protocol](README.md)
and its unapproved preparation metadata remain unchanged.

## Joint retention

All 2 generations × 2 reads × 2 orders must match for a case to count. These repeated
answers are not independent people;the denominator is 64 unique person/cases/view.

| Endpoint | Compact card | Own equal-character raw tail |
| --- | ---: | ---: |
| All cases | 64/64 | 28/64 |
| Known choices | 48/48 | 12/48 |
| Unrecorded targets / unknown | 16/16 | 16/16 |
| Condition composition | 16/16 | 4/16 |
| Missing cases | 0/64 | 0/64 |

Every cohort has 16 cases. Cards retain 16/16 ordinary, 16/16 changed-condition,
16/16 compositional-override and 16/16 unrecorded-target cases. Tails retain 4/16,
4/16, 4/16 and 16/16 respectively. Each card generation separately retains 64/64;
tails retain 30/64 in generation 0 and 28/64 in generation 1. Card answer vectors
are identical across generations on these cases.

## Losses and boundary sensitivity

All 36 joint tail losses concern known choices. Thirty-four answer U in all eight
positions;two answer correctly in all four generation 0 positions and U in all four
generation 1 positions. These two are `bryn/support_2` and `dune/support_2`.
Their tails change with their own card lengths (737→730 and 750→717 characters),
so this is **not** evidence of instability on an identical reader input.
The shorter suffixes cut further into the supporting override sentence. This
boundary observation is descriptive,not a causal ablation or an optimal-tail
comparison. The public replay lists every failed case and its eight answers,
including cohort and systematic/intermittent-unknown classification.

## Whole-card lengths

| Person | Generation 0 | Generation 1 |
| --- | ---: | ---: |
| auri | 735 | 694 |
| bryn | 737 | 730 |
| cato | 722 | 657 |
| dune | 750 | 717 |

All eight cards fit 657–750 Unicode characters (mean 717.75),including name,
tagline, guide and all public text. Each source contains 2,229–2,235 text characters
before role labels. This is not a token compression ratio. Character-matched
suffixes are not token-matched or an optimized raw-history selection.

## Reported usage

| Stage | Actual attempts | Reported input + output tokens |
| --- | ---: | ---: |
| No memory | 1 | 12,575 |
| Full source | 4 | 57,474 |
| Extraction | 8 | 108,575 |
| Card reads | 16 | 212,156 |
| Tail reads | 16 | 211,360 |
| Total | 45 | 602,140 |

Total input 559,893 and output 42,247. Cached input 64,000 and reasoning output 4,317
are reported subsets,not extra tokens to add again. These counts include the
whole controlled evaluation,not a one-user card cost,and are not dollar prices.
The requested model is `gpt-6.1-sol`;resolved identity is unreported. Local
preflight reported `codex-cli 0.165.0-alpha.1.2`, a changed runtime since the prior
repeat. Expected CLI options were checked before activation and the new binary
was pinned throughout; scientific requests,code and frozen input stayed fixed.
Runtime metadata is not independent service/model attestation.

## Reproduce and inspect

```sh
python3 -B benchmarks/fresh-decision-v1/check.py
python3 -B scripts/replay_fresh_decision.py
python3 -B -m unittest discover -s tests -p test_fresh_decision_evidence.py -v
```

[Portable values](measured.synthetic.json) and [checksum](measured.synthetic.sha256)
contain only reviewed fictional inputs,exact requests,raw model answers,public
cards, safe usage/counter fields and derived status. Replay reconstructs the
controller and verifies control gates, both generations, all denominators, own-tail
construction, artifacts and usage with an injected archived backend. It makes
zero new model calls. Nine damage/classification tests cover corrupted inputs,
responses, artifacts, schedules, counters, claims and missing-vs-U handling. The
private audit also confirmed 14 previous sealed observation sets unchanged and
that the owned temporary guard had exited. Grants, runtime paths, credentials,
provider envelopes and real-person data are excluded from this export.

## What this supports

The fixed method retains these four newly authored fictional trajectories and
explicit condition changes under two separately generated cards/person. It adds
source-controlled evidence beyond the previously consumed two-domain examples.
The 36 tail losses are information absent or incomplete in the selected suffix,
not proof that a model lacks the ability to read the full source.

The author knew prior failures, and generated sources and reference together.
Four people form two opposite pairs; 64 cases and repeated reads are correlated.
The unknown targets are absent tool/place preferences or execution facts, not a
complete test of partially specified conditions or withdrawn guarantees. This
is **not** independently authored holdout,independent semantic gold, real-user
fidelity, population stability, cross-provider transfer, RIG or an optimal budget
frontier. Passing does not promote a production default or close older losses.
Old observations, references and closed call scopes remain unchanged.
