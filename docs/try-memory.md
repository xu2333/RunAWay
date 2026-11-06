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

Plain text is your self-report. For mixed-speaker conversations, preserve roles:

```json
{"schema_version":1,"sources":[
  {"id":"s1","episode_id":"launch","role":"user",
   "text":"需求未验证时，我愿意先上线小版本，再决定是否扩展。"},
  {"id":"s2","episode_id":"launch","role":"assistant",
   "text":"助手候选仅是上下文，不是用户背书。"}
]}
```

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
