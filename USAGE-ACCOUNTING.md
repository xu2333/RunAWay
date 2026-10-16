# Request fingerprints and execution identities

`request_id` in the self-play cache is SHA-256 of the prompt, schema, requested model and system instructions. It identifies identical **input**, not one service execution. Separate run directories can execute the same request independently. Deduplicating their costs by request ID loses those executions; counting every file instead double-counts copies.

The decision-memory experiment has **38 completed response records but 36 unique request fingerprints**. Two requests ran once in `development` and again in `development-audited`. Their answer choices match, but recorded usage and elapsed time differ. Private native launch receipts corroborate separate commands and process sessions; the historical wrapper cached only within each output directory. Original requests, responses, frozen plans and the evidence archive remain unchanged.

The [synthetic ledger](examples/execution-ledger.synthetic.json) preserves all 38 records. Known input is **348,867**, output **47,006**, total **395,873** tokens. Cached input (20,352) is part of input; reasoning output (3,805) is part of output. They must not be added again. These are locally recorded service usage counts, not an invoice or proof of complete historical coverage.

## Identity contract

For historical records without an attempt ID, the offline tool uses `legacy-response-sha256:<checkpoint hash>`. This fingerprint covers the entire validated result, including answer and provenance. Formatting-only copies deduplicate. Distinct usage or elapsed values distinguish the repeated executions in this audited run. The original request fingerprint is retained separately.

This is explicitly a **retrospective artifact identity**, not a recovered service `response_id`. Identical historical execution records are conservatively treated as copies; if two real executions left exactly identical records, they cannot now be distinguished. Filesystem modification times are not promoted to execution timestamps. Local checkpoint hashes establish consistency, not service-side authenticity.

New calls through `selfplay.Calls` persist `<request_id>.attempt.json` before invoking the backend. Its `execution_id` is `local-attempt:<random UUID>` and is copied into the completed response or failure checkpoint. The attempt's timestamp records local invocation intent, not a service receipt. A cached call keeps its existing execution ID; a separate invocation gets another ID even with identical input and identical usage. Copying both checkpoints keeps the same ID. Inconsistent result/attempt IDs or conflicting results for one ID fail validation.

An attempt with no result is unresolved. It blocks automatic retry and consumes the finite invocation budget conservatively. Its usage is unknown, not zero. A malformed answer returned with known usage is recorded as a failed attempt with that usage retained. Historical hashless failure files are not silently trusted by this strict importer; they require a separately documented migration.

## Offline import

```sh
python3 -m runaway.execution_ledger \
  --root decision-memory-v1 --out execution-ledger
```

Use a new output directory. The tool verifies request and result hashes and writes one normalized `records/*.execution.json` per execution identity plus `summary.json`. It does not invoke a model, modify original artifacts, or invent upstream IDs. Full provenance and original artifact paths/hashes remain available for audit. Unresolved attempts and missing usage are counted separately from known usage totals.

This run's ready-to-import local ledger is `runs/decision-memory-v1/execution-audit/ledger/records`. The public JSON is a reproducible readout; it is not an additional set of service calls.

## Collector integration

For the central collector, register **only** the normalized `*.execution.json` directory for this new experiment. Do not also register its raw `*.response.json` files or the public summary. Leave the already registered older self-play source unchanged. Use a separate source kind, for example `memory_execution`, and deduplicate by `execution_id` in a separate namespace:

```python
# Inside the collector's source dispatch; add/normalize/summed already exist.
elif kind == 'memory_execution':
    x = self.json(path)
    p = x.get('provenance', {})
    us = [normalize(u) for u in p.get('usage', [])]
    us = [u for u in us if u is not None]
    # Missing or partially invalid usage must stay unknown.
    measured = x.get('usage') is not None and len(us) == len(p.get('usage', []))
    add(tid, 'memory-execution:' + x['execution_id'],
        summed(us) if measured and us else None,
        p.get('resolved_model') or p.get('model_requested'), path)
```

Validate the importer output and `summary.json` manifest before registration. Keep the original `request_id` as a diagnostic, never overwrite it with an invented response ID. Copies under different paths must have the same execution identity. An identity collision with different usage must produce an explicit conflict, not silently select or invent another ID. The existing older `memory_response` rule can remain for its historical scope; it must not be used to ingest this ledger by request fingerprint.

Minimum collector regression: two independent executions with the same request, a copy of one execution, an unresolved attempt and a conflicting same-ID record. This repository tests those cases offline, plus changed legacy usage, cached reuse, hash tampering, preserving usage after a parse failure and conservative finite-budget handling. The central collector and its source configuration are maintained separately; producing this ledger does not itself assert that central totals have been updated.
