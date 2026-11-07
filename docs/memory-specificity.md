# Does the card preserve whose choices these are?

High total accuracy can conceal shared answers. This offline audit reuses the
sealed [fresh-decision](../benchmarks/fresh-decision-v1/RESULTS.md) and
[partial-information](../benchmarks/partial-information-v1/RESULTS.md) responses
to ask how the same card-reader answers score against another fictional person's
reference. It adds **zero model calls**, extractions or independent trials.
The original scores, references and sealed records remain unchanged.

## Comparability before rescoring

Both original evidence sets must pass their existing complete archive replay.
The audit additionally verifies each of the 16 card-reader requests per study:
the material must equal its exact public parent card, and model, system, schema,
reader prefix and ordered public questions must all match after replacing only
the material with an empty string. No recipient-specific instructions may remain.
The resulting common-contract fingerprints are emitted with the report.

This permits **donor-response rescoring**: a donor's existing answers can be
compared with a recipient's reference under the same neutral question contract.
It is not a newly executed wrong-card trial, a test of identity routing, or proof
that a model can authenticate the card's owner. The intended recipient changes
in the scorer only; the model saw the donor's card.

Every recipient/donor/case requires all two parent versions × two reads × two
option orders to match. Missing answers stay in the denominator and remain
distinct from U. All 12 ordered mismatched-person pairs are included; no pair is
selected for an especially large gap.

## Results

| Endpoint | Own card | Other-card response rescore | Other-card known choices | Other-card unknowns |
| --- | ---: | ---: | ---: | ---: |
| Fresh decisions, all cases | 64/64 | 96/192 | 48/144 | 48/48 |
| Partial information, primary only | 48/48 | 112/144 | 16/48 | 96/96 |
| Complete anchors, separately | 16/16 | 16/48 | 16/48 | 0/0 |

Each other-card denominator repeats the same recipient cases for three donors;
these are **pair/case units, not new people or independent observations**. The
fresh and partial studies also share the same eight cards and four people.
Do not sum the studies or compare their total accuracies as a method trend.
The 0/0 cell means no unknown cases, not perfect unknown accuracy.

On partial primary cases, an incorrect person's responses still score
112/144 = **77.8%**. Of those successes, 96 are shared unknown answers and 16 are
known choices on which the two people agree. Total accuracy alone therefore
cannot establish preservation of personal distinctions.

Only consider cases where recipient and donor both have a known reference and
their choices differ:

| Contrast endpoint | Unique recipient cases | Own card on those unique cases | Other card on directed pair/cases |
| --- | ---: | ---: | ---: |
| Fresh known choices | 48 | 48/48 | 0/96 |
| Partial primary known choices | 16 | 16/16 | 0/32 |
| Complete anchors | 16 | 16/16 | 0/32 |

The differing-choice pairs are recoverable from the old references, without
inventing new gold. On these observed cases, cards retain person-specific
choices rather than merely exploiting the shared U answers. The directed
pair/cases remain correlated repeats of the unique recipient cases.

The fresh known-choice matrix gives a compact view. Rows are the intended
recipient reference; columns are the card whose existing responses are used.
Every cell has the same 12 known cases and requires all eight answers:

| Recipient / card | auri | bryn | cato | dune |
| --- | ---: | ---: | ---: | ---: |
| auri | 12/12 | 0/12 | 6/12 | 6/12 |
| bryn | 0/12 | 12/12 | 6/12 | 6/12 |
| cato | 6/12 | 6/12 | 12/12 | 0/12 |
| dune | 6/12 | 6/12 | 0/12 | 12/12 |

## Use this alongside retention

For the next fidelity comparison, keep three separate checks: full-source
licensed choices must survive compression; contrasts between people must survive;
and unsupported targets must stay unknown. Qualify the full-source/no-memory
control first. A shared unknown answer must not count as evidence of a personal
distinction, and an always-U policy cannot pass the known-choice check.

This audit is post-hoc and uses consumed, procedurally authored fiction with
explicit rules. It adds no new source diversity, question-paraphrase coverage,
human validation, model/provider transfer, statistical independence, RIG or
production-default promotion. Older compression failures remain open.

## Reproduce and inspect

```sh
python3 -B scripts/audit_memory_specificity.py
python3 -B scripts/audit_memory_specificity.py --study partial --details
python3 -B -m unittest discover -s tests -p test_memory_specificity.py -v
```

Default output contains the full 4×4 matrices, known/unknown/contrast counts,
unique and directed-pair denominators, pinned original evidence hashes and
request-contract fingerprints. `--details` adds every recipient/donor/case with
its two parent groups of four answers. All inputs are published fictional data;
the command has no service transport or authorization path.
