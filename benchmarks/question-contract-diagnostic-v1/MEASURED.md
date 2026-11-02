# Unchanged memory: original task11/12,explicit choice task12/12

All8 new local Codex CLI attempts completed requesting gpt-6.1-sol:each question
packet received its own no-memory/full controls(4calls),then two reads of the
same original495-character e0card(4calls). No extraction,marker,card/source/
option/reference changes,missing answers,skips,retries,repairs or unused slots.

Both full controls immediately pass12/12and5/5personal-known;their own no-memory
controls each score4/12and0/5personal-known. Both qualify before any memory read.
The packets are separate calls,old/explicit then reversed. Each method requires
two new reads and both option orders correct:4answers per case from1inherited
producer,not generation stability or independent human samples.

| Question packet | Card chars | First read | Second read | Strict known | Strict unknown | Strict total |
|---|---:|---:|---:|---:|---:|---:|
|Original naming wording|495|11/12|11/12|7/8|4/4|11/12|
|Explicit existing-flow choice|495|12/12|12/12|8/8|4/4|12/12|

The only difference is c05. Original asks`问题只问活动命名方式`;explicit asks
`问题只问本人会选哪套活动流程（返回方案完整名称）`in both option orders.
Original returnsUin all4answers;explicit returns`先摆书后讲故事`in all4.
All other11cases pass in every read. There is no within-packet read disagreement.

## What the controlled difference supports

The unchanged card supports the author-intended future-choice task under the
explicit request. The reproduced original false-Uand stable explicit answers
support **task-formulation sensitivity under fixed memory** in this one example.
They do not establish that a better encoder recovered lost information.

A post-hoc application-request audit confirms model/system/schema fields match,
and replacing only the two task descriptors makes the full prompts identical,
for both control pairs and both reader pairs. The new original-reader request
digests also match the preceding name-marker cohort's original requests. This
verifies application-level isolation;served model identity and the internal
harness context remain unobservable. No historical answers are pooled into the
new endpoint.

The explicit task is an author-intent clarification after failure,**not an
independently accepted semantic paraphrase**. The original wording could support
a different reading;this probe does not adjudicate question/gold truth or isolate
lexical matching,attention,semantics and encoding as a unique cause. Old questions,
reference values,responses and scores stay intact. In particular,the earlier
fresh-source45/48and name-marker11/12are not upgraded retrospectively.

This is1fixed e0parent in consumed synthetic development data,not t1/e1,
all48cases,new producer stability,independent semantic acceptance,real-person
or cross-model/harness validation. No default encoder/reader changed and there
is0new original232-inventory coverage.

## Reproduction and cost

```sh
python scripts/replay_question_contract_diagnostic.py
python -m unittest discover -s tests -p test_question_contract_evidence.py -v
```

Exact fictional requests/raw values,question packets,parent/view hashes,usage,
all control gates and12-case denominators are retained. Replay has no service
capability. Eight mutation checks reject source/reference/question/view/parent
drift,request/raw tampering,changed gates/scores/missing denominators,removed
attempts,usage changes and false equivalence/old-score-replacement/fix claims.
Seven controller fixtures remain separate oracle calibration.

Recorded usage:86764input+1964output=88728tokens. Reasoning output146is a
subset,not an extra charge;cached/cache-write input0. No token or monetary
ceiling applied;these counters are not a bill. Requested metadata does not
independently verify served identity,internal RPC/retries or cancellation.
Local grants,credentials,paths and private transport envelopes are excluded.
The actual8scope is closed with0remaining calls.

Input manifest SHA256:
`1151d353e2ca3cda9c7d66a37b9093d9266c8fc6e4fc0e0a58151295768909f2`.
