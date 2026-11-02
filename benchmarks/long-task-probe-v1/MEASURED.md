# Closed long-task52 result: card 40/40, matched transcript tail 26/40

The 52 planned local Codex inference attempts completed on 2026-11-02, requesting
`gpt-6.1-sol`. All eight full-transcript controls qualified before extraction.
All eight new cards were valid. There were no missing cases, invalid products,
skipped readers, retries, repairs or unused slots. The scope is closed.

The result supports retention on this **controlled long-context derivative**.
It is not independent semantic acceptance, naturalistic human fidelity, a new-world
holdout, repeated-generation stability, cross-model/harness validation or a
production-default change. The earlier short questions, references and scores
remain unchanged. No original-inventory progress is inferred from this probe.

## Fixed endpoint and comparison

Eight fictional people in four dependent template families contribute five cases
each. Each card/tail case must be correct in two separate reader invocations and
both option orders: four answers must agree with the fixed author reference.
These are 40 person/case endpoints, not 160 independent samples. Each person has
one newly generated card. Full controls have one invocation/person and two option
orders; they are admission gates, not a matched repeat-stability comparison.

| Strict cases | Whole card | Own equal-character transcript tail |
|---|---:|---:|
| All planned | 40/40 | 26/40 |
| Known | 28/28 | 14/28 |
| Unknown | 12/12 | 12/12 |
| Missing | 0 | 0 |

Paired cases: 26 both correct, 14 card-only, 0 tail-only, 0 neither. All 14 tail
losses were known cases answered U in all four answers (56 answer entries).
No first/second-read or option-order disagreement was observed in this run.
This describes returned choices; it does not independently diagnose whether each
tail loss came from omitted text, incomplete context or retrieval failure.

| Task role | Planned | Card | Tail |
|---|---:|---:|---:|
| Future choice, including undecided condition | 16 | 16 | 12 |
| Recorded execution order | 8 | 8 | 4 |
| Past observation | 8 | 8 | 4 |
| Acceptance/rejection commitment | 8 | 8 | 6 |

These task roles are intentionally separate. The pooled score includes past
facts and commitments; it is not a pure future-preference or personality score.

## Character footprint

Both full controls and raw tails use every message's role and text, in order,
with JSON keys, source IDs and episode IDs removed. This avoids crediting the
card just for removing JSON wrappers. Message text alone is 2,008–2,016 characters,
still above the 1,536 whole-card ceiling. The card includes its fixed header/guide.

| Profile | Full role-labelled transcript chars | Whole card chars | Card /5 | Tail /5 |
|---|---:|---:|---:|---:|
| repair0 | 2235 | 742 | 5 | 3 |
| repair1 | 2215 | 912 | 5 | 3 |
| field0 | 2230 | 841 | 5 | 4 |
| field1 | 2210 | 1012 | 5 | 3 |
| kitchen0 | 2230 | 859 | 5 | 4 |
| kitchen1 | 2210 | 1026 | 5 | 3 |
| music0 | 2238 | 777 | 5 | 3 |
| music1 | 2218 | 1031 | 5 | 3 |

Matched whole-card/full-transcript character ratios range from about 1:2.15 to
1:3.01. The raw tail has exactly its own card's character count and can start
mid-message. This is a simple chronological-tail baseline, not optimal retrieval,
equal-token material or a Shannon information-compression measurement.

## Reported usage and practical cost limit

| Stage | Attempts | Input tokens | Output tokens | Input + output |
|---|---:|---:|---:|---:|
| Shared no memory | 4 | 31,410 | 338 | 31,748 |
| Own full transcript | 8 | 76,017 | 888 | 76,905 |
| Source-only extraction | 8 | 79,582 | 39,030 | 118,612 |
| Card reading | 16 | 137,296 | 1,776 | 139,072 |
| Matched-tail reading | 16 | 136,212 | 1,568 | 137,780 |
| Total | 52 | 460,517 | 43,600 | 504,117 |

Cached input 14,208 and reasoning output 5,409 are reported subsets; do not add
them to the total again. Cache-write input is 0. No usage receipt is missing.
These are CLI-reported counters including request/schema/harness overhead,
not independent billing records or verified internal RPC counts. Served-model
identity and upstream retries are not independently observable.

**The fidelity result does not establish end-to-end cost savings.** Despite
equal characters, card reading used slightly more reported input/total tokens
than tail reading over the same 16 invocations. Extraction adds another 118,612
reported tokens. Future reuse, pricing, caching and alternative extraction wires
need separate measurement; no monetary or amortized-product saving is claimed.

## Provenance, remaining limits and reproduction

The 192 messages are authored extensions of the same short-bank people and
references. Corrections and active-record recency positions were designed before
the calls, counterbalanced by role across the four families. This is neither a
random history sample nor eight independent authors. Unscored operational facts
remain in the sources; 40 correct endpoints do not establish that every detail
was preserved. Source/query/reference/encoder/reader inputs were frozen before
execution. No question, card or reference was repaired after seeing responses.

Paired-person rescoring reuses the same card responses on 32 divergent
person/cases; it yields 0/32 against those opposite references. This follows from
the correct own responses and opposite labels. It is algebraically dependent,
not a new wrong-card experiment or independent evidence of persona fidelity.

Post-close audit recomputed all requests, raw/schema decoding, artifacts, usage,
control gates and scores; the owned temporary sleep guard was absent after exit.
Only reviewed fictional requests, raw answer values, artifacts and safe counters
are exported. Local grants, machine paths and private transport envelopes remain
outside the repository. The original observations remain sealed.

```sh
python scripts/replay_long_task_probe.py
python -m unittest discover -s tests -p test_long_task_evidence.py -v
```

The [portable archive](measured.synthetic.json) and its checksum retain all
52 observations, denominators and the 14 tail losses. Eight archive damage checks
reject scope/input/source/question/reference changes, own-parent/request
substitution, reclaimed slots, changed usage,
altered raw responses/artifacts and unsupported independence/stability claims.
The report also omits unrelated inherited inventory counters and recomputes
stage usage totals without double-counting the cached/reasoning subsets.
Replay uses injected archived values only; it sends no new model requests.
All 52 attempts are used and the scope has no remaining experimental authority.
