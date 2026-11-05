# Frozen historical source

Issue #64 changes the current executor's output-directory setup. Historical
experiments recorded the SHA-256 of the entire old executor, including code they
did not call. Replacing those recorded hashes would misrepresent what ran.

`taste_executor.py.txt` preserves the original bytes from commit `292dd6c` with
SHA-256 `57b7165a596cc731547a804b7b81f2a2c22feaa14b44182f478f222acdebb041`.
No measured JSON, encoder lock, input manifest, answer, denominator, or historical
test assertion is changed. The failed first PR65 CI run remains visible.

Run **all** Python tests with:

```sh
python3 scripts/frozen_history.py tests
```

The runner assigns every `test*.py` module exactly once. The 53 modules listed in
`manifest.json` exercise version-bound historical protocols, evidence, or their
experimental memory bridges. They run in a separate interpreter and temporary
source tree containing the verified original executor. Every other module,
including `test_taste_executor` and the snapshot integrity tests, runs against the
current tree. New modules default to current code. Both groups run even if one
fails, and any failure makes the command fail; the final JSON reports each
group's exit code and test counts. This replaces full plain unittest discovery,
which mixes two incompatible source versions. Individual current-code tests can
still use ordinary unittest discovery.

Run a listed historical replay or experimental memory utility explicitly:

```sh
python3 scripts/frozen_history.py run scripts/replay_source_id_enum_comparison.py
python3 scripts/frozen_history.py run scripts/review_memory.py demo --out enum-demo --request-schema enumerated
```

The script allowlist is in `manifest.json`. Inputs and output paths retain the
caller's location; the temporary source copy is discarded. Existing historical
documentation's replay commands need this prefix when run from the current tree.
CI uses the same entry point. Wheel installation and installed-product smoke
tests continue to test the current package.

Only the one explicitly pinned file is restored. Other code and all evidence are
copied from the working tree, so the original integrity checks still reject
unreviewed drift. Snapshot corruption, other dependency drift, interpreter
isolation, and test partition completeness have regression coverage.

The historical interpreter blocks the known Codex generation backend and Codex
subprocess entry. This tool supports offline fixtures and archive reconstruction;
it does not authorize model calls, resume a closed scope, migrate approvals, or
make the old executor a supported production entry point. Real experiments stay
bound to their separately approved source checkout and execution records.
