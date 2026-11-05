# Offline CI and hosted-runner failures

The required matrix runs the same full checks on Ubuntu 24.04 / Python 3.9,
Ubuntu latest / Python 3.13, and macOS 15 Intel / Python 3.13. It retains unit/CLI
tests, browser tests, sealed-evidence replays, synthetic artifact reconstruction,
wheel installation and the installed demo. These checks make no model calls.

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
