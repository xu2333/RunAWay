# Review downloaded choice feedback locally

From a repository clone with Node 22+, select the exact files to inspect:

```sh
node scripts/choice_feedback.mjs summarize \
  --input first-trial.private.json --input second-trial.private.json \
  --input reviewed-summary.json --out new-feedback-review
```

The inputs are the version-2 private trials or version-1 text-free summaries
downloaded from [`/choices.html`](../WEB.md). Older or unrelated feedback
formats are rejected. This command does not scan directories, fetch Issues,
upload feedback, call a model, alter a prompt or modify an input file.

The new output directory contains:

| File | Contents |
| --- | --- |
| `summary.json` | Counts and fixed reason labels; no filenames, hashes, timestamps, prompt, task, options, answers or correction text |
| `review.private.json` | Selected local paths, per-file validation status and event/version hashes for locating records that need inspection |

The directory starts with mode 700 and both files with mode 600. Keep the
review file private. Inspect the summary before sharing even aggregate counts.
An existing output directory is never overwritten. Any rejected input produces
exit code 2 **and a report retaining that input in the denominator**. Setup or
output-I/O failures also return 2, with a fixed error code on stderr; they may
leave incomplete output, so use a new directory after inspecting the failure.

## Counts that keep their meaning

Private records are reconstructed and checked against their exact request,
reference, raw prediction, decoded answer and derived flags. Duplicate decoded
JSON keys, malformed UTF-8/Unicode, changed metrics and unsupported fields are
rejected. Limits are 256 selected files, 2 MB per file, 32 MB read per batch
(plus at most one byte to detect growth past the limit), and 64 JSON levels.
Special files are rejected without waiting for a writer.

A local event key uses the recorded creation time, exact request, prediction
import time and raw answer. Reformatting, renaming or selecting the same record
twice does not add an event. Feedback edits remain versions of that event.
Changed references, reference timing or demo origin conflict rather than being
resolved by whichever file was read first or last. Even reselecting the same
reference at another recorded time is conservatively treated as a conflict.
These hashes cannot authenticate users or prevent deliberate timestamp edits;
distinct local events are **not** distinct people or independent experiments.

Every private event goes into exactly one partition:

| Partition | Treatment |
| --- | --- |
| Conflicting versions | Preserve all file pointers; resolve locally before use |
| Demo or edited demo | Exclude from personal-fidelity conclusions |
| No declared reference | Keep unscored |
| Reference recorded after prediction | Keep outside the manual-review candidate queue |
| Reference recorded before prediction in the page session | Queue for manual source/consent review only |

The last partition separates a declared match, a disagreement and an unknown
answer. Unknown is not automatically a fidelity failure: the original source
may not license that choice. A pre-recorded reference is still self-report; the
app cannot detect predictions seen elsewhere or certify a held-out episode.

Text-free public summaries have no event identity. Their counts stay in a
**separate file denominator**. Identical-content groups are reported for
inspection, but cannot establish whether files came from one person or several,
or overlap the private records. No combined accuracy or unique-user count is
computed. Conflicting ratings are retained as multiple versions, not averaged
or cherry-picked.

## From feedback to a test case

Open the private review file and follow its selected-file indexes. For a queued
case, inspect the original experience, the extraction material, the real
decision and available options, and what the user actually saw before choosing.
The trial download alone does not contain a certified original trajectory.
Resolve conflicts and check source permissions and episode independence before
building a test. Do not feed a revealed answer back into an extractor and call
it a new held-out success. External model evaluation needs its own selected
data and authorization; the collector grants no service-call budget.

The existing [`try_memory.py`](try-memory.md) path can generate a candidate;
the browser can record a local choice; this collector makes those exported
records inspectable. It does not make a user's candidate validated.

## Reproduce the offline wiring check

```sh
node --test tests/feedback-intake.test.mjs
```

The mixed fixture uses ten hand-written/simulated files: seven private files
represent six local events, two identical public-summary files and one rejected
file. Three local events enter manual review (one match, one disagreement, one
unknown); one demo, one post-prediction and one unscored event are excluded.
This is a deterministic software check with zero model calls, not new evidence
of compression quality, real-user fidelity or cross-provider transfer.
