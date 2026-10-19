# A runnable synthetic metric for compression quality

New opt-in [temporal partial-context calibration](TEMPORAL-PARTIAL-CONTEXT.md) exposes two false passes: treating missing conditions as false passes every complete-context question; deleting conflicting observations preserves U answers while losing conflict state. It reuses the existing fidelity scorer and product codec, keeps historical denominators and complete input lengths, and makes zero model calls. Existing calibration and sealed service results remain unchanged.

The main quality measure is **query recovery over every planned query**:

```text
Q(memory) = correct answers / all predeclared queries
```

An answer is correct if it is in the query's executable allowed set. Missing output, failure and timeout remain in the denominator. A missing answer is never credited as an informed “unknown.” Fact recovery, preference strength, hard constraints, conditions, exceptions, updates, revocations and matched-person disagreements are reported separately. No LLM judge supplies the reference answer.

## Try it without a model service

Python 3.9+ is sufficient for the default byte-budget calibration:

```sh
python3 -m runaway.synthetic_metric freeze --out my-metric --seed 91831
python3 -m runaway.synthetic_metric calibrate --run my-metric
```

The default budget unit is explicitly **UTF-8 bytes**, not a claim about LLM tokens. For actual token budgets, use an already available GGUF tokenizer and the optional evaluation environment, with the same file at both steps:

```sh
python3 -m runaway.synthetic_metric freeze --out token-metric \
  --seed 91831 --gguf /path/to/existing-model.gguf
python3 -m runaway.synthetic_metric calibrate --run token-metric \
  --gguf /path/to/existing-model.gguf
```

The tokenizer hash is frozen. Tokenization loads a vocabulary and performs no model inference, network calls or downloads. The measured example uses the existing Qwen3 0.6B tokenizer. Re-running the same completed calibration validates and reuses its sealed artifacts; a newly reconstructed run produces the same scores. Source, world or plan changes require a new snapshot.

For the interactive checked-in result:

```sh
python3 -m http.server 8081 --bind 127.0.0.1 --directory examples/metric-view
```

Open `http://127.0.0.1:8081`. The local project dashboard also serves this view at `/metric`.

## What is generated and isolated

The generator creates structured dated events first, then renders them as synthetic first-person histories. The public event protocol defines stronger-vs-weaker preferences, hard limits, conditional exceptions, explicit replacement, clearing and revocation, including revoking a revocation. Queries are answered by applying that protocol to the original event truth.

The default fixture has 16 people: eight development and eight evaluation people. Their parameter combinations and history-rendering templates are disjoint. Each matched pair differs only in a specific conditional preference, making “averagely similar” memories insufficient. Each person has 24 predeclared queries. The sets share a finite event ontology; this is not arbitrary population or language generalization.

`world.private.json` holds events, parameters, queries and answers. **Do not send it to a compressor.** `compressor-jobs.jsonl` contains only opaque persona IDs, history, budgets and the public protocol. `decoder-jobs.jsonl` contains only a chosen memory, public query/options, an opaque ID and the protocol. It excludes hidden strata, event truth, seeds and correct answers. The audit viewer intentionally reveals answers to a human reviewer and is not a model-input file.

## Calibration results, not product ranking

The first step uses a transparent protocol reader and reference memory adapters to check whether the metric detects damage. `current_reference_naive` keeps only the last record per key; `new_reference_codec` retains dated events while removing narrative padding. **These names are adapter slots, not measured old/new RunAWay or LLM compression results.** Real compressor/reader results must be imported separately.

At the 1,024-token budget on the eight evaluation people:

| Memory / control | Correct / planned | Hard constraint violations | Both matched people correct |
| --- | ---: | ---: | ---: |
| No memory | 16/192 | 0, with 16 constraint abstentions | 0/12 |
| Full history, actually read | 192/192 | 0 | 12/12 |
| Last-record reference | 78/192 | 0 | 12/12 |
| Event-preserving reference | 192/192 | 0 | 12/12 |
| Delete critical exceptions | 172/192 | 0 | 0/12 |
| Delete hard constraints | 188/192 | **4** | 12/12 |
| Swap similar people's memories | 168/192 | 0 | **0/12** |
| Randomly delete half the events | 116/192 | 2 | 0/12 |
| Lose later updates | 118/192 | 0 | 0/12 |
| Simulated timeout | 0/192, all missing | No observed action; all missing | 0/12 |

