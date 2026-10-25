# Source review v2: separate link bookkeeping from semantic review

**Zero-call prepare/import prototype;the first service comparison is now recorded.**
At[whole1536](../source-review-comparison-v1/README.md),all4reviews imported but2flagged inherited conditions;two admitted cards retained40/40observed cells and40planned cells stayed missing. Direct grouped cards retained80/80. The pipeline does not pass the four-profile gate. The earlier[whole512 comparison](../source-coverage-comparison-v1/README.md)
rejected one audit because two user reaffirmations had context references but no
decision references. The model called them `covered` with an empty decision-unit
list, which v1 correctly rejected under its frozen contract. Those results stay
failed; this variant never converts them into successful calls.

The program now derives separate `decision_unit_ids` and `context_unit_ids` for
every selected source, including retired units. The audit receives that index,
the entire original source and the fresh inventory. It reviews meaning and
reports findings; it does not transcribe the index back. A user row is
`reviewed` or `uncertain`; non-user rows remain `context_only`. `reviewed` means
the model reports having reviewed the message, **not that its choices are covered**.
Every source still needs one exact quote and reason. Any finding or uncertainty
blocks compression. A finding may point to an omission even when its source has
no inventory decision link.

Fresh inventory preparation also asks the model to keep internal unit IDs only
in`id`/`supersedes`,rather than writing potentially stale successor IDs into old
unit prose. This is a prompt instruction,not a verified semantic repair or new
schema guarantee. Inventory import remains the unchanged v1 validator.

Use this variant from the first stage:

```sh
PROTO=benchmarks/source-coverage-review-v2/cli.py
python3 "$PROTO" inventory-prepare --sources selected-sources.json > inventory-request.private.json
# Give system/prompt/schema to the model; save its JSON.
python3 "$PROTO" inventory-import --sources selected-sources.json --answer inventory-answer.private.json --out ledger.private.json
python3 "$PROTO" audit-prepare --ledger ledger.private.json > review-request.private.json
# Give system/prompt/schema to a fresh, independent inference; save its JSON.
python3 "$PROTO" audit-import --ledger ledger.private.json --answer review-answer.private.json --out review.private.json
python3 "$PROTO" card-prepare --ledger ledger.private.json --audit review.private.json --budget-chars 512 > card-request.private.json
# Only a clear review admits compression. Save its JSON reply.
python3 "$PROTO" card-import --ledger ledger.private.json --audit review.private.json --budget-chars 512 --answer card-answer.private.json --out card.private.json
```

All six commands are offline, read explicitly selected files and refuse
duplicate JSON, symlinks and overwrites. Imported files are private0600. There is
no backend, retry, inventory repair, portable export or default change. v1 audits
and v2 reviews are distinct bound artifacts and cannot be silently interchanged.

The whole-card budget, exact public-span accounting, supersession and counted
partial-card label are unchanged. The index is private; it is never extra reader
memory. A clear review does not prove inventory completeness, semantic equivalence
or fresh-inference independence. It may still miss choices. The new prompt cannot
guarantee correct update prose or fix the model-reported missing boundary by
itself. Neither change establishes a fidelity improvement.

```sh
python3 -B -m unittest discover -s benchmarks/source-coverage-review-v2 -p 'test_*.py' -v
```

10 independent toy tests cover context-only user reaffirmations, old/new unit
links, source/role/quote damage, uncertainty/findings, forged flags/indexes,
distinct artifact versions, counted partial cards and all six CLI commands.
These10tests themselves make no service calls. The later service study above
used37actual inferences and retains all failures;the original512results were not repaired.
