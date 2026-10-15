# Browser prototype

RunAWay's browser entry is a static app with no dependencies or build step:

```sh
git clone https://github.com/xu2333/RunAWay.git
cd RunAWay
python3 -m http.server 8080 --bind 127.0.0.1 --directory web/dist
```

Open http://127.0.0.1:8080. Use localhost or HTTPS; hashing and copying need a secure context.

1. Paste a selected experience or resume. For conversations, choose the trajectory type and preserve `用户：` / `助手：` / `工具：` labels, or import the source JSON format used by the CLI.
2. Copy the extraction request to an LLM you already use, then paste its JSON response back. This is a manual round trip, not an integrated model service. The request contains the selected source material; that service's account, terms and fees apply.
3. Inspect the evidence and unknowns, edit the compact text, then copy it into a real task or download `portable.json` for [harness installation](QUICKSTART.md). A private archive preserves the detailed profile, source and session records; there is no archive restore UI yet.
4. After using an exported version, record where it helped or missed and what you corrected. Preview/download the report, or open a GitHub Issue draft and submit it yourself.

The fictional frog example is ready immediately and makes no model call. It remains tagged as a demo in usage reports. Clear the page before starting a real submission.

New model results include an editable share card: a short name, a joke, one concrete behavior and its boundary. Preview and download the exact PNG locally, or copy its text. Card changes never change the portable prompt. Optional card feedback separates recognition, humor and willingness to share. Download a card sample or inspect the full sample before explicitly opening a public Issue draft; a manual GitHub submission is still required. This card submission path intentionally includes approved card text, unlike the older usage-statistics draft. See [the 700-output target and audit](OUTPUTS.md).

## Data and evidence

Materials and feedback stay in tab memory until the user copies, downloads or submits them. Closing or reloading loses this state. The app has no automatic analytics or feedback ingestion endpoint. Hosting providers may retain ordinary HTTP access logs; source text and local feedback are not sent with those requests.

Feedback defaults to event times, platform, rating and version identifiers. Optional content export adds the actual task, reply, correction and exported prompt. Original source/evidence fields are excluded, but user-entered feedback or model text can still contain private details. GitHub drafts always omit free text and prompt text, even when content export is selected. GitHub Issues are public and need a GitHub account to submit.

The latest copied/downloaded prompt is the feedback target. Editing the text afterward does not silently change that target. Browser feedback is voluntary self-report, not a controlled experiment or independent evidence of fidelity. Demo usage must be excluded from user conclusions, and multiple reports from one person are not independent users.

Local validation checks exact quotes, speaker attribution, schema, declared claim coverage and Unicode character budget. It does **not** prove the claims are semantically justified or the compact prompt retains every condition. The browser path does not run the CLI's additional model critiques/compression audit. Every exported artifact remains `candidate_unvalidated`; character counts are not token counts.

## Development

```sh
node --test tests/web.test.mjs
python3 -m unittest discover -s tests -p test_web.py -q
```

Node 22+ runs the browser-core tests. The Python interoperability check validates the browser-generated hashes and installs its portable expression into temporary Codex, Claude Code and OpenCode project files. The public source includes only static assets and a fictional example; hosting identity and private research are excluded.
