# Generation failures and observed losses

Original one-shot answers only. No repairs or replacement candidates. Missing cells are separate from observed mistakes.

| Person | Format | Valid | Packed characters when available | Over budget | Rejection |
| --- | --- | --- | ---: | ---: | --- |
| h17 | support-v1 | False | 673 | 161 | Complete prompt exceeds budget after lossless packing: 673 > 512; no truncation |
| h42 | grouped-v1 | True | 473 | 0 |  |
| h68 | support-v1 | False | 749 | 237 | Complete prompt exceeds budget after lossless packing: 749 > 512; no truncation |
| h93 | grouped-v1 | True | 474 | 0 |  |
| h17 | grouped-v1 | True | 482 | 0 |  |
| h42 | support-v1 | False | 611 | 99 | Complete prompt exceeds budget after lossless packing: 611 > 512; no truncation |
| h68 | grouped-v1 | True | 492 | 0 |  |
| h93 | support-v1 | False | 690 | 178 | Complete prompt exceeds budget after lossless packing: 690 > 512; no truncation |

Greedy phrase packing is not a minimum possible representation length. Character decompositions describe original strings and grammar, not an information-theoretic lower bound or proof of semantic completeness.

## support-v1

Observed own errors:0; missing own cells:80; observed tail errors:0; observed donor errors:0.

## grouped-v1

Observed own errors:23; missing own cells:0; observed tail errors:48; observed donor errors:23.

### h17 / t03 / scoped_exception

临时内部脚本没有外部调用者，团队确定不留旧格式，三天后弃用，输出不进入长期管线。按我的记录选择接口方案。

Reference: 切换新接口并标注新版本. Own (two positions): ["U", "U"]. Full: ["切换新接口并标注新版本", "切换新接口并标注新版本"].

临时内部脚本是单独例外，公共接口改口不覆盖它。

Exact reference support: [{"source_id": "m21", "quote": "刚才公共接口之外，还有一个临时内部一次性脚本：没有任何外部调用者，三天后弃用；团队确认不保留旧格式，输出也不进入长期管线。"}, {"source_id": "m22", "quote": "对这个临时一次性脚本，选切换新接口并标注新版本，别为它加旧接口兼容层。这是单独的情境，不是改掉公共接口的安排。"}, {"source_id": "m32", "quote": "临时内部脚本那一项不受公共接口改口影响。三天后弃用、没有外部调用者这些前提还在，不要把两个项目拼成一个全局“求稳”或“求快”的性格。"}]

### h17 / t04 / research_tradeoff

内部探索性复现实验的方案尚未锁定，预留盲测集还没看；只找候选方向，不把探索结果称作独立确认，没有近期对外提交期限。按我记录的数据使用取舍选。

Reference: 留住盲测集，等方案锁定再查看. Own (two positions): ["U", "U"]. Full: ["留住盲测集，等方案锁定再查看", "留住盲测集，等方案锁定再查看"].

该内部探索性实验的明确用户取舍；不是助手建议。

Exact reference support: [{"source_id": "m6", "quote": "另一件事是内部探索性复现实验：有一份预留盲测集，还没看结果；方案尚未锁定。现在只是找候选方向，不把探索结果包装成独立确认，也没有近期对外提交期限。"}, {"source_id": "m8", "quote": "在刚才这个内部探索阶段，我选：留住盲测集，等方案锁定再查看。这是这次数据使用上的取舍，别从我的岗位猜一个相反答案。"}]

### h17 / t12 / document_purpose

给熟悉方法的研究者写公开复现报告；两种写法都能复现最终结果，篇幅也都允许。按我的记录怎样呈现？

Reference: 保留失败路线和最终复现步骤. Own (two positions): ["U", "U"]. Full: ["保留失败路线和最终复现步骤", "保留失败路线和最终复现步骤"].

公开研究复现报告的明确选择。

Exact reference support: [{"source_id": "m24", "quote": "接下来是给熟悉方法的研究者看的公开复现报告。两种写法都能把最终结果复现，篇幅也都允许；可以连失败路线一起交代，也可以只留最终步骤。"}, {"source_id": "m26", "quote": "对这份面向熟悉方法读者的公开复现报告，我选：保留失败路线和最终复现步骤。注意不是在定义所有文档都该这么写。"}]

