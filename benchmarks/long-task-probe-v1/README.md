# Long-source task probe

The [actual closed52 result](MEASURED.md) is now available: card40/40 versus
matched transcript-tail26/40,with no missing/invalid/skipped observations. This
is a controlled length-stress result,not human or independent holdout validation.
Reported card-read tokens were slightly higher than equal-character tail-read
tokens,and extraction adds118612tokens;net product cost savings are unproven.

## Frozen preparation record

The following describes the original pre-execution package. `protocol.json`
retains its unapproved intake flags; the later private grant did not rewrite it.
Preparation itself made0service attempts. Actual observations are separate above.

The [short task bank](../task-scenarios-v1/README.md) has about 480 canonical JSON
characters per person. It can calibrate question roles, but a 1,536-character
memory ceiling would not impose compression. This protocol extends the same
eight fictional people to 24 messages each: provisional decisions, later user
corrections, assistant suggestions and operational context. It retains the same
40 person/cases, question wording, options and author reference values.

This is **controlled length/retention stress**, not new-world generalization,
naturalistic human data, independent semantic review or a holdout. Four paired
template families remain dependent. Operational context also contains valid
unscored decisions; the probe is not a complete-personality reconstruction test.
The four active user records occupy predetermined recency ranks, counterbalanced
by role across families: positions 5/6, 11/12, 17/18 and 23/24. This placement is
designed, not a distribution sampled from real histories. Old draft values are
explicitly corrected; a later assistant suggestion does not become a user decision.

Each source has 3,587–3,615 canonical JSON characters, of which 2,008–2,016 are
message text. **Even the text alone exceeds the whole-card ceiling.** Metadata
removal therefore cannot by itself satisfy that ceiling. Exact counts are in
`protocol.json`; these are Unicode character counts, not token counts or entropy.

The unchanged source-order-v3 encoder receives its own full structured source,
the 1,536 whole-card character budget and fixed guidance/schema. It sees no
questions, references, old cards, previous responses/scores or manual binding.
One new card per person is planned; this does **not** measure repeat-generation
stability. The inherited encoder/reader dependencies remain hash-locked.

The raw comparator is stronger than a suffix of JSON: `plan.transcript` keeps
every message's role and text in order while removing source IDs, episode IDs and
JSON keys. Both the full-history control and the tail use this same transcript
layout. The tail is exactly the last N characters, where N is that person's
whole compiled card length including its header/guide. It can start mid-message;
there is no repair, chosen span or reordering. This remains a simple tail
heuristic, not optimal retrieval. Character matching is not token/cost matching.

## Finite proposed schedule

| Stage | Maximum local CLI attempts |
|---|---:|
| Four shared no-memory controls and eight own full-transcript controls | 12 |
| Source-only extraction, one per person | 8 |
| Two card reads per person, both option orders each | 16 |
| Two own equal-character transcript-tail reads per person | 16 |
| Total | 52 |

Each full control must answer its own five cases correctly in both option orders,
without missing answers, and recover more known cases than its family's shared
no-memory response. All eight must qualify before extraction 13. A failed control
closes the entire scope. The shared no-memory responses are reused within each
pair, not counted as independent person observations.

Each view has a fixed 40-case denominator (28 known / 12 unknown). One producer,
two independent reader invocations and two option orders give four answers per
case; all must be correct. These repeats/orders are not independent samples.
Task-specific summaries separate future choice, execution, past facts and
commitment. An invalid parent skips only its own four planned card/tail reads;
its five cases remain missing in **both** view denominators. Missing responses
never shrink a denominator and there is no best-of selection.

Paired-person rescoring reuses the same card answers on 32 divergent person/cases.
It costs no extra request and is algebraically dependent, not a fresh wrong-card
experiment. No confidence interval or population significance is claimed from
the 40 authored cases. Old scores remain unchanged.

Control, transport, schema, decode, unknown usage, requested-model, runtime,
input-integrity or owned-guard failure closes the remaining scope. No retry,
repair, truncation, resume, replacement or slot replenishment is allowed. Unused
slots expire. The 180-second local-child timeout is neither a total-duration nor
a token/money cap. Local CLI attempts are observable; internal service requests,
server-side retries and served-model identity are not independently verified.

## Reproduce offline

```sh
python benchmarks/long-task-probe-v1/check.py
python -m unittest discover -s tests -p test_long_task_probe.py -v
python benchmarks/long-task-probe-v1/plan.py --out /tmp/my-new-long-task-review
```

The last command writes a new review directory only: 20 exact static requests,
32 own-parent dynamic request rules, references separately marked private, and
input/implementation SHA-256 manifests. It does not call a service or grant
authority. `engine.run` requires explicit caller-supplied invocation and guard
callbacks; an actual host must verify a **new, exact human grant** before use.
The old scopes are closed. No automatic service backend is included here.

Eight instrument tests cover unchanged questions/labels and grounded user quotes,
counterbalanced recency, source/question isolation, exact transcript tails,
52-slot fixture completion, failure closure, invalid-parent/missing accounting,
one-bad-order failure, input drift and the mandatory actual-mode owned guard.
Oracle fixture success is controller calibration, not model fidelity evidence.
New model/API experiment attempts: **0**. Proposal unapproved, no token/money cap
accepted, no production-default change and no claim of measured compression gain.
