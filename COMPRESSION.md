# Compression: fewer tokens, with the distinctions still present

The compressor works from an existing evidence-linked profile. It merges repeated qualifications into readable prose, then checks each statement, scope, evidence basis, condition, exception and unknown. The reviewer must quote the compressed prompt itself. A claim ID or a general impression of similarity is insufficient.

Candidates that omit a facet, contradict the reference or add an unsupported preference receive bounded repair feedback. Every facet must pass and the complete prompt must fit the budget before a portable compact artifact is exported. Unsuccessful attempts remain visible; the detailed representation is preserved.

```sh
runaway profile compress my-profile/profile.private.json --backend codex \
  --model YOUR_GENERATOR_MODEL --review-model YOUR_REVIEW_MODEL \
  --budget-chars 1000 --attempts 2 --out compressed
```

Generation and review models are explicit, with at most two calls per attempt. There are no silent transport retries. `compression-plan` reports the projected constraint count, hash and call bound; `compression-audit` checks an existing prompt in one call. See the [full guide](QUICKSTART.md#compress-without-silently-dropping-conditions).

## A measured development example

This is one **fictional**, already-seen book-club profile: nine claims and 42 reference facets. It is not a real-user or held-out benchmark. The source profile was fixed while compression changed. Generator: `gpt-6-luna`; reviewer: `gpt-6.1-sol` through Codex. Model names were requested explicitly; immutable server-side model revisions were not exposed.

| Candidate | Characters | Qwen3 tokens | Reviewer-retained facets | Result |
| --- | ---: | ---: | ---: | --- |
| Full detailed representation | 2,216 | 953 | Reference, not scored | Baseline |
| Previous compact prompt | 775 | 351 | 30 / 42 | Rejected |
| Previous body, same header as new compressor | 665 | 330 | 30 / 42 | Rejected |
| New first attempt | 419 | 232 | 38 / 42 | Rejected; repaired |
| New repaired candidate | 446 | 244 | 42 / 42 | Model check passed |
| Deliberately reversed exception | 447 | 244 | 40 / 42 | Rejected; unsupported addition |

The repaired prompt uses **26.1% fewer tokens than the previous body with the same header** (330 → 244), or 30.5% fewer than the original full compact prompt (351 → 244). Tokens were actually counted using the existing local Qwen3 tokenizer, including the complete preference prompt. Harness and chat-template overhead is excluded. These are not tokenizer-independent savings.

The first attempt omitted, among other details, that the hidden export button was motivated by simplification and that two evidence omissions remained unresolved. The repair restored those distinctions. For the negative control, the exact phrase “但不省权限检查” was changed to “可以省略权限检查”; the reviewer rejected the reversed exception. This is a fault-injection check, not an invented user-choice question.

The current offline demo includes the repaired candidate. The [saved comparison](examples/compression-results.synthetic.json) contains the reference facets, all five compact texts, exact quoted audits, model-call provenance and tokenizer hashes. It includes the previous prompt for comparison after the demo was updated.

## What these numbers do not establish

- **A model's retention verdict is not proof of entailment.** Exact quote existence is checked in code; interpretation remains fallible. Both generator and reviewer are from the same provider.
- **Facet counts are correlated.** Eight of the previous prompt's twelve flagged facets concern repeated self-report/provenance distinctions. They are not eight independent missing behavioral preferences. The other flagged distinctions concern simplification, privacy context, an explicit rejection of a generalization and paper testing versus shipping.
- **The acceptance reviewer also supplied repair feedback.** This is development optimization against that checker, not a held-out judge or independent test. One negative control does not establish its false-acceptance rate.
- **Preserving a profile does not prove that the profile describes a person correctly.** RIG on real later messages and reproduction of actual choices are separate evaluations. No RIG improvement is claimed here.
- **The initial `build` path still uses its earlier paragraph-level check.** `profile compress` is the explicit stricter pass; it does not require repeating source extraction.

The objective is to reduce the complete portable representation while retaining distinctions that change judgments. A shorter candidate that drops those distinctions fails even when it sounds convincing.
