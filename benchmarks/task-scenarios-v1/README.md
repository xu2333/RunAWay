# Source-grounded task scenarios — offline calibration, not a model result

This bank prepares the next test of **whose decision a tiny memory preserves**.
The previous [unchanged-card result](../question-contract-diagnostic-v1/MEASURED.md)
changed from 11/12 to 12/12 after a post-hoc task clarification. Here the task is
explicit before any model answers exist. Nothing replaces that earlier wording,
reference or score. No model has generated or read these new sources or cards.

There are four fictional settings: community repair, field sampling, community
cooking and ensemble rehearsal. Each has two people with opposing choices,
recorded execution orders and past states. Both see exactly the same questions.
An assistant suggests accepting a new arrangement; one person remains undecided,
the other explicitly accepts. Acceptance is actually in that question's answer
space, so adopting an assistant suggestion can produce a detectable scored error.

| Fixed design | Count |
|---|---:|
| Profiles / dependent authored template families | 8 / 4 |
| Short, explicit source messages | 48 |
| Person/case endpoints | 40 |
| Known / unknown endpoints | 28 / 12 |
| Distinct public forms / person-form combinations | 40 / 80 |
| Planned reads × option orders per case | 2 × 2 |
| Baseline answer slots | 160 |
| One-span source interventions | 40 |
| Full-bank answer slots across interventions | 800 |

Each person has five cases: a future choice in a decided condition, an undecided
condition, recorded execution order, a past fact, and a commitment. There are
16 choice cases and eight each of the other three task roles. A full option
name containing “先…” is a future scheme label; execution uses a separate
explicit past record. The sources are deliberately short calibration material,
not a new long-history compression frontier, naturalistic user study or holdout.
Exact canonical character lengths are in `design.json`; they are not token sizes.

`corpus.py` uses the existing offline authoring validator. Every reference has a
user-source quote. Every case also has a reversible edit of exactly one user
span, a declared different reference inside the same options+U, and unchanged
full ten-form question packet, not just the two target forms. This holds question
context and quantity constant between baseline and intervention. For example, undecided commitment can become explicit
acceptance while the assistant's recommendation stays fixed. **These are authored
source changes, not observed compressor damage or independently verified semantic
transitions.** Reversal and quote checks cannot establish truth or entailment.

`check.py` scores four answers strictly per fixed case: one wrong answer loses
that case; absent answers remain in the denominator. It rejects duplicate reads,
foreign questions/people, extra fields and positional A/B answers. Supply literal
labels or U. The optional transition score requires both the original reference
and the changed-source reference over both reads and orders. These 40 transitions
depend on the baseline cases; they are not another 40 independent observations.
Non-target preservation is reported separately on 160 dependent case/intervention
combinations; it requires all four baseline and all four changed-source answers
to retain that other case's author reference. All 800 intervention answer slots
remain planned even if records are missing; 160 of those target the edited case.
The scorer cannot verify response authenticity, a budget or service execution.

Offline fixture calibration produces:

| Constructed response vector — not a model response | Strict cases |
|---|---:|
| Authored reference vector | 40/40 |
| Always U | 12/40 |
| Declared faulty-answer vector | 0/40 |
| Paired person's reference vector | 8/40 |

The transition instrument accepts the two authored correct vectors at 40/40 and
rejects unchanged baseline answers at 0/40. This proves the scoring instrument
distinguishes those supplied vectors; it is **not observed model fidelity**.
Wrong-person rescoring reuses authored labels and is dependent calibration.

## Files and isolation

- `sources.synthetic.json`: raw fictional conversations, keyed by person.
- `questions.public.json`: task text and both option orders, keyed by person.
- `author-reference.synthetic.json`: authored labels, anchors, witnesses and pairs.
- `source-interventions.synthetic.json`: edited sources **and author references**.
- `design.json` and `fixture-calibration.json`: counts, hashes, limits and fixture scores.

All files are public because all people are fictional. Public availability does
not make author references legitimate model inputs. For later extraction use
`encoder_packet(person)` (own raw sources only); for reading use
`reader_packet(person, memory)` (supplied memory plus own questions only).
`intervention_packet(person, case)` returns edited sources and the same complete
ten-form question packet separately, without the reference/guide. It does not combine them into an
extraction request. Do not send either author-reference artifact to a model.
These helpers return values only: no backend, network call or service grant.

## Reproduce or score locally

```sh
python benchmarks/task-scenarios-v1/check.py
python -m unittest discover -s tests -p test_task_scenarios.py -v
python benchmarks/task-scenarios-v1/check.py --score baseline-records.json
python benchmarks/task-scenarios-v1/check.py --score baseline-records.json --transitions changed-source-records.json
```

Baseline records are a list of `{profile, read_repeat, answers}` objects, where
`read_repeat` is 0 or 1 and `answers` maps public question IDs to literal labels
or U. Transition records also require `case` (the source edit's target), and use
the same complete ten-question bank, including non-target questions. Missing records are allowed and reported, never removed from the
planned denominators. `--write` explicitly regenerates fictional local artifacts;
the default command verifies byte-for-byte reconstruction without writing.

Nine instrument tests cover reproducible artifacts, opposing pairs, single-span
edits, task/role distinctions, packet isolation, discriminating fixtures,
fixed missing denominators, invalid records and frozen-answer transition failure.
New model/API calls: **0**. Existing call scopes remain closed; there is no new
experiment authority, independent semantic review or production-default change.
Any later empirical study still needs its exact requests, budget, controls,
producer/reader accounting and approval frozen separately before execution.
