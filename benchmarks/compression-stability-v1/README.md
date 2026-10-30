# Compression and repeated extraction: unexecuted study plan

The preceding [decision-target comparison](../decision-targets-v1/MEASURED.md)
tied at96/96 and added99characters. It did not justify promoting target-v2.
This plan instead keeps the measured **scope-v1 research method** fixed and
tests lower budgets with repeated extraction. It does not change the production
default. No actual service run or new fidelity result is included here.

| Factor | Frozen choice |
|---|---|
| Source material |h68/h93,48fictional messages each; dev,14authored messages|
| Whole-card budgets |768and1024Unicode characters, including header and guide|
| Extraction per source/budget |2new outputs from identical request text in fresh contexts|
| Reading per generated card |2identical requests, each with both option orders|
| Method and reader |Published source-policy v1, unchanged schema/binder/renderer; standard text reader|
| Scope ceiling |5controls +12extractions +24reads = **41new local CLI attempts**|

All12extractions finish before any card is read. The second generation reverses
budget order and rotates profile order; the second reader pass reverses card
order. Neither generation sees questions, old cards, outputs from the other
generation, feedback, target labels, truth or references. Readers see only the
public card and natural-language questions/options. No seed is fixed, upstream
sampling is unobservable, and fresh contexts do not establish statistical
independence.

The dev source previously yielded a615-character v1 card. It may fit both budgets
without compression pressure; it is an execution/unknown-boundary and generation
control, not evidence that a long history compresses equally well. The two
48-message sources previously needed1118/1219characters. Do not compare old
1536-budget samples to this cohort as a causal budget effect.

## Planned scoring and refusal to select successful samples

The same96developer-visible cases remain:40each for h68/h93 and16for dev,
comprising54known decisions and42unknown cases. The dev cases have11preference
and5execution questions. Older80cases have no authored preference/execution
stratum and are reported as **untyped**, not added to either stratum. These are
three fictional source units, not96independent people or a new holdout. Original
inventory coverage remains160/232; the other72cases and w14 are outside scope.

Report each generation's length, validity and first/second/strict reading scores.
At each budget, the primary case score requires all **2generations ×2reads
×2option orders** to match its frozen reference. Denominator stays96per budget.
An invalid or missing generation remains missing even when its sibling passes.
Scores conditional on valid products must not replace this primary endpoint.
Do not choose a better generation, shorten a failed card, retry or borrow a card
from another budget. Every whole-card byte comes from its own source-bound output.

Within-card read disagreement and observed between-card disagreement are reported
separately. They describe this nested observation, not a causal decomposition of
generation variance versus reader variance. Two generations and three source
units do not support significance claims about a population. Stable wrong
answers still fail. No-memory returning allU can pass the42unknown cases while
retaining zero known choices; always report known and unknown strata separately.

The first5jobs are shared h no-memory, h68 full, h93 full, dev no-memory, dev full.
Each full must immediately pass all cases/both orders with no missing values;
h personal-known must exceed shared h no-memory, and dev known must exceed dev
no-memory. Any failed full closes the remainder before extraction. A bound
product failure skips only its own2readers. Transport, wire, decode, unknown
usage, requested model, runtime, input hash or owned-guard failure closes the
entire remainder. Unused slots expire; no retry, repair, resume or replenishment.

Requests target gpt-6.1-sol, fixed as_of2026-10-30, tool-free contexts.41is a
call ceiling with **no token or monetary ceiling**.180seconds per local child,
nominally7380seconds in total, is neither an overall duration/spend bound nor
guaranteed upstream cancellation. Internal RPC/retry count and served model
identity are not independently observable. All prior scopes remain closed.

## Offline preparation and fault simulation

```sh
python benchmarks/compression-stability-v1/plan.py --out /path/to/new-proposal
python -m unittest discover -s tests -p test_compression_stability.py -v
```

Preparation freezes17exact static requests and24conditional reader rules plus
sources, public questions, isolated references, slots, implementation hashes and
a manifest. It creates no backend, approval receipt, process or service call.
The references are model-input isolation, not secret independent truth.

`engine.py` has mandatory injected transport/pre-call callbacks and no CLI or
backend of its own. Actual use needs a separately verified exact new human grant
in the local host.15offline tests cover schedule, source-only extraction,
identical repeats, invalid sibling isolation, failed controls, wrong-read
retention, missing/unknown/stable-wrong scoring, unbound-answer rejection, usage,
final-attempt failure and no-resume behavior.
Fixtures return oracle choices against partial cards to exercise plumbing;
their simulated96/96 scores are **not measured model fidelity** and cost zero
service calls. Publication does not authorize the planned41attempts.
