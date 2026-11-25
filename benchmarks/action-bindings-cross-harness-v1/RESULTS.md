# 放行人和用料能否同时保住？

本轮固定九张卡和原题，在 Codex、Claude Code 和 Antigravity 的新会话各做一轮配对。表内箭头从本轮重新生成的上轮读法指向新增提示的读法。

《盐汀》的两项要求在三端同答保留，从 0/3 升至 3/3。前四题的 12 组完整配对里，两种读法均未要求等时间确认或排班通知。

54 个预定槽位实际尝试 48 次，收到 47 份原答。Antigravity 的《雾港字盘》对照组达到 180 秒限时，之后六个槽位按约定关闭。其余两端完成全部任务。下表的 27 是预定分母，其中对照组 4 份未知，候选组 3 份未知；未知项没有判成“无门槛”。

| 项目 | 上轮读法（本轮重测） | 新增提示 |
|---|---:|---:|
| 《盐汀》放行人 | 0/3 | 3/3 |
| 《盐汀》已许可操作的用料 | 2/3 | 3/3 |
| 《盐汀》同答保住两项 | 0/3 | 3/3 |
| 前四题另等时间或排班 | 0/12 | 0/12 |
| 出现额外执行门槛 | 3/27 | 0/27 |
| 强制立刻执行 | 0/27 | 0/27 |

### 《盐汀》逐份核对

| 客户端 | 读法 | 放行人 | 用料 | 原答判读 |
|---|---|---|---|---|
| codex | old | × | ✓ | 写了收到确认过的新定位纸，没写由谁发；白棉线保住。 |
| codex | new | ✓ | ✓ | “待我发来经我确认的新定位纸”；第五、六列都点名白棉线和原线序，两项同答恢复。 |
| claude-code | old | × | × | 只有“拿到确认过的新定位纸”，两列只写“穿线”；又把收起旧纸的交代写成已经收起。 |
| claude-code | new | ✓ | ✓ | 明确由“我（原作者）”确认并发新纸；第五、六列按原图用白棉线。另谈尚未放行的后四列用料，未阻碍当前动作。 |
| antigravity | old | × | ✓ | 未指明谁发新纸，白棉线保住。“原定位纸已收起”没有完成证据。 |
| antigravity | new | ✓ | ✓ | 交班人（我）确认并发新纸；五、六列按原线序用白棉线，不受发纸日期影响。旧纸仍写作待收。 |

### 九题严格通过情况

单个格子须保住所有预登记条件，且交接指令之间相容。原答和逐项引文可在 [observations.json](observations.json) 查阅。

| 卡 | Codex | Claude Code | Antigravity |
|---|---|---|---|
| greenhouse | ✓ → ✓ | ✓ → ✓ | ✓ → ✓ |
| listening | ✓ → ✓ | × → ✓ | ✓ → ✓ |
| puzzle | ✓ → ✓ | ✓ → ✓ | × → ✓ |
| caption | ✓ → ✓ | ✓ → ✓ | ✓ → ✓ |
| thread | × → ✓ | × → ✓ | × → ✓ |
| type | × → × | × → × | — → × |
| reels | ✓ → ✓ | × → × | — → — |
| foldout | ✓ → ✓ | × → ✓ | — → — |
| swatch | × → × | × → × | — → — |

### 新增和残留的问题

| 客户端／题 | 读法 | 判读 |
|---|---|---|
| codex/thread | old | 写了收到确认过的新定位纸，没写由谁发；白棉线保住。 |
| codex/type | new | 写明须夹好保存，未交代实际夹存情况未知。分清校样员签名与本人传达放行。 |
| codex/type | old | 夹样要求与数量保留，没明确是否已经夹好；在各自签名之外还要求“后续放行”。 |
| codex/swatch | old | 苔阶是否放条的选择保住，之前放过没有未交代。 |
| codex/swatch | new | 写了是否决定放，没说明已经放没放仍未知；瓦巷同批次和替换片保留。 |
| claude-code/listening | old | 排班没有卡住上架，但第36行要求逐条填完建议表再执行。 |
| claude-code/thread | old | 只有“拿到确认过的新定位纸”，两列只写“穿线”；又把收起旧纸的交代写成已经收起。 |
| claude-code/type | old | 四块都已开印、已夹好，被写成事实；数目和本格签名范围正确。 |
| claude-code/type | new | 数字列对，背景却说四块都已开印；夹样完成仍未说明，又让接班人沿用未指明的原用料。 |
| claude-code/reels | new | 保住未知且没派回读，但“已有就记为已存”仍另派了登记。若将“记为”仅理解为确认现状，此项可判通过。 |
| claude-code/reels | old | 杉汀被另派回读和记账；第8行还要求开剪前重查已经确认的第2段。 |
| claude-code/foldout | old | 保留自选拍摄，第24行却要求按未拍处理，把未知当成未拍。 |
| claude-code/swatch | new | 保留两套用料、瓦巷配色师和同批次要求；未交代苔阶是否已经放条。 |
| claude-code/swatch | old | 苔阶可选与已经放入与否是两件事，只写了前者。 |
| antigravity/puzzle | old | 回柜条件正确、雨雀不用等，但把石桥“先放核查桌”写成“目前已放置”，接班人会漏做。 |
| antigravity/thread | old | 未指明谁发新纸，白棉线保住。“原定位纸已收起”没有完成证据。 |
| antigravity/type | new | 四版许可和张数保住，三张样张被无依据地写成均已夹好。另将成品类别“铅字样册”列作用料。 |
| antigravity/type | old | client failure |
| antigravity/reels | old | not attempted after client failure |
| antigravity/reels | new | not attempted after client failure |
| antigravity/foldout | new | not attempted after client failure |
| antigravity/foldout | old | not attempted after client failure |
| antigravity/swatch | old | not attempted after client failure |
| antigravity/swatch | new | not attempted after client failure |

### 计数与局限

九题合计有 23 组拿到了成对回答。严格判分从失败变为通过的有 6 组，维持通过 12 组，两份都没通过 5 组；其余 4 组缺至少一份回答。上轮通过的 14 项中，候选这次复现了 13 项，剩下的 Antigravity《双溪听册》未执行。网页继续使用原有默认导出。

- 本轮对照收到 23/27 份。九题在三端同时通过 2/9；真正的前提完整保留 20/27，弱化 3 份，删除 0 份。上次通过的 14 项，这次通过 12/14。
- 候选收到 24/27 份。九题在三端同时通过 5/9；真正的前提完整保留 24/27，弱化 0 份，删除 0 份。上次通过的 14 项，这次通过 13/14。

服务报告的用量为 Codex 输入 212,556、输出 6,916 tokens，Claude Code 估算 USD 0.358655。Antigravity 的文本输出未返回用量，三端总费用未知。

每题每端每种读法只有一份回答。九个虚构案例在开发中用过；评分由一个知道分组的助手对照引文完成。客户端与底层模型一同变化。
