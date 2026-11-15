# What RunAWay has shown

**真人保真度尚未验证。Real-person fidelity is unverified.**

RunAWay can turn selected experiences into an editable, evidence-linked prompt. Whether that prompt usefully reproduces a real person's later choices remains an open question.

| Evidence | Observed result | What it supports |
| --- | --- | --- |
| Published PRISM pilot: 2 actual people, 4 later questions | Full history, no history, own card and wrong-person card all chose the same answers: 3/4 distinct questions correct, or 6/8 with two option orders | No demonstrated personalization gain; equal scores do not establish compression fidelity |
| Real writing-correction diagnostic: 1 consumed episode | Current task, available history and generic advice each score 0/1 under the frozen strict rubric; 61,379 reported tokens | No demonstrated history advantage; incomplete prior article context and target-aware study design limit interpretation |
| Finite synthetic worlds | Several compression/reader pipelines preserve authored choices; others lose aliases, conditions or known choices | Useful regression and failure-localization tests; not real-person validation |
| Latest source-domain study | Both methods retain 94/94 authored cases, with no observed recovery or new loss; 749,984 reported service tokens | A measured null comparison on consumed development material, not evidence of user benefit |
| File and harness tooling | Local checks cover artifact integrity and managed project-file exports | Mechanical integrity; not proof that every harness loads a prompt or that models make the same decisions |

A post-hoc length-only audit agrees with PRISM ratings on 32/40 prepared questions and 3/4 pilot questions. This is a confound warning, not a preregistered model baseline. Repeated reads and option orders do not create more people or independent episodes.

## The next evidence must come from real use

1. Freeze real agent episodes with actual user corrections, preserving their original conditions and chronology. Keep later decisions outside the historical input.
2. First test whether full history improves on no personal history. If that comparison has no useful signal, stop before running compression comparisons.
3. On qualifying episodes, compare the portable prompt with full history, count both recovered choices and new losses, and report cost. A 768-character target is not an acceptance requirement.
4. Keep a local ledger of which preference/version was accepted or corrected in which situation. Do not infer per-rule credit from whole-prompt feedback, or treat adoption as factual correctness.

The initial real-use study can be a clearly labeled single-person pilot. Generalization and a prospective holdout remain separate requirements. No new model experiment is authorized by this plan.

[Real correction diagnostic](docs/results/real-correction-signal-v1.md) · [Real pilot and limits](REAL-SCENARIO-PILOT.md) · [Synthetic failures and costs](REGRESSION-PROGRESS.md) · [Real-use protocol and feedback-ledger contract](docs/real-user-plan.md)

Historical reports and frozen evidence remain intact; their current locations are retained while references are audited. They are supporting records, not alternative first-time-user routes.
