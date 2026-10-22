# Removing the shared decoder: standalone ablation

[Results](RESULTS.md) · [Every actual error](LOSSES.md) ·
[Next contract design, not implemented](NEXT-CONTRACT.md)

**All 19 calls completed. Full history remains 102/102, but unchanged standalone
cards and their independent donor reads are 80/102. All 22 losses are known choices
answered U; all 47 unknowns remain correct. Standalone fidelity is not solved.**

A new, separately frozen 19-call ablation after the completed
[31-call shared-decoder study](../latent-transfer-v1/RESULTS.md). The old proposal
stays closed; no answer, failed slot or unused balance is reused. The combined
cap explicitly announced for this human continuation is50physical calls.

All six existing 296–387-character cards are kept byte-identical. The new request
removes exactly the 619-character decoder prefix from **every** reader arm. Every
other field, source history, question, option order, gold label, model request,
active timeout and generic absent-option instruction is unchanged. Full histories
still contain their original user-stated family definitions; cards receive no
appended codebook. Removing the prefix removes both family definitions and
reasoning instructions, so full controls are necessary before attributing losses.

This uses the production request builder plus the existing generic absent-option
instruction. It does not assert that all CLI defaults, vendors or harness loading
paths were exercised. The corpus is consumed and this is an exploratory sequential
ablation, not a fresh holdout or randomized causal effect. Sampling/service drift
is not eliminated. No model is asked to re-encode or repair the cards.

The fixed matrix is shared none1, contemporary full6, own6 and wrong-person6.
Two interleaved full/own waves cover all six people before wrong-person donor
repeats. Nineteen physical calls yield 13 unique inputs if all complete; wrong-person
reads are new executions of donor-own requests, not cached answers.

All 102 person/scene cases remain planned: 55 known and 47 unknown, with 43 personally
discriminating knowns and 12 family invariants. The latter 12 are not free public
knowledge in this condition. Earlier no-history 59/102 reference does not apply as
a decoder/accuracy ceiling after removal. Every option rotation must be correct.

Contemporary full qualifies only at 102/102 with no missing outputs and personal-known(full-none)/43
>=.25. Standalone retention is interpretable only with this control. The strict
standalone gate also requires own and donor-repeat 102/102; identity specificity
requires a wrong-target personal-known drop. Missing cases, paired losses and
independent repeated-answer changes are retained. No cherry-picking old controls.

```sh
python benchmarks/standalone-latent-v1/study.py prepare --out NEW_DIRECTORY
python benchmarks/standalone-latent-v1/study.py preflight --out NEW_DIRECTORY
python scripts/with_awake.py -- python benchmarks/standalone-latent-v1/study.py run --out NEW_ACCEPTED_DIRECTORY
```

Before real service execution: matching offline acceptance, runtime/source binding,
existing human authorization and an owned macOS idle-sleep assertion are required.
The exclusive intent forbids resume. Any transport, format/decode, unknownusage,
guard or binding failure stops all later calls. Quality errors do not stop fixed
remaining slots. No retry, repair, deadline extension, fallback, extra extraction
or replenishment. Nineteen is a call cap, not a token/money cap. Mocks are not model
evidence. No human data, real-person fidelity, population generalization,
cross-vendor/runtime portability or likelihood information gain claim.
