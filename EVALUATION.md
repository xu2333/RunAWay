# Does a smaller prompt preserve useful information?

A compression audit checks whether a prompt retains its reference profile. It does not establish that the profile predicts a person's later judgments. This evaluator measures a separate signal: the likelihood of **actual later user text**, under four frozen memory conditions.

No reviewer invents answers or assigns probabilities. An optional local model scores every observed target token before seeing that token, using teacher forcing. The base package still has no runtime dependencies; scoring requires the optional `evaluation` dependencies and an existing local Qwen3 GGUF file. Nothing downloads a model or sends records to a service.

## Freeze before observing evaluation data

```sh
runaway eval freeze my-run/profile.private.json \
  --compact my-compression/portable.json \
  --model /path/to/local-qwen3.gguf \
  --out frozen-evaluation
```

Repeat `--model` to freeze additional model files. `--gpu-layers -1` requests all supported GPU layers; the default is CPU. `--n-ctx` defaults to 8192. The snapshot records full file hashes, complete memory texts, profile and expression IDs, source episodes, source text hashes, settings and a local creation timestamp. The compact expression must come from the same profile.

Four conditions are fixed together:

| Condition | Purpose |
| --- | --- |
| `none` | Context without an extra memory |
| `generic` | A fixed generic instruction, to detect benefits of merely adding a prompt |
| `detailed` | The complete deterministic profile export |
| `compact` | The exact selected portable expression |

Keep the same snapshot for all subsequent cases. Do not rewrite it after viewing results or select only favorable episodes. If a new profile or compressor is tuned using these results, those episodes become development data for that version.

## Supply observed records

Use the actual preceding assistant response and the subsequent user message, preserving text and timestamps. The dataset has `schema_version: 1`, `origin: "observed"`, and a `cases` array. Each case contains:

- `id`: unique case ID.
- `episode_id`: stable original episode identifier, consistent with profile sources.
- `context_scope`: `complete` or `excerpt`; acknowledge omissions.
- `context`: chronological messages, each with `id`, `role`, `text`, and Unix-seconds `timestamp`.
- `target`: the actual user message, with the same four fields.

The last context message must be from the assistant; the target must be from the user. Tool text keeps its original role. IDs use 1–96 ASCII letters, digits, dots, hyphens or underscores. Do not rename source episodes to make overlap checks pass.

```sh
runaway eval check frozen-evaluation/snapshot.private.json \
  --episodes observed-followups.private.json

# Optional dependency installation, performed explicitly by you:
python -m pip install '.[evaluation]'

runaway eval run frozen-evaluation/snapshot.private.json \
  --episodes observed-followups.private.json --out evaluation-results
```

Default `prospective` mode rejects records at or before the snapshot time, records with future timestamps, source episode/message overlap, exact source-text reuse, duplicate targets, invalid speakers and future information in context. **These checks trust supplied metadata.** Local hashes and timestamps cannot authenticate records, detect all aliases or prove that a target was previously unseen. They also cannot prevent selectively supplying favorable future cases. The report always keeps `independence_verified` false.

`--mode development` must be selected when freezing a retrospective or software-test run. It permits old/source-overlapping records, labels the report accordingly and retains chronology, target-identity and score-completeness checks. The [synthetic fixture](examples/evaluation.synthetic.json) is only an engine smoke test; use it with `runaway demo` and development mode. Its output is not evidence about a person.

## Read the paired results

Every model scores identical target tokens under all four conditions. Original target whitespace is preserved; EOS and prompt tokens are not scored. Context overflow fails explicitly instead of truncating. Recorded conversation and memory text use ordinary tokens, so embedded chat delimiters do not become special control tokens.

For each episode, losses are token-weighted within that episode. Across episodes, the report takes the equal-weighted mean of episode losses. With these losses:

```text
RIG(condition) = (loss(none) - loss(condition)) / loss(none)
compact_gain_over_generic = loss(generic) - loss(compact)
compact_nll_increase_over_detailed = loss(compact) - loss(detailed)
detailed_relative_gain_retention =
    (loss(none) - loss(compact)) / (loss(none) - loss(detailed))
```

Positive RIG means the actual text was easier to predict. Negative results remain negative. Retention is `null` when the detailed gain is at or below the frozen 0.01 nats/token denominator floor; this floor avoids unstable division and is not a significance threshold. Retention can exceed one or be negative and is never clipped.

Compare compact against both detailed and generic. A positive RIG alone does not establish personal information transfer. Likelihood also reflects topic, language, formatting and wording; it is not decision accuracy, task utility or a personality score. One episode gives no credible population-level conclusion. Reports include per-episode values and do not manufacture confidence intervals from dependent tokens.

Each run saves the frozen inputs, model/runtime metadata, target token IDs, actual log probabilities, prefix token counts, memory token counts and report. All files are private. Partial runs preserve diagnostics and a failure marker; they cannot produce a complete report. No automatic retries or candidate selection are performed.

The report pairs these loss measurements with actual per-model memory token counts and the compact token reduction against detailed memory. Counts include the complete memory text; scoring-prefix overhead is saved separately in each row. Do not substitute character counts for model tokens.

The current backend supports the Qwen3 chat template and `llama-cpp-python==0.3.36` low-level logits interface. It verifies streamed versus batched scores on a short causal check before scoring. That check is not a numerical error bound for long contexts or proof of cross-model/harness portability. Other architectures must have their templates and scoring behavior validated before being supported.

This release's live model run is a synthetic software smoke test only. It makes no new real-user RIG, compression-utility or independent-fidelity claim.
