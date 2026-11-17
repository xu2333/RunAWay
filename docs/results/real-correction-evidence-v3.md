# Explicit earlier evidence still did not produce a history win

Four separately authorized calls completed on the one retained real workflow
episode from the [offline intake audit](real-correction-history-audit-v3.md).
Current material, available prior text and generic guidance each scored **0/1**
under the frozen strict criterion. Two manually selected earlier owner statements
produced a partial response, also **not a strict hit**. No compression comparison
followed.

| Condition | Observed main concern | Strict result |
| --- | --- | --- |
| Current material only | Preserve the owner's normal workflow rather than requesting extra demonstrations | 0/1 |
| Available prior text | Apply earlier speed improvements to reduce the remaining runtime delay | 0/1 |
| Fixed generic guidance | Make decisions before the operation window closes | 0/1 |
| Manually selected earlier evidence; diagnostic only | Read the full guide and establish foundational understanding before concentrating on local fixes | Partial; 0/1 strict |

The target was a repeated correction about obtaining foundational rules from
existing documentation instead of primarily learning them through more recorded
demonstrations. Earlier owner statements explicitly requested documentation review
in the same scope, and both were verified in the actual history input. The shared
current material retained the assistant's report of rule-related issues; it was
not edited to hide useful clues from controls.

The manual-evidence response clearly matched reading the guide first. Its rejection
of depending mainly on further demonstrations was not clear enough to count the
second frozen facet as satisfied. We record that facet as unresolved, with the
case retained in the denominator; this is not a zero-loss success. The scorer knew
the target, and this conservative judgment is not independent blind adjudication.
No further owner adjudication has been obtained for this response.

## What this narrows, and what it does not

The history response visibly used earlier workflow concerns, but selected a
different recurring concern from the one the owner next expressed. The selected
evidence response moved toward the relevant rule-source concern. That motivates
studying retrieval and applicability, but does **not** isolate retrieval as the
cause: manual selection changes length, salience and the mixture of competing
concerns, and was performed with the target known.

Predicting one next correction remains an underdetermined endpoint. A model may
mention an applicable requirement while missing the particular concern voiced
next. Broader requirement coverage or actual task usefulness would be different
endpoints, requiring new cases and a separately frozen protocol. We do not
retroactively score other useful suggestions as hits, add more predicted items,
or reuse this target as a new holdout.

This study strengthens the evidence that an explicit earlier statement was
available. It still **does not establish useful full-history personalization**.
The next useful test should preserve a real decision or task and its applicable
earlier constraints, with current-only and generic controls, rather than quietly
relabeling this correction-prediction result as task performance.

## Accounting and scope

- 4/4 serial local CLI attempts completed; scope closed with zero remaining.
- **155,141 reported tokens**: 154,146 input and 995 output. No retries, repair,
  resume, replacement or additional grading call.
- Requested `gpt-6.1-sol`; resolved model identity was not reported.
- One owner, one retrospective development episode, one sample per condition.
  The original correction contains several concerns; one facet was selected for
  this test before execution. This is not blind case discovery or a population estimate.
- The available-history condition received 1,144 earlier visible messages; all
  four conditions shared the same 34 current messages. The diagnostic condition
  received only two manually selected earlier owner messages.
- Recovered history excludes automation-driven turns, tools, reasoning, environment
  metadata and flagged authorization/credential replies. Ordinary structured choices
  were retained. Unavailable media were not reconstructed; this is not full personal
  history or an evaluation of live game actions.
- Targets, later conversation and reference labels were absent from each request.
  Private original texts, exact requests, responses and grants remain local.
- The generator module matched the already CI-passed implementation; this result
  makes no claim about the status of documentation PR checks.

[Counts and usage](real-correction-evidence-v3.json) ·
[Intake and prior failure audit](real-correction-history-audit-v3.md) ·
[Results overview](../../RESULTS.md)
