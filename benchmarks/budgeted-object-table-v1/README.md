# Budget-aware object-table encoder — unmeasured

The [object-table probe](../object-table-probe-v1/MEASURED.md) reaches the
12-object capacity but both candidate outputs exceed1536characters after
lossless packing:1999and2170. Neither is a valid card; all40cases remain missing.

This candidate changes **only the encoder request**, relative to that wire and
compiler. It exposes the budget and fixed public header/guide, asks for short,
self-contained decision-target labels, and keeps trigger conditions in each
row's requirements. Ordinary/exception branches for the same target should
reuse that target label. Different targets, meaningful order, numerical bounds,
negative conditions, unknowns and execution permission still need preservation.

The response schema/version, object capacity, index expansion, source-quote
checks, condition factoring, renderer, codec and hard binder limits are
unchanged. The request cannot secretly read questions, references, old cards or
model responses. Four offline tests check those boundaries and exact binding
parity for the same toy answer. A preexisting over-budget answer still fails;
this code does not shorten or repair it. A new encoder must generate a new
answer from source to test the hypothesis.

```sh
python -m unittest discover -s tests -p test_budgeted_object_table.py -v
```

Showing a ceiling does not prove fitting or complete semantic retention. Budget
information and wording guidance change together, so any measured effect would
concern the bundled request, not an isolated budget-information intervention.
The [new14-attempt plan](../budgeted-table-probe-v1/README.md) is separately
frozen, unapproved and unrun. No new model calls, repair of historical products,
reference acceptance or production-default change is included.
