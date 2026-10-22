# Next extraction contract: preserve meaning without an external decoder

This is a design proposal, **not implemented or model-validated**. No recorded
card was repaired and no extra call was made to create these results.

The ablation is a real product limitation: original histories permit 102/102,
while unchanged cards permit only 80/102 under the same request builder without
the added shared decoder. All 22 lost conclusions were abstentions. It is unsafe
to "fix" this by asking the reader to guess more: the 47 genuinely unknown cases,
including ambiguity between compatible policies, must remain unknown.

The next source-only extractor should preserve four distinctions privately:

1. An explicitly observed decision, with its source/role/update evidence.
2. A source-stated constraint on possible policies, including finite scope.
3. A conclusion entailed by every remaining source-compatible policy.
4. A disagreement or unsupported scope that still requires abstention.

Public output can remain a playful name and connected prose. It must carry the
meaning of every referenced alternative; labels such as "candidate 3 or 8" are
not portable unless their definitions accompany them. If a rule is uniquely
entailed by explicit source constraints, preserve its self-contained meaning and
scope. If multiple rules remain, describe the concrete alternatives and their
agreement/disagreement, rather than selecting one or flattening all future cases
to unknown. "Not directly observed" and "not logically determined" differ.

Do not generalize from a few examples as if the family were guaranteed when the
source never supplies that guarantee. Do not quote candidate definitions as though
the user had explicitly chosen them. Derived conclusions need their assumptions
and observations preserved in private evidence, not a fabricated direct decision.

Implementation should introduce an explicitly versioned extraction contract
instead of silently changing v1's request text or historical bindings. Existing
benchmarks reconstruct exact requests and source-bound profiles; historical v1
must continue to reproduce. Keep whole-card budget checks and candidate-unvalidated
status until the new contract is measured. A source-reference linter can flag
undefined labels, but cannot certify semantic completeness.

Validation requirements before changing defaults:

- Use these consumed six people/cases only as development regressions.
- Add fresh narratives and a different family of explicit source constraints,
  including multi-rule uncertainty, absent family guarantees, and changing scope.
- Encoder must never see held-out questions, author policies or gold.
- Qualify contemporary full without the external decoder; test own and an
  independent donor read against all planned cases and rotations.
- Separate observed decisions, entailed unseen combinations, missing necessary
  features and unidentifiable preferences; retain no-memory/wrong-person and
  equal-size recency baselines with actual, not forced, scores.
- Preserve all failures and costs, predeclare finite calls and source versions,
  and run through the temporary owned idle-sleep guard.

The present experiment diagnoses a self-contained representation gap, not a new
universal personality taxonomy or proof that a proposed v2 already fixes it.
