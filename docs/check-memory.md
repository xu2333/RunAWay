# Check a memory against its selected source

This repository-only Node 22+ tool prepares the **same questions** with three
materials: selected original experience (`full`), your complete portable prompt
(`card`), and an empty material (`none`). You choose the LLM and bring its three
answers back. The tool never calls a model, fetches history or uploads files.
It helps locate losses; it does not certify a personal replica.

## Prepare a real case

Select the exact experience used to make your memory. Preserve user, assistant
and tool roles in that text; an assistant suggestion is not your preference.
For a future-choice check, remove the target episode from **both** extraction
and full-source material before generating the memory. Use actual alternatives
and facts available before the decision, rather than a retrospective explanation
that reveals the answer. The tool cannot detect semantic leakage or certify
that an episode is independent.

Write `questions.json` with 1–32 questions and 2–8 distinct options each:

```json
[
  {"id":"q1","scenario":"The situation and limits known at the time.",
   "options":{"A":"The first actual option","B":"The second actual option"}}
]
```

In a separate private file, record your choice before seeing any predictions:

```json
{"q1":"A"}
```

Reference values are option labels or `U`, with exactly the same question IDs.
Use `U` only for a declared **source-underdetermined** case after checking the
source, not for a missing answer or to make a bad prediction score well. A known
choice may still be unsupported by the selected experience. You can omit the
reference entirely and leave all answers unscored.

```sh
node scripts/check_memory.mjs prepare \
  --source selected-experience.txt --memory prompt.md \
  --questions questions.json --reference reference.private.json \
  --out my-check
```

Each selected input must fit 64 KB. Material is preserved as UTF-8 text; JSON
files require strict JSON without duplicate keys. No truncation or repair is
performed. The default reader is the published `standard` protocol; optionally
choose `--reader-mode coverage` for all three arms. Neither is a validated
cross-provider guarantee.

The output directory is private (700; files 600):

| File | Use |
| --- | --- |
| `full.request.private.md` | Send only when you choose to disclose the selected full experience |
| `card.request.private.md` | Send only when you choose to disclose the compact prompt |
| `none.request.private.md` | Same task, with empty personal material |
| Corresponding `.json` requests | Exact structured request and answer schema |
| `prepared.private.json` | Local case, references, requests and dependency fingerprints; **do not send this file** |

The reference stays outside every request. This does not remove information
that you accidentally included in the source, prompt, question or options.
Inspect each request before choosing to send it. Use three separate fresh
conversations with the same model/settings, without showing one answer to the
other conditions. Those actions and any service fees are yours; preparation
does not send anything or authorize an experiment.

The empty-material arm still follows the same **source-constrained reader**.
It may answer U. This is a control for that protocol, not a general-purpose AI
recommendation baseline. No equal-length source-tail comparison is supplied.

## Import without losing failures

Save each complete answer as a JSON object mapping IDs to the exact option
text, or `U`. Option labels are not accepted as predictions. Then run:

```sh
node scripts/check_memory.mjs import --prepared my-check \
  --full-answer full-answer.json --card-answer card-answer.json \
  --none-answer none-answer.json --out my-check-result
```

You may omit a response flag for a condition that never returned. At least one
response flag is required. Missing, unreadable or invalid responses return exit
code 2 **with a report**, retaining all questions in the denominator. A partial
answer rejects that entire arm; missing keys never become U. A complete import
returns 0 even if choices disagree: command success is not memory success.

Preparation/import setup failures also return 2 with a fixed error code and no
content on stderr. They may leave incomplete output. Existing output directories
are never overwritten. Changed source/reference packets, request files, manual
request text or relevant local code require a fresh preparation. These are local
consistency checks, not authenticated provenance; a malicious user can recreate
a packet and its hashes. Bare model JSON does not prove which request, model,
settings or service produced it.

The result includes a private per-question table (`review.private.json`) and a
text-free aggregate (`summary.json`). Both start private. The private table
contains reference choices and returned text. Review even aggregate counts
before sharing. These files are separate from the single-choice browser feedback
format; the feedback-intake command does not silently treat them as that format.

## Read the diagnostic

Every question belongs to one partition; none are dropped:

| Observation | Interpretation to inspect |
| --- | --- |
| Any arm missing/invalid | Incomplete response set; no three-way conclusion |
| No declared reference | Unscored, even if predictions agree |
| Full source disagrees with reference | Source control not established; inspect source sufficiency, task wording, reference and reader |
| Source/card/reference all U | Unknown retained on a self-declared underdetermined case |
| Source/card match a known reference | Choice retained; separately record whether no-memory also matched |
| Source matches a known reference, card U | Candidate known-to-unknown loss |
| Source matches a known reference, card chooses differently | Candidate choice loss |
| Source/reference U, card chooses | Candidate unwarranted certainty |

These are source/answer relationships, not causal proof. A no-memory difference
on one case is not measured information gain. This tool computes no RIG, log
loss, population accuracy, unique-user count or independent significance.
Material lengths are Unicode characters, not tokens or service-cost estimates.
No prompt is automatically changed, and no result authorizes a follow-up model
call. Inspect the original source and decision before deciding what to fix.

## Offline software check

```sh
node --test tests/memory-check.test.mjs
```

The eight-question fixture uses hand-written mock answers. It covers retained
choices, known-to-unknown loss, a different-choice loss, unwarranted certainty,
unknown retention and a failing source control. A separate partial import keeps
all eight questions incomplete. These are software tests with zero model calls,
not new measured fidelity results. See the [published compression measurements](../REGRESSION-PROGRESS.md)
for actual model evidence and its consumed-fictional-source limits.
