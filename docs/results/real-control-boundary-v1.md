# A general extraction hint preserved the goal but missed the control split

An owner wanted the same learning pipeline to work across games. An earlier assistant proposed an implementation distinction: menu entries can use visual matching and discrete actions, while movement or combat needs a controller for continuous input. The current task asked how to learn from demonstrations. On this same retrospective task, the candidate told the encoder to preserve a project boundary that changes execution and to identify whose proposal it was. The hint gave no game or control examples.

All four new cards stated the transfer goal. Neither candidate card explained when to switch controllers or how execution would change. One called it layered control and left navigation and combat coverage open. The other mentioned controller layers and marked them as proposed. The body of each card retained the provenance but omitted the useful distinction. One observed full-history plan did spell it out, using visual rules for menus and a separate low-latency controller for movement and combat.

## What the reader actually produced

Each row keeps its original denominator. Each of the six returned plans explained how to learn an executable policy and verify its outcome. None reported multi-touch or misrepresented the proposed controller as an owner mandate or an established capability. A blank second reading cannot show consistency.

| Context | Returned / planned | Concrete cross-game transfer | Menu vs continuous with an execution consequence | Both in one usable plan |
|---|---:|---:|---:|---:|
| Current exchange | 1/2 | 0/2 (one unclear) | 0/2 | 0/2 |
| Full earlier text | 1/2 | 1/2 | 1/2 | 1/2 |
| Current encoder, two cards | 2/4 | 1/4 (one unclear) | 0/4 | 0/4 |
| Candidate encoder, two cards | 2/4 | 2/4 | 0/4 | 0/4 |

Each card received exactly one completed reading. Of the two original-method cards, the 510-character card elicited cross-game transfer and the 526-character card elicited only variation within a task. Both candidate readers offered concrete reusable infrastructure and game-specific adaptation. No card satisfied the frozen rule requiring two jointly successful readings. The full-history group also lacked its second reading. Neither a method-level advantage nor repeatability follows from these data.

## Where the content went

The source explicitly distinguished menus from movement, camera and combat and discussed sustained and simultaneous touch. Both original-method profiles omitted the distinction. Neither candidate attached that distinction to an extracted decision. The 507-character candidate qualified the device goal with the owner's direction to progress without hardware. The 495-character candidate qualified the first-game scope with the owner's transfer goal. Both used valid evidence, but chose boundaries already covered elsewhere. The second detailed profile mentioned fast and slow control among unconfirmed suggestions. Its portable body reduced this to layered control. Neither explained the trigger and the corresponding change of action, even before the reader saw it. All four whole cards had at least 242 characters of headroom under the 768-character cap.

| Content checked against the earlier 507-character card | Original-method cards (510 / 526 characters) | Candidate cards (507 / 495 characters) |
|---|---|---|
| Phone preferred, tablet acceptable; demonstrations followed by takeover | Both preserved the device options, goal and uncertain readiness | Both preserved the options and goal. The second kept uncertainty about demonstration count and acceptance but left the takeover threshold less explicit. |
| One game as a starting point; progress without a connected device | Both kept both conditions | Both kept both conditions |
| Guided interface with one or two buttons per page | Both kept the number and local scope | Both kept the number and local scope. Both dropped the explicit complaint about appearance from the portable text. The original 510-character card retained that complaint; the 526-character card omitted it too. |
| Unknown need for local or cloud-assisted processing; implementation proposals lack owner endorsement | Both preserved these qualifications | Both preserved them. The first omitted the older card's specific caveat about visual-style preferences, while the second kept examples. |

These differences describe observed cards. Spare character capacity and variation between two baseline generations prevent attributing omissions to a full budget. The finding points to **selection** in the detailed extraction: a generic request to keep one boundary can select another valid boundary. A further candidate could ask which shared mechanism stops working, what replaces it, and where the source proposes that switch. That change remains untested.

## Scope and accounting

The requested model was gpt-6.1-sol. The run started after all three [protocol CI jobs](https://github.com/xu2333/RunAWay/actions/runs/44272275905) passed. Slot 11, the second read of the 526-character baseline, timed out at the 180-second limit. All four extractions and six deliveries returned. The runner closed the other five slots without retries. The ten responses reported 87,749 input and 16,257 output tokens (104,006 combined, including 4,224 cached input tokens in the input count). Usage for the timed-out attempt and total monetary cost are unknown.

One local analyst scored shuffled deliveries and locked judgments with excerpts before opening the assignment key and comparing the cards. The analyst knew the source and earlier failure. This was one owner and one previously inspected task, with no independent owner assessment or device execution. The [per-slot record](../../benchmarks/real-control-boundary-v1/result.json) and [frozen criteria](../../benchmarks/real-control-boundary-v1/README.md) preserve the distinction between an observed omission and a missing delivery.
