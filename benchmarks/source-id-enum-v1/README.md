# Enumerate actual source IDs: offline candidate only

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

There have been **zero model calls with this candidate**. Request-schema
constraints do not themselves prove that a provider will generate conforming
or faithful output. Schema size/input tokens increase;no cost-saving claim is
made. The original31-call result and its missing cases remain unchanged. The
user bridge's measured/default request is not silently replaced.

A separately prepared [paired schema comparison](../source-id-enum-repeat-v1/README.md)
requires a fresh finite grant and implementation-commit CI before live execution.
