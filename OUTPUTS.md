# 700 fictional residents

RunAWay ships **700 AI-authored original synthetic characters**, grouped into 28 everyday settings with 25 entries each. They are written ahead of user submissions. Familiar behaviors provide the anchor; absurd names and jokes provide the expression. The source is creative world knowledge, not private trajectories, psychological measurements or a celebrity imitation library.

Open `gallery.html` in the [browser app](WEB.md). Search, filter, browse, meet a random resident, download a card or copy a fictional role-play prompt to any LLM. A stable link such as `gallery.html#RW-0101` opens one resident directly. Random browsing is entertainment, not a personality assignment. The browser needs no model service to use the catalogue.

| Resident | Line | Behavioral anchor |
| --- | --- | --- |
| 未来的我外包公司 | 本公司的唯一员工暂时还没上班。 | 把麻烦留给之后的自己。 |
| 后悔药分装师 | 人生没有撤销键？我先焊一个。 | 做决定前先设计退出方式。 |
| 满减数学教授 | 为了省二十，我正在花两百。 | 为优惠门槛增加购买。 |
| 临时气氛代理人 | 本来想安静，怎么又归我热场。 | 冷场时主动活跃气氛。 |
| 规则内跑酷者 | 栏杆不翻，但这条路可以跳着走。 | 在允许范围内寻找更高效做法。 |

## What the 700 count means

Each source row explicitly supplies an original name, tagline and behavioral anchor. Names, taglines and anchors are unique after punctuation/spacing normalization. There is no prefix/suffix cross-product or fabricated user record. Categories are editorial shelves, not mutually exclusive personality types. Behaviors can overlap and the same person can recognize several, or none.

Category-level boundaries are **shared editorial cautions**, not 700 separately inferred personal exceptions. Cards and role prompts retain their synthetic origin. Shared category cautions appear in details, copied text and role prompts; catalogue PNGs focus on the name, joke and behavioral anchor. Evidence-based personal cards retain their own boundary on the PNG. Being readable, funny, identifiable and worth sharing are separate judgments; a count and a duplicate scan do not prove those qualities, virality, behavioral diversity or fidelity.

## Keep expression separate from personal memory

The detailed evidence-linked profile and compressed prompt remain RunAWay's core. The catalogue does not automatically classify users, inject fictional traits into a profile or provide evidence for a claim. A fictional role prompt is explicitly marked as fiction and is not a harness-installable personal profile.

The real-experience path still creates an open-ended, editable expression from the user's sources. Editing that card never rewrites the portable prompt or profile identity. Its optional `presentation.claim_ids` are checked for existing IDs; this is a structural check, not proof that the joke faithfully summarizes the evidence. Future matching should retrieve a few relevant expressions only after grounded extraction, retaining conditions and uncertainty. Never send the whole catalogue as someone's memory.

## Edit and verify

Source: seven explicit UTF-8 files under `catalog/`. Headers use `@category_id|label|shared_boundary`; entries use `name|tagline|tell`. IDs are assigned in fixed source order (`RW-0001`–`RW-0700`). Preserve row order when editing published entries; additions or taxonomy changes require an explicit version/migration plan so shared links keep their meaning.

```sh
python3 scripts/build_catalog.py
python3 scripts/build_catalog.py --check
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p test_catalog.py -q
```

The compiler checks 28 × 25, field limits, exact normalized duplicates and source reproducibility. It prints character-bigram similarity candidates for editorial review (name ≥ 0.55; tagline/anchor ≥ 0.65). These heuristics can miss semantic overlap and weak jokes. They are review aids, not a humor score. The build uses only the seven named creative source files and has no network calls.

## Real usage is a separate evaluation

Voluntary share-card feedback still separates **recognizable**, **amusing** and **would share**, all initially `unsure`. The app does not collect automatically. Exporting is not uploading; opening a GitHub Issue draft still requires manual submission. Original histories and portable prompts are excluded from card samples, though users should inspect card wording before sharing.

```sh
node scripts/audit-output-samples.mjs sample1.json sample2.json
```

This audit excludes demos and deduplicates files/behavior text. It no longer defaults to a 700-user target. Synthetic catalogue entries cannot enter the real-sample schema. Self-reports, profile IDs and exports are not unique people or controlled fidelity evidence. Evaluate compression against held-out real choices separately; grow the fictional library through editorial revision rather than waiting for real submissions.
