# Single-pass generation repeat — measured result

The new scope completes **45 actual attempts / 45 local CLI children**, with
zero invalid products, skipped readers, missing usage receipts or expired
slots. The scope is closed. No request was retried, repaired or replenished.

| Fixed joint endpoint | Card | Own equal-character raw tail |
| --- | ---: | ---: |
| All cases | **64/64** | 48/64 |
| Known choices | **24/24** | 8/24 |
| Correct unknowns | 40/40 | 40/40 |
| Derived knowns | **8/8** | 4/8 |
| Missing | 0 | 0 |

A joint case requires **2 generations × 2 reads × 2 option orders = 8 correct
answers**. Each view keeps 64 unique person/cases, comprising 24 known and 40
unknown cases. The two generations use separate calls and share no cards or
reader feedback. Repeated draws, reads and option orders are not new people.

| Generation | Card /64 | Tail /64 |
| --- | ---: | ---: |
| 0 | 64/64 | 48/64 |
| 1 | 64/64 | 48/64 |

| Person | Generation 0 chars | Generation 1 chars | Each card /16 | Each tail /16 |
| --- | ---: | ---: | ---: | ---: |
| pavo | 439 | 457 | 16/16 | 10/16 |
| rill | 542 | 508 | 16/16 | 10/16 |
| tavi | 519 | 473 | 16/16 | 14/16 |
| wren | 448 | 454 | 16/16 | 14/16 |

Cards average 480 whole-public characters, ranging from 439 to 542, against a
1,536-character ceiling. Length includes the complete header, guide, name and
tagline. This is observed output length under that ceiling, not a test of a
smaller generation budget.

All case/view answer vectors match between the two generations. The sixteen
tail losses are known choices answered `U` in all eight answers: twelve explicit
final/revised choices and four source-entailed choices. Neither cards nor tails
invent choices in the forty true-unknown cases. Every raw response, request,
public card, reference, missing case and usage receipt is retained in the
portable snapshot and reconstructed by offline replay.

## Reported usage

| Stage | Actual attempts | Reported total tokens |
| --- | ---: | ---: |
| Shared none | 1 | 11,330 |
| Own full controls | 4 | 52,450 |
| Initial extraction | 8 | 98,886 |
| Card readers | 16 | 187,948 |
| Own matched-tail readers | 16 | 187,496 |

Total **511,725 input + 26,385 output = 538,110 tokens**, with no missing usage.
Cached input 101,376 and reasoning output 3,026 are subsets, not extra tokens.
This covers the whole benchmark, including controls and repeated readers; it
is not one user's card cost or a dollar price. Eight initial extractions
account for 98,886 tokens. No review is included in this scope.

## Limits and provenance

These are **four consumed fictional people in two opposite pairs**, with
explicit XOR/XNOR rules and withdrawn rules. Two draws per person do not
establish population stability, real-person fidelity, an independent holdout,
citation semantics or cross-provider transfer. Requested model is
`gpt-6.1-sol`; resolved backend identity is not independently reported.
Tails match whole-public characters, not tokens or optimal source selection.
The encoder, reader, reference and production defaults remain unchanged;
prior observations are not pooled into the new primary denominator.

The scientific source is CI-qualified commit
`29d3b5eaa50802b2cb16fffacca148d81a4a744d`. A read-only GitHub qualification
observer lost network before activation, when no execution intent or model
attempt existed. After verifying the passed CI, the existing new grant was
used for its first actual execution. No model request was retried. The original
monitor failure is preserved, along with the unchanged source, intake and
thirteen prior sealed observation sets. Private grants, runtime details, host
paths, processes and full provider envelopes stay local. Checksums support
integrity and replay, not independent service or semantic attestation.

## Replay without a model

```sh
python3 -B scripts/replay_single_pass_repeat.py
```

Nine evidence damage tests protect input/reference versions, generation and
read routing, raw/card preservation, matched tails, per-generation/joint
scores, denominators, usage, child counts and reviewed public field sets.
They reject unsupported population/real-user claims and extra private fields.
The frozen preparation below remains a separate intake record: its check
reports preparation status, not the measured outcome above.

## Original frozen preparation

The [fresh45 result](../fresh-enum-pipeline-v1/README.md) has four successful
initial cards, but only one initial generation per person. Earlier consumed
sources produced different omissions from identical extraction requests. This
protocol checks that remaining reliability gap without changing the encoder.

**Status when this preparation was frozen:** no model call had run or been
authorized. The measured, separately approved scope is reported above.
The controller accepts an injected backend, has no service transport or grant,
and requires a new finite-scope approval and exact-head three-platform CI before
any real execution.

| Proposed stage | Maximum local attempts |
| --- | ---: |
| New shared none + four own full controls | 5 |
| Two independent initial extractions per person | 8 |
| Two reads of each initial card | 16 |
| Two reads of each own equal-character raw tail | 16 |
| Total | **45** |

The four **consumed synthetic** sources,88messages,32public question forms,
source-licensed labels,coverage producer,compiler,reader and1536whole-character
ceiling remain unchanged. No review is included. The second generation never
sees the first card,questions,reference,reader feedback or earlier observations.
Controls are called anew and must qualify before any extraction. Generation
order reverses between rounds;card/tail read order alternates and reverses.

Each view keeps64unique person/cases:24known,40unknown,including8derived-knowns.
Every case needs **2generations ×2reads ×2option orders =8correct answers**.
Each generation's four-answer endpoint is also reported. A wrong answer in one
generation cannot be erased by another successful generation. Invalid initial
products skip only their own four readers and retain missing cases in the fixed
denominators;other independent generations continue. Fatal control,transport,
wire/decode,unknown-usage,model or runtime failures close all remaining slots.
No retry,repair,resume,replacement or replenishment.

This is four people in two opposite pairs,not128independent samples. Two draws
per source do not establish population stability,independent-holdout,real-person
or cross-provider fidelity,citation semantics or production readiness. Raw tails
are character-matched to each own card,not token-matched or optimal extracts.
Old cards,results,denominators and production defaults remain intact.

```sh
python3 -B benchmarks/single-pass-repeat-v1/check.py
python3 -B -m unittest discover -s tests -p 'test_single_pass_repeat.py' -v
```

The public protocol and prepared-file hashes reconstruct from `plan.py`;the
existing fresh45 folder publishes the exact synthetic sources and reference.
`fixtures.py` deliberately supplies incomplete cards and returns reference-aware
answers separately. Its perfect oracle result tests **bookkeeping only**,never
compression fidelity. Damage fixtures cover generation/order loss,invalid
parents,unknown usage,stops,source/request separation and output-before-claim.
The scientific dependency list excludes the unused legacy taste executor;
the next host still needs its own separately frozen runtime/claim verification.
