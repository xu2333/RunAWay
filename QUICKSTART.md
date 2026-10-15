# RunAWay

**Your taste, to go.** 把你的经历，变成带得走的 taste。

RunAWay builds an evidence-linked representation of how a person chooses and judges, then exports a portable prompt. The detailed profile is the core; playful short cards remain a separate prototype interface.

This is a working CLI prototype. Generated profiles are editable hypotheses, not validated personality replicas. It includes a local review page; a hosted service, mini-app and public package release are not shipped yet.

## Start locally

Python 3.9 or newer; the core has no runtime dependencies.

```sh
python3 -m pip install .
runaway --help
```

Without installing, replace `runaway` with `python3 -m runaway` from this directory. The distribution name is `runaway-taste`; no PyPI release is implied.

### Try it without an account

```sh
runaway demo --out my-run
```

This writes a complete, pre-generated **fictional** book-club example: a readable prompt, source-linked profile, model critiques and local review page. No login, network request or model call is needed. It does not infer anything about you. Open `my-run/prompt.md` or `my-run/review.private.html`, then try attaching `my-run/portable.json` to a disposable project. Use `build` below to process your own explicitly selected material.

## One command, from experience to portable prompt

Use an explicitly selected narrative (`.txt` / `.md`) or role-labelled conversation (`.json`). Plain text is treated as your self-report: do not paste mixed-speaker logs into it. The fictional example can be run without using personal material:

```sh
# Offline preview: chunks and maximum number of model calls.
runaway plan --input examples/multi-episode.synthetic.json --budget-chars 2400

# Explicitly sends this selected input to the logged-in Codex service.
runaway build --input examples/multi-episode.synthetic.json --backend codex \
  --model YOUR_MODEL --budget-chars 2400 --out my-run

# Copy my-run/prompt.md into a chat, or attach to native project instructions.
runaway attach my-run/portable.json --project /path/to/project --target codex,claude,opencode
runaway doctor --project /path/to/project
```

Open `my-run/review.private.html` in a browser to read the prompt, every candidate interpretation, exact quotes, model critiques and unresolved omissions. It is self-contained, uses no scripts or external requests, and remains local. All output files are private until you review their contents, including the portable prompt.

The pipeline extracts each source chunk, critiques support against its source fragments, connects dependencies across chunks, withholds unsupported claims and their linked groups, then writes a natural-language compact expression and critiques its faithfulness. If compaction loses conditions or exceeds the budget, it falls back to selecting complete evidence groups. If even those cannot fit, detailed output remains available and compact output is explicitly unavailable. Candidate claims and critiques are retained for correction. A same-model critique can repeat the extractor's mistakes; it does not establish fidelity or completeness.

| Output | Use |
| --- | --- |
| `prompt.md`, `portable.json` | Compact prompt and native harness transport, when the budget is feasible |
| `detailed.private.md`, `detailed.portable.json` | Full review-supported representation, without a short-card limit |
| `candidate.private.json` | Every extracted claim, including withheld ones |
| `profile.private.json` | Review-supported claims, linked conditions and unknowns, with original sources |
| `review.private.html`, `review.private.json` | Evidence review and possible omissions requiring correction |
| `compact-export.private.json` | Included and omitted claims, exact size, fallback reason |
| `*.step.private.json` | Cached model outputs, usage/provenance and request fingerprints |

Every detailed or compact artifact remains `candidate_unvalidated`. The detailed profile has no branding or personality taxonomy. `--budget-chars` counts the entire prompt in Unicode characters, not tokens; native harness block delimiters add a small transport overhead.

Source chunks default to 16,000 UTF-8 bytes. `--chunk-bytes` accepts 2,000–128,000. Splits preserve source IDs, roles, episode boundaries and character offsets; oversized messages overlap by up to 128 characters. This preserves input coverage but cannot guarantee that long-distance context survives per-chunk interpretation. Claims merge additively, so duplicates may remain. Global linking/review requests have a 256 KB limit and fail explicitly when exceeded. This prototype does not support arbitrarily large archives.

