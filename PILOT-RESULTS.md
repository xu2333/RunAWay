# Actual compressors: a failed retention pilot

Both product paths scored **4/48, exactly the no-memory baseline**, at both
budgets. All 192 compressed-memory answers were valid `U` abstentions. Nothing
timed out or disappeared. No method wins this pilot.

| Actual product path | Budget / mean actual tokens | Correct / planned | Normalized accuracy retention | Matched distinctions |
| --- | ---: | ---: | ---: | ---: |
| Browser extraction + prompt | 128 / 81 | 4/48 | 0% | 0/3 |
| Browser extraction + prompt | 384 / 136 | 4/48 | 0% | 0/3 |
| Same extraction + bound compression | 128 / 107.5 | 4/48 | 0% | 0/3 |
| Same extraction + bound compression | 384 / 157 | 4/48 | 0% | 0/3 |

These are actual model outputs through the [production adapters](PRODUCTION-ADAPTERS.md),
not the transparent reference codecs in the [metric calibration](SYNTHETIC-METRIC.md).
Two freshly generated synthetic people, 24 dated queries each, were fixed before
execution. The generator requested `gpt-6-luna`; the independent reader requested
`gpt-6.1-sol`. The CLI did not report resolved model identities. Both use the same
service; this is not cross-provider validation. Actual memory tokens use the
frozen Qwen3 0.6B tokenizer, not an assertion about service-billed tokens.

## The reader passed the controls

| Reader input | Correct / planned | Matched distinctions |
| --- | ---: | ---: |
| Full history | 48/48 | 3/3 |
| No memory | 4/48 | 0/3 |
| Similar person's full history | 42/48 | 0/3 |
| History with exceptions deleted | 43/48 | 0/3 |

The full-history gate required at least90% and no hard-constraint errors. The
wrong-person and deleted-exception sensitivity gates also passed. Comparing the
four raw scores is allowed by that contract, but their identical baseline score
provides no useful ranking signal. Each compressed-memory condition missed all
four constraint queries by abstaining; there were **zero observed constraint
violations**, a different quantity from correct constraint recovery.

## What broke, and what this does not establish

All eight generated prompts lacked explicit day or record anchors. They describe
current preferences; the frozen queries ask what held at particular historical
times. The shared extraction also turns dated records into broader statements
and often quotes only the sentence body. A source quote or private binding can
therefore pass while the memory loses the temporal support the reader needs.

This is evidence of a representation/task mismatch. It is consistent with the
all-unknown answers, but no causal repair ablation was run. Retrospective state
reconstruction is also a different task from carrying current taste into new
choices. **Do not turn this score into a claim about real-person fidelity**, or
silently change the questions or denominator after seeing it. A future test must
specify which task it targets, preserve required scope/validity information and
freeze new unseen decisions before execution.

## Calls and cost

Exactly24 experiment invocations completed:8 control reads,4 shared extractions,
4 bound compressions and8 memory reads. Each generation entry used a180-second
deadline; the longest observed generation was15.65seconds. No retries, repairs,
replacement people or old batch allowance were used. All24 reported usage:
207,514input +14,575output =222,089tokens. The3,448reasoning tokens are included
within output, not added again. These local usage records are not an invoice.

Current's shared extraction cost31,502input /5,893output. New additionally cost
27,079input /1,744output for compression. Charge **both stages** to an independent
new pipeline; count shared extraction once in the batch. Memory-reading cost
and the8 controls are separately listed in the result JSON. There is no combined
quality/token utility score and no claimed likelihood-based information gain.

## Recompute without a model

[Result JSON](examples/pilot-results.synthetic.json) and
[sealed synthetic evidence](examples/pilot-evidence.synthetic.zip) include the
original request/response/attempt records, memories, predictions, metric truth,
source snapshots and a checksum manifest. Files named `private` belong to the
scorer interface; all data in this archive is explicitly synthetic. Approval
messages, real histories, credentials and workspace files are excluded. Published
fixtures become development data for subsequent experiments.

After extracting the archive into `pilot-replay/`:

```sh
python3 -m runaway.metric_jobs score --run pilot-replay/d0015/metric \
  --trials pilot-replay/d0015/trials.private.json \
  --answers pilot-replay/d0015/decoder-answers.synthetic.json --out replay.json
python3 -m runaway.execution_ledger --root pilot-replay/d0015 --out replay-ledger
python3 -m unittest tests.test_pilot_evidence
```

These commands make zero model calls. They reproduce scoring and accounting;
they do not restart the sealed service experiment.
