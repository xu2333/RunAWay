# One real correction: no demonstrated history advantage

Three approved calls completed on one actual writing episode. Under the frozen
strict rubric, current-task-only, available session history and generic editing
advice each scored **0/1**. This does not establish that personal history is
useless; it does not establish a useful personalization signal either. No
compression comparison followed.

The model was asked to predict the author's primary correction to an actual
review. All conditions saw the same task, draft and review. The history condition
also saw recoverable earlier user/assistant messages and attached drafts. The
actual later correction, subsequent replies and grading rubric were withheld.
Earlier published articles and some generated artifacts were unavailable, so
this was **available session history**, not complete personal history.

| Condition | Strict hit | Observed focus | Input / output tokens |
| --- | --- | --- | --- |
| Current task only | 0/1 | A technical distinction in the argument | 13,389 / 370 |
| Available session history | 0/1 | Preserve the author's recurring thesis and rhetorical force | 33,703 / 212 |
| Generic editing advice | 0/1 | Avoid turning a popular essay into a paper | 13,431 / 274 |

The strict criterion required both identifying excessive emphasis on rigor and
requesting renewed grounding in the author's prior series style. The history and
generic responses had relevant partial overlap, but neither met both parts. We
did not relax the criterion after seeing the responses. All three comparisons
concern the same episode; they are not three independent cases or people.

The requested model was `gpt-6.1-sol`; resolved identity was not reported. The
service reported **61,379 tokens** total (60,523 input, 856 output, zero cached
input tokens). Three attempts completed, with no retries, repairs or replacement.
Reported call times were 20.927, 10.599 and 14.264 seconds. The scope is closed.

## What remains uncertain

- This was a retrospectively selected, previously consumed correction, with one
  response per condition. It is not a holdout or a prospective user-benefit test.
- The designer knew the correction and wrote the generic advice with that
  knowledge. This is a diagnostic control, not an independent generic baseline.
- The current task already requested attention to the series, so task compliance
  and generic editorial quality can explain relevant responses without memory.
- Scoring applies a frozen conjunctive criterion manually; it was not blind or
  independently adjudicated. Partial similarity does not establish relative gain.
- Original conversations, drafts, responses and authorization records remain
  private. Public aggregates support arithmetic checks, not independent rescoring.

The next dataset should contain multiple real episodes with complete earlier
context, actual later decisions, and a temporal split fixed before model results.
Include cases whose current task does not itself reveal the preference. First
compare history with no history and generic-quality controls. Keep null cases and
ambiguity visible; do not select a favorable outcome and call it general fidelity.

[Machine-readable aggregates](real-correction-signal-v1.json) ·
[Overall evidence](../../RESULTS.md)