For N chunks, `plan` reports at most 2N + 3 calls (2N + 2 for one chunk). It is a call count, not a price or token estimate. No automatic paid retries. To continue after a failed call, explicitly rerun the identical command with `--resume`; completed calls are reused. The failed call may already have incurred usage. A cached structurally invalid answer fails again rather than silently calling the model again; choose a new run after correcting the input or extraction code. Output/configuration changes are rejected. After a hard process kill, check that it has stopped before removing a stale `.build.lock`. Never edit cached results to hide a failed review.

## Compress without silently dropping conditions

For tighter compression of an existing profile, check every statement, scope, evidence basis, condition, exception and unknown separately:

```sh
runaway profile compression-plan my-run/profile.private.json --budget-chars 1000
runaway profile compress my-run/profile.private.json --backend codex \
  --model YOUR_GENERATOR_MODEL --review-model YOUR_REVIEW_MODEL \
  --budget-chars 1000 --attempts 2 --out my-compression
```

This sends the profile's projected constraints and necessary counter-context to Codex, without sending all original supporting source messages. It does not invent questions or hypothetical user choices. A reviewer must cite exact substrings from the compressed prompt for every preserved reference facet and flag unsupported additions. Failed candidates receive bounded repair feedback. Generation and review models are explicit; using the same model is recorded. All verdicts remain model judgments, not independent personal-fidelity validation.

`--attempts` accepts 1–3 and costs at most two calls per attempt; over-budget candidates skip review. The complete prompt, including its fixed header, must fit. If no candidate passes every facet, only the detailed fallback and diagnostic attempts are saved: no compact `portable.json` is silently installed. Completed calls can be reused with identical arguments and `--resume`. There are no automatic transport retries.

To check an existing prompt in one review call:

```sh
runaway profile compression-audit my-run/profile.private.json --prompt existing-prompt.md \
  --backend codex --review-model YOUR_REVIEW_MODEL --budget-chars 1000 --out my-audit
```

The initial `build` compression retains its earlier paragraph-level checker; this explicit second pass provides finer checks without re-extracting your sources. See [compression measurements and limits](COMPRESSION.md) for the fictional development comparison. Reference retention is separate from RIG or prediction of real future choices.

To test prediction of actual later messages, use `runaway eval freeze`, `eval check`, and `eval run`. They freeze the detailed/compact representations and local model hashes, validate recorded follow-ups, and compare four conditions using actual token probabilities. `eval import` converts explicitly supplied Codex thread pages, excluding known automation and recording selection reasons. See [the evaluation guide](EVALUATION.md) for the data format, optional local scoring dependencies and limits. Previously used development episodes do not become independent evidence merely by being scored again.

## Detailed personal representation: manual control

Start with an explicitly selected, role-labelled source file. Source and episode IDs must be unique per source / consistent per episode; use `context` for curator descriptions, not `user`. The source file has this shape:

```json
{
  "schema_version": 1,
  "sources": [
    {"id": "message-1", "episode_id": "project-a", "role": "user", "text": "Your actual message or narrative"},
    {"id": "message-2", "episode_id": "project-a", "role": "assistant", "text": "The actual surrounding assistant response"}
  ]
}
```

Generate through your logged-in Codex CLI, or prepare a request for another model:

```sh
runaway profile generate --input sources.json --backend codex \
  --model YOUR_MODEL --out my-profile

# Alternative: use your own model and import its JSON result.
runaway profile prepare --input sources.json > profile-request.private.txt
runaway profile import --input sources.json --answer profile-answer.private.json \
  --out my-profile
```

`profile generate` explicitly sends the selected sources to Codex in a single extraction call, without the `build` review stages. The other commands are offline; choosing to send a prepared request to a model is your own step. No history is auto-scanned. This single-call path rejects inputs above 256 KB; use `build` for bounded chunking and merging.

Each claim retains its statement, evidence basis, scope, conditions, exceptions, exact source quotes and links to related claims. Bases distinguish self-report, observed choice, inference and current task requirements. There is no fixed personality taxonomy, eight-claim limit or 1,200-character profile limit. Missing evidence may produce only unknowns. The validator rejects absent/misattributed quotes and non-user support; it cannot determine whether a claimed inference is justified or whether all relevant details were found.

