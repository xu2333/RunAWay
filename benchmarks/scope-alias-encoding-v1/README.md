# Preserve scope aliases across compression

**Measured on two consumed fictional development sources:**the separately
approved [source-only comparison](../scope-alias-comparison-v1/RESULTS.md) improves
48/64→64/64,restores16old-name choices and preserves48other cases across both
generations/reads/orders. No missing or invalid cards. This is an explicit
experimental CLI option (`--encoder scope-alias`);defaults remain unchanged and
user cards remain unvalidated. The [binding-stress measurement](../scope-binding-stress-v1/RESULTS.md)
found a concrete omission in a source-accounted card: its four objects use only
their current names. Eight old-name cases return U in both reads/orders. The
original rename messages and private `source_accounting.reason` preserve the
mapping, but readers receive neither. No new action choice occurs in a rename;
classifying it `no_choice` was compatible with discarding a necessary scope link.
One smaller-budget card also drops the current names,leaving only domain labels;
that loses12additional known choices. The new request must retain canonical
current names in objects as well as their declared aliases. The binder rejects
relations whose canonical name is absent;it does not automatically patch an
old domain-only object or prove model regeneration will satisfy this contract.

The repair keeps those non-choice relations in a typed, source-bound field and
projects them into the public object name. It does not guess them from free text
or insert a private decoder into the reader request.

## Changed contract

`object_aliases` names a canonical object, its other source name and the user
quotation supporting the relation. Every user accounting entry also has
`alias_ids`, independent of whether it records an action choice. Thus a rename
can remain `no_choice`, with no decision node, while its scope relation survives.
Each relation's witnesses and accounting supporters must match in both directions.

The binder checks existing user roles and literal quotations, both names in the
same quoted message, a real object owner, unique relation IDs and unambiguous
declared name ownership. It appends all declared aliases to the corresponding
public object and verifies their presence after the original wire is decoded.
It leaves nodes, conditions, actions, priority, revision links, unknown boundaries,
compiler, reader and whole-card character cap unchanged. Existing original guards
still run. Oversized objects/cards fail rather than truncate a name or a choice.

The request sees only its own source, budget and general encoding instructions.
It contains no questions, reference, failing card, hand-authored alias map or
case-level feedback. This is a new schema/guidance contract, not a claim that
the old method has been fixed or that a model will reliably fill the new fields.

## Fixed-card mechanism diagnostic

```sh
python3 -B benchmarks/scope-alias-encoding-v1/diagnostic.py
python3 -B -m unittest discover -s tests -p 'test_scope_alias_encoder.py' -v
```

The diagnostic takes original slot7 unchanged and adds four **developer-written,
post-hoc relation annotations** from its own rename messages m37–m40. Its public
card grows from768 to793characters, keeping all four old names. Every non-object
ledger field, every original node and all unknown text stay identical. This
demonstrates the public projection mechanism at1,536characters; the793-character
result exceeds a768-character cap. No reader is called and no choice recovery is
measured. The annotations never enter the candidate's source-only request.

Ten offline checks cover source-only routing, public name conservation,
bidirectional accounting, role/quote/name/owner failures, existing action witnesses,
whole-card budget refusal,the original measured counterexample and direct CLI
execution outside the checkout. Two explicit
counterexamples keep the limits visible: omitting all alias declarations can
still pass, and a quotation denying a same-scope relation can satisfy literal
checks. Neither structural accounting nor name presence proves semantic truth,
complete alias extraction, automatic generation stability or behavioral fidelity.

The separate source-only27scope is now closed after all27attempts. It never used
these developer annotations or the old51scope's unused readers. Further model
validation needs another finite,frozen approval. Old sources,cards,answers,references and scores
remain intact. No product default, real-user fidelity or cross-provider claim.
