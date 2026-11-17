# Real use before tighter compression

This is an offline development plan, not a completed study or a model-call grant. The public acceptance claim remains: **real-person fidelity is unverified**.

## First establish useful personal signal

Use actual conversations in which a user corrected an agent's proposed action or judgment. Preserve the earlier situation, available options and the user's later decision. A correction can be a task requirement or a preference change; it is not automatically a stable personal trait.

Before execution, freeze the selection criteria, source hashes, chronological cutoff, target decision, ambiguity annotations and generic-quality controls. Put original private text and consent records outside the public repository. Neither the extractor nor reader receives the target correction, reference labels or feedback from a previous evaluation attempt on that target. Referenced artifacts needed to understand a decision must be explicitly selected, not silently fetched by an agent.

Require an explicit earlier owner statement in the applicable scope, and inspect the entire shared current material for cues—including assistant proposals and choice questions. Do not remove a revealing current message to manufacture a history advantage. Preserve every qualifying message in multi-message turns. Record exclusions and unavailable media. A manually selected earlier-evidence condition may diagnose the reading problem, but target-aware selection cannot count as automatic retrieval or full-history benefit. The [first audit](results/real-correction-history-audit-v3.md) applies these checks to actual failed cases and new candidates.

Start with full historical input versus no personal history, using the same task, model and reading contract. Include matched generic-quality and answer-length controls where relevant. Report paired disagreements and errors by original episode; repeated generations and option orders are not independent people. A null full-history comparison leaves compression retention undefined and stops that stage.

Only after this gate should a frozen candidate be compared with full history. Measure preserved and newly lost choices, condition handling, justified uncertainty and actual prompt/service cost. Do not tune to a revealed held-out correction or promote reused development episodes into a new holdout. A single-person retrospective pilot does not establish prospective or population performance. New data/service execution needs its own exact disclosure and explicit authorization; all closed scopes stay closed.

## One local preference ledger

The current choice downloader records whole-prompt feedback. The timeline records preference events and retractions. The local ledger at `web/dist/ledger.html` now joins a validated timeline artifact and portable prompt to a validated private choice trial. Owners select an active preference and explicitly attribute an adopted/corrected/unresolved outcome. It supports file save/restore, deduplication, conflicting feedback, per-version counts and context inspection. It does not yet support ordinary profile claims or automatic prompt revision.

The minimal append-only record binds:

- The exact profile or timeline artifact, prompt version, preference/event ID and preference-content version.
- The original local choice-event ID and the situation/conditions under which the preference was used.
- The user's judgment: adopted, corrected or unresolved; whether the user explicitly attributed that outcome to this preference.
- Its provenance and any superseding judgment or preference revision, retaining the previous record.

The existing private trial validator supplies request, prediction, reference timing and event identity. Reimporting the same event must not increase counts. Conflicting feedback versions remain unresolved until the user resolves them. Demo-derived feedback stays separate from user-supplied records. Public summaries cannot be linked back to individual rules and cannot populate this ledger.

Display adopted/corrected/unresolved counts per active preference version and context. A correction should trigger review or lower its local use priority; repeated adoption can raise its local use priority. These are local usage signals, not calibrated probabilities or causal proof. Historical success does not transfer automatically to a revised rule, cancel an explicit retraction, outrank current user instructions or erase unknown conditions.

Keep ledger data local. A future export may include the owner's reviewed current preferences and bounded usage notes, with a preview; raw corrections and original conversations remain private. Changes to a prompt must be visible and create a new version. Software fixtures can verify accounting and export behavior but cannot validate personal fidelity.

## Keep the first-use route small

The primary route is conversation → reviewed prompt → Codex/Claude Code. Existing mobile, CLI and synthetic demos can remain available through supporting documentation. No new gallery, theater, personality taxonomy or mobile feature is needed to test the core hypothesis.

Historical result relocation is a separate compatibility task: inventory inbound links and frozen checker dependencies before moving files. Preserve measured inputs, observations and denominators. Formatting repairs must not silently change reported numbers.