### h17 / t13 / scoped_exception

给半夜值班同事准备查到就能照做的故障处置手册。按我的记录怎样呈现？

Reference: 只保留最终处置步骤. Own (two positions): ["U", "U"]. Full: ["只保留最终处置步骤", "只保留最终处置步骤"].

值班故障手册的具体例外，不套用研究报告风格。

Exact reference support: [{"source_id": "m27", "quote": "另外，给半夜值班的同事看的故障处置手册，我只保留当前可执行的最终处置步骤，不放失败路线。那是查到就要能照做的文档，别套研究复现报告的取舍。"}]

### h17 / t15 / observed_choice_paraphrase

去做工作报告，行程两天；白天提前到与前晚夜间出发价格相同，都能赶上报告，没有紧急会面或必须晚走的要求。按我的记录选行程。

Reference: 前一天白天出发，留出空档. Own (two positions): ["U", "U"]. Full: ["前一天白天出发，留出空档", "前一天白天出发，留出空档"].

工作报告同义改写，前提一致。

Exact reference support: [{"source_id": "m18", "quote": "下月要去一次工作报告，两天行程；机票价格相同，白天提前到和前晚夜间出发都能按时到场。没有紧急会面，也没有要求我必须在出发前一天留在本地。"}, {"source_id": "m20", "quote": "在上面这组工作报告条件下，我选：前一天白天出发，留出空档。这只是这类工作行程的安排，休假出游没有在这里讨论。"}]

### h42 / t02 / partial_context_identifiability

此次任务只可能是记录中的这两项之一：已有120个客户端、一个月迁不完且无硬期限的公共接口升级；或无外部调用者、三天后弃用、不接长期管线的内部脚本。究竟是哪项还没确认；除此以外，各自记录的条件均保持不变。该选哪种接口方案？

Reference: 切换新接口并标注新版本. Own (two positions): ["U", "U"]. Full: ["切换新接口并标注新版本", "切换新接口并标注新版本"].

只可能为这两种已覆盖项目；动作同选才可确定，异选则信息不足。

Exact reference support: [{"source_id": "m3", "quote": "这次要升级的是对外公共接口，已有120个客户端依赖旧格式，客户端一个月内不会全部迁完。没有必须今天发布的期限；可以加兼容层，也可以明确升新版本后切换。"}, {"source_id": "m21", "quote": "刚才公共接口之外，还有一个临时内部一次性脚本：没有任何外部调用者，三天后弃用；团队确认不保留旧格式，输出也不进入长期管线。"}, {"source_id": "m22", "quote": "对这个临时一次性脚本，选切换新接口并标注新版本，别为它加旧接口兼容层。这是单独的情境，不是改掉公共接口的安排。"}, {"source_id": "m29", "quote": "关于已有120个客户端、一个月迁不完且没有硬发布时间的对外公共接口，我现在明确改口：上周那个升级选择作废，这次选切换新接口并标注新版本。更改只限这个公共接口安排，临时内部脚本照旧。"}]

### h42 / t03 / scoped_exception

临时内部脚本没有外部调用者，团队确定不留旧格式，三天后弃用，输出不进入长期管线。按我的记录选择接口方案。

Reference: 切换新接口并标注新版本. Own (two positions): ["U", "U"]. Full: ["切换新接口并标注新版本", "切换新接口并标注新版本"].

临时内部脚本是单独例外，公共接口改口不覆盖它。

Exact reference support: [{"source_id": "m21", "quote": "刚才公共接口之外，还有一个临时内部一次性脚本：没有任何外部调用者，三天后弃用；团队确认不保留旧格式，输出也不进入长期管线。"}, {"source_id": "m22", "quote": "对这个临时一次性脚本，选切换新接口并标注新版本，别为它加旧接口兼容层。这是单独的情境，不是改掉公共接口的安排。"}, {"source_id": "m32", "quote": "临时内部脚本那一项不受公共接口改口影响。三天后弃用、没有外部调用者这些前提还在，不要把两个项目拼成一个全局“求稳”或“求快”的性格。"}]

