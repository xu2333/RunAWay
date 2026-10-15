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

New model results include an editable share card: a short name, a joke, one concrete behavior and its boundary. Preview and download the exact PNG locally, or copy its text. Card changes never change the portable prompt. Optional card feedback separates recognition, humor and willingness to share. Download a card sample or inspect the full sample before explicitly opening a public Issue draft; a manual GitHub submission is still required. This card submission path intentionally includes approved card text, unlike the older usage-statistics draft. See [the synthetic catalogue and separate feedback audit](OUTPUTS.md).

## My operating manual and a held-out choice

The main result now starts with an editable “我的使用说明书”: how to persuade me, what creates friction, and when I change my mind. Each included item references existing evidence-backed claims; unsupported angles are omitted. References establish traceability, not semantic truth. Inspect the original claims and quotes locally, edit the phrasing, and confirm the preview before copying text or downloading a PNG. Manual edits do not change the detailed profile or portable prompt. Older responses without a manual remain valid.

Before extraction, optionally reserve one **separate real episode** in step 1. Remove the entire related episode from the extraction material, supply a verbatim decision quote, and write the situation as it stood before the decision with two options that actually existed. The extractor receives only the training material. The browser rejects matching decision quotes in training, but cannot detect paraphrases, partial or semantic leakage, invented histories, or biased options. The user must check independence and neutrality.

After extraction, lock the current portable version. Run the two requests in separate fresh conversations with the same model/settings: one sees only the situation, the other also receives the portable prompt. Neither request receives the held-out source, decision quote, actual answer or retrospective reason. Paste both JSON predictions (A, B, or unknown) and lock them before revealing the actual answer. Request identifiers reject mismatched imports; prompt edits clear the active comparison. Repeating a revealed case in the current session is labeled a retest. This is a user-operated, self-reported check, not a tamper-proof blind experiment. Refreshing or clearing the page loses that bookkeeping.

The puzzle share preview includes only the situation and options. The reveal additionally includes the actual answer, the user's retrospective reason and both predicted choices; it excludes original source/quote fields and model rationales. Both require review before copying. The private archive also contains the held-out episode, edited manual, requests and imported results (including earlier revealed rounds retained in this tab); ordinary usage feedback never includes them. No results are uploaded automatically.

The fictional example includes a separately written fictional holdout and an explicitly labeled button for **prewritten** predictions. Loading these makes no model call and is not an empirical evaluation. One choice cannot establish accuracy, relative information gain, causal improvement or general fidelity. Aggregate evaluation should use predeclared, independent cases and model probabilities/log-loss where available; this UI does not fabricate those metrics.

## 700 fictional residents

Open `/gallery.html` from the browser entry. Search names, behaviors or stable IDs, filter 28 editorial categories, browse pages or meet a random character. Each detail view exports a local PNG, card text, deep link and a clearly fictional role-play prompt. No model call or source history is needed. This catalogue is AI-authored original fiction, not 700 real people or evidence of personal fidelity. It does not assign a type to the visitor or alter the evidence-based profile.

The 700 entries are authored in `catalog/*.txt`, compiled by `python3 scripts/build_catalog.py` into committed static JSON. Run with `--check` to verify reproducibility. Category boundaries are shared editorial cautions. See [catalogue scope](OUTPUTS.md).

## Two-character theater

Open `/theater.html` or invite a resident from a gallery detail. Eight clearly labeled, prewritten fictional scenes work immediately. Pick any two different catalogue residents and one of eight settings, copy a generation request to your own LLM, then import its six-turn JSON story. No automatic model call, backend, account creation, saved history or public chat room is added.

Export the full dialogue as a PNG or text. Preset links reproduce a known scripted scene. Combination invitations include only two public catalogue IDs and a scene ID; they do **not** reproduce imported dialogue. Imported text stays in tab memory and is lost on reload. Changing the cast or scene clears the prior result so the old story cannot be relabeled as a new pairing. Structural validation cannot prove character fidelity, mutual influence or entertainment quality. See [interaction design and evaluation](INTERACTIONS.md).

## Data and evidence

Materials and feedback stay in tab memory until the user copies, downloads or submits them. Closing or reloading loses this state. The app has no automatic analytics or feedback ingestion endpoint. Hosting providers may retain ordinary HTTP access logs; source text and local feedback are not sent with those requests.

Feedback defaults to event times, platform, rating and version identifiers. Optional content export adds the actual task, reply, correction and exported prompt. Original source/evidence fields are excluded, but user-entered feedback or model text can still contain private details. GitHub drafts always omit free text and prompt text, even when content export is selected. GitHub Issues are public and need a GitHub account to submit.

The latest copied/downloaded prompt is the feedback target. Editing the text afterward does not silently change that target. Browser feedback is voluntary self-report, not a controlled experiment or independent evidence of fidelity. Demo usage must be excluded from user conclusions, and multiple reports from one person are not independent users.

Local validation checks exact quotes, speaker attribution, schema, declared claim coverage and Unicode character budget. It does **not** prove the claims are semantically justified or the compact prompt retains every condition. The browser path does not run the CLI's additional model critiques/compression audit. Every exported artifact remains `candidate_unvalidated`; character counts are not token counts.

## Development

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p test_web.py -q
```

Node 22+ runs the browser-core tests. The Python interoperability check validates the browser-generated hashes and installs its portable expression into temporary Codex, Claude Code and OpenCode project files. The public source includes only static assets and a fictional example; hosting identity and private research are excluded.
