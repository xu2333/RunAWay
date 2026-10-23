# Source constraints v2: measured extraction, consumed regression

`distill --format constraints-v2` preserves the measured source-only request,
strict wire schema, compiler and complete public renderer. This directory stores
six actual fictional-source extraction requests, raw JSON answers and expected
compiled products from the sealed 43-call study, rather than regenerated answers.

```sh
python3 benchmarks/source-constraints-v2/check.py
```

This makes **zero model calls**. It checks exact request/schema, compilation,
source hashes and portable text parity. It does **not** rescore the reader or
create a fresh holdout. The original manifest SHA-256 is recorded in the fixture;
checksums detect changes, not authorship or semantic truth.

The preceding prospective study requested `gpt-6.1-sol` (resolved server model
identity unavailable). It used 6 fictional people, 24 scenes each, 2 option
rotations; both rotations had to be right for each of the 144 person/scene cells.
The developer constructed the corpus. It was unseen by the model, **not** blind
to the developer, and is now consumed development data.

| Material | All / 144 | Known / 65 | Unknown / 79 |
| --- | ---: | ---: | ---: |
| None | 79 | 0 | 79 |
| Full source | 144 | 65 | 79 |
| v1 standalone card | 133 | 54 | 79 |
| v2 standalone card | 144 | 65 | 79 |
| Raw tail matched to v2 characters | 85 | 6 | 79 |
| Wrong person's v2, target scored | 89 | 27 | 62 |
| Wrong person's v2, donor scored | 144 | 65 | 79 |

v2 recovered 11 known-case abstentions without a new error. The six complete
public cards used 250–325 Unicode characters including all inference guidance;
this is not a token-saving or billing claim. The whole study consumed 43 local
CLI attempts, 518,699 input + 56,917 output = 575,616 observed tokens, without
retry or card repair. Upstream RPC attempts were unobservable.

Five source histories promised a stable exhaustive finite rule family. One did
not, and v2 retained only its observed choices. In this bounded setting, a
post-hoc check also matched all 640 typed rule/state values to the source rule
definitions. Exact quotes alone cannot establish this semantic correspondence
for new inputs. Six fictional people are the dependence units; 144 scenes are
not 144 independent people. General real-person, cross-model and actual-harness
fidelity remain unverified. No defaults changed based on these results.

See [usage and limitations](../../docs/source-constraints.md) and the
[earlier decoder-removal ablation](../standalone-latent-v1/RESULTS.md).

A separate [naturalistic source-control study](../natural-controls-v1/README.md)
qualified full histories on 56/56 cells without a finite-family promise. It has
not yet tested compact cards and does not extend the v2 result above.
