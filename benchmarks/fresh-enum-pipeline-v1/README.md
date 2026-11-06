# Fresh-source pipeline — measured45-call result

The separately authorized run completes **45actual calls / 543815reported
tokens**,with no transport stops,invalid cards,skipped readers or missing usage
receipts. All45slots are used and the scope is closed. No retries,manual repairs,
resumption,best-of or new call budget is implied by these results.

| Fixed endpoint | Initial card | Reviewed card | Initial-length raw tail | Review-length raw tail |
| --- | ---: | ---: | ---: | ---: |
| Joint correct / planned cases | **64/64** | **64/64** | 48/64 | 48/64 |
| Known choices | **24/24** | **24/24** | 8/24 | 8/24 |
| Correct unknowns | 40/40 | 40/40 | 40/40 | 40/40 |
| Derived known choices | **8/8** | **8/8** | 4/8 | 4/8 |
| Missing | 0 | 0 | 0 | 0 |

Every card/view must answer both independent reads ×both option orders(all4)
correctly for each case. Full-source controls qualify64/64;shared none scores
40/64,all on unknowns. Controls have one read/two orders and are not additional
four-answer card measurements. These64cases represent **four fictional people**,not
64independent people. Repeated views,reads and option orders are not new people.

The sixteen tail losses per tail-view are all known choices answeredU in all
four answers:12explicit final/revised choices and4source-entailed choices.
The32listed tail case/view failures are16unique person/cases reused across two
length controls. All40unknowns remain correct,including8unseen withdrawn-rule
combinations,16missing-feature cases,8outside-feature cases,4outside-domain
cases and4unrecorded execution-status cases.

| Person | Source text chars | Initial card chars / joint | Reviewed chars / joint | Each raw-tail joint |
| --- | ---: | --- | --- | --- |
| pavo | 2290 | 440 / 16/16 | 490 / 16/16 | 10/16 |
| rill | 2292 | 460 / 16/16 | 487 / 16/16 | 10/16 |
| tavi | 2290 | 454 / 16/16 | 474 / 16/16 | 14/16 |
| wren | 2292 | 434 / 16/16 | 496 / 16/16 | 14/16 |

All4initial and4reviewed products bind within1536whole-public characters.
Initial cards average447characters;reviewed cards486.75. Role-labelled full
sources are2463–2465characters. Initial cards use about19–20%of source-text
characters,including the complete public header/guide/name/tagline.

## Review added no measured accuracy here

Both initial and reviewed cards already meet64/64. Review recovers zero
observed initial errors and causes zero observed choice regressions or missing
products. It adds4model calls/55780reported tokens and increases average public
length by39.75characters(about8.9%). This sample provides **no measured accuracy
benefit from automatically reviewing every fresh card**. It does not show that
review never helps:the [previous fixed-draft comparison](../source-id-enum-repeat-v1/README.md)
had selected incomplete drafts and a different reference-ID availability failure.
The installed default and the explicit optional-review choice remain unchanged.

## Reported usage and limits

| Stage | Actual calls | Reported total tokens |
| --- | ---: | ---: |
| Shared none | 1 | 11326 |
| Own full controls | 4 | 52450 |
| Initial extraction | 4 | 48993 |
| Enum review | 4 | 55780 |
| Initial card readers | 8 | 93863 |
| Reviewed card readers | 8 | 94011 |
| Initial-length raw-tail readers | 8 | 93571 |
| Review-length raw-tail readers | 8 | 93821 |

Total521277input +22538output =**543815tokens**. Cached input39424and reasoning
output2455are subsets,not extra tokens. This is usage for the whole45-call
experiment,not a dollar bill or the cost of one user's card. Four one-pass
extractions account for48993tokens;the benchmark additionally pays for controls,
review and repeated readers. Card/reader lengths are character-matched to their
own raw tail,not token-matched,and the tail is not an optimal extractive summary.

This run uses one fresh initial generation/person and one review/draft. It does
not establish generation/review stability,population safety,independent-holdout
or real-user fidelity,citation sufficiency,cross-provider transfer,information-
theoretic RIG or a whole-system cost saving. The explicit binary-rule grammar
and unknown-heavy source-author reference remain artificial. Both methods use
the same requested gpt-6.1-sol;resolved backend identity is not independently
reported. No production-default promotion follows from this sample.

The scientific source is the exact CI-qualified commit
`fcf9c9799abcd8e18683602f31afd0fcbbdbbde3`,exported read-only for this run after
later unrelated executor changes. The original input manifest remains byte-
identical;no old source hashes or observations are rewritten. The separate
bounded host claims its single-use scope only after output-directory creation;
it never invokes the legacy taste executor. All12earlier observation sets and
the original unapproved intake are verified unchanged after execution. Grants,
runtime/activation details,host paths,process IDs and private envelopes stay local.

## Reproduce without any model call

```sh
python scripts/frozen_history.py run scripts/replay_fresh_enum_pipeline.py
python scripts/frozen_history.py run scripts/demo_fresh_memory.py --person pavo --out fresh-demo
python -m runaway export fresh-demo/candidate/portable.json
```

The portable snapshot retains exact fictional inputs,requests/raw values,
references,cards and safe counters. Replay reconstructs all45slots,controls,
fixed denominators,character-matched tails,bindings,scores and usage using only
archived responses. Checksums support content integrity,not independent
attestation of the service or semantics. The source/schema/compiler files remain
frozen;`protocol.json` preserves the unapproved preparation separately from the
closed measured record.

