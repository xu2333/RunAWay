# Offline CI and hosted-runner failures

The required matrix runs the same full checks on Ubuntu 24.04 / Python 3.9,
Ubuntu latest / Python 3.13, and macOS 15 Intel / Python 3.13. It retains unit/CLI
tests, browser tests, sealed-evidence replays, synthetic artifact reconstruction,
wheel installation and the installed demo. These checks make no model calls.

The Python entry point is `python3 scripts/frozen_history.py tests`. It runs every
test module once, separating current implementation tests from historical tests
whose full-source hashes bind the original executor. Historical replays use
`python3 scripts/frozen_history.py run <script> ...` in a disposable source copy;
their recorded hashes and integrity assertions remain unchanged. See the
[snapshot contract](../benchmarks/frozen-history-v1/README.md). The current
executor regressions and installed-wheel smoke tests always use current code.

On 2026-11-02 the [PR45 run](https://github.com/xu2333/RunAWay/actions/runs/41514367598)
passed both Linux jobs, but its macOS job had zero steps and was cancelled with
the annotation “The job was not acquired by Runner of type hosted even after
multiple attempts”. GitHub also reported capacity constraints for macOS arm64.
The [earlier main run](https://github.com/xu2333/RunAWay/actions/runs/41506361359)
failed in the same way. These are runner-allocation failures, not failing tests;
the failed runs remain visible. PR45's completion process stopped without merging.

The workflow now explicitly requests `macos-15-intel`, a
[standard supported hosted runner](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
This moves the macOS job to a different runner pool; it neither guarantees runner
availability nor proves that the new run passes. All test steps remain required,
and merge still needs three successful jobs on the reviewed head commit.

The current matrix tests macOS x86_64. It does **not** provide current GitHub CI
coverage of Apple Silicon / arm64. Prior successful ARM runs retain their original
results; this configuration change does not replace them or add portability
claims. Product defaults and sealed experiment records are unchanged.

When diagnosing a red run, inspect job annotations and steps first. A job with
no acquired runner has no test log to repair. A failing test step with logs needs
its actual test failure investigated; do not treat it as a capacity incident.

A local publication observer for [PR62](https://github.com/xu2333/RunAWay/pull/62)
reported a deadline even though all1,086local Python tests and the three CI jobs
passed. The observer incorrectly required the combined log to end with `OK`;
a CLI demo printed buffered JSON after the unittest summary. The original stop
record is retained privately. A separate delivery check recognized the actual
summary and rechecked the successful exact-head CI before merging;no successful
suite or model experiment was rerun to repair that observer failure. Future
local delivery checks also record the test subprocess exit code explicitly,
rather than deriving success from the last line of a mixed-output log.

The initial historical-test compatibility helper had another false-success
case: a child exiting zero without writing its result was logged as an error,
but the wrapper still returned zero. A zero-backend regression reproduces this
on `b158d37`. The wrapper now requires both the observed exit code and a valid
structured result for each partition. Missing, malformed or empty reports,
invalid fields/counters and reported failures cannot produce a successful
overall result. Both partitions still run and retain their real exit codes.
Historical source bytes and all existing evidence/hash checks stay unchanged.
