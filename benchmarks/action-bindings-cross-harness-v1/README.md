# Does the handoff retain who releases the work and what to use?

This experiment uses the nine previously studied synthetic handoffs. It compares the [previous reader](../release-gate-cross-harness-v1/README.md) with that same reader plus one generic paragraph after the exported card:

> 原文指定了由谁确认或传达放行决定，就在对应动作旁写明各自的角色。交代已获准的动作时，一并写明原文指定的用料及规格。只保留有依据的细节，不另加手续。

The protocol allocated nine tasks per arm to each client. Codex and Claude Code completed 18 calls each. Antigravity returned 11 answers and reached its 180-second limit on its twelfth call. Its remaining six slots closed. Each attempt started with one web-exported rule installed in a fresh project and session. The user message contained only the original task. The two arms used byte-identical cards, task text and installer metadata. Arm order alternated across cases and clients.

[Paired results](RESULTS.md) · [All replies and clause assessments](observations.json) · [Registration](https://github.com/xu2333/RunAWay/pull/131#issuecomment-7149259270)

## Offline verification

Run `node check.mjs` and `python3 score.py` here. The first command recreates all 54 rule files from the original web exporter and compares the 27 controls with the prior candidate. The second checks the recorded replies, verifies that the quoted text occurs in each answer and recounts the assessed results.

In the thread-panel task, record the issuer of the confirmed replacement and the material for the released threading independently. An issuer can be identified explicitly by role or by an unambiguous first-person instruction. A generic reference to receiving a confirmed replacement leaves the issuer open. A material can be specified for the released action directly or by an unambiguous project-wide rule. The combined endpoint requires both in one answer. Retain the full nine-case rubric separately.

The waiting endpoint covers the four previously affected tasks in all three clients. Count an unsettled time or shift as a gate only when the answer instructs the next shift to wait for it. Track other added gates separately. Qualified permission to act immediately is compatible with discretion. An instruction that immediate action is compulsory changes the rule. Each note describes the basis for the judgment, and clause excerpts locate the relevant passage in the raw answer. Missing responses remain in fixed denominators.
