# Real-task delivery: one observed history benefit

**Real-person fidelity remains unverified.** This pilot found a bounded benefit
on one actual recording-design task: both full-history outputs explicitly
preserved an earlier input-capture requirement, while both no-history outputs
left it unspecified. It did not test compression, device operation or adoption.

Unlike the earlier correction-prediction diagnostics, the model completed the
actual user task. References came from earlier owner statements; the original
later answer, later criticism and rubric were withheld. The two conditions had
identical current material. Each was generated twice in counterbalanced order.

| Frozen stratum and constraint | No history | Available earlier text | Interpretation |
| --- | --- | --- | --- |
| Primary recording-plan task: preserve observed inputs and their timing/state association | 0 met, 2 unclear deliveries | 2 met, 0 unclear deliveries | An explicit earlier requirement appeared in both history outputs |
| Exploratory creative task: retain the fictional world's setting boundary | 2 met deliveries | 2 met deliveries | No observed advantage on this constraint; current subject matter already provided indirect cues |

The primary case endpoint requires **both** deliveries to complete the task and
meet the constraint: history **1/1**, no history **0/1**. There is only **one
primary case and one owner**. Two generations are not two people or independent
cases, and the exploratory task does not enlarge the primary denominator.

## What differed in the actual work

Both recording-plan conditions distinguished session length from sampling rate,
handled decision, auction and automatic-combat phases, and preserved visual
context around important events. All four passed the bounded task-quality gate.

The no-history plans remained about video sampling and decision clips. Neither
specified how actual input events would be directly recorded and retain their
sequence and timing. This is **unclear compliance**, not evidence that they would
deliberately discard input data.

Both history plans explicitly retained touch-event sequences. One named press,
move, release and multi-touch relationships, with video and events on a shared
timeline. The other retained those events and timestamps when capture is
available, prohibited inventing unobserved actions through interpolation, and
linked events across recording segments. These are proposed designs, not tested
capture implementations.

The creative outputs all stayed within the intended story world. The two
no-history lyrics left a separate **current-task tone** judgment unclear: their
requests for recognition or self-limiting remarks can conflict with the supplied
confident-character proposal, but can also be read as satire. Unclear quality
stays non-passing under the frozen conjunctive endpoint; it is not declared a
confirmed failure. The two history lyrics passed that limited quality gate.
Thus the combined two-case endpoint is history 2/2 versus no history 0/2, but
**that aggregate must not be presented as two recovered historical constraints**.
The creative setting constraint was retained equally in both conditions.

## Cost, evidence and limits

All **8/8** authorized local CLI attempts completed, with no retry or replacement.
The scope is closed. Reported usage was **129,759 tokens**: 122,964 input and 6,795
output. The 8,448 cached input tokens are included in input, not an extra total.
Money cost was not measured. The requested model was `gpt-6.1-sol`; the CLI did
not independently identify a resolved model. Each attempt had a 180-second
local deadline; there was no token or monetary cap.

The implementation at
[`d213878`](https://github.com/xu2333/RunAWay/commit/d213878488466802dc331ec01504cba672bc3226)
passed all three CI jobs and all 288 steps before execution. The original inputs,
responses, exact output excerpts, rubric, authorization and usage records remain
private. The [portable aggregate](real-task-history-v1.json) exposes each slot's
judgment, output fingerprint, counts and reported usage. Recount it locally:

```sh
python scripts/check_real_task_history.py
python -m unittest tests.test_real_task_history_results -v
```

These checks verify accounting and reject dropped slots, inflated denominators
and inconsistent summaries. They do not independently grade private text.
Assessment was by the assistant analyst, not independently blinded or confirmed
by the owner. The sources were previously inspected retrospective material from
two projects. Available qualifying visible text is not complete personal or
multimodal history. Added history includes other context and prior assistant
proposals, so the result does not isolate a unique trait or one causal sentence.

This is evidence that history can change one relevant, observable design choice
in a real task. It does not establish stable personalization or general benefit.
No preference-ledger adoption was recorded automatically. The next useful check
is another real task with earlier evidence and no explicit current cue; a later
compression comparison must protect the recovered input-capture requirement.
Neither next step has a service-call budget from this closed scope.
