# Bound memory and the UTF-8 transport fix

This iteration fixes a concrete reliability defect and adds an experimental manual compression path. It does **not** establish better behavioral fidelity. The old compressor remains the default.

## A transport bug looked like memory loss

The Python-to-Node benchmark bridge appended each stdin `Buffer` to a string. That implicitly decoded chunks separately. A valid multi-byte Chinese character split across chunks became replacement characters before JSON validation. The saved model answer could be intact while the derived profile contained `���`.

The bridge now buffers bytes, decodes UTF-8 once with a fatal decoder, then parses JSON. Separate validators reject replacement characters and unpaired surrogates before profile/prompt export, without guessing repairs. Raw artifacts are preserved. Regressions cover every single-byte boundary, Chinese, emoji and invalid UTF-8.

Offline replay confirms that the previous `t01` raw model statement said “修改建议” while its derived profile said “修改建���”. Against the intact original answer, the previously rejected exact anchor passes. The original failed experiment is unchanged: this is a corrected diagnosis of its pipeline failure, not a retroactive behavioral score.

## A usable manual prototype

The new compressor asks for compact clauses and claim references. Code attaches the original facets privately, so the model does not have to retype quotes. Each claim must have exactly one clause. This checks reference identity and coverage; it cannot prove that the clause preserves the referenced meaning.

```sh
runaway profile bound-plan my-profile/profile.private.json \
  --budget-chars 1000 > request.txt
# Give request.txt to an LLM you choose; save its complete JSON as answer.json.
runaway profile bound-import my-profile/profile.private.json \
  --answer answer.json --budget-chars 1000 --out candidate
```

Both commands are offline. `bound-import` writes `prompt.md` and `portable.json`, with original facet bindings in a separate private file. The result is explicitly `candidate_unvalidated`. It receives no automatic semantic-audit pass, behavioral certification, installation or permission to act. You can copy the prompt into any harness, then use the existing [installation workflow](QUICKSTART.md); cross-harness behavior remains unverified.

## The new frozen test stopped

The independent call limit was 24; the previous unit's seven unused calls were not reused. Two fresh synthetic policies differ only in reversible automation, with different task settings from the consumed cohorts. There are 24 primary choices per person plus order, current-instruction and unknown controls. The control decoder passed 48/48 primary choices, all three matched-person disagreements and every control.

The run then encountered two extraction rejections caused by the bridge defect, a candidate at 334 characters against a 333-character limit, and a model-review timeout. It stopped without a transport retry. **No memory-condition behavior predictions completed**, so old/new accuracy and fidelity improvement are unmeasured.

There were seven completed calls with recorded usage, one timed-out backend invocation with unknown usage, and one local guard rejection before invoking a backend. Nine persisted intents count conservatively against the cap. Known input is 67,854 and known output 9,202 tokens; **77,056 is a partial known total**, not the full cost of the timed-out invocation. The local guard rejection is classified separately using its exact error and the frozen pre-call guard. No upstream response IDs were invented.

After the stop, zero-call development replay through the fixed bridge recovered both original profiles. Omitting an unnecessary final newline let the one already-generated candidate fit its original character budget. Its full text uses 177 Qwen tokenizer tokens versus the same person's old 189: a 6.3% reduction, below the frozen 10% target. The other candidate was never generated. No behavioral comparison or complete-pair cost claim follows from this replay, and no candidate is promoted.

See [results](examples/bound-memory-results.synthetic.json) and [evidence](examples/bound-memory-evidence.synthetic.zip). Public copies redact local checkout prefixes and retain original/published hashes in a redaction manifest. A redacted request cannot be used as an identical-request cache checkpoint; its original request fingerprint is retained as a reference. Original unredacted files stay in the local run directory.

## Further evaluation

Future runs checkpoint extracted profiles and candidate stages before reviews, and stop immediately after a backend failure. The code and frozen plan capture the byte reader as well as the validators. A new comparison must declare its own finite budget after the service issue is resolved; no retries are hidden in this result. Inspected fixtures are development data. Synthetic success, if obtained later, still cannot establish fidelity to real people.
