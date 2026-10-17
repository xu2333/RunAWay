# Stress-test the metric before trusting a compression score

D-0018: [Subsequent approved service comparison and retained failure denominators](STRESS-RESULTS.md). This document preserves the earlier offline calibration.

The new suite detects distinct kinds of semantic loss across six preference
domains. **These are deterministic development controls, not model performance.**
No new inference was run. The [last actual comparison](COMPARISON-RESULTS.md)
still ties on current choices and fails historical recovery; it remains sealed.

## Why aggregate accuracy is insufficient

The development fixture has12 fully synthetic people in6 paired clusters.
Each pair differs in one conditional domain; across pairs all six domains vary.
The fields concern feedback, product validation, routine organization, interface
layout, research and collaboration. Default choice, conditional choice, update
revocation and constraint restoration vary; none is inferred from a real person.

Each person has28 current scenarios, each in two option orders, and19 historical
queries. Both orders must be correct to recover a scenario. Six matched-domain
contrasts require recovering **both people in every differing context and order**.
Context variants are not additional independent preferences. Statistical units
are the6 paired clusters, not672 queries or12 independent people. Per-person and
per-cluster rows remain available; no population confidence interval is claimed.

| Program-controlled input | Current /672 | Scenarios /336 | History /228 | Matched domains /6 | Observed hard violations |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete semantic state |672|336|228|6|0|
| No memory |96|48|0|0|0|
| Similar person's state |624|312|204|0|0|
| Delete one domain |576|288|192|5|0|
| Delete exceptions |552|276|188|0|0|
| Delete hard constraints |600|300|156|6|72|
| Ignore replacements and clears |480|240|156|6|0|
| Ignore revocations |480|240|156|0|0|
| Wrong exception condition |512|256|228|0|0|
| Wrong historical times |672|336|84|6|0|
| Delete strong evidence |552|276|228|6|0|
| Invent choices for unknowns |600|300|228|6|0|

Two additional controls separately weaken an AND constraint into a one-condition
rule and arbitrarily resolve equal-strength contradictions. Their complete
counts and layer diagnostics are in the [calibration](examples/fidelity-stress/calibration.synthetic.json).

A wrong person scores92.9% on ordinary questions while losing **every** targeted
personal distinction. Therefore raw accuracy is never sufficient to qualify a
compressor. Similarly, a memory with wrong timestamps can retain all current
choices while losing most historical answers. A single pooled score conceals
that tradeoff. Hard-error counts distinguish abstention/missing from an observed
choice violating an active constraint; invalid outputs are errors, not actions.

## Semantics and boundaries

The authored event grammar includes strong/weak evidence, explicit replacement,
clear, conditional exceptions, conjunctions, hard constraints, revocations and
revocations of revocations. All four Boolean condition combinations are queried,
so an AND rule cannot pass merely by remembering its last condition. Two opposite
equal-strength active observations remain unknown, rather than letting an
arbitrary record ID or ordering choose a winner. Current explicit requests win
over remembered preferences. Every query falls within the source coverage.

This version is deliberately separate from the old event grammar. It uses the
same browser extraction and bound-compression product functions, with the new
narrated history as their only source. It does **not** append the old helper's
incompatible “latest on ties” protocol. Changing task semantics is disclosed;
new scores must not be compared with D-0015/D-0016 as a product improvement.

The program reads event objects directly for these controls. It does not parse
the meaning of arbitrary generated prose. Mutations were chosen to exercise
specific requirements; they do not prove how often such failures happen in real
compression. Narrative templates and explicit preference records are also much
simpler than inferring taste from natural agent trajectories. Synthetic success
cannot establish real-user fidelity or cross-provider portability.

## Reproduce offline

```sh
python3 -m runaway.fidelity_stress --out my-stress-calibration
python3 -m unittest tests.test_fidelity_stress tests.test_fidelity_runner tests.test_fidelity_artifacts
```

The [published fixtures](examples/fidelity-stress/fixtures.synthetic.json) are
**development data**, including their hidden semantic annotations. Encoder
requests contain only narrated history; reader requests contain memory, public
queries, instruction and cutoff. Seeds, event objects, parameters, tags, paired
identity and scoring mappings are absent. The audit viewer intentionally reveals
answers and must never be supplied to the compressor.

## Next actual comparison: prepared, not approved or executed

A local frozen proposal and runner are ready for separate review. The unreleased
future cohort uses4 people in **2 paired clusters**, each pair differing across
three domains, with new parameter combinations and question wording. It is still
the same six-domain ontology and a small descriptive pilot, not an independent
population sample or a domain-generalization test. Future histories/truth are
excluded from this public export.

The upper bound is48 experiment generations:16 full/wrong/oracle/none reads,
8 shared extractions,8 additional bound compressions,16 actual-memory reads.
Each subject is tested at128/384 actual tokenizer tokens, requesting256/768
characters. The methods share the exact extracted profile within each budget.
Standalone new-pipeline cost includes extraction **and** extra compression.
Because the extraction request bound changes with budget, cross-budget results
measure the end-to-end pipeline, not an isolated compression stage.

Full history and source-derived current-policy oracle must each recover at
least90% of current queries, collapsed scenarios and every critical layer, zero constraint errors,
all6 matched domain contrasts and at least90% action consistency. Full history
must also recover at least90% of historical answers. Wrong-person input may
recover at most1/6 matched domains. Full versus no-memory current accuracy must
differ by at least25percentage points. These thresholds use exact counts.
The oracle intentionally contains answer-bearing source information, is
unbudgeted, and never enters extraction/compression; its historical losses are
reported without making them a current-reader qualification threshold.

Each method/budget always retains224 current +76 historical =300 planned
answers,112 collapsed current scenarios and6 matched domain contrasts. Two
paired clusters are too few for significance or a population winner claim.
Current/historical tradeoffs, weakest layers and active-constraint violations
remain visible. No invented likelihood-based relative information gain is used.

Real invocation requires matching separately verified human approval, frozen
source/input/runtime checks and an exclusive single-use intent. An approval
receipt is operator bookkeeping, not cryptographic human authentication. Every
backend entry uses180seconds and the unchanged2+2second cleanup/isolation
observer. Control failure, timeout, transport/format failure, unknown usage or
uncertain checkpoints stop the whole remainder. No repair, retry, replacement
person, truncation or old-budget reuse. Local product/budget rejection keeps
failed method rows. Identical requests reuse one authenticated completed response
offline; reused answers are not independent model reads or extra allowance.

This preparation made **zero experimental model calls and zero experimental
service tokens**. Native chat development usage is tracked separately by the
host; unavailable totals are not assumed zero. The proposed48-call cap is not
a hard aggregate token/HTTP/time/money cap. No resources were purchased.
