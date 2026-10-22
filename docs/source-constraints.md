# Preserve source constraints explicitly (experimental v2)

Use `distill --format constraints-v2` when your selected trajectory explicitly
defines finite feature values and two actions, with at least one actual user
choice. Ordinary resumes and open-ended narratives should continue using the
default `distill` path. v2 is an explicit, bounded experiment; it does not turn
every biography into a decision rule.

Try the entire local path with a **hand-authored fictional toy-lamp example**:

```sh
python3 -m runaway distill --format constraints-v2 \
  --input examples/constraints-sources.synthetic.json \
  --answer examples/constraints-answer.synthetic.json \
  --budget-chars 512 --out lamp-taste
python3 -m runaway export lamp-taste/portable.json
```

This makes zero model calls. The source contains one observed choice: with
nobody present, turn off the toy lamp. It does not promise a stable rule family,
so the card preserves that observation and leaves the presence case unknown.
The included answer demonstrates transport and validation, not automatic
extraction quality.

## Use your selected trajectory

Use the [existing role-labelled JSON format](automatic-support.md). Select the
episodes yourself; sources are never scanned. Exact feature values, action
vocabulary, rule definitions and current scope must be supported by user quotes.
Assistant suggestions are not user choices. A family is permitted only when the
user explicitly promises a stable, exhaustive finite set of possible rules.
Otherwise `family` must be `null` and the card covers actual observations only.

With any LLM or harness, prepare a request and import its strict JSON answer:

```sh
runaway distill --format constraints-v2 --input selected-sources.json \
  --budget-chars 512 --prepare > request.private.json
# Give this request's system, prompt and schema to your chosen LLM.
runaway distill --format constraints-v2 --input selected-sources.json \
  --budget-chars 512 --answer answer.private.json --out my-constraints
```

Both commands run locally without a model service call. Alternatively, explicitly
ask the logged-in Codex backend to make **one attempt**:

```sh
runaway distill --format constraints-v2 --input selected-sources.json \
  --backend codex --model YOUR_MODEL --budget-chars 512 --out my-constraints
```

It sends the selected sources to that service. There is no automatic retry,
repair, second extraction or fallback call. Keep the same budget when preparing
and importing. If the source cannot be represented, the answer has invalid
evidence, or the full card cannot fit, import/export fails explicitly. To try the
ordinary path, select `--format support-v1` yourself; that is also the default.
v2 uses its measured fixed renderer and rejects `--layout rows` / `relayout`.

The finite limits are 1–6 features with 2–8 values each, at most 256 joint
states, exactly 2 actions, 1–64 observations and optionally 1–16 candidate rules.
Selected source JSON must fit 96 KB. The whole public Unicode budget is
300–16,000 characters; 512 is a useful experimental starting point, not tokens.
The compiler retains every source-compatible candidate, including ambiguity,
and includes the remaining rule meanings, feature values and unknown boundary
in the public card. It does not expose only opaque candidate IDs or truncate
instructions to fit. Missing conditions require agreement across all possible
completions and compatible rules. Outside scope, unobserved combinations without
a family promise, conflicting rules or an absent known action stay unknown.

## Carry the card to another harness

```sh
runaway attach my-constraints/portable.json --project /path/to/project \
  --target codex,claude,opencode,antigravity,deepseek
runaway doctor --project /path/to/project
runaway choices prepare --card lamp-taste/portable.json \
  --questions examples/constraints-questions.synthetic.json --answer-format text
```

These operations make zero model calls. `prompt.md` is the complete copyable
card; `portable.json` works with the existing exporter, choice reader and native
file adapters. Binding files successfully does not verify that a particular
running harness loads them or reproduces the choices. See [harness setup](../QUICKSTART.md).

`profile.private.json` stores all selected sources, the wire answer, provenance
and source hash. Its artifact type is `source_constraints_profile`, distinct
from v1. `contract.private.json` contains the converted finite annotations;
`compilation.private.json` records every candidate's observation conflicts.
`summary.private.json` reports the mode and complete public size. Explicit
generation additionally stores the request, raw response and any failure.
Directories are new, private and never overwritten.

Review the actual public text before sharing: v2 preserves verbatim scope and
rule meanings, which may contain identifying details. Quote, role, chronology
and finite-consistency checks **do not** certify semantic translation,
completeness, privacy or personal fidelity. All exports remain
`candidate_unvalidated`. The [six-person synthetic study and consumed parity
check](../benchmarks/source-constraints-v2/README.md) support this narrow path;
unstructured real-person and cross-model fidelity remain unverified.
