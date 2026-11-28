# 从首页带进一段对话

测试的是用户取得内容之后，到 RunAWay 显示带角色的本地提炼请求为止。操作数从打开首页算起。点选文件和确认系统选择算作一次选文件操作；复制之前寻找会话、邮箱等待、系统剪贴板权限、切换 App 等另外发生，次数因设备而异。未调用提炼模型。

在 2026-11-27 上线的旧首页，用同一段虚构的三条消息做了八次输入。带 ChatGPT 标题的粘贴和手工标明用户／助手的文件都识别成用户两条、助手一条。无标题粘贴、Codex Markdown、两种 CLI JSONL、ChatGPT 和 Claude 的 conversations JSON 均未生成请求。五份客户端格式文件都要先展开高级选项，选完都先显示“材料已在本机读入”，直到按生成才暴露格式错误。

| 输入 | 新首页最短走法 | 核对点 |
| --- | --- | --- |
| Codex 本机 rollout，Claude Code 单会话 JSONL | 点导入并选文件，自动进入请求页 | 消息按原角色保存；忽略工具结果和重复事件 |
| Codex CLI 的整段 Markdown，带标题的 ChatGPT 片段 | 粘贴，点生成 | 双方文字与实际顺序 |
| ChatGPT／Claude 导出 ZIP 或 JSON | 点导入并选文件；多会话时选标题，确认所选对话 | 只使用选中对话；ChatGPT 只走当前分支 |
| Claude Code 的终端文字导出 | 粘贴并生成，或选文件；勾选实际助手原话，确认 | 终端对助手文字和系统提示都用圆点 |
| 单条复制时没有说话人 | 展开逐条输入，粘贴并选「我的／助手」；最后点生成 | 不猜没有标签的发言人 |

样本均为虚构材料。Claude Code 2.1.322 在隔离工作区恢复虚构三条消息后实际执行了本地 `/export`，公开文本仅替换了工作目录。其余原生格式样本是固定构造，未登录消费者账号请求整库导出。未把桌面浏览器的手机宽度测试计为 iPhone 或 Android 真机验收。

[可复现的输入样本](../../apps/mobile/tests/fixtures/chat-import) · [解析测试](../../apps/mobile/tests/conversation-import.test.mjs) · [浏览器操作测试](../../apps/mobile/tests/app.test.mjs)

[Codex CLI 导出](https://developers.openai.com/codex/cli/slash-commands) · [Codex 官方 Markdown 样本](https://github.com/openai/codex/blob/main/codex-rs/tui/src/app/snapshots/codex_tui__app__transcript_export__tests__markdown_transcript.snap) · [Claude Code 导出](https://code.claude.com/docs/en/commands) · [ChatGPT 数据导出](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data) · [Claude 数据导出](https://support.claude.com/en/articles/9450526-export-your-claude-data)

### Claude 桌面版的一问一答

操作者在 macOS Claude 桌面版拖选了一段虚构提问和一段实际回复，按 ⌘C，并确认已复制。系统剪贴板的纯文本共有 55 个字符，两段之间有一个空行，未带角色标签。旧线上页粘贴后点生成，提示无法识别说话人。桌面控制工具当时未能读取 Claude 窗口，App 内两步来自操作者确认。

针对由空行隔开的两行普通文字，网页现在提供「确认第一段是我、第二段是助手，生成请求」。确认才赋予角色。超过两段、段内换行及带有角色标签的内容沿用原有入口。[实际虚构样本](../../apps/mobile/tests/fixtures/chat-import/claude-desktop-pair.txt)

### Claude 桌面版多轮复制

另一段虚构对话有四条发言。操作者在 Claude 桌面版从第一问拖到最后一答并复制。纯文本有五个自然段，八个换行。富文本给四条消息分别编号，第一条回复的两个自然段同属第二条消息。旧版整段粘贴后无法生成请求。

网页现在读取粘贴事件里的编号消息块，按块保留内容。只有消息文本能按原顺序逐字还原同时粘贴的纯文本，才显示角色核对。用户可以逐条改说话人，确认后才生成请求。遇到仅有纯文本的这份样本，勾选两段提问即可。确认后连续同角色段落会按原有空行连成一条消息。该路径适用于相邻发言交替换人的对话。

[复制出的纯文本](../../apps/mobile/tests/fixtures/chat-import/claude-desktop-four.txt) · [仅保留编号和段落的富文本样本](../../apps/mobile/tests/fixtures/chat-import/claude-desktop-four.html)
