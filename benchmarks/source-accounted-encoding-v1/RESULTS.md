# Source-accounted encoding: recovery and regressions

The separately authorized scope is **closed after27actual local inference
attempts /27recorded children**. All8cards are valid; no missing usage, skipped
readers, expired slots, retries or repairs. Two full-source controls pass30/30
in both orders before extraction; shared no-memory passes17/30. Its one response
is reused for two people, not two independent control runs.

## Did the lost choices return? Did anything else get worse?

| Strict endpoint | Current coverage encoder | Source-accounted candidate |
| --- | ---: | ---: |
| All planned person/cases | 30/30 | 30/30 |
| Known choices | 13/13 | 13/13 |
| True unknowns | 17/17 | 17/17 |
| Source-entailed knowns, overlapping knowns | 6/6 | 6/6 |
| Withdrawal-sensitive cases | 7/7 | 7/7 |
| Historical seven-loss targets | 7/7 | 7/7 |
| Missing cases | 0/30 | 0/30 |

Every case requires all two extractions × two reads × two option orders to
match: eight answers, not eight independent people. Each generation separately
also passes30/30 for both methods. Paired transitions:30kept,0candidate-only
recoveries,0new losses,0both-failed. None of the other23cases regresses; no
known-to-U or unknown-to-choice error is observed.

New cards reproduce all seven choices lost by the historical240/312-character
cards. **The contemporaneous current encoder also reproduces all seven.** This
does not establish an extra accuracy benefit from the new contract. Old failing
cards and scores remain failures; they were not repaired, replaced or sent to
this round's source-only encoder.

| Person / historical case | Required choice | Old failed-parent answers | Current, all8 | Candidate, all8 |
| --- | --- | --- | --- | --- |
| f7s / notes_complete_0 | 保持手动整理 | U,U,U,U | correct | correct |
| f7s / notes_complete_2 | 保持手动整理 | U,U,U,U | correct | correct |
| f7s / signup_complete_1 | 保持手动分组 | U,U,U,U | correct | correct |
| f7s / signup_complete_2 | 保持手动分组 | U,U,U,U | correct | correct |
| c2v / notes_complete_3 | 启用自动整理 | U,U,U,U | correct | correct |
| c2v / signup_complete_1 | 启用自动分组 | U,U,U,U | correct | correct |
| c2v / signup_complete_2 | 启用自动分组 | U,U,U,U | correct | correct |

Replay derives these seven targets from the two original bad parents' recorded
reader answers, then checks the old and new reference labels match. These are
an overlapping diagnostic subset of30, not extra cases or new independent gold.
Replay emits all eight answers for every new case/method, including failures.

## Public length and extraction overhead

| Person | Current g0 / g1 characters | Candidate g0 / g1 characters |
| --- | ---: | ---: |
| c2v | 542 /549 | 471 /467 |
| f7s | 405 /401 | 397 /430 |

All complete public cards fit the same1,536-character cap. Mean length is474.25
for current versus441.25 for candidate:33characters, about7% less in these four
samples. f7s's candidate mean is slightly longer. This is descriptive, not a
token-matched comparison or optimal compression frontier.

Candidate cards contain5/5nodes across c2v's draws and6/6 across f7s's draws,
including2declared derived nodes each. Source accounting reports3direct choices
for c2v and4for f7s; f7s's second draw also declares two contextual reaffirmations.
These are model classifications, not independent completeness evidence. Private
bookkeeping is not extra reader memory; only the public card is read.

## Reported usage

| Stage | Actual attempts | Reported input + output tokens |
| --- | ---: | ---: |
| Shared no memory | 1 | 11,699 |
| Own full controls | 2 | 26,667 |
| Current extraction | 4 | 48,668 |
| Candidate extraction | 4 | 57,895 |
| Current card reads | 8 | 96,830 |
| Candidate card reads | 8 | 96,757 |
| Total | 27 | **338,516** |

Input312,284 + output26,232. Cached input34,816 and reasoning output3,545 are
subsets, not additional tokens. Candidate extraction reports9,227more tokens
(about19%) despite slightly shorter public cards. This is whole-study usage,
not a dollar bill, one-user card cost or demonstrated overall saving. Requested
model: `gpt-6.1-sol`; resolved service identity is unreported. Pinned local CLI:
0.165.0-alpha.1.2.

## Reproduce and limits

```sh
python3 -B scripts/replay_source_accounted.py
python3 -B -m unittest discover -s tests -p test_source_accounted_evidence.py -v
```

[Portable evidence](measured.synthetic.json) and [checksum](measured.synthetic.sha256)
retain reviewed fictional inputs, exact requests/raw answers, source-accounting
graphs, compiled cards and safe usage/counters. Replay reconstructs the original
controller, controls, binding/invalid-product routing, full denominators, all
answers, recovery/regression transitions and usage with archived callbacks and
blocked model services. Eight damage/classification checks protect those values,
numeric types and private-field boundaries. The private audit verifies original
intake and whole scientific source unchanged,16prior seals intact, and the owned
temporary wake guard exited. Grants, credentials, host paths and provider
envelopes remain private.

These are two selected consumed fictional development sources. Design knew the
old failures; source/reference semantics and message classification are not
independently accepted. Two generations/person/method cannot establish population
stability. Size and extraction overhead differ; there is no isolated causal
effect, real-person/cross-provider result, RIG, unseen-scene validation or default
promotion. The conclusion is retention in both arms with no observed new loss,
**not a measured candidate accuracy improvement**. Original unapproved metadata
stays frozen; publication does not reopen this closed27scope or grant new calls.
