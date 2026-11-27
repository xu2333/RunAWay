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
