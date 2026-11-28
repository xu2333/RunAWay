# RunAWay

**Your taste, to go.** 把真实对话中的选择、条件和例外，变成带得走的 prompt。

[手机打开 RunAWay · Open the preview](https://zichengxu.com/)

Import a conversation file or paste an exchange, generate a short card with your own model and export it for Codex or Claude Code.

Experimental: **real-person fidelity is unverified**. A prompt is a revisable hypothesis about your preferences, not an identity or permission to act.

## Run the web app locally (Node.js 22+)

```sh
git clone https://github.com/xu2333/RunAWay.git
cd RunAWay/apps/mobile
npm ci
npm run build
python3 -m http.server 8080 --bind 127.0.0.1 --directory dist
```

Open **http://127.0.0.1:8080**:

1. Paste a real conversation, including your corrections and who said what.
2. Copy the extraction request to an LLM you already use, then bring back its JSON.
3. Review the evidence, conditions and unknowns. Copy the resulting prompt into a new Codex or Claude Code session, or use the [project-file setup](QUICKSTART.md#attach-to-a-project).

The browser does not automatically scan or upload your history. Sending the request to your chosen model is your own explicit step. Keep private archives private.

[What has actually been shown](RESULTS.md) · [Full guide](QUICKSTART.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)
