# Why the available history did not help

**Real-person fidelity remains unverified.** This is an offline audit of the
four completed creative-work cases, followed by stricter screening of additional
real episodes. It adds **zero model calls** and does not alter sealed inputs,
responses, original scores or the separate owner adjudication.

The owner-informed result remains **0/4 in all three conditions**. The historical
record still contains the original unresolved R5 judgment; see the
[adjudication](real-correction-music-v2-adjudication.md).

## What the evidence supports

| Case | Earlier evidence versus later correction | Observed history response | What remains unresolved |
| --- | --- | --- | --- |
| R2 | An earlier named inspiration was present, among several inspirations. The current task explicitly asked for a different kind of analysis. | Prioritized the current explicit request; missed the inspiration the owner next revisited. | The earlier mention did not uniquely establish the owner's next priority. We have not isolated retrieval failure from prioritization. |
| R3 | Earlier requests supported both the fictional setting and contemporary resonance. The correction narrowed the acceptable balance. | Reinforced the contemporary direction, while the owner rejected excessive modernization. | The precise boundary may have first become explicit in the target. This is not evidence that a previously explicit boundary was forgotten. |
| R4 | Story emphasis was present. Earlier feedback also concerned delivery and density. The later correction specifically concerned fragmented scenes and insufficient dramatic conflict. | Retrieved a concern about wordiness and flow instead. | A broader story preference is not the same as the precise later criticism; generic writing quality remains a competing explanation. |
| R5 | Earlier character confidence and an old-status persona were explicit. No clear earlier requirement for trendy humor was established in the audited anchors. | Protected the character's stature. The owner's later clarification concerned dated humor. | The two concerns differ. The clarification resolves the match as a miss; it does not retroactively make the earlier history contain the missing requirement. |

These are observations and bounded interpretations, **not a causal diagnosis of
long-context failure**. Some responses visibly used earlier context. None of
these calls tested compressed memory, and none establishes that the model ignored
all history. Selecting one next correction also conflates retrieval, applicability
and which concern the owner will voice first. A useful alternative concern still
fails that endpoint.

## Input check: incomplete citations, not omitted history

The old reference helper selected only the first user message from each cited
turn. Some turns contained several user messages. An offline comparison against
the exact sent history confirmed:

| Case | User messages in cited turns | Messages quoted by the reference helper | Present in actual history input |
| --- | ---: | ---: | ---: |
| R2 | 2 | 2 | 2 |
| R3 | 8 | 2 | 8 |
| R4 | 7 | 3 | 7 |
| R5 | 2 | 2 | 2 |

Counts are message occurrences per case, not distinct preferences or independent
evidence; shared turns occur in more than one case. All four history/current
payloads matched the saved exact requests. The sealed request digest stayed
unchanged. The citation shortcut understated the evidence available to an auditor,
but did **not** remove those messages from the model input. The new local intake
retains all qualifying messages with their chronological positions and source
digests. It does not reuse the first-message shortcut.

## Stricter screening, including rejected candidates

Additional screening examined game-agent, research and this project's real
conversation records. This was targeted discovery, not an exhaustive census, so
we do not publish an acceptance rate. It found one stronger candidate for a new
bounded diagnostic, not a validated history benefit:

- **Retained candidate:** a repeated workflow correction about consulting existing
  rule documentation instead of learning basic rules mainly through repeated
  demonstrations. Earlier owner statements explicitly requested the same kind of
  documentation review in the same game. The current report exposes rule-related
  problems but does not restate that earlier request. Generic engineering advice
  could still succeed; it must remain a control.
- **Rejected after inspecting the full current material:** a repeated concern
  about slow operation. The assistant's current question and update already
  mentioned continuous operation. Removing those messages to manufacture a
  history-only signal would make the comparison misleading.
- **Rejected:** reusing existing recordings. The current user request already
  explicitly requested offline iteration with the existing material.
- **Rejected:** repeated credential-entry friction. The current failure already
  exposes the friction, and the user had just chosen to keep using the old version.
- **Rejected:** repeated musical execution concerns without the original audio,
  or cases where the current artifact already names the supposed hidden preference.
- **Not selected:** research direction changes and general methodology requests
  without a sufficiently clear earlier statement in the same scope.

The candidate is a project-specific working preference, not a timeless personality
trait. It is one owner's retrospective episode, selected with the correction
already visible. Its endpoint isolates one facet of a multi-part real correction;
that selection must be disclosed, not presented as blind discovery.

## Next diagnostic and its limits

The private packet contains four unexecuted requests: current material only,
available prior text, generic quality advice, and two manually selected earlier
owner statements. The last condition is a **target-aware diagnostic**, not an
automatic retrieval method or evidence of full-history utility. If that condition
helps but the full available text does not, it would motivate a retrieval or
relevance intervention; it would not identify a unique mechanism.

The history condition preserves all recovered user/visible-assistant text before
the episode, with documented exclusions for automation, tool results, reasoning,
environment metadata and flagged authorization/credential replies. Ordinary
structured workflow choices are retained as question/answer text. Unavailable media stay unavailable.
This is not full personal history. Current material is identical across conditions;
targets, later conversation and labels stay out of every request.

New execution requires separate authorization. Even a positive single-case result
would be a local signal requiring more cases, not permission to claim personal
fidelity or resume compression optimization. A null comparison leaves compression
retention undefined. No compression run has been added.

[Portable audit counts](real-correction-history-audit-v3.json) ·
[Original study](real-correction-music-v2.md) · [Results overview](../../RESULTS.md)