Deleting constraints leaves a 97.9% aggregate score while violating four hard requirements. Swapping nearly identical people scores 87.5% but loses every distinguishing pair. These are concrete sensitivity checks for the metric. The full-history score is measured through the reader, not hard-coded to 100%; this particular protocol reader recovers it perfectly. No inference about an LLM's full-history capacity follows.

The output includes nine budget points from zero through 1,024, actual complete-memory token counts, quality relative to the full-history baseline, coverage, each critical layer and all simulated failures. The full-history control is unbudgeted and identified as such. No result is collapsed into a quality/token ratio. Program runtime, memory length, and external generation/use costs are separate; this calibration used **zero external model calls**.

Optional normalized retention is:

```text
(Q(memory) - Q(no memory)) / (Q(full history) - Q(no memory))
```

It is undefined when the denominator is nonpositive or at most `1e-9`. Negative and above-one values are retained. Here a total timeout is worse than the no-memory baseline, which correctly abstains on genuinely unknown questions. Neither baseline is a forced-guess human or language-model benchmark.

## Score an actual compressor later

The [actual product adapters](PRODUCTION-ADAPTERS.md) connect browser extraction and program-bound compression to this metric. Their offline tests verify integration without measuring LLM quality.

That first approved service pilot is now complete: [both actual paths matched the no-memory baseline](PILOT-RESULTS.md). The result exposes missing temporal support and a task mismatch; it is separate from the reference calibration above.

Use the isolated history jobs to generate memories, then the isolated decoder jobs with the actual selected memories. Decode to the categorical IDs in `answer_options`, not arbitrary paraphrases. A prediction file maps `persona_id` to `{query_id: answer_id}`:

```sh
python3 -m runaway.synthetic_metric score --run my-metric \
  --predictions predictions.json --out scored.json
```

Partial output stays partial; missing queries are scored as misses. Invalid persona/query/answer formats are reported, with rejected outputs retained in the planned denominator. Allowed sets can represent declared ambiguity; arbitrary model-judge preferences do not replace truth.

For actual compressor outputs, a safer bridge predeclares the entire trial matrix and exports only usable memories to a decoder:

```sh
python3 -m runaway.metric_jobs prepare --run my-metric \
  --memories actual-memories.json --conditions current,new \
  --budgets 128,384 --out actual-jobs
python3 -m runaway.metric_jobs score --run my-metric \
  --trials actual-jobs/trials.private.json \
  --answers decoder-answers.json --out actual-quality.json
```

`actual-memories.json` is an array of `{persona_id, condition, budget, memory}`. Missing/failed memories use `null`; a deliberately empty memory is a valid zero-length input. Decoder answers map exported `trial_id` to `{query_id: answer_id}`. The adapter keeps every planned person/condition/budget, rejects oversized outputs without truncation, isolates public decoder queries, and seals its trial manifest. Missing compressor outputs cannot disappear from the denominator. With a frozen GGUF tokenizer, add the same `--gguf` file at prepare time. The `full_history` baseline is explicitly unbudgeted. Actual generation and decoder service costs stay in their executor's ledger, not this offline tool.

Before a service comparison, freeze fresh unpublished people, budgets, actual old/new adapters, models, a finite call limit and stopping rules. Measure full-history and no-memory readers, keep corrupted controls, and stop compression-quality interpretation if the reader cannot execute the protocol. The prepared pilot contract caps a separate fresh black-box comparison at 24 calls; it has not run. The prior timed-out batch is sealed and no unused budget is reused.

See the [complete result](examples/synthetic-metric-results.synthetic.json), [synthetic evidence](examples/synthetic-metric-evidence.synthetic.zip), and standalone viewer. Calibration snapshots and intermediate protocol/export refinements are preserved locally; the refinements changed no generated truth or scores. Published fixtures are development data for subsequent model tuning. Synthetic query recovery is an engineering metric, **not evidence of fidelity to actual people**.
