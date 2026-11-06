# Experimental condition-aware memory

A repository-only, offline bridge to the frozen source-order / source-coverage
methods. Prepare a request, use a model you choose, import its JSON, then carry
the resulting prompt into the existing harness adapters. Explicit method choice
is required; the installed CLI's default generation flow is unchanged.

## Try a complete example without a model call

```sh
python3 scripts/frozen_history.py run scripts/memory.py demo --out my-memory-demo
python3 -m runaway export my-memory-demo/candidate/portable.json
```

This replays one published fictional c2v response into the same509-character
public prompt. It is an archive replay, not a new generation or your personal
profile. The source, request and raw answer remain in files named `.private.*`.

## Use your own experience or trajectory

```sh
python3 scripts/frozen_history.py run scripts/memory.py prepare --input experience.txt --method coverage \
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
python3 scripts/frozen_history.py run scripts/memory.py import --prepared my-memory-request \
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

## Optional source-ID review

An additional experimental pass can review a structurally valid initial v3
graph against the same selected source. Keep the original files and save the
reviewed candidate in a new directory:

```sh
python3 scripts/frozen_history.py run scripts/review_memory.py prepare --original-prepared my-memory-request \
  --draft-answer answer.json --out my-review-request
```

To explicitly use the tested source-ID enum request, add
`--request-schema enumerated` to that command. It lists all selected source IDs
in the request schema; the prompt and binder/compiler stay the same. The
default is `existing`, preserving the earlier measured request. The prepared
manifest pins the selected mode and, for enum requests, its implementation.
Import reads that mode from the prepared bundle rather than choosing a new one.

Use `my-review-request/request.private.json` with a model you choose, or its
Markdown counterpart for a manual chat. Both contain the original selected
source and draft graph. Save the new graph JSON as `review-answer.json`:

```sh
python3 scripts/frozen_history.py run scripts/review_memory.py import --prepared my-review-request \
  --answer review-answer.json --out my-reviewed-memory
python3 -m runaway export my-reviewed-memory/portable.json
```

The response references source IDs; the program supplies whole-message quotes
to the existing compiler. Every selected message must fit2,000characters for
this review entrypoint. Long messages are rejected before preparation rather
than split or truncated. Source IDs and correct quotes do not prove semantic
support or complete coverage. Review is optional, has no automatic backend or
retry, and leaves the original candidate untouched.
Prepared files are checked against the256KB local import limit before writing;
the canonical selected-source limit remains64KB even when readable JSON adds
formatting bytes. Oversized packets fail before an unusable bundle is created.

To replay the measured fictional example without sending anything:

```sh
python3 scripts/frozen_history.py run scripts/review_memory.py demo --out reviewed-demo
python3 -m runaway export reviewed-demo/portable.json
```

The enum example replays a separate395-character reviewed card:

```sh
python3 scripts/frozen_history.py run scripts/review_memory.py demo --request-schema enumerated --out enum-demo
python3 -m runaway export enum-demo/portable.json
```

The [fixed-case study](../benchmarks/source-id-review-v1/README.md) improves one
selected failed card from11/15 at240characters to15/15 at381characters, while
an observed citation-sufficiency gap remains. The subsequent
[unconstrained repeat](../benchmarks/source-id-review-repeat-v1/README.md) leaves
15joint cases missing after two invalid-ID products. In a separately authorized
[matched comparison](../benchmarks/source-id-enum-repeat-v1/README.md), enum
requests produce8/8valid cards and60/60joint parent/case cells; existing
requests produce4/8valid cards and15/60, with45missing. This represents only
two consumed fictional people,30unique person/cases and four posthoc drafts.
The enum card lengths and schema/input costs are not matched to the originals.
These results do not establish sufficient citations, initial-generation
stability, new-scene/general benefit, real-user fidelity or other-provider
performance. An enum lists valid IDs; it cannot certify a valid interpretation.
All new imports remain `candidate_unvalidated`; demo scores are not inherited
by another user's card. Share only the inspected prompt/portable files, not
the source, draft or request files named `.private.*`.

## Fresh-source examples

The [four-person fresh-source experiment](../benchmarks/fresh-enum-pipeline-v1/README.md)
now has an offline example for each initial/reviewed card. To replay the measured
440-character“小团分格记”card without sending any source to a service:

```sh
python3 scripts/frozen_history.py run scripts/demo_fresh_memory.py --person pavo --out fresh-demo
python3 -m runaway export fresh-demo/candidate/portable.json
```

Other fictional examples are`rill`,`tavi`and`wren`;add`--stage reviewed`for the
corresponding reviewed card. The default is the initial card. Both initial and
reviewed cards retain64/64fixed cases in this sample,while own-character raw
tails retain48/64;all four sources are synthetic and each has one initial
model generation. Review increases length/cost without a measured accuracy
improvement here,so it remains an explicit optional step. These examples do not
establish real-person fidelity or stability. Every exported candidate retains
unverified flags;share only the inspected prompt/portable files,not source,
request or graph files named`.private.*`.
