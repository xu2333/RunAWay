# RunAWay

**Your taste, to go.** 把你的经历，变成带得走的 taste。

Turn resumes, experiences and agent conversations into a portable prompt for how you choose and judge. Keep the evidence, conditions and uncertainty—then inspect and correct what the model infers.

**Your history → an editable profile → a prompt for any LLM.**

## Try it

**Browser app:** paste an experience, bring back a result from an LLM you already use, then take away your prompt and a shareable “my operating manual.” Optionally hold out a real choice to compare ordinary AI with your personalized prompt. No API key or build step.

```sh
git clone https://github.com/xu2333/RunAWay.git
cd RunAWay
python3 -m http.server 8080 --bind 127.0.0.1 --directory web/dist
```

Open **http://127.0.0.1:8080**. Or visit **/gallery.html** for 700 original synthetic characters, share cards and fictional role prompts; **/theater.html** pairs them in 8 short scenes. [Browser guide & data handling](WEB.md) · [700-character catalogue](OUTPUTS.md).

## Make it yours

Prefer the terminal? Python 3.9+, a logged-in Codex CLI and a model available to your account:

```sh
python3 -m runaway build --input experience.txt --backend codex \
  --model YOUR_MODEL --out my-profile
```

Copy the resulting prompt into a chat, or install it as project instructions for Codex, Claude Code, OpenCode and other harnesses. You can revise the profile without regenerating everything.

Browser feedback is shared only when you choose to submit it. CLI generation sends selected input to its backend. Fidelity to real personal choices remains unverified.

[Self-play results & limits](COMPARISON-RESULTS.md) · [Automatic compression metric](SYNTHETIC-METRIC.md) · [Bound-memory prototype](BOUND-MEMORY.md) · [Full guide & harness setup](QUICKSTART.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)
