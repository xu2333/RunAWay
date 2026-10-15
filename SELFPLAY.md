# Synthetic self-play: can the prompt recover hidden decisions?

This benchmark tests **behavioral information transfer in a defined synthetic world**. It cannot establish fidelity to actual people. Gold choices come from executable policies, not an LLM grading its own writing. Nothing reads the user's history or imports the 700 fictional entertainment cards.

## What runs

Six authored policies form three matched pairs. Each pair differs in exactly one rule: whether irreversibility changes planning, whether reversible repetitive work is automated, or whether public feedback changes tone. A fourth preference tests changing a design after repeated complaints. These are narrow decision procedures, not human personality types. Changing `--seed` alone changes IDs and option ordering, not these policies or settings; it is not a new held-out population. The suite does not evaluate the 700 entertainment cards.

1. A model assistant proposes choices in three rounds of four tasks. A deterministic synthetic user accepts or corrects each proposal according to its hidden policy. The assistant sees earlier interactions in later rounds. This is **model–simulator self-play**, not two independently validated human simulators.
2. The actual browser extraction request and validator turn those 12 interactions into evidence-linked claims, a detailed export, a portable prompt, and the normal presentation fields. The extractor never receives the policy or test cases.
3. An extra compressor produces a smaller-budget candidate from the **same** fixed profile. It is structurally checked and measured, not certified faithful by an LLM judge. No truncation, score-based repair or candidate selection is allowed.
4. All memories are frozen before decoding any test cases. In fresh, tool-free Codex calls, a decoder predicts choices with nine conditions: none, generic advice, original trajectory, detailed profile, compact prompt, smaller-budget prompt, matched twin's prompt, name/tagline only, and oracle rules.
5. Code scores every output against the hidden policy. All failures remain in the report. The oracle condition is a decoder diagnostic: even a correct rule description can be misapplied by a model.

Each person has 24 held-out cases: 12 matched situations with a changed condition. Training and testing use different settings and sentence templates, but the same four rule families. This is limited transfer, not arbitrary out-of-distribution generalization. Four action-order reversals and two unobserved preferences are separate controls, not extra independent primary cases. Opaque question IDs and shuffled order hide case categories; internal rule names, gold labels and pair links never enter ordinary prediction requests.

## Run from a checkout

