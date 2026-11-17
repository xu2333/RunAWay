# Does history change the actual work?

**No new model results yet. Real-person fidelity remains unverified.**

The previous diagnostics asked a model to predict a later user correction. That
measures which complaint it selects, not whether it can do useful work while
respecting earlier instructions. This protocol instead replays an actual task
and checks the resulting deliverable against an earlier, still-applicable owner
constraint. Previous observations and scores stay unchanged.

## Selection and comparison

Select a real text-delivery task with an explicit earlier owner statement. Review
the statement's scope, later revisions and the entire current context, including
assistant proposals. Exclude explicit restatements of the target constraint;
preserve indirect cues and report them. Never delete a revealing current message
to manufacture an advantage, or replace an unavailable media/device task with a
text proxy. History means all recoverable qualifying visible text before the
frozen cutoff, not an assertion of complete lifetime or multimodal history.

The first prepared pilot has two tasks from one owner's previously inspected
projects. One engineering-plan task is primary. One creative-writing task is
exploratory because its current subject matter may already suggest the target
boundary. They are reused retrospective sources, not unseen people or a holdout.
Original task answers were seen during screening but are excluded from requests;
references must be licensed by earlier owner statements, not later criticism.

Each task has two conditions: identical current material alone, or that same
material plus available earlier text. Each condition is generated twice, with
counterbalanced request order: eight proposed attempts, not eight independent
tasks. The model produces the requested deliverable, not a forecast of feedback.
No compression, retrieval oracle, generic-advice arm or model-based grader is
included in this small gate.

## Inspectable scoring

Freeze the constraint, its earlier exact quotation, scope interpretation and a
minimum task-quality rubric before calling the model. Assess each actual output
as `met`, `violated` or `unclear`, retaining exact output excerpts and an
explanation. Task completion is a separate gate: an empty promise to obey cannot
pass. Under-specification is `unclear`, not compliance by default. The local
analyst review is not an independent or blinded assessment; ambiguous ratings
must remain visible and any owner clarification is a separate later record.

A task is retained only if both repeats complete it and meet every frozen
constraint. Report each task and repeat, primary and exploratory strata,
history-only recoveries, no-history-only losses, both-pass and both-fail cases.
Missing or unscored output remains in the fixed denominator. Repetitions do not
increase the number of people or tasks. Both-pass demonstrates no advantage on
that case; both-fail cannot support compression fidelity. A difference can show
an effect of added context in these tasks, not that a unique personal trait or a
particular earlier sentence caused it. The primary stratum is only one task.

## Implemented offline contract

[`runaway.real_task_history`](../runaway/real_task_history.py) validates temporal
cutoffs, owner quotations, scope annotations and complete current-context review.
`paired_requests(cases, repeats=2)` retains every selected message and puts no
rubric, evidence binding or target label in the prompt. The current messages are
byte-equivalent across the pair; only the earlier-history field differs.

`score_deliveries(cases, requests, deliveries, judgments, repeats=2)` requires the
exact schedule and binds each judgment to the supplied observed delivery. It
checks literal output excerpts and preserves missing denominators. `deliveries`
maps integer slot IDs to the sealed output text; the caller is responsible for
loading authentic observations. This is accounting, not a semantic grader or a
proof that a source is complete. Synthetic software checks are reproducible with:

```sh
python -m unittest tests.test_real_task_history -v
```

Ten tests cover leakage, chronology, multi-message context, quality failures,
unclear/missing outputs, fabricated excerpts, rewritten deliveries and dropped
schedule slots. They make no service calls and establish no personal benefit.

The proposed private execution is separately manifest-bound: eight maximum
Codex attempts requesting `gpt-6.1-sol`, 180 seconds per attempt, no token or
money cap. Transport, output-schema or unknown-usage failure closes the scope;
there are no retries, resumed runs or replacement slots. The exact private
requests and execution implementation need owner authorization, and the public
implementation must pass all required CI checks before execution. Local
authorization, source text, outputs and machine identifiers stay outside GitHub.

Only an observed history benefit warrants a subsequent, separately authorized
compression comparison. This package does not authorize those calls or update
the user's preference ledger automatically.
