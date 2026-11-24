# Can one exported card carry the same decision across clients?

Nine previously used fictional handoffs each have one fixed portable card, one original task and one set of scoring clauses. Each client receives the same card bytes in its native project-rule format, in a fresh project, and gets only the task as the user message. This measures a reader using an installed card. The extractor is outside the experiment.

| Client | Requested model | Project instruction |
|---|---|---|
| Codex | gpt-6.1-sol | `AGENTS.md` |
| Claude Code | sonnet | `.claude/rules/runaway.md` |
| Antigravity | gemini-3.8-flash-medium | `.agents/rules/runaway.md` |

The [registered protocol](protocol.json) freezes each card, task and rubric. The [public preregistration](https://github.com/xu2333/RunAWay/pull/129#issuecomment-7147365172) predates inference. Here the model and client vary together. A matched-model study would be needed to isolate client effects.

## Results

All 27 sessions returned an answer. No retries or missing cells. The strict all-three score is **0/9**. Most individual clauses survived.

| Configuration | Cases passing all clauses without a conflicting instruction | Clauses fully preserved |
|---|---:|---:|
| Codex / gpt-6.1-sol | 2/9 | 24/30 |
| Claude Code / sonnet (reported claude-sonnet-5-5) | 1/9 | 22/30 |
| Antigravity / gemini-3.8-flash-medium | 0/9 | 21/30 |

| Historical task | Codex | Claude Code | Antigravity | What made the difference |
|---|---|---|---|---|
| Greenhouse map | Fail | Fail | Fail | All required another timing confirmation or announcement after the gardener signed. |
| Listening room | Fail | Fail | Fail | All required a shift assignment or notification after copyright and clip-ID conditions were satisfied. |
| Puzzle returns | Fail | Fail | Fail | All recognized that the rainbird box qualified, then made its return wait for a time decision. |
| Shadow captions | Fail | Fail | Fail | All preserved the 07/06 distinction. Codex and Antigravity added a timing gate after clearance; Claude Code required asking about the two unsettled details before switching. |
| Thread panel | Pass | Pass | Fail | Antigravity retained the permitted threading and stopped the correct drilling, but left the issuer of the confirmed replacement sheet unspecified. |
| Type specimen | Fail | Fail | Fail | Codex presumed the samples should remain clipped. Claude Code and Antigravity stated that clipping had already happened. |
| Two reels | Fail | Fail | Fail | All imposed a readback check on the second reel. Only the first reel had a recorded readback. |
| Foldout books | Pass | Fail | Fail | Codex retained the optional photo and unknown completion. Claude Code acknowledged uncertainty but instructed the next shift to treat it as untaken when acting. Antigravity omitted the prior-photo uncertainty. |
| Color swatches | Fail | Fail | Fail | All retained the selective waiver; none explicitly preserved the unknown insertion status for the optional strip. |

The shadow-caption case illustrates the distinction between clause coverage and a contradictory extra: the reader can retain all four registered details and still add a prerequisite in its instructions. The judgments are unblinded, excerpt-backed semantic assessments by one reviewer. The strict score is sensitive to details such as preserving the issuer of a permission. Each case represents one archived, previously inspected synthetic scenario.

The study used nine attempts per configuration with a 180-second limit per attempt. Codex reported 92,641 input and 3,406 output tokens. Claude Code reported an estimated USD 0.1353562. The Antigravity text output did not expose usage; total provider cost is unknown.

## Reproduce the inputs and inspect the results

From this directory, with Node 22+ and Python 3.9+:

```sh
node exports.mjs
python3 score.py
```

The first command rebuilds each ZIP with the web application's exporter and compares it to the download receipt. The second checks the answer hashes, matches every cited excerpt against the answer and recounts the recorded qualitative judgments. Neither command starts a model. To export an individual fixture, run `node exports.mjs puzzle codex /path/to/new.zip`. Unzip outside the intended project and run the installer with `node install.mjs --project DIR`. Use a separate empty Git project per client/task. Give the client only the case's `task`. The card is already installed. Keep the rubric and previous outputs outside the project.

[Per-cell records](observations.json) preserve the full answer, one marked excerpt per clause, added obligations, material conflicts and whether the next action is usable. Excerpts locate the judgment; omissions are assessed against the full answer. An extra bookkeeping suggestion can be visible even when it does not change what is allowed. A conflicting prerequisite fails the case. A matched success means all three configurations pass the *same case*. Each configuration has nine observations, with no independent repeat per cell or empty-card control.

## Other historical cases

- The [paper crane](https://github.com/xu2333/RunAWay/pull/129#issuecomment-7147002436) and [prism box](https://github.com/xu2333/RunAWay/pull/129#issuecomment-7147237882) already have matched three-client observations. Their short-output scores use their own denominators.
- The next synthetic families cover [unknowns under partial information](../partial-information-v1/README.md) and [alias- and scope-bound choices](../scope-alias-comparison-v1/README.md). Retain original option order, answer key and missing-case policy when bringing those tasks across clients. The [historical inventory](../regression-inventory-v1/README.md) also identifies disputed cases.
- Real-task studies, including [recording](../real-recording-card-v1/README.md), have different disclosure scopes. No real-person data were used here. Trajectory-to-card experiments can test cross-provider extraction separately from the fixed-card handoff.
