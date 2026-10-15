# RunAWay

**Your taste, to go.** 把你的经历，变成带得走的 taste。

Turn resumes, experiences and agent conversations into a portable prompt for how you choose and judge. Keep the evidence, conditions and uncertainty—then inspect and correct what the model infers.

**Your history → an editable profile → a prompt for any LLM.**

## Try it

Python 3.9+. No account, dependencies or model calls needed for the fictional demo.

```sh
git clone https://github.com/xu2333/RunAWay.git
cd RunAWay
python3 -m runaway demo --out my-demo
```

Read `my-demo/prompt.md`, or open `my-demo/review.private.html` to explore its evidence.

## Make it yours

With a logged-in Codex CLI and a model available to your account:

```sh
python3 -m runaway build --input experience.txt --backend codex \
  --model YOUR_MODEL --out my-profile
```

Copy the resulting prompt into a chat, or install it as project instructions for Codex, Claude Code, OpenCode and other harnesses. You can revise the profile without regenerating everything.

Generation sends your selected input to the backend. This is an early prototype; fidelity to real personal choices remains unverified.

[Full guide & harness setup](QUICKSTART.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)
