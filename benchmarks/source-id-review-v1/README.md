# Source-ID evidence: offline prototype, fidelity unmeasured

The [preceding review](../source-review-diagnostic-v1/README.md) failed because
one generated quotation appended text absent from its source. Its rejected
graph is preserved; this prototype never corrects or compiles that graph.

This new contract asks the producer for evidence anchors containing only
`source_id`. The program resolves each ID to the **whole original message**,
then passes the resulting graph to the existing source-order-v3 binder and
compiler. It never guesses an ID, normalizes quotation text or substitutes a
nearby message. Unknown IDs, non-user decision evidence, invalid inheritance,
out-of-budget cards and whole messages over the existing 2,000-character anchor
limit are rejected. It does not truncate a long source to make it fit.

Input schema/version change; the public wire, compiler, reader and whole-card
1,536-character budget stay the same. Full-message evidence is coarser than a
selected quote and may affect condition factoring. This design removes generated
quote text as an error channel; it does not establish relevance, sufficient
support, complete coverage, correct ID selection or correct decisions. A toy
counterexample binds a substantively wrong action, explicitly retaining false
semantic-verification flags. Structural success is not a fidelity endpoint.

Nine offline adapter tests and four finite-controller fixtures cover source
resolution, foreign IDs, injected quotes, assistant/tool evidence, long-message
rejection, old-version rejection, graph constraints, byte preservation and
fixed missing-case/stop accounting. The oracle fixture is not model evidence.
Mechanical re-encoding of all36 already valid archived v3 outputs preserves
their public prompt bytes, including the losing240/252/312-character cards.
No new behavioral reading or repair is implied by this compatibility check.

```sh
python -m unittest discover -s tests -p 'test_source_id*.py' -q
```

The seven-slot proposal in `protocol.json` rechecks the original240-character
f7s draft, not the later rejected review. It keeps15cases/view, two reads and
both option orders. The reviewer receives its own22fictional messages and the
original draft; no questions, references, old reader scores/responses, rejected
review response or manual correction. Both full-source and no-memory controls
precede it. Invalid new products skip their own two reads and retain15missing;
other fatal failures stop the remainder. No retries, manual patching, resumption
or slot replacement. One posthoc draft/review is not fresh-generation stability,
independent generalization, causal superiority or real-person fidelity evidence.

The frozen input manifest is
`d5be78db9c0c3cba75c29fd15b057303b25673857fc955037dac96eb1fa45c44`.
The retained unapproved intake is not execution authority. Any live execution
needs its separate local grant and exact-head CI; no backend is included here.
Production defaults and the completed120-case grid remain unchanged.
