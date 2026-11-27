# RunAWay on your phone

The native iOS 15.4+ / Android 7+ prototype bundles its interface and validation code in
the app. It reads only files you select and writes only exports you request.
There is no RunAWay account, backend, telemetry, automatic upload or API key.

[Open the mobile web preview](https://xu2333.github.io/RunAWay/). The browser downloads exports to the device. The native apps use the system document picker.

## Use it

1. Choose a local `.txt`, `.md` or source `.json`, or paste an experience.
   Choose the correct material type; conversations retain speaker attribution.
2. Inspect the extraction request. Copy it to **your chosen model**, then bring
   its JSON result back. This hand-off may leave your device according to that
   model's policies. This prototype does **not** include an on-device LLM.
3. Inspect the supporting quotations, conditions and exceptions. Edit the
   portable prompt and confirm before exporting it.
4. Tap Codex, Claude Code or Antigravity to export a private ZIP. Use the system
   document picker to save on your phone, then transfer the ZIP to your computer.
   If you select a cloud file provider, its policies and network behavior apply.
5. Save the **private archive** if you want to continue later. It includes original
   material and detailed evidence. The smaller harness ZIP contains only the
   portable prompt and public installation code, without the source archive.

Existing browser `runaway.private.json` sessions and `portable.json` can be opened
locally. Private archives accept up to 2 MB; source intake remains 64 KB and model
results remain 512 KB. Fictional demo provenance survives archive restoration. Only a private archive restores evidence; a portable prompt alone cannot
recover details that compression omitted. Imported prompts remain candidates.

Nothing is automatically persisted between app launches. On Android, explicit exports stay in memory until the system-selected document
is written. On iOS, exports are staged in local **cache** for the system document
picker, then cleared on completion/cancellation or the next cold launch. Cache is not encrypted
by RunAWay. Exported files, clipboard contents, device backups and destinations
selected in the system picker remain under the owner's/device's control.

Android requests no Internet or broad storage permissions and disables application
backups. AndroidX adds one app-scoped signature permission for internal receivers;
CI allows only that exact permission and verifies its signature protection. Both platforms bundle all assets; the page's
CSP disallows network connections. No automatic HTTP/cookie bridge is enabled.
The only app plugin is a small local document-saving bridge: Android uses
`ACTION_CREATE_DOCUMENT`; iOS uses `UIDocumentPickerViewController`. It has no
HTTP, account, analytics, model or arbitrary-path write method.

## Three independent harness modules

| Module | Project-scoped output | Loading convention |
| --- | --- | --- |
| `packages/harnesses/codex.mjs` | `AGENTS.md` | Fresh Codex session; non-empty `AGENTS.override.md` blocks installation |
| `packages/harnesses/claude-code.mjs` | `.claude/rules/runaway.md` | Unscoped project rule; project rules must be enabled |
| `packages/harnesses/antigravity.mjs` | `.agents/rules/runaway.md` | Explicit `trigger: always_on` frontmatter |

Shared code validates Unicode, preserves the exact prompt, renders the complete
envelope and produces a ZIP. Each module owns its path, activation, export byte
limit and documentation link. Future harnesses add a module and registry entry.
Mobile and terminal exports use the **same** modules. No model paraphrases the
prompt during adaptation. The manifest reports prompt and full file sizes.

On a computer, unzip into a temporary folder, inspect the instructions, then run:

```sh
node install.mjs --project "/path/to/project" --dry-run
node install.mjs --project "/path/to/project"
# Later, from the same exported package:
node install.mjs --project "/path/to/project" --remove
```

Node 22+ is required; RunAWay/Python is not. Installation appends an owned block
to Codex instructions and creates dedicated files for the other two harnesses.
It preserves unrelated text, refuses symlinks, edited or untracked blocks and
existing dedicated files, and uses a project-local exclusive lock. Ordinary
write failures roll back the target file. A machine crash between the file and
state writes can require manual reconciliation; the installer refuses to take
ownership of an untracked block. Existing Python `runaway attach` state is a
separate format: detach it before using this installer. Do not install two
bindings into a harness configured to load both files, which duplicates context.

For repository users, an offline terminal export also works:

```sh
node scripts/export_harness.mjs --portable portable.json --target codex --out codex.zip
# --target claude-code or antigravity
```

The installer does not start a model or verify that a harness loaded its file.
Successful packaging/installation does not establish personal-choice fidelity.
Provider rule behavior is based on [Codex instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[Claude Code rules](https://code.claude.com/docs/en/memory#organize-rules-with-clauderules)
and [Antigravity rules](https://antigravity.google/docs/rules), checked 2026-11-14.

## Build and verify

```sh
cd apps/mobile
npm ci --ignore-scripts --no-audit --no-fund
npm run sync
npm run android  # Android Studio / Android SDK + Java 21
npm run ios      # macOS + full Xcode; device installation requires your signing team
```

`npm run build` creates the bundled UI. `npm test` runs the desktop-browser
mobile-viewport smoke test after a build. Install its Chromium first with
`node node_modules/playwright-core/cli.js install chromium`, or set
`RUNAWAY_CHROME` to an existing Chrome executable. The test uses fictional demo
data, checks local file import and archive recovery, all three ZIPs, output
integrity, no spontaneous external requests, and real CSP rejection of an
external fetch. It is **not** a physical-phone or native-picker test.

`Local mobile app` CI compiles an Android debug APK, checks its packaged
permissions, runs the bundled app in a real Android emulator WebView (including
WebCrypto, evidence validation and native bridge availability), compiles an unsigned
iOS simulator app, and runs the browser UI smoke test.
The APK and simulator archive are workflow artifacts, not store releases.
iPhone device distribution/TestFlight requires signing; simulator output cannot
be installed on an iPhone. Physical-device file pick/save and real harness
loading remain release checks. No new model calls are part of this work.

## Thanksgiving preview acceptance

On November 21, 2026 a physical Android phone opened the public preview from a locally rendered copy of the article draft. Its browser prepared a 768-character-budget extraction request from a three-message fictional conversation. A separate trusted clipboard paste on the same phone reproduced the exact request. The owner-authorized model handoff used Codex CLI on the connected computer. The returned JSON passed validation on the phone, and the phone downloaded the Codex ZIP. Its installer was checked against the repository and run in a fresh project. The SHA-256 of the 266-character card matched the export manifest, and the full card appeared in Codex startup input.

The two calls requested gpt-6.1-sol. The fictional speaker wanted archive boxes named “纸鹤” followed by the date, or just “纸鹤” when undated. Already in the detailed claims, the fixed name had become a generic text label. The unedited card retained the ordering and missing-date rule. Asked for an undated box name without seeing the conversation, the new session returned “档案资料”. File transfer and harness loading passed. Exact name retention failed on this example.

One extraction and one fresh-project answer consumed 20,309 reported input tokens and 1,705 output tokens. No retries or human correction were used. This check covers the web preview in an Android browser. Distribution signing and native APK acceptance are separate.

## Publish the phone preview

Build in `apps/mobile` with the locked dependencies and `npm run build`. Publish only `dist/index.html`, `dist/app.js`, `dist/style.css` and `dist/icon.svg` to the root of the `gh-pages` branch, keeping the existing `.nojekyll` and `CNAME` (zichengxu.com) files in place. Serve it over HTTPS. Check each public asset against the build before linking a new version.

The [designated-value comparison](../benchmarks/designated-value-v1/README.md) follows the naming loss through extraction, export and two fresh sessions per card. The Thanksgiving launch scope is the article and phone web preview. Native Android acceptance awaits the existing release signing key.

In the 12-call follow-up on the same fictional dialogue, one of two original cards and both revised cards kept the name and undated rule. All four fresh sessions reading revised cards returned exactly “纸鹤”. The two sessions reading the original card that had generalized the name both returned “档案资料”. See the [per-card results and exact replies](../benchmarks/designated-value-v1/README.md#observed-on-the-frozen-commit).

The article entry opens the dialogue field directly. “先看「纸鹤」示例” previews the source dialogue and measured card body without replacing a draft. Readers can explicitly open the full 267-character fictional card from [the naming comparison](../benchmarks/designated-value-v1/README.md#observed-on-the-frozen-commit). It can be inspected or exported offline. Readers can switch to their own dialogue, copy the extraction request into their model, then paste back its JSON. After review they can copy the whole card for a new conversation or download a project ZIP.