Python 3.9+, Node 22+, and an existing Codex login are needed. The base Python package has no new dependencies. Model inference uses your configured Codex service and consumes its quota. Freeze is offline; run sends only newly synthesized records and frozen derived memories. The [Codex evaluation workflow](https://developers.openai.com/blog/eval-skills) supports the structured, recorded execution used by the existing backend.

```sh
python3 -m runaway.selfplay freeze --out selfplay-plan \
  --model YOUR_MODEL --decoder-model YOUR_DECODER \
  --budget 1000 --tiny-budget 400

python3 -m runaway.selfplay run selfplay-plan/snapshot.synthetic.json \
  --out selfplay-run --workers 2
```

The default six-person plan bounds model calls at 84 before exact-request caching. Model identifiers must be explicit and available to your account. A source checkout is required because the benchmark invokes the actual browser modules through `scripts/selfplay-browser.mjs`. Different generator/decoder models can be declared before running.

`--resume` reuses identical hashed requests and responses; it does not retry failed calls or alter rejected candidates. A changed model, code, policy, budget or condition requires a new frozen plan. The run lock prevents concurrent duplicate execution. Inspect the plan and outputs before sending anything from a modified fork to a service. Do not resume into unrelated directories.

## Read the measurements

- **Choice accuracy** on the 24 primary cases, with completed/planned denominators. The separate failure-inclusive rate treats missing end-to-end outputs as incorrect.
- **Counterfactual pair accuracy** requires both sides to be correct. Required-flip pairs are reported separately from policies that should keep the same answer.
- **Matched-twin discrimination** requires both similar people to make their respective, different correct choices on the same case. Aggregate accuracy alone can miss lost distinctions.
- **Order consistency** checks whether reversing option labels preserves the chosen action. Two abstentions do not count as evidence of action consistency.
- **Unknown-preference abstention** checks whether the prompt invents a color or music preference never observed in training.
- **Actual length**, not just the budget. A 400-character budget does not guarantee a shorter output than a 1,000-character budget. Character counts are not token counts.

Codex results contain choices, not logits. They deliberately report no invented probabilities or RIG. No-memory models may abstain because the task explicitly permits uncertainty: a gain over that baseline is not evidence that a personalized model outperforms a forced-guess baseline. Compare with the raw history, detailed profile and wrong-person controls, and inspect response coverage in the saved predictions.

The six policies were authored, not sampled from a population. Cases and variants are correlated. No confidence interval treats 144 choices as 144 independent users. Identifiability is checked only within the declared policy family; it does not prove that arbitrary hidden preferences can be inferred from the same amount of human data.

## Optional local information gain

The optional local audit uses an existing Qwen3 GGUF and the previously validated `llama-cpp-python==0.3.36` backend. It makes no network calls or model downloads. Install optional dependencies yourself if needed (`pip install '.[evaluation]'`).

```sh
python3 -m runaway.selfplay_local freeze --run selfplay-run \
  --model /path/to/existing-qwen3.gguf --out local-selfplay
python3 -m runaway.selfplay_local run local-selfplay/plan.local.json
python3 -m runaway.selfplay_diagnostics local-selfplay
```

The scorer checks model-file hashes, architecture, exact single-token A/B/U labels, context capacity and a causal-logit consistency test. It feeds only memory plus the public pre-decision case, reads actual next-token logits, and renormalizes over those three labels. It records raw log probabilities and the unconstrained total probability mass of the labels, so this constrained score cannot be mistaken for unconstrained text likelihood.

```text
closed-choice NLL = mean[-log p(actual choice | A, B, U)]
closed-choice RIG = (NLL(none) - NLL(memory)) / NLL(none)
```

Primary NLL uses the same 24 cases per available person. Missing memories are excluded explicitly; every paired comparison identifies the exact common people. Negative gains remain negative. Token counts include the actual full memory text. Closed-choice RIG is **not** the real-follow-up free-text RIG described in [EVALUATION.md](EVALUATION.md), and neither is a personality-fidelity certificate. Weak oracle results indicate that decoder capacity or framing may dominate.

## First measured run

See [the checked-in result summary](examples/selfplay-results.synthetic.json) and [the synthetic evidence bundle](examples/selfplay-evidence.synthetic.zip). The bundle includes policies, trajectories, generated representations, every original structured model response and request, predictions, the initial run, the amended run, and local-logit results when completed. It contains no real histories, credentials or local model files.

The local Qwen3 0.6B run produced **A for every one of 1,440 rows**, including the oracle condition; action-order consistency and unobserved-preference abstention are both zero. Its saved closed-choice RIG is +13.1% for detailed memory and −10.3% for compact memory on the same five available profiles, but these numbers are **decoder diagnostics, not successful portability or compression-quality evidence**. A constant oracle decoder fails the basic control. A post-hoc, reproducible diagnostic command now flags this failure without changing scores. Actual Qwen tokenizer counts are 793 tokens for detailed and 207 for compact on those five profiles (ratio of totals: 26.1%); the four smaller-budget candidates average 201.5 tokens.

The first Codex run requested `gpt-6-luna` for interaction, extraction and decoding; it made 54 unique calls after caching. Model revision IDs were not exposed. Five of six profiles passed the unmodified product validator: the sixth rewrote an evidence quote and was rejected. One of the five eligible smaller-budget outputs exceeded 400 characters and was rejected without repair.

On the **same five completed profiles** (120 held-out choices):

| Representation | Mean characters | Correct choices | Both twins correct on distinguishing cases* |
| --- | ---: | ---: | ---: |
| Detailed profile | 1,886.6 | 116/120 (96.7%) | 6/6 |
| Portable prompt | 386.0 | 112/120 (93.3%) | 3/6 |
| Name and tagline | 29.2 | 69/120 (57.5%) | 1/6 |

*Twin comparison uses the same two complete pairs; the third pair lacks one extracted profile. Failure-inclusive compact recovery is **112/144 (77.8%)**, not 93.3%. The original-trajectory control is available for all six and scores 134/144; on the same five completed profiles it scores 111/120. No-memory output abstained on all 144 cases, so its 0% must not be presented as an ordinary forced-choice baseline. A 50% random A/B expectation is a more informative reference for such a claim, although it does not measure calibrated abstention.

The compact text still mentions some exceptions that the decoder fails to apply. These are observed behavioral differences, not proof that the compressor literally deleted the meaning. Scope/uncertainty wording, decoder behavior, and limited evidence can all contribute. Even the oracle-rule condition scores only 127/144, showing that knowing a policy in text does not ensure executing it.

The smaller-budget candidates average 379.75 characters on four available profiles, versus their corresponding original prompts averaging 377.00. Thus this particular 400-character setting does **not** establish further compression; the budget alone is not a compression ratio. These five profiles are development examples after inspection.

The initial evaluator incorrectly suppressed available raw-history and wrong-person controls for a person whose profile extraction failed. That runner bug was amended without changing any questions, answers, memories, inference instructions or scoring rules. Identical calls were reused; both original and amended results remain available. The failed profile and over-budget candidate were not repaired or removed from the denominator.

Use these cases for development after inspecting their results. A tuned compressor needs new frozen cases/policies for a subsequent generalization claim. A later real-user evaluation remains necessary; synthetic success cannot establish human validity, and synthetic failure usefully reveals where a claim is already too strong.
