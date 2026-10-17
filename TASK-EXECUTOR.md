# Offline executor acceptance before a new service batch

This is the pre-execution acceptance record. The separately approved one-time
batch has since completed; see [results and limitations](COMPARISON-RESULTS.md).

The proposed24-call comparison now has a frozen direct runner,
`runaway.taste_executor.execute`. This preparation makes **zero model calls** and
does not authorize a new service batch. D-0015's24 calls and negative results
remain sealed.

## One call implementation, one budget

`FrozenCalls.call` adapts D-0015's existing checkpoint and180-second observer
implementation to the frozen slots. It uses the unchanged
`generation.run_bounded` cleanup: at most2seconds to drain, then2seconds to wait.
It does not use legacy `selfplay.Calls` with its240-second argument, nor add an
automatic retry layer. All18 static and6 dynamic slots reach the same backend
entry with `timeout=180`; the subprocess observer checks it again.

There is a24-generation global cap and separate stage caps. An exclusive
proposal invocation intent prevents restarting with another output directory;
the frozen proposal directory also prevents an accidental copied-plan bypass.
Unresolved/failed attempts or uncertain checkpoint integrity latch the batch
closed. Missing usage remains unknown. Exact original D-0015 body/reader request
fingerprints are forbidden and their responses are referenced offline only.

## Numeric reader gates

Both **full history** and **current-policy oracle** require:

- Current-query accuracy at least90%.
- Zero hard-constraint errors, including abstentions and missing answers.
- At least90% in every required layer: strength, conditions, exceptions, hard
  constraints, updates, revocations, current instructions and unknowns.
- Both matched distinction items correct:2/2 in this two-person fixture.
- Action consistency in at least15/16 option-order pairs.

Thresholds use exact counts, not rounded displays. The wrong-person control
requires a positive matched denominator equal to full history and strictly fewer
correct matched distinctions. The oracle's historical score is not a current
reader qualification threshold; every historical answer remains scored.

The schedule is fixed:

```text
full → wrong person → current-policy oracle → none
     → extraction/compression → actual-memory reads → eight old-data diagnostics
```

Any full/wrong/oracle gate failure stops **all later calls**, not only the new
compressor. Tests exercise stops after2/4/6 fake calls. For every unreached fresh
condition,32 current +16 historical queries and joint48 remain planned. Every
old diagnostic condition retains48 queries. Missing is never credited as U.
Transport, format or uncertain-invocation failures also stop the batch without
repair. Local product-validation or budget failures retain failed method rows
without truncation or another generation.

## Controls intentionally contain information

Source-complete prose and the current-policy oracle are **answer-bearing
reader controls** derived from the source. Excluding literal scoring gold labels
and private truth objects does not mean these controls contain no reference
answer information. They are unbudgeted controls, not compressed candidates,
and never enter product extraction or bound compression. The8 consumed-data
diagnostics cannot establish a fresh heldout win; the new paired cohort remains
a separate interpretation.

## Bound evidence and runtime

A prepared plan binds the runner, product modules and test source hashes,
immutable source snapshots, all payload hashes, exact gate/config IDs and the
local Python runtime. Offline preflight checks Node22+, the local Codex version,
the frozen tokenizer hash and `llama-cpp-python==0.3.36` using vocabulary-only
tokenization. It performs no model inference or download. Runtime drift since
the bound evidence requires another offline check before approval.

```sh
python3 -m unittest tests.test_taste_executor tests.test_taste_contract
# On an already accepted plan, using its frozen Python executable:
/path/to/frozen/python -m runaway.taste_executor --proposal /path/to/plan
```

The18 related tests use injected fake outputs or a fake subprocess: every slot,
180-second arguments,2+2cleanup, stage/global caps, uncertain-state stopping,
sealed-request refusal, oracle isolation and unconditional denominators. Fake
scores are execution tests, not model-quality evidence.

Real execution requires a separately verified human approval matching the new
proposal ID. Its receipt is operator bookkeeping, not cryptographic proof of
human authorization; the calling agent must verify the actual human message.
No real call has been made by this preparation, and current service availability
has not been probed. [Task contract and audit](TASK-CONTRACT.md).
