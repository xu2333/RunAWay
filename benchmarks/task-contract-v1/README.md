# Offline task-contract authoring — structure is not semantic truth

The [unchanged-card diagnostic](../question-contract-diagnostic-v1/MEASURED.md)
shows that naming wording and an explicit future-choice request produce different
answers. This small authoring API makes intended task roles explicit **before
future cases are rendered**. It does not retrofit old questions,relabel old gold,
change existing scores or call a model. Its generated wording has not itself
been empirically validated by that diagnostic.

`authoring.prepare(contract,sources)` returns public questions separately from
the private author contract and audit. Only `questions.public` is a reader input;
the private reference,support and counterfactual witnesses must stay out of model
requests. Both option orders use the same declared target and condition facts.

| Intent | Temporal role | Answer kind |
|---|---|---|
|preferred_option|future_policy|existing_option_label|
|execution_order|explicit_sequence|execution_order_label|
|past_observation|recorded_past|observed_status_label|
|decision_polarity|recorded_commitment|decision_polarity_label|

Selecting an existing option is different from inventing a new name. An actual
past fact is different from future preference. A known recorded state such as
`尚未决定`is also different from having no unique accepted/rejected decision
among the supplied polarity options. Unsupported or inconsistent role pairs
are rejected. The renderer supplies a task-specific verb instead of leaving the
author to reuse an ambiguous generic naming descriptor.

This version is deliberately narrow:two distinct literal labels plusU;known
labels must occur in user-support quotes. Anchors must cite existing user text,
not an assistant proposal or fabricated quote. Unknown references require an
explicit author reason(missing condition,uncovered policy,conflicting sources,
or not decided). This does not handle arbitrary normalized/paraphrased labels.

Every case also needs an **author-declared contrast witness**:a proposed faulty
interpretation must produce a different answer inside the actual option space.
For example,testing an invented acceptance of a remote proposal against two
unrelated ordinary-method options is rejected:the corrupted action is outside
the answer space and may still be scoredU. A decision-polarity contract with
accept/reject options and an undecidedUreference can express that intended test.

These checks establish neither that the model will exhibit the contrast nor
that the source semantically entails the author reference. Literal occurrence
does not verify negation,scope,causality or truth. All audits explicitly keep
`semantic_entailment_verified`,`reference_independently_accepted`,
`question_source_equivalence_independently_accepted`and
`contrast_behaviour_observed`false. A structurally valid contract still needs
separate semantic review and full-source/control calibration.

```sh
python -m unittest discover -s tests -p test_task_contract_authoring.py -v
```

Seven instrument checks exercise task/temporal mismatch,known undecided versus
unknown polarity,option-space blind spots,nondiscriminating witnesses,user
quote/label provenance,public/private separation and input immutability. Their
toy fixtures are not new model-fidelity observations or new real-person data.
The module has no service backend and grants0new experiment authority.
