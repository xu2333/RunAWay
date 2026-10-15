# Contributing to RunAWay

The core objective is evidence-grounded, portable personal preferences. Preserve conditions, uncertainty, contradictions and source roles before improving entertainment or brevity.

Use Python 3.9 or newer. There are no runtime dependencies. Run the offline suite with `python3 -m unittest discover -s tests -q`. Try the packaged fictional example with `python3 -m runaway demo --out my-run`.

Tests and public examples must use fictional or explicitly public, licensed material. Do not submit private trajectories, resumes, model logs, credentials or screenshots of personal profiles in issues or pull requests. Prefer a small fictional reproduction of the failure. The local research workspace is not the public release tree.

New extraction behavior should retain exact source attribution and distinguish user statements, self-reports, assistant messages and editor annotations. Passing schema checks or model critique is not evidence that a prompt reproduces a person. Changes to compression should account for omitted claims and preserve relevant conditions and linked counterexamples. A smaller character count is not a token measurement or a fidelity result.

New harness bindings should preserve existing file bytes outside managed blocks, detect conflicting edits, support removal, and state whether they were tested only as file bindings or also in a real harness session. Generation tests that call a model must be explicit opt-ins and use a documented data scope. CI makes no model calls and needs no provider credentials.

The CI workflow follows the official [setup-python documentation](https://github.com/actions/setup-python/blob/main/docs/advanced-usage.md). It runs unit tests and an installed-package offline demo on Linux and macOS. Windows is not currently a verified platform. A workflow included in source has not run on GitHub until the repository is published and its run completes.
