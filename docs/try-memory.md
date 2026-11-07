# Try condition-aware memory

This experimental, repository-only entry uses the same single-pass encoder and
compiler as the [published repeat](../benchmarks/single-pass-repeat-v1/README.md).
It turns one explicitly selected experience or conversation into a portable
prompt. It keeps conditions, revisions and unknowns; it does not certify a
personal replica. The installed CLI's existing defaults are unchanged.

## Start without an account

From a clone of this repository:

```sh
python3 -B scripts/try_memory.py demo --out my-demo
python3 -m runaway export my-demo/candidate/portable.json
```

This replays the published fictional 439-character “两只小抽屉” card. It makes
zero model calls and infers nothing about you. The example's measured score is
not inherited by your future card.

## Use your own selected experience in one call

You need Python 3.9+, a logged-in Codex CLI and an explicit model available to
your account:

```sh
python3 -B scripts/try_memory.py generate --input experience.txt --backend codex \
  --model YOUR_MODEL --out my-memory
```

Choosing `generate --backend codex` sends the selected source and extraction
request to your configured Codex service. It makes at most one local model
child, with a 180-second limit and no automatic retry or resume. This is a call
limit, not a token or price cap. No history is scanned, and no harness files are
changed. A resume alone may support facts without supporting decision preferences.
If the CLI is missing, the command leaves an offline request and makes no backend
attempt; use `request.private.md` with another LLM and import its answer below.

Open `my-memory/candidate/prompt.md`, compare it with your source, and edit a new
request or source if necessary. Structural validation cannot prove that every
important preference survived. All output starts private (directories 700,
files 600); only the inspected `prompt.md` and `portable.json` are sharing
candidates. Other files contain source text, quotations, requests or backend
metadata. Check the sharing candidates for identifiers and sensitive details.

```sh
python3 -m runaway export my-memory/candidate/portable.json
python3 -m runaway attach my-memory/candidate/portable.json \
  --project /path/to/project --target codex,claude,opencode,antigravity,deepseek --dry-run
```

Remove `--dry-run` when you choose to apply the attachment. You can also copy
the prompt directly into another LLM, or paste it into `/choices.html` in the
[browser app](../WEB.md) to try a concrete choice and keep feedback locally.
Other models and providers have not been fidelity-validated by this wrapper.

On the choice page, you can record your own choice before bringing back a
prediction. It stays out of the model request. A later edit is marked as
post-prediction within that page session. Download the complete private trial,
or review a separate text-free summary before choosing to share it. The summary
is voluntary self-report and carries no verified personal-fidelity claim.
Use the [offline feedback collector](feedback-intake.md) to validate selected
downloads and locate disagreements, unknowns or conflicting versions locally.
For a direct source/card/no-memory comparison on questions you select, use the
[offline memory check](check-memory.md). It keeps missing answers and source
control failures visible rather than counting them as successful compression.

## Keep old and current project names

For a history with explicit project renames, choose the experimental alias encoder:

```sh
python3 -B scripts/try_memory.py generate --input experience.txt --backend codex \
  --model YOUR_MODEL --encoder scope-alias --out my-alias-memory
```

It records source-bound name relations separately from action choices and adds
the declared aliases to the public objects. This addresses a measured failure
where the rules survived but readers could no longer identify the project by
its old name. See the [encoding contract](../benchmarks/scope-alias-encoding-v1/README.md)
and [source-only comparison](../benchmarks/scope-alias-comparison-v1/RESULTS.md).
Check the names and their ownership alongside the choices: literal quotations
do not prove that two names really refer to the same thing or that all relevant
names were extracted. Your card remains `candidate_unvalidated`.
Both old and current names become part of the sharing candidates; inspect them
before sharing.

The same selector works with offline `prepare`; `import` reads the encoder from
its prepared packet automatically. Alias packets bind both the encoder and its
compiler fingerprints. Existing packets and the default `coverage` path keep
their original protocol. Both paths use the same one-child limit, private output
handling and portable format; the five harness attachment targets above apply.

## Other LLMs: prepare, then import

