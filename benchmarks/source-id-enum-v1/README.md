# Enumerate actual source IDs: experimental request schema

The [paired review repeat](../source-id-review-repeat-v1/README.md) rejects two
new reviews with three out-of-table ID strings. The existing output schema
allows arbitrary short source-ID text;the binder later checks table membership.

This candidate adds the actual source table's ID list as `enum` at every anchor
position in the **request schema**. The request prompt/system, source/draft,
response version, binder, compiler, public budget and reader remain unchanged.
It lists all source IDs, not evaluator-selected correct citations. No reference,
question, old reader response, rejected output or case correction is appended.
The original global schema is not mutated.

For the same valid source table,the final client-admissible graph set remains
the same:successful old binding already requires every referenced ID to belong
to that table. The new request states that existing requirement earlier. This
is not an automatic spelling correction or a weaker binder. Undefined IDs are
still rejected;known but wrong-role decision IDs still fail the old role check.

Eight offline tests reject both actual invalid outputs without changing them,
retain the public bytes of seven valid archived source-ID responses, and admit
36previously valid quoted graphs after the existing ID conversion. They also
check every schema anchor position, source-table dependence, nonmutation and
an unsupported-action counterexample. Valid IDs still do not certify semantic
support, complete coverage or preserved behavior.

```sh
python -m unittest discover -s tests -p 'test_source_id_enum.py' -q
```

A separately authorized [same-batch comparison](../source-id-enum-repeat-v1/README.md)
now closes51actual calls across both methods and their controls/readers. Enum
review yields8/8valid cards and60/60joint parent/case cells;the existing request
has4/8valid cards,15/60joint cells and45missing. Both use the same original
sources/drafts,prompt,binder/compiler/reader and matched review repetitions.
The original31-call result remains unchanged.

This is two consumed fictional people/four posthoc drafts,not new-scene,
population,real-user,semantic-citation or initial-generation verification.
Request constraints do not certify fidelity. Schema bytes/input tokens increase;
no cost-saving claim is made. The [offline review bridge](../../docs/experimental-memory.md#optional-source-id-review)
exposes this as explicit`--request-schema enumerated`;the default existing
request and installed generation flow remain unchanged. Import status stays
candidate-unvalidated even when an archived demo has measured passing scores.
