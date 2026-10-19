# Temporal memory: preserve changes before shortening them

D-0018 lost a restored constraint in the **extracted profile**, before the extra compressor ran. The new optional `timeline` route preserves individual observations, changes and retraction edges. Code computes the effective rules and renders whole domain groups into a portable prompt. It does not ask a second model to paraphrase those rules.

**Current status:** usable [browser route](web/dist/timeline.html) and manual CLI. D-0023 extended the route to complete six-domain synthetic histories: actual memories346/336 tokens, current112/112, historical0/38. [Actual results, costs and limits](TEMPORAL-SCALE-RESULTS.md). Only one consumed development pair; general and real-person fidelity remain unverified. The earlier [D-0021 single-domain diagnostic](TEMPORAL-RESULTS.md) and D-0018 remain sealed.

[D-0024 negative controls](TEMPORAL-DISCRIMINATION-RESULTS.md) then measured actual reading of swapped-person and hard-constraint-deleted memories: current88/112 and100/112, with150/150 concordance to each fixed manipulation. This supports sensitivity to those two specific corruptions on the same consumed pair, not new-domain or real-person fidelity.

**New lexical transfer did not pass:** [D-0025](TEMPORAL-TRANSFER-RESULTS.md) stopped after5 calls. Full-source controls were300/300, but the first extraction classified two explicit conflicting observations as unmodeled. All27 action checks passed; source-event coverage caught the loss. No compressed memory was read in that batch. The live extraction instruction was corrected afterward; D-0026 tested that repair separately below.

[D-0026 repair diagnostic](TEMPORAL-CONFLICT-REPAIR-RESULTS.md) subsequently passed on its first consumed pair: both conflicts preserved,54state checks passed, memories311/312tokens, current112/112, historical0/38. This supports the consumed-case repair, not D-0025 transfer success or general fidelity; that batch evaluated only the first pair.

[D-0027](TEMPORAL-CONFLICT-TRANSFER-RESULTS.md) then tested that remaining pair with unchanged instructions/rendering: memories309/308tokens, current112/112, historical0/38. Its histories had already been source-read; this is a separate consumed-data batch, not a fresh holdout or a completed rerun of D-0025.

[D-0028](TEMPORAL-CONCISE-RESULTS.md) tested a shorter encoding on the same four consumed policies: 264/265/261/260 actual tokens (15.32% fewer memory tokens in the frozen vocabulary), current224/224, contrasts6/6, historical0/76. It is now an optional output in the browser and CLI; readable output remains the default. This is not total service-cost savings, full-trajectory losslessness or new-person validation.

## Use it

Prepare a request from your experience text or existing role-labelled source JSON:

```sh
python3 -m runaway timeline prepare --input experience.txt > request.txt
```

Send that request to an LLM you choose and save its complete JSON answer as `answer.json`. Import locally:

```sh
python3 -m runaway timeline import --input experience.txt \
  --answer answer.json --budget-chars 768 --out my-timeline
```

`my-timeline/prompt.md` and `portable.json` contain the candidate current-state memory. `timeline.private.json` retains the original sources, exact spans and event graph; `delivery.private.json` records included/omitted domains and budget checks. Review the interpretation and portable text before use or sharing. The source-to-event interpretation is still a model candidate.

Use the resulting portable expression with the existing harness installer:

```sh
python3 -m runaway attach my-timeline/portable.json \
  --project /path/to/project --target codex,claude,opencode
```

This installs the same prompt through existing file bindings; it is not new cross-provider behavioral validation. Other existing harness targets work through the same adapter.

## What is checked

