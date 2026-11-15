# Local preference usage ledger

Open `web/dist/ledger.html` using the same local HTTP server as the web app. Start
from the links at the bottom of Choices or Timeline. There is no upload, service
call or background persistence.

1. Export a private timeline artifact and its portable JSON from Timeline.
2. Use that exact prompt in Choices. Complete a trial and download its private
   record. Public summaries cannot identify a rule and are rejected.
3. Load all three files in the ledger, choose an active event and explicitly
   attribute an adopted, corrected or unresolved outcome to it.
4. Download the private ledger. Next session, merge that file and load the current
   timeline artifact to see its counts and original situations.

Each entry binds the complete validated temporal artifact, portable content
hash, private trial, preference content hash and stable choice event identity.
Reimporting identical entries is idempotent. Conflicting judgments of the same
trial are retained and counted once as unresolved; there is no last-write win.
Demo and user-supplied origins are separate. A changed artifact/version starts
without inherited credit. Retracted or superseded events cannot receive new
credit. Imported hashes detect inconsistent content, not forged owner assertions.

Corrections move a rule into the priority-review category; this is a local usage
signal. Current instructions, conditions, explicit retractions and unknowns keep
their original authority. No automatic prompt rewrite, calibrated confidence or
real-person accuracy is claimed. The first implementation supports timeline
events, not ordinary profile claims. Conflict resolution and reviewed prompt
revision remain future work. Private files contain sources and corrections.

## Verification

`node --test tests/preference-ledger.test.mjs tests/choice-feedback.test.mjs`
passed 14 tests. The browser check completed actual file upload, attribution,
duplicate submission, download, page reload and restoration with an existing
fictional timeline fixture. No model calls were made. Run it after installing
`apps/mobile` dependencies and a Playwright Chromium browser:

```sh
node scripts/check_ledger_browser.mjs
```

`RUNAWAY_BROWSER_EXECUTABLE` can select an installed Chromium/Chrome executable.
The test's private files are generated at runtime and never uploaded. These
checks establish accounting behavior, not personal fidelity.
