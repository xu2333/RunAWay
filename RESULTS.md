# What RunAWay has shown

**真人保真度尚未验证。Real-person fidelity is unverified.**

RunAWay can turn selected experiences into an editable, evidence-linked prompt. Whether that prompt usefully reproduces a real person's later choices remains an open question.

| Evidence | Observed result | What it supports |
| --- | --- | --- |
| Published PRISM pilot: 2 actual people, 4 later questions | Full history, no history, own card and wrong-person card all chose the same answers: 3/4 distinct questions correct, or 6/8 with two option orders | No demonstrated personalization gain; equal scores do not establish compression fidelity |
| Real writing-correction diagnostic: 1 consumed episode | Current task, available history and generic advice each score 0/1 under the frozen strict rubric; 61,379 reported tokens | No demonstrated history advantage; incomplete prior article context and target-aware study design limit interpretation |
| Four additional real creative-work corrections | Frozen history score: 0 confirmed + 1 ambiguous / 4; later owner-informed adjudication: 0/4 in all conditions; 129,250 reported tokens | The unresolved prediction did not match the owner clarification; no demonstrated history gain, no compression comparison |
| Real workflow correction with explicit earlier evidence | Current material, available history and generic guidance each score 0/1; manually selected earlier evidence is partial, not a strict hit; 155,141 reported tokens | Earlier evidence was present, but full history selected a different concern; no demonstrated history gain or compression comparison |
| Actual task delivery, one primary real case | Both history outputs explicitly retain the earlier input-capture requirement; both no-history outputs leave it unspecified. Primary case endpoint: 1/1 versus 0/1; 8 calls across primary and exploratory tasks, 129,759 reported tokens | One bounded history benefit in a design proposal; not device execution, compression fidelity, user adoption or independent generalization |
| [Short card on the real recording task](docs/results/real-recording-card-v1.md) | Card and full history each preserved timed input sequences in 2/2 plans, current-only 0/2. The 674-character card omitted the device timestamp detail. | One retrospective design task and one generated card |
| [Short card on a second real design task](docs/results/real-demo-learning-card-v1.md) | Concrete cross-game design appeared in 2/2 card, 1/2 history and 0/2 current-only plans. The 507-character card omitted an earlier continuous-control qualification. | Same owner and project, one new retrospective endpoint |
| Finite synthetic worlds | Several compression/reader pipelines preserve authored choices; others lose aliases, conditions or known choices | Useful regression and failure-localization tests; not real-person validation |
| Latest source-domain study | Both methods retain 94/94 authored cases, with no observed recovery or new loss; 749,984 reported service tokens | A measured null comparison on consumed development material, not evidence of user benefit |
| File and harness tooling | Local checks cover artifact integrity and managed project-file exports | Mechanical integrity; not proof that every harness loads a prompt or that models make the same decisions |

A post-hoc length-only audit agrees with PRISM ratings on 32/40 prepared questions and 3/4 pilot questions. This is a confound warning, not a preregistered model baseline. Repeated reads and option orders do not create more people or independent episodes.

An [offline history audit](docs/results/real-correction-history-audit-v3.md) found incomplete evidence citations but no corresponding omission from the four actual history inputs. It records why several additional candidates fail the stricter no-current-cue screen. The retained candidate was then tested in a [separate four-call diagnostic](docs/results/real-correction-evidence-v3.md); history still did not predict the observed correction. These findings do not isolate retrieval failure from competing priorities.

## The next evidence must come from real use

1. Freeze real tasks with explicit earlier owner constraints, preserving their original conditions and chronology. Check actual deliverables, not forecasts of later criticism. The [first task-delivery result](docs/results/real-task-history-v1.md) has one positive primary case; its exploratory setting constraint was satisfied equally by both conditions.
2. First test whether full history improves on no personal history. If that comparison has no useful signal, stop before running compression comparisons.
3. On qualifying episodes, compare the portable prompt with full history, count both recovered choices and new losses, and report cost. A 768-character target is not an acceptance requirement.
4. Keep a local ledger of which preference/version was accepted or corrected in which situation. Do not infer per-rule credit from whole-prompt feedback, or treat adoption as factual correctness.

The initial real-use study can be a clearly labeled single-person pilot. Generalization and a prospective holdout remain separate requirements. No new model experiment is authorized by this plan.

[Four-case follow-up](docs/results/real-correction-music-v2.md) · [Real correction diagnostic](docs/results/real-correction-signal-v1.md) · [Real pilot and limits](REAL-SCENARIO-PILOT.md) · [Synthetic failures and costs](REGRESSION-PROGRESS.md) · [Real-use protocol and feedback-ledger contract](docs/real-user-plan.md)

Historical reports and frozen evidence remain intact; their current locations are retained while references are audited. They are supporting records, not alternative first-time-user routes.
