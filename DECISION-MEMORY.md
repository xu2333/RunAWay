# Testing decision fidelity before promoting a compressor

Synthetic self-play can expose broken information transfer. It cannot establish fidelity to a real person. This experiment uses executable hidden policies to generate corrections, so the reference choice is independent of an LLM's opinion about its own output. It extends [SELFPLAY.md](SELFPLAY.md); it does not use the 700 entertainment characters.

The loop is **hidden policy → interactions → the product's evidence-linked extraction → memory → fresh decisions → code scoring**. The extractor and compressor see no hidden rules or test cases. The oracle-rule condition goes only to a separate decoder control. Each plan freezes code hashes, cases, models, stopping rules and budgets before inference. Reading the results consumes that test set for development.

The new memory represents each observed claim as a condition, a chosen action and its bounds. Every claim has a separate branch and a private, exact source anchor. The public text contains readable prose. These checks establish coverage of references, not preservation of their meaning. The existing compressor remains the default.

## What happened

Five stages used **38 of a 45-call limit**; no transport failures or hidden retries occurred. All original failures and structured model requests/responses are in the [synthetic evidence bundle](examples/decision-memory-evidence.synthetic.zip). [Machine-readable results](examples/decision-memory-results.synthetic.json) include usage and a separate offline readout. Calls use the already configured Codex service; no resources were purchased or models downloaded.

| Stage | Calls | Finding |
| --- | ---: | --- |
| Previously inspected examples | 6 | New candidate 44/48 vs old 39/48, but inspection found an omitted exception; this is not a valid win. |
| Dedicated branches and semantic audit | 8 | Both candidates rejected by the facet audit. Diagnostic decoding of rejected candidates: 39/48, equal to old. |
| Four new policy combinations | 4 | Oracle decoder 85/96, but option-order consistency 62.5% fell below the frozen 75% gate. Memory comparison never ran. |
| Decoder development on consumed controls | 4 | Selecting full action text, then binding it to labels in code, reached 45/48 and 100% order consistency. Development only. |
| Fresh two-person comparison | 16 | Stronger decoder passed oracle controls; old prompt 48/48. New candidate 24/48 end to end because one compression failed. |

The last run used `gpt-6-luna` for generation and `gpt-6.1-sol` for decoding. New and old memories share the same extracted profile, questions and decoder within this run. Comparing its aggregate score with the earlier Luna run would confound decoder and compressor changes.

There are 24 primary choices per person, plus four order swaps, four current-instruction controls and two unknown-preference controls. A matched pair differs only in whether repeated complaints change a design decision. The new two-person cohort uses policy combinations and task wording absent from the earlier cohorts, but still the same four authored rule families. It is a small, correlated transfer test, not a population benchmark.

| Last run | Primary choices | Available predictions | Both similar people correct on distinguishing cases |
| --- | ---: | ---: | ---: |
| Original trajectory | 48/48 | 48/48 | 3/3 |
| Detailed profile | 48/48 | 48/48 | 3/3 |
| Old portable prompt | 48/48 | 48/48 | 3/3 |
| New condition/action candidate | 24/48 | 24/48 | No complete pair; 3 cases missing |

The one generated candidate is 24/24, but that success-conditioned rate hides the pipeline failure. Its 232 Qwen tokenizer tokens exceed the same person's old prompt's 192 tokens by 20.8%. It is 59.7% shorter than that person's detailed profile (576 tokens). These are actual counts of complete memory text from an existing local tokenizer, not Codex billing tokens. Two-person means must not be compared with a one-person cost mean as though the cohorts match.

The failed candidate copied a normal-looking word where its extracted source contained three `U+FFFD` replacement characters. Strict anchoring rejected it. The frozen extractor had accepted the damaged statement. The source corruption and exact-match failure remain in the evidence; neither is silently repaired or presented as lost preference semantics. The other candidate's semantic audit also flagged losses (21/26 facets and one unsupported addition). The experimental behavioral runner retained it with a warning; the CLI's strict export path would reject it. Behavioral accuracy on these few choices cannot certify complete preservation of the profile.

The original runner's `constraint_violations` includes missing predictions as failures. The added `fidelity-audit.json` leaves that report untouched and separates observed violations from missing outputs: the new candidate has **0 observed violations, 4 missing current-instruction cases**, and 4 correct. Unrun memory conditions in the gate-failed stage are unmeasured. No-memory output abstains; its 0/48 does not establish an improvement over a forced-choice generic model. Wrong-person output exists for only one person and misses that person's three distinguishing choices (21/24); this is a useful diagnostic, not a complete paired effect.

## Reproduce and inspect

Offline readout of an unpacked evidence folder:

```sh
python3 -m runaway.decision_audit \
  --run decision-memory-v1/transfer-validation --out my-readout.json
```

To declare a new run from a source checkout (requires Node 22+ and models available to your Codex account):

```sh
python3 -m runaway.decision_transfer freeze --out my-new-run
# Inspect the plan, including models and finite call cap, before inference.
python3 -m runaway.decision_transfer run --out my-new-run
```

The checked-in worlds are now consumed development fixtures. Rerunning them is a regression check. A subsequent generalization claim needs separately authored, frozen policies/settings, not just a changed random seed. The two-person plan's stopping text mistakenly says “all four people”; its actual world and global extraction repair limit are two people and one repair. That original wording is preserved in the frozen artifact. Source hashes must match the frozen source; current development changes are not retroactively substituted.

Experimental strict compression of your own profile is explicit:

```sh
runaway profile decision-plan my-profile/profile.private.json --budget-chars 1000
runaway profile decision-compress my-profile/profile.private.json \
  --backend codex --model YOUR_MODEL --budget-chars 1000 --out candidate
```

This sends only the projected profile to the configured model, then makes one semantic-audit call. Rejected candidates keep their private diagnostics and export no portable prompt. A model auditor can be wrong; passing its audit still does not certify behavioral or human fidelity.

## What this validates

Use failure-inclusive recovery, required-flip **and** required-stability pairs, matched-person disagreement, option-order controls, current instructions, unknown preferences, and actual token cost together. First check whether the decoder can execute the known rule; otherwise the run cannot diagnose compression reliably. Keep missing outputs visible at extraction, compression and prediction stages.

The service returned choices, not logits. There is **no RIG estimate** for this run; an accuracy difference is not relative information gain. The old local Qwen decoder failed its oracle control, so its earlier likelihood results cannot establish portability either. Real-person fidelity still needs predictions of real choices held out of profile construction, ideally compared with both generic and wrong-person memories. Synthetic worlds establish a falsifiable engineering check before that step.