### h42 / t04 / research_tradeoff

内部探索性复现实验的方案尚未锁定，预留盲测集还没看；只找候选方向，不把探索结果称作独立确认，没有近期对外提交期限。按我记录的数据使用取舍选。

Reference: 现在查看全部数据做内部探索. Own (two positions): ["U", "U"]. Full: ["现在查看全部数据做内部探索", "现在查看全部数据做内部探索"].

该内部探索性实验的明确用户取舍；不是助手建议。

Exact reference support: [{"source_id": "m6", "quote": "另一件事是内部探索性复现实验：有一份预留盲测集，还没看结果；方案尚未锁定。现在只是找候选方向，不把探索结果包装成独立确认，也没有近期对外提交期限。"}, {"source_id": "m8", "quote": "在刚才这个内部探索阶段，我选：现在查看全部数据做内部探索。这是这次数据使用上的取舍，别从我的岗位猜一个相反答案。"}]

### h42 / t12 / document_purpose

给熟悉方法的研究者写公开复现报告；两种写法都能复现最终结果，篇幅也都允许。按我的记录怎样呈现？

Reference: 只保留最终复现步骤. Own (two positions): ["U", "U"]. Full: ["只保留最终复现步骤", "只保留最终复现步骤"].

公开研究复现报告的明确选择。

Exact reference support: [{"source_id": "m24", "quote": "接下来是给熟悉方法的研究者看的公开复现报告。两种写法都能把最终结果复现，篇幅也都允许；可以连失败路线一起交代，也可以只留最终步骤。"}, {"source_id": "m26", "quote": "对这份面向熟悉方法读者的公开复现报告，我选：只保留最终复现步骤。注意不是在定义所有文档都该这么写。"}]

### h42 / t13 / scoped_exception

给半夜值班同事准备查到就能照做的故障处置手册。按我的记录怎样呈现？

Reference: 只保留最终处置步骤. Own (two positions): ["U", "U"]. Full: ["只保留最终处置步骤", "只保留最终处置步骤"].

值班故障手册的具体例外，不套用研究报告风格。

Exact reference support: [{"source_id": "m27", "quote": "另外，给半夜值班的同事看的故障处置手册，我只保留当前可执行的最终处置步骤，不放失败路线。那是查到就要能照做的文档，别套研究复现报告的取舍。"}]

### h42 / t15 / observed_choice_paraphrase

去做工作报告，行程两天；白天提前到与前晚夜间出发价格相同，都能赶上报告，没有紧急会面或必须晚走的要求。按我的记录选行程。

Reference: 前一晚夜间出发，压缩行程. Own (two positions): ["U", "U"]. Full: ["前一晚夜间出发，压缩行程", "前一晚夜间出发，压缩行程"].

工作报告同义改写，前提一致。

Exact reference support: [{"source_id": "m18", "quote": "下月要去一次工作报告，两天行程；机票价格相同，白天提前到和前晚夜间出发都能按时到场。没有紧急会面，也没有要求我必须在出发前一天留在本地。"}, {"source_id": "m20", "quote": "在上面这组工作报告条件下，我选：前一晚夜间出发，压缩行程。这只是这类工作行程的安排，休假出游没有在这里讨论。"}]

### h42 / t16 / single_point_observation

仅在手机本地运行的通知分类器，误屏蔽率估计6%，恢复入口始终可用；其他条件与记录中那次相同。按我的记录选。

Reference: 每次手动确认. Own (two positions): ["U", "U"]. Full: ["每次手动确认", "每次手动确认"].

通知分类器6%那次明确观察；不套文档去重区间。

Exact reference support: [{"source_id": "m33", "quote": "前次我试过一个仅在手机本地运行的通知分类器：误屏蔽率估计6%，恢复入口始终可用。那一次，我选每次手动确认。我只报告那次条件下的选择，没有给通知分类器定数值区间，也别拿文档去重的门槛套过来。"}]