Both commands below are offline. Choose your own service for the middle step:

```sh
python3 -B scripts/try_memory.py prepare --input experience.txt --out my-request
# Send my-request/request.private.md to the LLM you choose.
# Save its graph JSON response as answer.json.
python3 -B scripts/try_memory.py import --prepared my-request \
  --answer answer.json --out my-candidate
```

`request.private.json` supplies the exact structured `system`, `prompt` and
`schema`; the Markdown file packages them for manual chat. Manual packaging is
not a measured cross-provider result. Imports check the source, request, manual
packet and relevant compiler fingerprints. An unrelated executor change does
not invalidate these packets. Changed requests or compilers require a new
preparation; imported results remain `candidate_unvalidated`.

## Input and failure behavior

Unlabelled plain text is treated as your self-report. The default `auto` format
rejects obvious role-labelled text instead of attributing the entire conversation
to you. For an explicitly selected, annotated conversation, use `role-text`:

```text
用户：需求未验证时，我愿意先上线小版本，再决定是否扩展。
助手：助手候选仅是上下文，不是用户背书。
工具：执行结果也不代表用户偏好。
上下文：这段讨论发生在项目启动时。
```

```sh
python3 -B scripts/try_memory.py prepare --input episode.txt \
  --input-format role-text --out my-request
```

Inspect `sources.private.json` and `request.private.md` before sending the request
to your chosen service. Preparation reports role counts and
`speaker_labels_verified: false`. Labels are annotations you supply; they do not
authenticate the author. `user` / `我` / `用户`, `assistant` / `助手`, `tool` /
`工具`, and `context` / `上下文` are supported, with English case ignored.
`system`, `developer` and `系统` become context, never request instructions.

Labels start at column zero followed by `:` or `：`. Message text preserves its
Unicode, line endings and whitespace after removing the label and at most one
following space or tab. A single initial file BOM is removed in role-text / JSON
parsing. Empty messages, unlabelled preambles and unclosed Markdown fences fail
the whole input. Inside a fenced code block, apparent role labels remain part
of that message. For quoted labels outside fences, indent them or use explicit
source JSON; an unfenced column-zero label cannot be distinguished from a new
speaker. Sources beginning with recognized runtime/control tags are rejected as
user evidence; review them and annotate context when appropriate. This guard
does not detect every automation message or authenticate selected text.

This annotated-text format is not a parser for native Codex, Claude Code,
OpenCode or other harness logs. Select and review a complete episode, then
provide these annotations or RunAWay source JSON with explicit IDs and roles:

```json
{"schema_version":1,"sources":[
  {"id":"s1","episode_id":"launch","role":"user",
   "text":"需求未验证时，我愿意先上线小版本，再决定是否扩展。"},
  {"id":"s2","episode_id":"launch","role":"assistant",
   "text":"助手候选仅是上下文，不是用户背书。"}
]}
```

`--input-format sources-json` selects that schema explicitly. In `auto`, a `.json`
filename or JSON-looking input must conform to it; unknown chat-export schemas
are rejected. `--input-format narrative` explicitly treats your own prose as a
single user source, including any quoted role labels. It does not verify origin.
The same format flag is available on `generate`; it does not add a model call.

Source files and the canonical selected source must fit 64 KB; packets and
answers must fit 256 KB. Oversize inputs fail explicitly. The default whole-card
budget is 1,536 Unicode characters, including the header, name, tagline and
guide. Other budgets are accepted but do not inherit the published results.

An existing output directory fails before any backend call. Once generation is
attempted, the directory retains its intent and available provenance even if
the response or binding fails. It cannot be silently reused to call again.
Failed responses are not repaired or truncated into a card. If you choose to
try again, inspect the first run and use a new output directory; this is a new
explicit call and may incur usage. A backend-call attempt and local child count
do not prove the number of upstream service requests or its dollar cost.

The new wrapper is tested with archived outputs and simulated CLI events; no
new service call was used to test its wiring. The underlying request/compiler
has measured evidence on four consumed fictional people, not independent
human validation or proof that source citations justify every interpretation.
