# Three-source graph study:74/79strict cases,five known choices become unknown

The24-slot scope closes on2026-11-01 with **24actual CLI children**,six valid
cards,no skips/failures/missing usage and **375,449reported tokens**. All three
new full controls qualify(40/40,23/23,16/16); no-memory gets16/6/7respectively.
The exact frozen encoder,renderer,reader and1536whole-character cap are unchanged
from the one-card pilot. No old card or response is supplied to extraction.

| Source | New card0/card1 characters | Strict cases | Known | Unknown | Personal-known |
|---|---:|---:|---:|---:|---:|
|h93|1133/1066|40/40|24/24|16/16|14/14|
|j16|732/835|18/23|12/17|6/6|9/11|
|Development|575/574|16/16|9/9|7/7|0/0|
|Pooled|All six≤1536|**74/79**|45/50|29/29|23/25|

No cases are missing. Each primary case needs both new cards × both reads ×
both orders correct,**8answers/case**. Development preference11/11and execution
5/5pass. The earlier one-card40/40is preserved separately and is not pooled into
this endpoint. These cases/reads/orders are not independent people or an
independent holdout; there is no fresh baseline arm or causal historical gain.

## Repeated generation and reading

| Source/card | Read0 | Read1 | Strict bothreads | Within-card disagreeing cases |
|---|---:|---:|---:|---:|
|h93/0|40/40|40/40|40/40|0/40|
|h93/1|40/40|40/40|40/40|0/40|
|j16/0|18/23|18/23|18/23|0/23|
|j16/1|23/23|20/23|20/23|3/23|
|dev/0|16/16|16/16|16/16|0/16|
|dev/1|16/16|16/16|16/16|0/16|

The two j16cards' response vectors differ on5/23cases;h93/dev have no observed
between-card differences. This is not a causal variance decomposition. The
identical j16/card1read requests still produce three different case outcomes.
Selecting its first23/23read would hide instability. All fixed unknown cases
remain correct; the five strict losses are known actions answered`U`.

## Source-linked failure audit

| Case | Frozen gold | Card0,read0/read1 | Card1,read0/read1 |
|---|---|---|---|
|w07,borrowed exhibit exception|隔柜看原件|U/U|gold/U|
|w11,night-shift exception|约定固定安静时段|U/U|gold/U|
|w19,meter-disabled week|按固定日期浇水|U/U|gold/gold|
|w21,gift rephrase|先给候选让对方挑|U/U|gold/gold|
|w22,new gift instance|先给候选让对方挑|U/U|gold/U|

Every cell summarizes both option orders,which agree within each listed read.
The complete raw responses and unchanged author labels remain in the archive.

Two source-linked hypotheses need attention:

- Action fields sometimes bundle the choice with explanation or scope text:
  card0uses“按出借约定隔柜看原件”,“先约定固定安静时段”,and“按固定日期浇水，仅覆盖停用周”;
  card1uses“履行约定，隔柜看原件”and“按固定日期浇水；恢复可靠读数后回通常规则”.
  The core offered actions are present,but these fields can be interpreted as
  a different unlisted action under the unchanged reader contract. Card1's
  successful first read shows that this wording does not deterministically
  force failure. Never mechanically strip“先”:it is part of the gift action.
- Both cards retain“无惊喜或保密硬要求”from the earlier concrete gift setup(m28)
  as a necessary condition. The later explicit future-policy restatement(m31)
  lists familiar/nonurgent/budget/unnamed/timely conditions without repeating
  surprise/confidentiality. w21states no surprise requirement,but not secrecy;
  w22does not restate either. Under the frozen authored criterion these added
  prerequisites produce overly conservative abstention. Treating an early
  instance detail as a universal condition differs from preserving a permission
  prerequisite on an action-only revision.

These are developer diagnoses,not independently accepted source semantics or
unique causal mechanisms. Night-shift prerequisites/scope may also contribute;
no per-question reasoning trace isolates a cause. The graph compiler guarantees
declared parent-condition inheritance,not correct edge/condition classification.
No reference is repaired or adjudicated from these responses.

Original disputed j16/w14stays unscored and outside controls. Its eight responses
all match the old“各自计分”annotation; agreement does not accept that annotation.
No failed case is removed,and no better card/read replaces an earlier sample.

## Accounting,replay and limits

Input339,577 + output35,872 = **375,449tokens**. Cached input35,968and reasoning
output5708are subsets,not additions. No missing counters. This is reported usage,
not a bill;24was an attempt cap without token/money ceilings. All24slots are used
and closed. No retry,repair,resume,replacement or replenishment. Owned temporary
guard exited. Requested model is gpt-6.1-sol;served identity,internal RPC/retries
and upstream cancellation remain unobservable.

```sh
python scripts/replay_action_revision_stability.py
python -m unittest discover -s tests -p test_action_revision_stability_evidence.py -v
```

The portable archive replays all24requests/raw values,source-only graph binding,
six artifacts,controls,counters and strict79case scoring. Eight damage tests
protect source/reference/disputed masks,parent lineage,raw/request/artifact hashes,
missing denominators,usage,runtime and unsupported claims. Private local grants,
machine paths and transport/error envelopes are excluded;their hashes are
provenance,not omitted-byte reconstruction. New replay calls0models.

No production default,new original232inventory cells,real-person/cross-model/
harness fidelity or population-stability claim. Next work must distinguish
action labels from scope/execution notes,and complete policy restatement from
same-context action revision,while preserving unknown and permission boundaries.
