# Toward 700 interesting outputs

The target is a body of distinctive, recognizable and shareable expressions grounded in people's experiences. There is no fixed 700-type personality taxonomy, no random assignment, and no claim that 700 good outputs already exist. Generated names remain open-ended.

Keep two artifacts: the detailed evidence-linked profile and portable prompt for decisions, and a small presentation card for people. A joke can change the wording; it must not add a trait or erase the condition that made a choice reasonable. Editing a presentation card never rewrites the portable prompt or its profile identity.

## What a result contains

- A short, accessible original name, preferably 4–12 Chinese characters.
- A one-line joke or contrast a friend can understand without a glossary.
- One specific recognizable way of choosing or acting.
- One boundary, exception or context that prevents overgeneralization.

The optional `presentation` field in model answers contains `tell`, `boundary` and `claim_ids`. Local validation checks that these IDs exist, but cannot establish semantic support or that the joke is good. A result without evidence says what is still unknown. Old model answers continue working without a share card.

No fixed animal suffix, celebrity label, hidden rarity, diagnosis, or random type code. Prefer familiar everyday language over obscure fandom references. The user can edit all four card fields, preview the exact PNG, then explicitly choose to copy or download it. Sharing uses no image-generation service.

## Original tone examples — fictional, not a type library

These editorial examples illustrate possible expressions. They are not real user outputs, are not counted toward 700, and are not embedded as names for the model to imitate. Their behavior and boundaries would require evidence in an actual person's history.

| Expression | Recognizable behavior | Necessary boundary |
| --- | --- | --- |
| 气氛组质检员 | 可以一起起哄，方案还得经得起追问。 | 支持气氛不等于为结论背书。 |
| 纸上谈兵行动派 | 能在纸上先试的，绝不只在嘴上开会。 | 纸面可试才先试；涉及隐私仍检查权限。 |
| 松弛感监工 | 过程可以松弛，交付不能随缘。 | 放松节奏，不降低已约定的验收要求。 |
| 人间补丁包 | 不抢开场，擅长把最后一公里补上。 | 补缺口不等于无限替别人兜底。 |
| 懂了但没全信 | 能复述你的道理，也会追问证据。 | 有新证据会改判断，不为反对而反对。 |
| 主打一个可撤销 | 可以试，先给我一个撤回键。 | 不可逆的决定不会沿用相同速度。 |
| 边界感糯米糍 | 靠近很软，越界不行。 | 亲近与同意是两件分别确认的事。 |
| 快乐扫兴员 | 点子不错，我们顺便想想失败怎么办。 | 讨论风险之后仍能支持有边界的尝试。 |
| 不鸽但会砍 | 约好的会交，没必要的会砍。 | 调整范围需沟通，不能偷偷减掉承诺。 |
| 嘴替售后部 | 话可以直说，后续怎么做也得说清。 | 直接针对问题，不替别人揣测动机。 |
| 省流但不省事 | 说明写短，关键步骤一个不少。 | 新手缺上下文时会补解释。 |
| 反向画饼师 | 愿景先放一边，今天先做成一小块。 | 已确认方向的长期投入也有位置。 |

## Count evidence, not just strings

Card feedback separates **recognizable**, **amusing**, and **would share**; each starts as `unsure`. Editing card text clears its ratings and sharing confirmation. The exported sample contains only the approved card, self-ratings and provenance identifiers. It omits raw source, evidence and portable prompt fields. Users must still inspect card text for identifying details.

The browser can download a sample, or show the full sample before opening a GitHub Issue draft. Posting requires a separate explicit checkbox and a manual submit on GitHub. The application does not automatically collect or publish anything, and opening a draft is not a submitted sample. Actual usage feedback remains separate from share-card feedback.

Run the local audit on explicitly collected exports:

```sh
node scripts/audit-output-samples.mjs sample1.json sample2.json
```

The report excludes fictional demos, deduplicates identical files, separates the three positive self-ratings, and counts distinct normalized behavior + boundary text. Renaming the same behavior does not add another behavior. Near-duplicate pairs are flagged for editorial review with character-bigram Jaccard similarity (0.65 threshold); this is a heuristic, not a semantic equivalence test. Only the first 50 pairs are displayed, with a truncation indicator and full pair count.

`remaining_to_target` is a **text-count planning aid**, not a quality pass. Self-report is not independent evidence. A profile ID is not a unique person. Multiple revisions, punctuation changes, near duplicates, exaggerated jokes and subtly unsupported claims still require review. We must evaluate actual decision fidelity separately using held-out real choices; entertaining wording cannot substitute for that.

First pilot: review the earliest 20–30 voluntary real outputs for missing evidence, generic praise and naming collisions before expanding toward 700. Track completed generation, exported prompt, actual use, card self-ratings and voluntary submission as distinct events. There is no automatic funnel telemetry in this prototype; data is biased toward users who choose to share.

## Reference

[SBTI's open-source secondary implementation](https://github.com/pingfanfan/SBTI) explicitly describes itself as a derivative entertainment test with 27 predefined outcomes. Its [type presentation on another SBTI site](https://www.sbti.ai/types) illustrates short names paired with recognizable lines. Neither is asserted here to be the original creator's authoritative site, nor evidence of what caused the original to spread. RunAWay borrows the general presentation idea and uses original wording; its core representation remains grounded in selected experiences.
