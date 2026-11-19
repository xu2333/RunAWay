# Both new cards recovered the control switch. One carried both requirements through two uses.

The owner wanted a learning pipeline that could serve different games. Earlier, an assistant suggested using recognition and rules for stable interface actions and switching to low-latency skills for sustained movement or coordinated inputs. The actual task asked for a design that learns a procedure from demonstrations. The current exchange did not restate the cross-game requirement.

The new extraction instruction asked when the existing method works, what triggers a switch, what replaces it, and who proposed that change. It supplied no domain example. The concurrent comparison used the preceding boundary instruction, which had produced two valid but unspecific cards in the [earlier run](real-control-boundary-v1.md).

## What the reader used

| Context | Plans | Concrete cross-game design | Concrete control distinction | Both in the same usable plan |
|---|---:|---:|---:|---:|
| Current exchange | 2 | 0 | 0 | 0 |
| Full prior text | 2 | 0 | 2 | 0 |
| Previous boundary instruction | 4 | 3 | 0 | 0 |
| Explicit switch instruction | 4 | 2 | 4 | 2 |

All twelve plans explained how to derive an executable procedure and verify its result. The two full-history plans explained how to control different activities within a game. Their route to a second game remained unclear under the frozen criterion. Four out of four new-card deliveries also mentioned simultaneous touch. No plan falsely attributed the controller to an owner requirement or claimed it had been validated. None of the twelve explicitly identified the earlier assistant as the source of this specific proposal. The readers were asked to deliver a design and received no instruction to cite a proposer.

## What survived each stage

The two new detailed profiles tied the owner's goal to the relevant assistant proposals with source references. Both portable cards identified where recognition works, named sustained movement, camera motion or simultaneous input as triggers, specified a low-latency controller with planning above it, and attributed that technical division to an unverified assistant proposal. Both also retained the owner's cross-game goal. The concurrent baseline profiles selected other boundaries. Their cards either named control architecture in general or mentioned fast and slow control without binding a trigger to its replacement.

| Generated card | Whole characters | Complete attributed switch plus owner goal on card | Transfer in two plans | Control distinction in two plans | Joint plans |
|---|---:|---|---:|---:|---:|
| Previous instruction 1 | 545 | No | 2/2 | 0/2 | 0/2 |
| Previous instruction 2 | 557 | No | 1/2 | 0/2 | 0/2 |
| New instruction 1 | 575 | Yes | 0/2 | 2/2 | 0/2 |
| New instruction 2 | 572 | Yes | 2/2 | 2/2 | 2/2 |

The 575-character card explicitly proposed shared learning, memory and verification with separately learned controls. Its readers specified different controllers for different actions, but neither explained how another game would use the pipeline. The 572-character card yielded two plans that did: both identified the shared learning loop and what game-specific skills or data would change. The difference between those readings does not establish which wording caused it.

The stronger endpoint requires a complete attributed card plus two jointly successful plans without false attribution. One of two new cards and zero of two baseline cards passed. Neither method passed the prespecified requirement that both independent cards succeed. Explicit source attribution survived on both new cards and was left unstated in all four of their plans.

## Displacement audit

All four cards retained phone priority with the tablet alternative, demonstrations before takeover with readiness uncertain, permission to start with one game, progress while hardware is unavailable, and the guided flow with one or two buttons per page. They also limited inference about visual taste and left the local inference requirement open.

All four retained the complaint about button crowding but omitted the explicit dislike of the interface's appearance found in an earlier archived card. Both new detailed profiles still reflected the negative appearance feedback. One new detailed profile explicitly left computer or cloud processing open; its card generalized this to uncertainty about processing location. Neither new card named those alternatives. One of the two concurrent baseline cards did. The new cards used 193 and 196 fewer characters than the 768-character ceiling. These are observed differences in wording and coverage; the data cannot identify crowding from a fixed budget as their cause.

## Evidence limits and cost

One owner, one previously examined design task, two generations per method and two reads per card. One local analyst scored shuffled plans before seeing arm assignments or card content. The grader knew the case and its previous failure. This comparison measures generated plans; device execution, owner acceptance and transfer to a different task remain unmeasured. The tested instruction remains experimental.

All 16 authorized attempts completed without retries after [protocol CI](https://github.com/xu2333/RunAWay/actions/runs/44401537174) passed. The requested model was gpt-6.1-sol. The service reported 132,308 input tokens, including 4,224 cached, and 23,402 output tokens, totaling 155,710. Monetary cost is unknown. The [per-attempt counts and component judgments](../../benchmarks/real-control-switch-v1/result.json) accompany the [protocol and extraction instruction](../../benchmarks/real-control-switch-v1/README.md).
