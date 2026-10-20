# Real human ratings: no personalization gain in the first pilot

We completed **10 real Codex calls** with requested model `gpt-6.1-sol`, using **two actual PRISM participants and four later questions**. Every arm made the **same choice on every question**. This pilot does **not** demonstrate that RunAWay improves predictions of personal taste.

| Reader input | Correct, both option orders | Distinct questions correct |
|---|---:|---:|
| Three complete earlier conversations |6/8|3/4|
| No personal history |6/8|3/4|
| Own compressed prompt |6/8|3/4|
| Other participant's compressed prompt |6/8|3/4|

All four arms were consistent under option swapping. There were no missing predictions, retries, repair calls or extra model probes. The 32 condition/order predictions are repeated measurements of **four questions from two people**, not 32 independent observations.

Because full-history accuracy equals no-history accuracy, `(own − none) / (full − none)` is **undefined**. Equal accuracy cannot be called “100% fidelity retention.” The transport provides no choice log-probabilities, so this is not likelihood RIG either.

## What was tested

[PRISM](https://github.com/HannahKirk/prism-alignment) contains actual participant prompts, model responses, ratings and continuation selections. We pinned source commit `a9ec82149036374768f70e132a2369a750e06bbe` and checked the downloaded conversation file against its official Git blob hash.

Before model execution, we selected 20 eligible participants by a fixed hash order, with three earlier conversations each and two later held-out conversations. The first two participants were used in this pilot; the other 36 questions were not model-tested. Target prompts and responses do not occur in the selected historical profiles. Official language, PII and moderation flags were applied; those automated flags are not a guarantee of privacy clearance. No survey demographics were loaded.

Each question uses the actual highest- and lowest-rated first-turn responses, with a human score gap of at least 20 and a matching recorded continuation selection. Whole target conversations and their ratings stay outside the encoder input. Target scores and model identity metadata are hidden from readers; unchanged response text can still identify its model naturally.

The encoder used the unchanged browser request, validation and complete export, with a **768-character ceiling including the boundary and newline**. The two resulting prompts were **758 / 732 characters**. Private claims and evidence were not added to reader context. Historical UI ratings are serialized as traceable actions, explicitly distinguished from user-authored speech or endorsement of every claim.

The no-memory arm still estimates ordinary response quality; it is not forced to abstain. This matters because good general answers can predict many human ratings without personal information.

## What the failure tells us

The pilot provides no evidence of personal-memory utility on these questions. It does not isolate whether the history lacks predictive preference evidence, the extraction loses useful signals, or the reader ignores them: even the full-history control fails to improve over baseline.

A **post-hoc descriptive audit**, not a preregistered model baseline, found that choosing the longer response agrees with human ratings on **32/40 questions** in the prepared bank and **3/4** in the pilot. All 40 first-turn pairs come from different models; 17 have a response-length ratio above 2. Selecting the best and worst rated responses can therefore introduce substantial general-quality or length confounding. These observations motivate a different next protocol; they do not prove its cause or license tuning this consumed pilot.

The next useful real tests should separate preservation of documented judgments from prediction of new choices, and include more comparable responses, such as same-model pairs with matched lengths. Those controls can reduce obvious confounds but do not themselves guarantee equal factual quality or useful personal signal. No additional model calls are authorized by this exhausted ten-call scope.

## Cost and evidence boundaries

Service records total **90,520 input + 5,628 output = 96,148 tokens**. Cached input, 4,224, is already within input; reasoning, 2,022, is already within output. This is experiment-service usage, not an invoice or total research/chat cost. Resolved model identity was not reported. No GPU instance was used.

The exact requests, outputs, profiles, source-label reconstruction and execution identities are retained in the local research workspace. Human text and model responses have different upstream terms; original PRISM text and derived private profiles are **not included in the MIT source release**. This public report contains aggregates, not a self-contained replay of the private service records.

[Aggregate results](examples/real-scenario-pilot-results.json) · [Earlier synthetic end-to-end test](END-TO-END-TASTE.md). The synthetic success and this real zero-gain result must remain separate.
