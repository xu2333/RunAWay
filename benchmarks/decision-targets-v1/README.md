# Decision-target candidate, calibration and measured comparison

The [closed 21-call comparison](MEASURED.md) finds **96/96 for both methods**,
with v2 adding 99 whole-card characters in aggregate. It shows no observed
accuracy or compression advantage. The earlier 118/120 versus 119/120 regression
is retained. This pack contains the source-only instruction candidate, symbolic
development calibration and actual model evidence, without changing the
production default.

```sh
python benchmarks/decision-targets-v1/check.py
python benchmarks/decision-targets-v1/measured.py
python -m unittest discover -s tests -p test_decision_targets.py -v
```

## Candidate

`prototype/decision_targets.py` adds only a generic instruction delta to the
published source-policy candidate. It accepts sources and a whole-card budget;
it does not accept questions, answers, scores, old cards or reader responses.
Schema, anchors, binder, header, guide, renderer and 1536 character ceiling remain
unchanged. No domain-specific failure IDs or recorded choices are in the delta.

The requested distinction is the decision question: choosing a plan, permission
to execute it and a status report can concern one object without being competing
preferences. Preserve refusal/waiting constraints as public content; a known
preference grants no permission. Retain any genuine prerequisite of the choice
itself, and retain real same-question conflicts and unresolved conditions.

The existing format permits at most 12 groups. A candidate can use separate
question-specific groups, or share a genuinely common object scope and clearly
name each rule's question in `when`. Neither requires a schema field or hidden
decoder. Group labels cannot be used to disguise a real conflict or revoke an
unrelated decision.

## Discriminating development calibration

The 14 messages and 16 questions in `development.synthetic.json` are newly authored
fiction, openly visible and **not a holdout**. Their target labels, boolean facts,
rules and references are author annotations, not a natural-language parser or
independent semantic acceptance. The oracle uses that structural rule memory;
source text only checks anchors and roles. Damaged views keep the original
expected labels, while intentionally corrupting the decoder's structural view.

Unknown boolean conditions are enumerated separately for each target. A choice
is known only if every possible world is covered and agrees. Uncovered worlds,
same-target conflicts, non-user suggestions and absent permission do not produce
an invented choice. Unknown is not false; all explicitly covered branches that
agree can still determine a choice. Supersession here is restricted to earlier
user evidence with the same target and exact condition scope; this small oracle
does not implement arbitrary partial-scope natural-language revocation.

| Structural view | All16 | Preference11 | Execution5 |
|---|---:|---:|---:|
| Intact typed view |16|11|5|
| Erase execution boundaries |13|11|2|
| Merge unrelated decision questions |7|5|2|
| Remove a real choice prerequisite |15|10|5|
| Delete one side of a real conflict |15|10|5|
| Treat assistant/tool statements as user choices |14|10|4|
| Treat missing conditions as false |15|10|5|
| Remove a covered consensus branch |14|9|5|

All denominators stay fixed. The execution-erasure control is particularly
important: a preference-only score remains perfect while 3 execution limits are
lost. This calibration detects a false pass that the old preference questions
alone could miss. These numbers measure transparent toy logic, **not LLM
performance** or an improvement from the new instructions.

`examples/` contains two **partial, manually authored** bag-choice/order examples:
228 characters in two groups and 216 in a shared group with explicit `when`
questions. Both bind with the original schema and preserve the refusal to order.
They omit the other development episodes and are not automatic extractions,
complete sixteen-question memories or evidence of a compression advantage.

`public_queries` and `reader_request` in `check.py` export only natural-language
questions/options. Private target IDs, predicates, truth, strata and references
never enter an extraction or reader request. `build.py` recreates the fictional
packet and hand-authored examples locally, with no service or randomness.

The [finite21call preparation](EXPERIMENT.md) and pure local job preparer are
preserved as the pre-execution plan. Its actual [results and limitations](MEASURED.md)
are appended separately. The plan's historical approval state is not a current
grant. The scope is closed, old 93/96 and 118/120 scores remain, and no new model
budget is implied. Both methods now pass the development bank, so promotion
requires evidence beyond this ceiling-level comparison.