The demo replays the measured440-character“**小团分格记**”example. Choose
`--person rill|tavi|wren`or`--stage reviewed`for the other measured cards. It
prepares the exact archived requests and imports through the existing offline
bridge. Source/graph/request files remain private;only inspected prompt/portable
files are sharing candidates. All imports stay`candidate_unvalidated`;the demo's
scores are not inherited by another user's card. See the
[user bridge guide](../../docs/experimental-memory.md#fresh-source-examples).

Nine measured-evidence damage checks guard exact source/input versions,all
request routing,raw/graph/artifact preservation,four64-case denominators,tail
material,review parent,counters/usage/conformance and unsupported claims. Four
demo checks round-trip all8cards/exact requests with zero services,verify export,
private permissions,overwrite rejection and CLI behavior. Oracle preparation
fixtures are not added to measured model evidence.

## Frozen design and material

Four newly authored fictional people,88messages,32common public question forms,
64unique person/cases per view (24known,40unknown;8derived-known). Two opposite
pairs have opposite actions at every known cell,so a generic answer cannot
match both. Source IDs are opaque person-specific ASCII IDs,not `m01` sequences.

The two domains are amateur podcast editing and board-game scheduling. Unlike
the prior monotone four-policy family,the active domain explicitly uses XOR or
XNOR over its two conditions. The other domain withdraws its initial complete
rule while preserving two final decisions. Each observation supersedes an
opposite provisional choice;assistant suggestions and stale tool displays are
not user endorsement or execution evidence. Missing features,out-of-definition
mixed plans,unseen withdrawn-rule combinations,another domain and unrecorded
publication status require unknown answers where source evidence is insufficient.

Reference labels use the current source rule or consensus over all16binary
policies consistent with the remaining decisions after withdrawal. An unseen
hidden generating table is never used. A separately written64-cell hand table
must agree with the enumerator. There are16explicit known cells,8derived-known
cells,8withdrawal/unseen unknowns,16missing-feature unknowns,8outside-feature
unknowns,4outside-domain unknowns and4execution-status unknowns.

These are new synthetic sources authored in the same development process,
not independently annotated human trajectories,an independent holdout or a
naturalistic population sample. The deliberate rule grammar remains artificial.
Source text alone is2290–2292characters/person;role-labelled full transcripts
are2463–2465,each exceeding the1536whole-public-character ceiling.

Reviewable material is in `sources.synthetic.json`,`questions.public.json`,
`author-reference.synthetic.json` and `author-evidence.synthetic.json`. Author
evidence,reference labels and questions are never included in producer/reviewer
requests. The generator and hand table are public for offline auditing.

## Finite plan

| Stage | Maximum local attempts |
| --- | ---: |
| Shared none + four own full controls | 5 |
| Fresh source-only coverage extraction,one/person | 4 |
| Enum review of each own valid fresh draft | 4 |
| Draft and reviewed card readers,two reads each | 16 |
| Own exact-card-character transcript tails,two reads each | 16 |
| Total | **45** |

All full controls must first pass16/16in both option orders with no missing and
personal-known gain over shared none. Then each person receives one independent
initial extraction and one review;review sees its own source and raw draft,
never reader feedback. Read/view ordering alternates by person and reverses
between repeats. No historical good/bad drafts or new model-specific fixes are
used. The existing coverage producer,enum reviewer,wire/binder/compiler and
reader remain frozen;all cards must fit1536characters.

Each of four views keeps64cases and requires both reads ×both option orders
(all4answers) per case. Report known/unknown,derived/withdrawn/status slices,
recoveries,observed regressions,missing,card availability/lengths and all usage.
This is **one initial generation/person and one review/draft**;it cannot estimate
initial-generation or review-repetition stability. Cases,reads and rotations
are not independent people.

`draft_tail` is the exact own-source role-labelled transcript suffix matching
the draft's realized character length;`reviewed_tail` separately matches the
reviewed card. No tail is selected by reference score,token-matched or supplied
an external decoder. This checks compression against cheap raw material.
An extra full-source review is an extra model pass/cost,so the pipeline contrast
is not an enum-only causal ablation or evidence of cheaper compression.

An invalid initial product skips its review and eight readers;an invalid review
skips only its own four card/tail readers. Corresponding cases remain missing
in all planned denominators. Missing matched tails mean no valid length source,
not demonstrated tail reasoning failure. Out-of-source enum IDs are rejected
as binding-invalid,with request conformance recorded separately. Other control,
transport,shared wire/schema/decode,unknown-usage,model,input/runtime/owned-guard
failure closes the remainder. Unused slots expire. No retry,repair,resumption,
slot replacement,best-of,fallback or older-budget reuse is allowed.

## Offline checks and execution boundary

Eleven original preparation tests check the source/hand reference,opposite profiles,source reconstruction,
absence of old-source reuse,9static/36dynamic inputs,own-parent routing,
exact tail lengths,45-slot accounting,fixed person/slice denominators,invalid
initial/review fan-out,single wrong-order retention,fatal closure,input drift,
public mirrors and a live call refused before any attempt. Oracle responses
validate accounting only;they are not fidelity measurements.

```sh
python -m unittest discover -s tests -p 'test_fresh_enum_pipeline.py' -q
```

The runner only accepts injected transport and guard functions;there is no live
backend or grant in this directory. `protocol.json` is an unapproved intake.
The original45-call grant and all three CI checks at the frozen implementation
commit were verified before execution. The closed grant cannot be reused.45was an attempt cap,
not a token/money cap;the disclosed local child timeout remains180seconds.
All old scopes stay closed,old scores unchanged,and production defaults unchanged.

Frozen input manifest:
`b27a444aca8e57a5027c75cd571e2e4161aede1836af489f38b472863967ae2f`.