### h68 / t03 / scoped_exception

临时内部脚本没有外部调用者，团队确定不留旧格式，三天后弃用，输出不进入长期管线。按我的记录选择接口方案。

Reference: 切换新接口并标注新版本. Own (two positions): ["U", "U"]. Full: ["切换新接口并标注新版本", "切换新接口并标注新版本"].

临时内部脚本是单独例外，公共接口改口不覆盖它。

Exact reference support: [{"source_id": "m21", "quote": "刚才公共接口之外，还有一个临时内部一次性脚本：没有任何外部调用者，三天后弃用；团队确认不保留旧格式，输出也不进入长期管线。"}, {"source_id": "m22", "quote": "对这个临时一次性脚本，选切换新接口并标注新版本，别为它加旧接口兼容层。这是单独的情境，不是改掉公共接口的安排。"}, {"source_id": "m32", "quote": "临时内部脚本那一项不受公共接口改口影响。三天后弃用、没有外部调用者这些前提还在，不要把两个项目拼成一个全局“求稳”或“求快”的性格。"}]

### h68 / t04 / research_tradeoff

内部探索性复现实验的方案尚未锁定，预留盲测集还没看；只找候选方向，不把探索结果称作独立确认，没有近期对外提交期限。按我记录的数据使用取舍选。

Reference: 现在查看全部数据做内部探索. Own (two positions): ["U", "U"]. Full: ["现在查看全部数据做内部探索", "现在查看全部数据做内部探索"].

该内部探索性实验的明确用户取舍；不是助手建议。

Exact reference support: [{"source_id": "m6", "quote": "另一件事是内部探索性复现实验：有一份预留盲测集，还没看结果；方案尚未锁定。现在只是找候选方向，不把探索结果包装成独立确认，也没有近期对外提交期限。"}, {"source_id": "m8", "quote": "在刚才这个内部探索阶段，我选：现在查看全部数据做内部探索。这是这次数据使用上的取舍，别从我的岗位猜一个相反答案。"}]

### h68 / t12 / document_purpose

给熟悉方法的研究者写公开复现报告；两种写法都能复现最终结果，篇幅也都允许。按我的记录怎样呈现？

Reference: 保留失败路线和最终复现步骤. Own (two positions): ["U", "U"]. Full: ["保留失败路线和最终复现步骤", "保留失败路线和最终复现步骤"].

公开研究复现报告的明确选择。

Exact reference support: [{"source_id": "m24", "quote": "接下来是给熟悉方法的研究者看的公开复现报告。两种写法都能把最终结果复现，篇幅也都允许；可以连失败路线一起交代，也可以只留最终步骤。"}, {"source_id": "m26", "quote": "对这份面向熟悉方法读者的公开复现报告，我选：保留失败路线和最终复现步骤。注意不是在定义所有文档都该这么写。"}]

### h68 / t13 / scoped_exception

给半夜值班同事准备查到就能照做的故障处置手册。按我的记录怎样呈现？

Reference: 只保留最终处置步骤. Own (two positions): ["U", "U"]. Full: ["只保留最终处置步骤", "只保留最终处置步骤"].

值班故障手册的具体例外，不套用研究报告风格。

Exact reference support: [{"source_id": "m27", "quote": "另外，给半夜值班的同事看的故障处置手册，我只保留当前可执行的最终处置步骤，不放失败路线。那是查到就要能照做的文档，别套研究复现报告的取舍。"}]

### h68 / t15 / observed_choice_paraphrase

去做工作报告，行程两天；白天提前到与前晚夜间出发价格相同，都能赶上报告，没有紧急会面或必须晚走的要求。按我的记录选行程。

Reference: 前一晚夜间出发，压缩行程. Own (two positions): ["U", "U"]. Full: ["前一晚夜间出发，压缩行程", "前一晚夜间出发，压缩行程"].

工作报告同义改写，前提一致。

