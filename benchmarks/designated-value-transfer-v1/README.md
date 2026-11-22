# A designated value that should be used in only one branch

The previous pocket-preview test asked fresh sessions only about an undated box. This follow-up uses a new fictional radio producer, a newly designated substitute bumper and a separate editing choice that applies to both bumpers. The same audition vote is unanimous in both cases. The desk's signature changes between the two requests.

## Materials and limits

The old web instruction and the released mobile instruction are unchanged from [the earlier comparison](../designated-value-v1/README.md). Each sees the same five turns and whole-card limit of 768 Unicode characters. Only the three user turns can support a claim. The two tasks are absent during extraction. Each reader receives one installed card and one task in a fresh ephemeral Codex project. There is no shared session across the two branches, no external decoder and no raw dialogue, reference or previous answer supplied to readers.

Run `node benchmarks/designated-value-transfer-v1/materials.mjs requests` offline to render both exact extraction prompts and the exact two tasks. Each arm generates two independent cards. Each fixed card is read twice on each branch, in 16 separate projects. Both tasks give the scheduled track and identical durations. They differ by one character in the signature status. Neither supplies the substitute's name, the preferred end of the audio clip or playback speed.

Up to 20 local CLI attempts with gpt-6.1-sol (4 extractions and 16 deliveries), 180 seconds each. Fresh maintainer approval and successful CI on the frozen head are required. A transport, extraction-validation or missing-usage failure closes the scope. No retries, repairs or replacement slots. An actual reader reply that misses the requested format counts as a scored failure. Missing replies remain in the scheduled denominators. GitHub CI runs offline only.

## Locked endpoints

| Case | Required track | Source interval (seconds) | Speed |
| --- | --- | --- | --- |
| Switch order signed | 雾铃邮差 | 4 through 12 | 1× |
| Switch order unsigned, vote still unanimous | 桥下回声 | 4 through 12 | 1× |

Score the delivered JSON offline with `python3 benchmarks/designated-value-transfer-v1/score.py CLOSED_DIRECTORY`. Check fields, selected name, retained tail and original speed separately. Joint credit requires all four with an exact JSON object, four distinct required fields, numeric timing and speed, and no surrounding prose. Both reads of both branches must pass for a card-level delivery pass. Per arm report 2 scheduled cards, 4 replies per branch and 8 replies overall. Report paired card outcomes and missing data without treating repeated reads as independent users.

Inspect the detailed claims and portable body separately. Credit the body only for an explicit binding of the designated name to a signed order, the scheduled-track fallback without a signature despite the vote, and preservation of the ending at original speed within the slot for either track. Also note whether the scope stays limited to transitions. A name only in a quotation or title does not count. Report omissions, reversed conditions, displaced editing preferences and failures to use a properly recorded rule. A full transfer pass for this fixture requires both cards to preserve those source requirements and pass all four deliveries each. If both methods pass, the comparison cannot establish an advantage. This tests a new synthetic dialogue on a single model; broader transfer remains unmeasured.
