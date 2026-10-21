# From selected trajectories to a portable taste card

`distill` is a one-call experimental path that extracts choices **and their observed support** directly from role-labelled trajectories. It preserves private source quotes and renders a compact, named card without a hand-written scope declaration. Exact anchors, roles, chronological supersession references and the complete character budget are checked locally. These checks do not prove semantic completeness or human fidelity.

```sh
runaway distill --input selected-sources.json --backend codex \
  --model YOUR_MODEL --budget-chars 768 --out my-taste
runaway attach my-taste/portable.json --project /path/to/project --target codex,claude,opencode
runaway doctor --project /path/to/project
```

The first command explicitly sends only the selected input to your logged-in Codex service and makes one model call. It never scans other chats. Use `runaway targets` for the other documented file adapters, including Antigravity and DeepSeek. File attachment is not proof that every harness/runtime loads the file or reproduces the choices equally well. `prompt.md` can also be pasted into another LLM directly.

Try the complete import/export path without an account, using a real pre-generated answer from the synthetic test:

```sh
runaway distill --input examples/support-sources.synthetic.json \
  --answer examples/support-answer.synthetic.json --out tiny-demo
```

This makes zero model calls and does not infer your preferences. The example was generated from a fictional trajectory by the model, not a hand-written scope declaration.

Prefer role-labelled source JSON, using the existing source format:

```json
{"schema_version":1,"sources":[
  {"id":"e1-context","episode_id":"e1","role":"user","text":"Automatic classification is familiar, about4%wrong, local-only and immediately reversible."},
  {"id":"e1-suggestion","episode_id":"e1","role":"assistant","text":"I suggest checking each item."},
  {"id":"e1-choice","episode_id":"e1","role":"user","text":"I choose automatic classification and restore mistakes."}
]}
```

A plain `.txt`/`.md` is treated as a user-authored narrative. Do not paste mixed-speaker logs into that format: convert them to role-labelled JSON first. A résumé with no observed choices may yield only explicit unknowns. Biography or job prestige must not stand in for a preference.

For another LLM or harness, prepare and import without model service calls:

```sh
runaway distill --input selected-sources.json --prepare > request.private.json
# Give only that request's system/prompt/schema to your chosen LLM.
runaway distill --input selected-sources.json --answer answer.private.json \
  --budget-chars 768 --out my-taste
```

The public surface is `prompt.md` / `portable.json`. `profile.private.json` retains the source-support extraction format, full selected sources, private quotes and provenance. `summary.private.json` reports actual size and the unverified status. Review public prose before sharing: literal quote validation does not automatically remove sensitive details or certify inferred traits. The new source-support private record is distinct from the older claim-profile format used by `runaway profile`.

The compiler first renders complete prose. If it exceeds the budget, repeated phrases can be replaced by a self-contained literal glossary; the complete glossary is counted, and expansion must reproduce the prose exactly. `expanded.private.md` keeps the plain version and `encoding.private.json` records the round-trip proof. If lossless packing still cannot fit, or an anchor is invalid, export fails explicitly; no truncated card is exported. Generation preserves the request, raw response and failure locally, makes no automatic retry, and never overwrites an existing directory. Offline import uses the same validator and renderer as generation. When possible branches all choose the same action, missing detail need not force `U`; this does not extend the action outside the union of observed conditions.

## Local layouts without another model call

The experimental `rows` layout puts each existing condition/action pair on its own line: `「condition」→chosen action`. The original `paragraph` layout stays the default. Both preserve the same extracted branches, priority order, name, tagline, guidance and unknown statements. Embedded delimiters, arrows, backslashes and line breaks are escaped reversibly. Literal round-trip checks do not prove semantic support or behavioral fidelity.

For an existing private `distill` profile, re-export offline:

```sh
runaway relayout my-taste/profile.private.json --layout rows --out my-taste-rows
runaway relayout my-taste-rows/profile.private.json --layout paragraph --out my-taste-prose
```

Both commands make zero model calls. They check the private record/source checksums and revalidate its source quotes, roles, references and whole character budget. Checksums detect damage; they do not authenticate the author or prove the inferences true. Every output directory must be new. Over-budget output fails without truncation. Private records retain selected original sources; inspect public text before sharing it. This command accepts the source-support profile from `distill`, not the older claim-profile format.

You can also add `--layout rows` when importing a saved extractor answer or explicitly generating a new `distill` result. The extraction prompt/schema stay unchanged; layout is applied locally afterward. Keep `--layout rows` on the import command when using `--prepare` with another LLM. A paragraph/rows change can also alter literal dictionary packing and token count; neither character length nor an exact round trip establishes how a different LLM will read it. [Frozen same-reader layout comparison](../benchmarks/support-extraction-v1/LAYOUT.md).

## Replay a choice with any LLM

Prefer a browser? Open **`/choices.html`** on the static app, paste `prompt.md`, add a scenario and 2–8 options, and copy the request to your chosen LLM. Paste its JSON back to inspect the choice and optionally download a private trial record with your rating/correction. Nothing is automatically submitted or saved; editing the memory/question invalidates the current prediction. This is an informal trial, not an independent fidelity measurement.

Create a tool-free reader request from your card and explicitly supplied options:

```sh
runaway choices prepare --card tiny-demo/portable.json \
  --questions examples/choice-questions.synthetic.json --answer-format text > choice-request.private.json
# Give the prompt/schema to your chosen LLM, then save its raw JSON.
runaway choices import --questions examples/choice-questions.synthetic.json \
  --answer examples/choice-answer.synthetic.json --answer-format text
```

The included answer is fictional and pre-generated; it is not a new model call. Both commands run offline. Import returns the offered action text, its current display label and whether the model chose unknown (`U`); it never performs the action or corrects a decision from memory or a reference answer. Text mode requires an exact offered string, including punctuation. Duplicate JSON keys, unexpected/missing answers and near-matches are rejected. The default `label` mode remains available.

Text mode asks for the action's original wording rather than its A/B/C position. It separates selecting a preferred action from tracking letters across reordered options. This can increase schema/answer tokens; it is not a smaller memory or an automatic faithfulness certificate. The [51-call comparison](../benchmarks/support-extraction-v1/READOUT-FORMATS.md) improved Luna's known-case results but lost some unknown cases; Luna still failed the strict reader gate. Scope inference, unknown handling and model limitations still apply.

### Experimental applicability check

Add `--reader-mode coverage` to `choices prepare`, or explicitly select “先核对适用条件（实验）” on `/choices.html`. The generic reader prefix checks whether the recorded conditions apply before choosing. It does not turn a decision observed at one number into a rule over a numeric range, or choose among conflicting branches when the question does not distinguish them. Exhaustive recorded branches that all choose the same action still support a known choice.

Only the instruction prefix changes; the same memory, options, answer schema and exact decoder are used. There is no program rule that changes a predicted answer to `U`. `standard` remains the default. In the [expanded comparison and fixed repeats](../benchmarks/support-extraction-v1/COVERAGE.md), coverage improved Luna's full-history results but **did not reliably repair its short-card unknown judgments** and lost some previously correct known cases. Sol passed this synthetic full/card comparison; there was no Sol-standard control on the new scenes, so that is not evidence of a Sol-specific improvement. This is an explicit experimental option, not a fidelity guarantee.
