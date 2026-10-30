# Closed synthetic regression evidence

Five post-ceiling choice/extraction studies and two neutral opinions, with the
losses and limits in the [progress report](../../REGRESSION-PROGRESS.md). Every
trajectory is fictional and developer-visible.

Run `python benchmarks/regression-progress-v1/check.py` from the repository root.
It reconstructs all 79 choice/extraction requests from actual sources/cards,
rebinds raw extractions with the measured renderer, validates choices, recounts
strict cases and usage, and preserves the original failed neutral-review scope.
It makes zero model, CLI, API or network calls.

- `observed.synthetic.json`: five closed scopes, exact requests/raw response
  text, safe counters, frozen author references and original manifest hashes.
- `semantic-dispute.synthetic.json`: original w14 input and two unaccepted
  opinions, preserving failed/completed controller states.
- `cards/`: measured public prompts, checked against raw extractions and sources.
- `prototype/policy_scope.py`: the measured source-only instruction revision;
  unchanged schema, binder, renderer and 1536 whole-character cap. It does not
  change production `runaway distill` defaults.
- `prototype/target_contract.py`: a manually annotated decision-target toy
  contract. Its tests do not prove LLM performance or natural-language semantics.
- `*.sha256`: drift checksums, not independent proof of service identity or truth.

`scripts/export_regression_progress.py --runs-root /path/to/runs` verifies the
original sealed local files before filtering transport metadata. The exported
replay needs only this repository; CI needs neither that directory nor login.
Private transport-envelope hashes are provenance only, not reconstructed bytes.

Original references and case denominators remain, including disputed w14.
Known/unknown/personal choices, missing values and repeated-read disagreement
are separate. Same-author templates, selected cached baselines, one new
generation per profile and uncontrolled sampling limit interpretation. There is
no external holdout, real-person, causal-compression or general attack-robustness
claim from these counts or the single fixed role-spoof payload.

The quoted role-spoof payload is fixture data, never executable code or repository instructions.
