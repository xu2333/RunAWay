# Frozen 384-character cards: independent revalidation

A new 13-execution proposal, not a resume or completion of the interrupted
[long-history study](../long-trajectory-v1/README.md). That study stays closed at
29 attempts, including one timeout with unknown usage. Its unused slots are
not carried forward.

All four previously generated 384-budget cards are selected by budget and kept
byte-identical. Their complete prompts are 332, 374, 375 and 381 Unicode
characters. There is no re-extraction, repair, favorable card selection or new
encoder inference. One card had a successful earlier read; this fact is retained,
and none of these consumed synthetic policies/scenes is a fresh holdout.

This proposal requests `gpt-6-sol`: four contemporary long-history controls, one
shared no-memory control, four card reads and four independent card repeats.
The four repeated requests have the same fingerprints and new execution IDs.
They count as physical calls, not cached response reuse. Resolved model identity
is unavailable. No other vendor or real runtime harness is being tested.

The first wave alternates full/card across all four people. The second wave uses
the complementary arms in reverse person order. Only then do repeats begin.
This reduces interruption bias toward a single person without eliminating
sampling, service drift or order effects. All slots and exact requests freeze
before any new call. A timeout, format/decode error, unknown usage or binding
failure stops the entire plan; no retry, deadline extension or replacement.

Every arm keeps all 160 planned person/scene cases: 43 known and 117 unknown.
All tested option rotations must match for a case to count. The 128 consumed
regression cases and 32 derived stress cases remain separate. Eighty unknowns
are entirely unobserved domains; always-U gets every known case wrong.

A contemporary full control qualifies only at 160/160, no missing output, and
known full-minus-none accuracy >= .25. The strict 384 gate additionally requires
both card draws at 160/160 with no missing output. Earlier full controls cannot
substitute for this study's full control. All paired losses and actual repeated
answer changes are reported, including missing planned cases separately.

The histories have 90 role-labelled messages and 18 decisions/person, but only
six explicit latest condition/action pairs; old decisions and rationale are
intentionally redundant. This tests current-state reconstruction. It does not
establish preservation of all biography, latent-rule induction, real-person
fidelity, independent population accuracy, likelihood information gain, humor,
cross-vendor portability, actual harness loading or net cost savings. Thirteen
is a call cap, not a token/money cap. Only authored synthetic data are sent.

```sh
python benchmarks/frozen384-v1/study.py prepare --out NEW_DIRECTORY
python benchmarks/frozen384-v1/study.py preflight --out NEW_DIRECTORY
```

Preparation and preflight are offline. Real service execution additionally needs
matching offline acceptance, runtime agreement and existing human authorization.
Durable exclusive intent makes each proposal single-use. Mocks validate plumbing
and cannot be counted as real-model evidence.