- **Retraction edges:** if B retracts A and C retracts B, A becomes effective again. Multiple independent retractions of A continue to disable A until all relevant retractions are disabled. Forward references/cycles are rejected.
- **All conditions:** `when_all` means conjunction. One false literal makes that conditional rule inapplicable; missing context that could change the result stays unknown.
- **Priority:** active hard constraints precede exceptions, which precede regular evidence. Conflicting applicable actions at the same conditional tier remain unresolved. Explicit regular replacement resets earlier regular evidence; clears reset the entire earlier domain state. Strongest regular evidence wins; equal opposing evidence remains unresolved.
- **Source anchors:** the model selects supplied user-source span IDs. Code copies exact codepoint ranges. Domain/action/predicate phrases must occur verbatim in the referenced spans. No rewritten quote field is accepted. This checks lexical grounding and structure, not whether the chosen event interpretation is true.
- **Budgets:** code renders the whole prompt, counts it, and withholds export if it does not fit. It keeps the complete private graph. It never truncates, automatically chooses a subset, or silently retries.

For actual token limits, install the existing evaluation extra and supply your GGUF vocabulary:

```sh
python3 -m runaway timeline export my-timeline/timeline.private.json \
  --budget-chars 256 --budget-tokens 128 --tokenizer /path/to/model.gguf \
  --out smaller-timeline
```

Without a tokenizer, the token count is explicitly unmeasured. An explicit `--domain '产品验证'` selects a whole observed domain group; omitted domains are reported and the prompt says unlisted areas are unknown. This is a partial export, not full coverage. Scope and conditional groups are never cut mid-rule.

For the optional concise grammar, choose **紧凑版** in the browser or add `--format concise` to either CLI import or export:

```sh
python3 -m runaway timeline export my-timeline/timeline.private.json \
  --format concise --budget-chars 768 --budget-tokens 288 \
  --tokenizer /path/to/model.gguf --out concise-timeline
```

The complete grammar explanation is inside `prompt.md`; take the whole prompt. The same `portable.json` transport works with existing harness adapters, and the private graph is retained unchanged. Domain selection stays explicit; a budget failure withholds the entire text. The format is not guaranteed shorter for every input. D-0028 validates only the four consumed synthetic policies, with no new cross-provider or real-person claim.

Inspect the private graph at an earlier event or under explicit conditions:

```sh
python3 -m runaway timeline resolve my-timeline/timeline.private.json \
  --domain '产品验证' --context '{"方向尚未验证":true,"改动不可撤销":true}'
```

`--through EVENT_ID` selects an inclusive event cutoff. The portable expression explicitly covers **current state only**; it does not reconstruct history for another LLM. Historical records remain in the private graph.

## Evidence and remaining uncertainty

[`examples/temporal-development`](examples/temporal-development) contains two **hand-annotated, consumed D-0018 development excerpts**, not outputs of a newly tested model. Program rendering of each one-domain annotation is 178 characters / 115 actual frozen-tokenizer tokens, including the new compact boundary. That does not establish a six-domain 128-token solution or successful model extraction.

The known error chain is source record r18 → retract r17 → retract r16, while the old extracted profile asserted the constraint was withdrawn. The new graph representation can express that chain directly; graph execution restores r16 without another free-form compression step. A model can still extract the wrong edge, action, chronology or conjunction, so real extraction and independent reading remain necessary.

The diagnostic used **six generations**: two full-source readers, two source-to-event extractions, two actual portable-memory readers. One consumed paired development unit; 16 current +4 historical queries per reader condition, all denominators retained. Four conjunction cases and both option orders remain. The 384-token/768-character cap isolated semantic extraction; actual complete memories were120/121 tokens. No D-0018 remainder was reused. These are not fresh holdout or population results.

```sh
python3 -m unittest discover -s tests -p 'test_temporal*.py' -v
```

Injected fake backends exercise stop conditions, accounting and the six-call path. They are not service quality evidence. Real invocation requires a separate direct human approval matching the newly frozen proposal, with unchanged source/runtime hashes, single-use intent, 180-second calls plus 2+2-second cleanup, zero retry/repair/resampling, and immediate whole-batch stop on control, extraction, budget, format, transport, usage or state failure.
