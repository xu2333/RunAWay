# Test the actual compressors, without changing the reference answers

`runaway.production_adapters` connects the synthetic metric to the same browser
request, validator and bundle builder used by the app, and to the new
`bound_memory.make_request` / `bind` path. It does not choose or invoke a service.

First freeze a synthetic metric, then an adapter plan:

```sh
python3 -m runaway.synthetic_metric freeze --out my-metric --seed 91831
python3 -m runaway.production_adapters --metric-run my-metric \
  --budgets 128,384 --generator-model YOUR_MODEL --out my-adapters
python3 -m unittest tests.test_production_adapters tests.test_generation_diagnostics
```

All commands above are offline. Default metric budgets are UTF-8 bytes. For
tokens, freeze the metric with the existing GGUF tokenizer described in
[the metric guide](SYNTHETIC-METRIC.md). The adapter requires the same tokenizer
identity and an explicitly supplied counting function; it never downloads one.

Each person/budget has two stages:

| Stage | Actual product path | Maximum calls |
| --- | --- | ---: |
| Shared extraction | Browser request → model answer → browser validation/bundle | 1 |
| New compression | The same extracted profile → bound request → model answer → binding | 1 |

The first stage produces the current browser prompt and the profile used by
the second. This compares compression **conditional on shared extraction**.
The new method has an extra model call; report its additional cost. Batch cost
counts shared extraction once; a standalone new pipeline costs both stages.
Neither path silently adds review or repair calls. No semantic audit is implied
by source quotes, coverage IDs or private bindings.

The frozen character request limit is `max(200, min(16000, 2 * budget))`. This is
a declared request constraint, not a character/token conversion. Every complete
rendered memory, including its fixed header, must also pass the actual frozen
token/byte budget. Oversized output fails without truncation or another attempt.

`run(plan_directory, calls, count, tokenizer)` requires an explicit checkpointed
executor such as `selfplay.Calls`. There is no implicit backend or network CLI
entry point. Transport failure stops later calls. Malformed extraction skips
its dependent compression. Empty profiles keep an informative current memory
but fail the new branch compiler. All planned person/method/budget rows survive.
Feed `memories.private.json` into `runaway.metric_jobs prepare`, then independently
decode and score the resulting jobs as described in the metric guide.

The freeze seals source hashes, models, stages, budgets and tokenizer identity.
Changing them requires a new plan. Model requests receive only visible history,
public protocol or the extracted profile. They never receive queries, answer
keys, event truth or seed. Exact request replay is handled by `Calls`; recorded
failures and unresolved attempts cannot be silently retried.

Tests use mocked answers and the existing fictional demo profile. They verify
plumbing and failures, **not LLM compression quality**. The broader synthetic
metric measures recovery of a finite family of known rules. A later real-person
test must hold out authentic future choices and compare against full history,
no memory and similar-but-different people. That test cannot be replaced by a
model judging its own resemblance to a person.

## Timeout evidence

Codex's [documented JSONL interface](https://learn.chatgpt.com/docs/non-interactive-mode)
exposes turn progress and completed usage. The previous wrapper discarded
partial events when timing out, so the historical upstream cause remains
unknown. A UTF-8 bridge repair is not evidence of service recovery.

New timeouts preserve sanitized event counts, an observed CLI thread ID if
present, output sizes/hashes, completed usage if present, and wall/monotonic
elapsed times. They never store message/reasoning text in generic diagnostics,
credit partial answers, invent usage or retry. POSIX subprocesses run in an
isolated group; timeout cleanup kills that group and bounds output draining.
Local fake-process tests exercise descendant pipe inheritance without a model
or network. These tests establish bounded local cleanup, not provider health.
