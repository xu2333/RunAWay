# Source coverage: inventory, independent audit, then compression

This runnable **zero-call prototype** follows the [whole512 failure](../grouped-comparison-v1/README.md):
grouped cards fit4/4 but retained29/52 known choices. All23 observed errors returned
U for an originally known choice. The new path makes omission accountable and
adds an audit of the inventory itself. The [first consumed comparison](../source-coverage-comparison-v1/README.md)
generated4valid inventories,but only1audit admitted compression and that card
exceeded512characters. No inventory-method reader was admitted;fidelity remains
unmeasured. The [unmeasured review-v2 interface](../source-coverage-review-v2/README.md)
addresses one decision/context annotation failure without changing these results.

The CLI prepares system/prompt/schema requests and imports saved JSON replies.
Give each prepared request to any chosen model or harness; the prototype itself
makes no service calls. Use a fresh independent inference for the audit when
evaluating this method. Imports cannot prove how the reply was obtained.

```sh
PROTO=benchmarks/source-coverage-pipeline-v1/cli.py
python3 "$PROTO" inventory-prepare --sources selected-sources.json > inventory-request.private.json
# Give only that request's system/prompt/schema to your model; save its JSON reply.
python3 "$PROTO" inventory-import --sources selected-sources.json --answer inventory-answer.private.json --out ledger.private.json
python3 "$PROTO" audit-prepare --ledger ledger.private.json > audit-request.private.json
# In a fresh inference, audit the original sources and inventory. Save the reply.
python3 "$PROTO" audit-import --ledger ledger.private.json --answer audit-answer.private.json --out audit.private.json
python3 "$PROTO" card-prepare --ledger ledger.private.json --audit audit.private.json --budget-chars 512 > card-request.private.json
# Only a clear audit admits this request. Save the compression reply.
python3 "$PROTO" card-import --ledger ledger.private.json --audit audit.private.json --budget-chars 512 --answer card-answer.private.json --out card.private.json
```

Input is an explicitly selected list of `id/role/text` sources, or the existing
`{"schema_version":1,"sources":[...]}` wrapper. Optional `episode_id` is retained.
No directories or chat history are scanned. Duplicate JSON, nonfinite values,
symlinks, unknown fields, bad role/quote references, oversized requests and
overwrites are refused. Imported private files use0600 permissions.

## Stages and gates

1. **Inventory:** enumerate user-endorsed choice observations, scope/condition,
   numeric or single-point boundaries, local updates and unresolved conflicts.
   Multiple choices in one message have separate unit IDs. Updating one unit
   does not globally delete the message's other choices. This request has no
   public-card budget, public evaluation questions or reference labels.
2. **Source-only audit:** reread all original messages with the new inventory.
   Every selected source gets one coverage entry and an exact quote. All units
   anchored to that message, including retired old units, must be addressed.
   Findings describe missing choices, unsupported claims, overgeneralization,
   bad updates, collapsed conflicts or uncertainty. The auditor reports issues;
   it does not repair the inventory. Any finding or user-source uncertainty
   blocks this person's compression. Other people/baselines need not stop.
3. **Compression:** only a clear, bound audit admits a card request. The compressor
   gets the validated inventory and complete budget, not questions/reference
   answers or the full raw source. Every declared unit gets a disposition:
   represented by an exact public span, explicitly omitted, or locally superseded.
   If any active unit is omitted, the public card must contain the counted
   `部分卡：` label. Header/name/explanations/glossary all count inside the budget.
4. **Import:** statuses are `accounted_candidate_unvalidated`,
   `declared_partial_candidate` or `budget_unmet`. Over-budget cards are retained
   as diagnostic imports; there is no truncation, retry, repair, automatic action
   or portable export. Review `card.private.json` before sharing its public prompt.

## What remains unverified

Every source being accounted for does not prove the auditor noticed every
choice. A clean audit is a model judgement; the inventory can still be incomplete.
Literal public-span mapping does not prove semantic equivalence. Tests deliberately
show that mapping units to `X` can pass accounting. Inventory completeness,
semantic support, real-person fidelity and fresh-inference independence therefore
remain false in these imports. A later fixed executor must verify actual distinct
calls and behavior; this prototype cannot certify them from a JSON flag.

27 independent toy tests cover the two-stage producer, full-message audit,
local supersession, conflicts, wrong roles/quotes, missing/duplicate units,
forged clear flags, counted partial labels, Unicode budgets, private files,
episode metadata and all six CLI commands:

```sh
python3 -B -m unittest discover -s benchmarks/source-coverage-pipeline-v1 -p 'test_*.py' -v
```

The45-slot comparison is closed:27 calls were used and18dependencies expired.
This prototype authorizes no new model calls or default change.
