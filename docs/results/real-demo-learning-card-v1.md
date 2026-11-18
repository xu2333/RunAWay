# A 507-character card carried the cross-game design goal into both plans

The owner asked how a system could learn the correct procedure from demonstrations. An earlier message explicitly prioritized a learning pipeline that could extend from the first game to others. The actual request and its preceding exchange discussed milestone recording without restating the cross-game goal.

| Context for the same task | Concrete cross-game design | What the two deliveries proposed |
| --- | --- | --- |
| Current exchange | 0/2 met, 2 unclear | Both proposed useful task-learning and outcome checks. Their examples addressed changes to inputs, records or starting screens within a task. |
| Full earlier text | 1/2 met, 1 unclear | One shared the skill interface and learning process across games while adapting controls. The other described sharing infrastructure between menu actions and navigation or combat, leaving the route to a second game unspecified. |
| Exported card | 2/2 met | One put game-specific goals and visual features in task configuration while sharing recognition, branching, execution and verification. The other shared localization and outcome checks while supplying each game's interface knowledge and task flow. |

All six plans explained how to derive an executable procedure and check completion. All passed the current-task quality gate. Under the frozen rule requiring both deliveries to meet the cross-game criterion, the single-case result is card 1/1, full history 0/1 and current-only 0/1. Full history exposed the requirement but did not pass consistently. The card's two successes show retention on this task; the observed difference cannot establish a general advantage over history.

## Where detail was lost

The owner allowed starting with a single game while prioritizing reuse across games. Both the detailed extraction and the portable card explicitly retained that tradeoff. The detailed extraction's evidence also contained the suggested first game's name. The card generalized it to one starting game. Naming that game was optional under the original requirement.

Earlier assistant proposals distinguished menu interactions from continuous controls for movement, camera and combat, including multi-touch support. That technical qualification was absent from the extracted decision claims and the card. Both full-history deliveries discussed the difference between menu and continuous control. Neither card-conditioned delivery addressed it. This collateral omission was identified after the primary scoring. The implementation proposal came from the assistant. It was not an additional owner requirement or a failure of the primary cross-game endpoint.

## Scope, grading and cost

The encoder received the 27 qualifying earlier messages, totaling 5,096 characters of message text. It produced one portable prompt of 507 characters including its header and final newline. The original seven current messages were held out of extraction and supplied identically for all six plans. The same owner and project appeared in the recording study, whose input contained this earlier exchange. This is a different task with reused source material.

The local analyst assessed six shuffled outputs with condition labels withheld and saved the judgments and exact excerpts before revealing the assignments. The analyst knew the source and criterion, and answer content could suggest its condition. No independent human rating or owner acceptance was measured. Unclear outputs stay in the denominator.

All seven approved attempts completed after the [three-platform CI run](https://github.com/xu2333/RunAWay/actions/runs/44235680786) passed. Reported usage was 57,755 input and 9,445 output tokens, totaling 67,200. This tests one generated card on one design question. Successful deployment to a second game and repeated card generation remain unmeasured. See the [frozen protocol](../../benchmarks/real-demo-learning-card-v1/README.md) and the [per-attempt counts](../../benchmarks/real-demo-learning-card-v1/result.json).