**All profile artifacts are private**, including the detailed prompt. Unlike legacy short-card bundles, the profile embeds selected original messages, with source hashes and provenance:

- `profile.private.json`: full evidence-linked candidate and selected source text.
- `detailed.private.md`: all claims with scope, conditions, limitations and counter/context evidence.
- `export.private.json`: source/profile hashes, included claims and exact output size.

Export the full profile, a selected set of claims, or a character-budgeted subset:

```sh
runaway profile export my-profile/profile.private.json --out full-export
runaway profile export my-profile/profile.private.json --budget-chars 2400 --out small-export
runaway profile export my-profile/profile.private.json --claims claim-a,claim-b --out task-export
```

Each export creates `prompt.md`, `portable.json` and `export.private.json` in a new private directory. Review the text before sharing or placing it in a repository. The `build` command additionally creates `detailed.portable.json`, accepted directly by `runaway attach`; no conversion to a legacy short card is needed.

The `profile export` budget exporter is a **deterministic selection baseline, not learned semantic compression**. It keeps whole claims with their conditions and exceptions, keeps linked claims together, and retains all unknowns. It reports every omitted claim, marks partial text, and refuses budgets too small for a complete group. Selection follows profile order, not a validated importance ranking. `--budget-chars` counts the entire injected text in Unicode characters, including wrappers; it is not a token budget. Missing contradiction links cannot be detected automatically.

## Correct a profile without regenerating everything

```sh
# Creates an editable answer, source copy and immutable base profile.
runaway profile checkout my-run/profile.private.json --out my-edit

# Edit my-edit/answer.private.json in a text editor.
# Add explicitly supplied evidence to sources.private.json if needed; keep existing sources unchanged.
runaway profile revise my-edit/base.private.json \
  --answer my-edit/answer.private.json --sources my-edit/sources.private.json \
  --reason "Restore the condition that changes this choice" --out my-revision

runaway profile diff my-edit/base.private.json my-revision/profile.private.json
runaway attach my-revision/portable.json --project /path/to/project --target codex,opencode
```

All these steps are offline. The old profile stays intact. `revision.private.json` records changed fields, additions, removals, uncertainty and evidence changes; the new profile records its predecessor and your edit reason. The revision is a local editorial action, not authenticated user endorsement or independent verification. Previous model-review verdicts are not carried over as approval of changed content.

Existing source messages cannot be edited, relabelled or removed in this revision path. Add a correction as a new source with a new ID and the correct speaker; new claims still need exact user-role quotes. To correct a fundamentally wrong source import, create a fresh profile instead. Deleting a claim also requires resolving references to it; the validator will reject dangling links. The CLI does not verify that a revised interpretation logically follows its quote.

Revisions export the full detailed prompt, preserving conditions. For a smaller, deterministic selection of complete evidence groups:

```sh
runaway profile export my-revision/profile.private.json --budget-chars 2400 --out my-small-revision
runaway attach my-small-revision/portable.json --project /path/to/project --target codex,opencode
```

The standalone `profile generate` / `import` commands also create `detailed.portable.json`, and every `profile export` creates `portable.json`. Manual prepare/import remains available for any LLM; use `--previous` on import to record a predecessor, or prefer `revise` when correcting existing evidence locally.

## Legacy short-card generation

Use your existing logged-in Codex CLI. Choose a model available to your account explicitly:

```sh
runaway generate --input experience.txt --kind experience \
  --backend codex --model YOUR_MODEL --out my-card
```

This command sends **only the selected input and extraction prompt** to Codex for one tool-free generation, using the CLI's existing authentication. It runs in a temporary empty directory with project instructions, memory, tools, plugins and browsing disabled. The backend uses CLI features tested with version 0.160.0; older or newer incompatible CLIs may require adapter changes. It never scans your history or silently retries a paid call. The 64 KB input limit fails explicitly rather than truncating your evidence.

`--kind` accepts `experience`, `resume`, or `trajectory`. Weak evidence, such as a job title alone, should produce a tentative expression with limits. JSON validation checks quote existence and structure; it cannot prove that the interpretation is correct or automatically remove every identifying fact.

