# Can the exported card preserve an earlier recording requirement?

One owner, one previously inspected real planning task. The [earlier study](../../docs/results/real-task-history-v1.md) observed that both history-conditioned plans specified a way to preserve actual inputs and both current-only plans left that route unclear. This follow-up measures the portable prompt on the same task.

Generate one card using the existing browser extraction, evidence validation and export, with a budget of 768 Unicode characters including its header and trailing newline. The encoder sees all 218 qualifying earlier messages in chronological order with speaker labels. The five current messages, scoring criteria, later answers and previous study results are withheld. This exercises the extraction core with structured sources, independent of the UI paste limit.

Make six fresh plans using the same task, system message, response schema and current messages. Supply respectively no prior context, the earlier messages or just the exported card. Repeat in reverse order, with a fresh isolated model invocation each time. All seven attempts request the same model. The card is used verbatim, without the detailed profile, source quotes or analyst hints.

Keep the earlier task-quality and constraint criteria. For each plan record whether it specifies actual input collection in order, event timestamps or equivalent timing, and alignment with video or screen state. Explicit contradiction is a violation. An unspecified mechanism stays unclear. Check whether each arm produces two usable plans that satisfy the original constraint. Report each component for each delivery with private supporting excerpts. Interpret short-card retention relative to the concurrent full and current-only results. If the controls converge, report their convergence. After scoring, trace any omission from source through the detailed profile, exported card and plans. Distinguish missing detail from reader non-use and from unscored output.

One generation tests one card. Two reads do not measure generation stability. The endpoint concerns written plans. Hardware recording and user adoption are unmeasured. The analyst knows the earlier result. Keep source text, generated outputs and authorization local.

Scope is one extraction and six deliveries. Any transport, usage, schema or card-validation failure closes the run. Keep missing deliveries in the denominator of two per arm. No retries, regeneration, repair or replacement. Results require a separate owner grant and successful CI.
