# Experimental condition-aware memory

A repository-only, offline bridge to the frozen source-order / source-coverage
methods. Prepare a request, use a model you choose, import its JSON, then carry
the resulting prompt into the existing harness adapters. Explicit method choice
is required; the installed CLI's default generation flow is unchanged.

## Try a complete example without a model call

```sh
python3 scripts/memory.py demo --out my-memory-demo
python3 -m runaway export my-memory-demo/candidate/portable.json
```

This replays one published fictional c2v response into the same509-character
public prompt. It is an archive replay, not a new generation or your personal
profile. The source, request and raw answer remain in files named `.private.*`.

## Use your own experience or trajectory

```sh
python3 scripts/memory.py prepare --input experience.txt --method coverage \
  --budget-chars 1536 --out my-memory-request
```

Choose `coverage` for the measured generic source-coverage prefix, or `baseline`
for the original source-order-v3 request. Both use the same schema/compiler.
Current comparative evidence is limited to the [published synthetic studies](../REGRESSION-PROGRESS.md).
The ceiling counts the whole public prompt, including its name, tagline and guide.
It is a character budget, not a token or service-cost cap.

`request.private.json` contains the structured `system`, `prompt` and `schema`.
`request.private.md` carries that content/schema for manual chat interfaces.
Either contains your selected source; send it only to the service you choose.
The bridge itself has no model backend, credentials, retry or network request.
Manual Markdown packaging and other providers have not been fidelity-validated.

Save the model's graph JSON as `answer.json` without Markdown fences:

```sh
python3 scripts/memory.py import --prepared my-memory-request \
  --answer answer.json --out my-memory
python3 -m runaway export my-memory/portable.json
python3 -m runaway attach my-memory/portable.json --project /path/to/project \
  --target codex,claude,opencode,antigravity,deepseek --dry-run
```

The existing attach command previews its harness edits with `--dry-run`;
remove that flag when you choose to apply them. Other existing targets include
Cursor,Pi,Cline,Windsurf,Gemini and Copilot. The portable text can also be copied
directly into a chat. To try a personal choice in the browser, paste `prompt.md`
into `/choices.html` and keep the resulting feedback locally;see the
[browser guide](../WEB.md). See [harness setup](../QUICKSTART.md).

## Input, output and limits

A text file is treated as your provided narrative. For agent trajectories, keep
roles explicit rather than pasting assistant suggestions as user decisions:

```json
{"schema_version":1,"sources":[
  {"id":"s1","episode_id":"launch","role":"user",
   "text":"方向未验证时，我愿意先用两天上线验证，再决定是否重构。"}
]}
```

This uses the existing sources schema. Source JSON/text is limited to64KB;
there is no silent truncation. A resume may establish past facts without
establishing a decision preference. Existing instructions preserve unknowns,
conditions, revisions and the distinction between choices and completed actions.

Import verifies the prepared source/request/code hashes, graph schema, literal
source quotes/roles, compiler projection and whole-character budget. It does not
prove that every relevant choice was retained, or that the model's interpretation
is correct. A structurally valid losing card can still import successfully;
status remains `candidate_unvalidated`, with behavioral/semantic verification
flags false. Inspect the result against your source before sharing.

Only `prompt.md` and `portable.json` are sharing candidates. Other generated
files contain source text, quotes, graph history or local import metadata.
They are private, with restrictive file permissions. Existing destinations are
never overwritten. Invalid responses are rejected without repair, truncation or
an automatic model retry. Preparation/import does not read harness histories or
change harness files; attachment is a separate explicit command.
