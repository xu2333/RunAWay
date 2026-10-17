# Synthetic self-play: current choices transfer, historical recovery does not

The second sealed comparison completed24 calls without retries. Both actual
product paths recovered32/32 current choices, but only2/16 historical answers.
Neither compressor wins. **This establishes a small synthetic task result, not
real-person fidelity.** The original [failed pilot](PILOT-RESULTS.md) is unchanged.

| Reader input | Current choices /32 | Historical /16 | Joint /48 | Matched distinctions /2 |
| --- | ---: | ---: | ---: | ---: |
| Full source history |32|16|48|2|
| No memory |8|2|10|0|
| Similar person's history |28|16|44|0|
| Current-policy oracle |32|2|34|2|
| Browser extraction + portable prompt |32|2|34|2|
| Same extraction + bound compression |32|2|34|2|

The browser prompts used90/100 tokens; bound prompts used84/108, including
their shared instruction header. The two source histories used672/674 tokens.
Mean memory sizes were95 and96 tokens, about14.1% and14.3% of pooled source
tokens, under a384-token ceiling. These are frozen Qwen tokenizer counts, not
service billing. Both current-choice rows have100% normalized accuracy retention
above no-memory; that quantity is **not likelihood-based relative information
gain**. Historical retention above no-memory is zero.

## What self-play tests

A deterministic synthetic world fixes dated preferences, their strength,
conditions, exceptions, hard constraints, updates and revocations. Only its
narrated history enters the actual product extractor. A separate requested
reader model receives the resulting memory and unseen scenario questions.
Scoring uses the world's rules, rather than another model's opinion about
whether a persona sounds convincing. Gold labels, hidden event objects and
query tags never enter the extractor or reader payloads.

Full-history and current-policy-oracle controls each recovered32/32 current
choices, every required layer, both matched items and16/16 action-consistent
option pairs, with zero current hard errors. Swapping the pair's histories
lost the matched distinction. The oracle intentionally contains source-derived
answer information: it is an unbudgeted reader control, never a compressor input.
The [frozen gates and stop rules](TASK-EXECUTOR.md) were fixed before execution.

This fixture has only **two people**, from one very similar pair. Each person's
16 current questions are8 scenarios in two option orders. The two matched
items are both orders of **one underlying conditional distinction**. A wrong
person still scores28/32. Thus32/32 is a useful pipeline check with a ceiling,
not evidence of broad individuality,32 independent preferences, or superiority
over the old method. Both requested models use OpenAI's service; resolved
identities were unavailable. Cross-provider transfer remains untested.

## Old failure: diagnostic results, not a new benchmark win

On the already consumed old cohort, using the old384-token browser memories:

| Intervention | Correct /48 |
| --- | ---: |
| Original response, referenced offline only |4|
| New reader instruction only |4|
| Source cutoff only |9|
| New instruction + cutoff |4|
| Source-complete, unbudgeted prose + cutoff + new instruction |44|

All four intervention rows retain48 planned answers. None has missing answers
or observed hard violations; the first three each have4 hard-constraint
abstentions. Source-complete prose recovers all4 constraint queries, but still
misses4 other queries: all are `U` on day16 questions beyond the supplied day15
source cutoff (two layout distinctions and two revoked-rule choices). This
leaves a temporal-contract issue even in the complete-content control.
A formatting/cutoff change alone did not reliably fix
the old failure. These one-shot diagnostics do not isolate a complete cause.
The new cohort also changes task and reader contract, so its current score
cannot be presented as an improvement over D-0015's historical score.

## Calls, cost and offline replay

Requested generator: `gpt-6-luna`; reader: `gpt-6.1-sol`; CLI default effort.
Exactly24 calls completed:8 new controls,2 shared extractions,2 additional
bound compressions,4 actual-memory reads and8 old-data diagnostics. Each had
a180-second deadline; maximum observed generation12.945seconds. No retries,
repairs, replacement subjects or further service calls were made.

Reported usage was209,480input +10,371output =219,851tokens. The23,680cached
input and1,726reasoning output tokens are already included, not added again.
All24 calls reported usage; these local records are not an invoice. Standalone
browser generation cost15,825input /2,381output. Standalone bound generation
must include that extraction **plus**13,216input /502output for compression.
Controls, readers and old diagnostics are separate in the result JSON.

[Result JSON](examples/comparison-results.synthetic.json) and
[sealed evidence](examples/comparison-evidence.synthetic.zip) contain fully
synthetic fixtures, all requests/responses/attempts, predictions, source
snapshots and a checksum manifest. No human approvals, real histories, central
messages or credentials are included. Published fixtures are now development
data and must not be reused as unseen evaluation subjects.

```sh
python3 -m unittest tests.test_comparison_evidence
# After extracting the archive into comparison-replay/:
python3 -m runaway.execution_ledger --root comparison-replay/d0016 --out replay-ledger
```

Replay makes zero model calls. A credible next evaluation needs many more
independent preference differences, richer domains and another provider; real
fidelity ultimately needs predictions of withheld real user choices. Synthetic
self-play can expose loss and regressions before that step, not replace it.