Output:

| File | Purpose |
| --- | --- |
| `my-card/prompt.md` | Complete portable prompt; review, then copy or share |
| `my-card/card.json` | Structured portable card with a content ID |
| `my-card/evidence.private.json` | Source quotes, interpretations, input hash and generation metadata; keep private |

An existing output directory is never overwritten. No source resume or full trajectory is copied into the output bundle. Review the actual public fields before sharing; the full folder includes private evidence.

## Use another LLM or an existing harness

No subscription to a particular provider is required for the core. Prepare the request, paste it into your preferred LLM, save its JSON answer, then import it locally:

```sh
runaway prepare --input experience.txt --kind experience > request.txt
# Ask your chosen LLM to process request.txt and save its answer as answer.json.
runaway import --input experience.txt --kind experience \
  --answer answer.json --out my-card
```

To edit a generated card, edit the answer fields, retain valid evidence, and import into a new output directory. This creates a new content ID rather than hiding changes under an old identity.

## Attach to a project

```sh
runaway attach my-card/card.json --project /path/to/project \
  --target codex,opencode,deepseek,antigravity --dry-run
runaway attach my-card/card.json --project /path/to/project \
  --target codex,opencode,deepseek,antigravity
runaway doctor --project /path/to/project
```

All four targets above share a **single managed block in `AGENTS.md`**. Cursor, Pi, Cline and Windsurf/Cascade can use that same binding. Other targets:

| Target | Native project file |
| --- | --- |
| `codex`, `opencode`, `deepseek`, `antigravity`, `cursor`, `pi`, `cline`, `windsurf` | `AGENTS.md` |
| `claude` | `.claude/rules/runaway.md` |
| `gemini` | `GEMINI.md` |
| `copilot` | `.github/copilot-instructions.md` |

See `runaway targets` for official sources. A file binding is not a promise that every installed version/configuration loads it. Start a **new session** after attaching, updating or removing. `doctor` checks local integrity; it does not pretend to inspect live model context.

Binding names do not isolate tools: any harness reading `AGENTS.md` can see its block. Install only the bindings you need. Some versions/configurations read multiple native files; `--target all` can therefore load duplicate text. `doctor` flags common duplication cases. Codex's `AGENTS.override.md` can shadow `AGENTS.md`; attaching for Codex refuses that unresolved case.

Attach is idempotent. Attaching a new card updates every binding already managed in that project so they carry the same expression. Existing text outside RunAWay's marked block is preserved. If someone edits inside the managed block, update/removal stops rather than discarding those changes. Symlinks in managed paths are rejected; global settings, credentials, tools, and hooks are untouched.

```sh
runaway detach --project /path/to/project --dry-run
runaway detach --project /path/to/project
```

Removal deletes only RunAWay's blocks, preserving original text and new text outside the blocks. Newly created empty instruction files are removed; empty directories may remain. Regular write failures are rolled back. A process kill or concurrent external editor can still interrupt a multi-file operation; inspect `.runaway/install.json` before recovery. The local installer lock prevents two RunAWay installers from operating together.

Generated prompt text may become version-controlled when attached to repository instruction files. `.runaway/` is local installer metadata; ignore it in the receiving repository. Attaching does not commit, push, publish or change `.gitignore` there.

## Copy to any chat

```sh
runaway export my-card/card.json
runaway export my-card/card.json --out portable-prompt.md
```

There is no background server, remote codebook, or extra model call for exporting, attaching, updating or removing. The receiver sees the full expression, including its scope. Token cost includes the full prompt and native wrapper, not just the nickname; CLI size output reports bytes and characters, never calls them tokens.

## Development

```sh
python3 -m unittest discover -s tests -q
```

`examples/synthetic-experience.txt` and `examples/profile-sources.synthetic.json` are fictional smoke-test inputs, not evidence that personalization works. Broader research on real held-out choices remains separate from transport and schema tests.

The current research workspace contains private data outside the distributable package. Packaging explicitly includes only the `runaway` module and public quickstart; do not upload the entire research directory as the public repository.