Exact reference support: [{"source_id": "m18", "quote": "下月要去一次工作报告，两天行程；机票价格相同，白天提前到和前晚夜间出发都能按时到场。没有紧急会面，也没有要求我必须在出发前一天留在本地。"}, {"source_id": "m20", "quote": "在上面这组工作报告条件下，我选：前一晚夜间出发，压缩行程。这只是这类工作行程的安排，休假出游没有在这里讨论。"}]

### h93 / t02 / partial_context_identifiability

此次任务只可能是记录中的这两项之一：已有120个客户端、一个月迁不完且无硬期限的公共接口升级；或无外部调用者、三天后弃用、不接长期管线的内部脚本。究竟是哪项还没确认；除此以外，各自记录的条件均保持不变。该选哪种接口方案？

Reference: 切换新接口并标注新版本. Own (two positions): ["U", "U"]. Full: ["切换新接口并标注新版本", "切换新接口并标注新版本"].

只可能为这两种已覆盖项目；动作同选才可确定，异选则信息不足。

Exact reference support: [{"source_id": "m3", "quote": "这次要升级的是对外公共接口，已有120个客户端依赖旧格式，客户端一个月内不会全部迁完。没有必须今天发布的期限；可以加兼容层，也可以明确升新版本后切换。"}, {"source_id": "m21", "quote": "刚才公共接口之外，还有一个临时内部一次性脚本：没有任何外部调用者，三天后弃用；团队确认不保留旧格式，输出也不进入长期管线。"}, {"source_id": "m22", "quote": "对这个临时一次性脚本，选切换新接口并标注新版本，别为它加旧接口兼容层。这是单独的情境，不是改掉公共接口的安排。"}, {"source_id": "m29", "quote": "关于已有120个客户端、一个月迁不完且没有硬发布时间的对外公共接口，我现在明确改口：上周那个升级选择作废，这次选切换新接口并标注新版本。更改只限这个公共接口安排，临时内部脚本照旧。"}]

### h93 / t03 / scoped_exception

临时内部脚本没有外部调用者，团队确定不留旧格式，三天后弃用，输出不进入长期管线。按我的记录选择接口方案。

Reference: 切换新接口并标注新版本. Own (two positions): ["U", "U"]. Full: ["切换新接口并标注新版本", "切换新接口并标注新版本"].

临时内部脚本是单独例外，公共接口改口不覆盖它。

Exact reference support: [{"source_id": "m21", "quote": "刚才公共接口之外，还有一个临时内部一次性脚本：没有任何外部调用者，三天后弃用；团队确认不保留旧格式，输出也不进入长期管线。"}, {"source_id": "m22", "quote": "对这个临时一次性脚本，选切换新接口并标注新版本，别为它加旧接口兼容层。这是单独的情境，不是改掉公共接口的安排。"}, {"source_id": "m32", "quote": "临时内部脚本那一项不受公共接口改口影响。三天后弃用、没有外部调用者这些前提还在，不要把两个项目拼成一个全局“求稳”或“求快”的性格。"}]

### h93 / t04 / research_tradeoff

内部探索性复现实验的方案尚未锁定，预留盲测集还没看；只找候选方向，不把探索结果称作独立确认，没有近期对外提交期限。按我记录的数据使用取舍选。

Reference: 留住盲测集，等方案锁定再查看. Own (two positions): ["U", "U"]. Full: ["留住盲测集，等方案锁定再查看", "留住盲测集，等方案锁定再查看"].

该内部探索性实验的明确用户取舍；不是助手建议。

Exact reference support: [{"source_id": "m6", "quote": "另一件事是内部探索性复现实验：有一份预留盲测集，还没看结果；方案尚未锁定。现在只是找候选方向，不把探索结果包装成独立确认，也没有近期对外提交期限。"}, {"source_id": "m8", "quote": "在刚才这个内部探索阶段，我选：留住盲测集，等方案锁定再查看。这是这次数据使用上的取舍，别从我的岗位猜一个相反答案。"}]

### h93 / t12 / document_purpose

给熟悉方法的研究者写公开复现报告；两种写法都能复现最终结果，篇幅也都允许。按我的记录怎样呈现？

