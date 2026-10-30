# Unmeasured when-field contract alignment

The [closed compression study](../compression-stability-v1/MEASURED.md) found
nine empty when strings in one invalid768-character h68output. The request's
wire schema allowed them; the local binder required nonempty text at most120
characters. Another output failed the whole-card ceiling at806characters.
These are different failures and neither has been repaired in the evidence.

`candidate.py` wraps the published scope-v1 producer and deep-copies its schema,
adding only minLength1/maxLength120to the when field. Source payload and prompt
are byte-identical, and the binder/renderer remain unchanged. It does not insert
replacement words, read questions, use references or modify observed outputs.
No source IDs, failure-case choices or person-specific logic enter the candidate.
The production default is unchanged and no new service run is included.

```sh
python -m unittest discover -s tests -p test_grouped_wire_contract.py -v
```

Four offline checks show that all10actually valid extractions remain locally
wire-valid and render identically, while the empty-when output is rejected
earlier. The806-character output remains too long. Whitespace-only text still
passes these length bounds and is rejected by the binder. Other contract gaps,
budget feasibility, completeness and behavioral fidelity remain open. Model/
backend compatibility and effects on generation are untested; local checks do
not establish that the model will produce better cards or fewer failures.
