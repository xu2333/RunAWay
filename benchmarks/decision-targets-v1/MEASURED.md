# Decision-target comparison: no observed advantage

On 2026-10-30, all 21 planned local Codex CLI children completed, requesting
`gpt-6.1-sol`. Both the source-policy baseline (v1) and decision-target candidate
(v2) scored **96/96** under the strict requirement that both reads and both
option orders match the frozen reference. There were no missing answers,
invalid products, skipped readers, retries or repairs. The production default
remains unchanged.

| Source | Cases | v1 first / second | v2 first / second | Whole characters v1 → v2 |
|---|---:|---|---|---:|
| h68, consumed fictional history |40|40 / 40|40 / 40|1118 → 1201|
| h93, consumed fictional history |40|40 / 40|40 / 40|1219 → 1211|
| New authored development fiction |16|16 / 16|16 / 16|615 → 639|
| Total |96|96 / 96|96 / 96|2952 → 3051|

All cards use the unchanged binder, schema, renderer, guide and whole-card
1536-character ceiling. v2 adds 99 characters in aggregate (about 3.4%). These
single generated samples establish neither a stable length effect nor improved
accuracy. h68/h93 v1 cards are cached outputs from the preceding source-policy
study; dev v1 and all v2 cards were independently extracted once in this scope.
This asymmetry prevents a generation-level causal comparison.

## Controls and unknown boundaries

Each full-source control passed every case in both orders and exceeded the
specified no-memory signal before any card reads or extractions began.
No memory scored 19/40 for h68, 16/40 for h93 and 7/16 for dev: **42/96**,
all from returning the correct `U`. Full sources and both card methods retained
54/54 known decisions and 42/42 unknown cases. Unknown accuracy alone therefore
does not distinguish these memories from no memory; the known-decision signal
is essential.

The new 16-case development bank has 11 preference and 5 execution questions,
with 9 known decisions and 7 unknown cases. Both methods retained all strata on
both reads. Neither erased execution limits to gain preference accuracy.
The older 80 cases have no separately authored execution stratum; do not count
them as additional execution tests. The separate symbolic corruption
calibration remains useful, but its sensitivity does not imply that these
natural-language cases discriminate v1 from v2.

The old h93 source-policy card previously lost t01/t02 on its first read and
recovered on its second. That same card now passes twice too. Current reader
requests use the newly fixed as-of date, while within this scope each card's two
requests are identical. This result does **not** show that target separation
fixed the previous failure; the baseline also recovered. Preserve the original
118/120 and 119/120 results rather than replacing them with this phase's scores.

## Limits, accounting and next decision

These are 2 consumed fictional profiles plus 1 openly authored development
fixture, not 96 independent users. The 80 old cases are repeats; the 16 new cases
are visible development material. They add **zero** cases to the original
232-case coverage inventory, which remains 160 measured and 72 unmeasured.
No confidence interval or significance claim treats option rotations, repeated
reads or shared templates as independent samples. Independent semantic custody,
real-person fidelity, cross-model transfer and producer variation remain open.
The disputed w14 labels are unchanged.

Recorded usage is 349,201 input plus 26,015 output = **375,216 tokens**.
35,840 cached-input tokens and 3,763 reasoning-output tokens are subsets,
not additions. This is recorded usage, not a monetary bill. There was no token
or money ceiling. Internal RPC retries, actual served model identity and
upstream cancellation are not independently observable. All 21 slots are used
and this scope is closed; this report grants no further service budget.

Do not promote v2 on this evidence. Before another service run, the next design
should distinguish card-generation variability from read variability and add
harder multi-question boundary cases rather than repeatedly replaying the same
ceiling-level bank. The remaining 72 original cases and their unresolved w14
cells require an explicit reference policy in any subsequent proposal.

## Offline replay

```sh
python benchmarks/decision-targets-v1/measured.py
python -m unittest discover -s tests -p test_decision_target_measured.py -v
```

`measured.synthetic.json` retains the exact 21 request objects and raw response
texts, safe usage rows, sources, frozen references and four generated cards.
The cached cards are bound to the earlier published evidence. Replay reconstructs
requests, binds each extraction to its own source/method, checks repeated reads,
recomputes full/no-memory gates, preserves denominators and validates counters.
CI also runs damage controls for altered requests, artifacts, raw text, usage,
references, slots, runtime files and unsupported claims. It makes no model calls.

`scripts/export_decision_target_results.py --run <sealed-local-run>` reproduces
the portable export. Local approvals, machine paths, credentials and private
transport envelopes are excluded. Original envelope hashes provide provenance;
public replay does not claim to reconstruct omitted envelope bytes.