Reference: 只保留最终复现步骤. Own (two positions): ["U", "U"]. Full: ["只保留最终复现步骤", "只保留最终复现步骤"].

公开研究复现报告的明确选择。

Exact reference support: [{"source_id": "m24", "quote": "接下来是给熟悉方法的研究者看的公开复现报告。两种写法都能把最终结果复现，篇幅也都允许；可以连失败路线一起交代，也可以只留最终步骤。"}, {"source_id": "m26", "quote": "对这份面向熟悉方法读者的公开复现报告，我选：只保留最终复现步骤。注意不是在定义所有文档都该这么写。"}]

### h93 / t13 / scoped_exception

给半夜值班同事准备查到就能照做的故障处置手册。按我的记录怎样呈现？

Reference: 只保留最终处置步骤. Own (two positions): ["U", "U"]. Full: ["只保留最终处置步骤", "只保留最终处置步骤"].

值班故障手册的具体例外，不套用研究报告风格。

Exact reference support: [{"source_id": "m27", "quote": "另外，给半夜值班的同事看的故障处置手册，我只保留当前可执行的最终处置步骤，不放失败路线。那是查到就要能照做的文档，别套研究复现报告的取舍。"}]

### h93 / t15 / observed_choice_paraphrase

去做工作报告，行程两天；白天提前到与前晚夜间出发价格相同，都能赶上报告，没有紧急会面或必须晚走的要求。按我的记录选行程。

Reference: 前一天白天出发，留出空档. Own (two positions): ["U", "U"]. Full: ["前一天白天出发，留出空档", "前一天白天出发，留出空档"].

工作报告同义改写，前提一致。

Exact reference support: [{"source_id": "m18", "quote": "下月要去一次工作报告，两天行程；机票价格相同，白天提前到和前晚夜间出发都能按时到场。没有紧急会面，也没有要求我必须在出发前一天留在本地。"}, {"source_id": "m20", "quote": "在上面这组工作报告条件下，我选：前一天白天出发，留出空档。这只是这类工作行程的安排，休假出游没有在这里讨论。"}]

Independent donor errors:

```json
[
  {
    "person": "h17",
    "case": "t03",
    "gold": "切换新接口并标注新版本",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h17",
    "case": "t04",
    "gold": "留住盲测集，等方案锁定再查看",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h17",
    "case": "t12",
    "gold": "保留失败路线和最终复现步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h17",
    "case": "t13",
    "gold": "只保留最终处置步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h17",
    "case": "t15",
    "gold": "前一天白天出发，留出空档",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t02",
    "gold": "切换新接口并标注新版本",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t03",
    "gold": "切换新接口并标注新版本",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t04",
    "gold": "现在查看全部数据做内部探索",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t12",
    "gold": "只保留最终复现步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t13",
    "gold": "只保留最终处置步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t15",
    "gold": "前一晚夜间出发，压缩行程",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h42",
    "case": "t16",
    "gold": "每次手动确认",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h68",
    "case": "t03",
    "gold": "切换新接口并标注新版本",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h68",
    "case": "t04",
    "gold": "现在查看全部数据做内部探索",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h68",
    "case": "t12",
    "gold": "保留失败路线和最终复现步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h68",
    "case": "t13",
    "gold": "只保留最终处置步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h68",
    "case": "t15",
    "gold": "前一晚夜间出发，压缩行程",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h93",
    "case": "t02",
    "gold": "切换新接口并标注新版本",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h93",
    "case": "t03",
    "gold": "切换新接口并标注新版本",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h93",
    "case": "t04",
    "gold": "留住盲测集，等方案锁定再查看",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h93",
    "case": "t12",
    "gold": "只保留最终复现步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h93",
    "case": "t13",
    "gold": "只保留最终处置步骤",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  },
  {
    "person": "h93",
    "case": "t15",
    "gold": "前一天白天出发，留出空档",
    "observed": [
      "U",
      "U"
    ],
    "missing": false
  }
]
```

These joins are descriptive. A matching literal quote does not prove reference semantics; no independent causal attribution or human fidelity is established. Full cell-level scores, original sources and responses remain in observed.synthetic.json.
