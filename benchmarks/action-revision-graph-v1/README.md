# Action-only revisions inherit conditions — experimental encoder

Update: the [one-card pilot](../action-revision-pilot-v1/MEASURED.md) now observes
1078characters and40/40across two reads/bothorders. One producer cannot verify
generation stability or general source completeness. The invariant below
remains conditional on the encoder's semantic annotations.

The [fixed-parent study](../dense-layout-probe-v1/MEASURED.md) finds a shared
upstream omission: changing feedback action loses an earlier permission
condition. This prototype asks the source-only encoder for a typed history graph.

A `base` node specifies a choice or past implementation fact,its object,target,
necessary conditions and user evidence. An `action_revision` points to an
earlier active choice and provides only the new action and source anchors.
The compiler copies parent conditions,object,question and priority exactly;
the encoder cannot override them on that edge. Only that choice becomes
inactive. Other choices/past facts from the same source message survive.
Independent priority exceptions have their own bases and conditions; ordinary
branch prerequisites are not automatically inherited.

Active rows pass the unchanged owned-condition source checks and dense renderer,
including the1536whole-public-character limit. Private superseded nodes do not
count as public memory. No new decoder/public syntax. The graph cannot prove
semantic edge types,parent selection,source completeness or factual entailment.
Misclassified bases can drop conditions; incorrectly declared revisions can
inherit too much. Only cross-message revisions are supported; same-message
updates need a complete current base or remain unknown. Limits:60history nodes,
30active rows,12objects,and original source/quote/budget constraints.

Six offline controls check exact inheritance,retained past facts,all eight toy
permission/weather/exception worlds,missing-permission damage,malformed parent/
timing/role/overrides,source-only requests and hard budget failure. Toy outcomes
are code invariants,not model fidelity or semantic acceptance. The separate
[five-call pilot](../action-revision-pilot-v1/README.md) is now closed. No
production-default change.

```sh
python -m unittest discover -s tests -p test_action_revision_graph.py -v
```
