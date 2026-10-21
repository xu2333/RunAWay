# Automatic support extraction: six synthetic policies

This regression pack exercises the whole **raw trajectory → source-bound branches → portable card → reader choices** path. The extractor sees only source dialogue. It never receives the private policy table or test questions. All histories and people are fictional.

The six policies have five topics with three or four actions: planning, automation, feedback, evidence sharing and learning. Each history has 17 episodes / 51 role-labelled messages, including contradictory assistant suggestions, January–March preference changes, retained exceptions, and permission taking priority over a consequential decision. `world.py` contains the explicit oracle and the raw-source generator. There are 24 semantic scenes, 82 known and62 unknown person-cases, and78 queries/person. Every action appears at every available label; all questions allow `U`. All orientations must be correct for a case to count.

`extractor-answers.synthetic.json` holds six **once-generated** model extractions. Their cards are compiled by the production validator/renderer, without hand-written scope patches. The complete cards are672–764 Unicode characters, including all headers/glossary text. Two cards use literal repeated-phrase dictionaries; expanding those references reproduces the extracted prose exactly. This is a reversible encoding check, not a guarantee that the earlier model extraction preserved every source fact.

From the repository root:

```sh
# Zero model calls: reproduce every recorded accuracy result.
python benchmarks/support-extraction-v1/run.py check-observed

# Prepare only the public reader input. Each record has system/prompt/schema.
python benchmarks/support-extraction-v1/run.py prepare --case-set development --arm card > requests.json
python benchmarks/support-extraction-v1/run.py prepare --case-set fresh --arm full > full-requests.json

# Score your raw model outputs (no answer repair or U filling).
python benchmarks/support-extraction-v1/run.py score --case-set development --answers answers.json
```

Response format: `{"p17":{"q01":"A",...},"p24":{...},"p38":{...},"p52":{...},"p69":{...},"p83":{...}}`. For `none`, save `{"shared":{...}}` and score with `--shared`. Missing answers are missing and incorrect, including unknown cases. Invalid labels, unexpected IDs and duplicate JSON keys are rejected.

The gold and recorded answers are public. Send **only** a prepared request's fields to a tool-free model in an empty context without repository access. Do not let it inspect this directory. Record your provider and requested/resolved model separately; the preparation command itself makes no service calls.

Initial32-call study (6 extraction calls plus13 reader calls/model):

| Requested reader | Material | Known /82 | Unknown /62 | All-orientation consistency /144 |
|---|---|---:|---:|---:|
| gpt-6-sol | Full history |81|62|143|
| gpt-6-sol | No memory |0|62|144|
| gpt-6-sol | Automatic card |82|62|144|
| gpt-6-luna | Full history |68|61|129|
| gpt-6-luna | No memory |0|62|144|
| gpt-6-luna | Automatic card |54|61|116|

**Neither initial full-history arm passes the preregistered perfect reader gate.** The Sol card's absolute oracle score is144/144, but this is not a certified100% compression-retention result. Luna remains a failed weaker-reader result; its errors are retained. An all-unknown strategy is not personality fidelity: the no-memory control demonstrates why known choices must also pass. `observed.synthetic.json` includes every raw projected answer, not just successful cases. Resolved server model identity was not exposed.

Earlier v1/v2 attempts stopped after3 completed calls because798/824-character outputs exceeded768. They were rejected without cropping and counted in costs. The final algorithm adds generic, exact repeated-phrase packing rather than trusting model character counting. This is an overall algorithm development revision, not an isolated causal estimate for the dictionary.

The fresh case set is a second set of surface formulations defined before the first primary service call; it uses the same six policies. It is not six additional people, an external blind holdout, or actual human fidelity. Repeated reads and cyclic orientations are correlated; do not count them as independent population samples. Choice-accuracy gain is not likelihood information gain. Automatic quote validation does not certify semantic completeness or privacy.

The fixed second surface set passed a fresh same-question full-history gate on requested gpt-6-sol: full82/82known+62/62unknown, card82/82+62/62, no-memory0/82+62/62. All144cases were position-consistent. The cards were unchanged; this is a second surface formulation of the same policies, not additional people. All9primary/fresh reader groups are reproduced by `check-observed`.

`old-regression.synthetic.json` additionally contains four earlier synthetic users, their original sources,22scenes, once-generated automatic extractions and raw card-reader answers. They now require no manual scope declaration: complete cards615–644characters,56/56known and32/32unknown. The checker rebuilds all4cards and verifies all88cases. The full-history floor on these old questions was inherited only after exact source/protocol/question binding; it is not13newfull-control calls. The new old-source stage used8calls.

A final9-call posthoc diagnostic used three selected Luna failures, with only the3/4orientations of one scene per request. Full history and own card were each correct on3/3focused cases; wrong-donor cards followed the donor on the2known preference cases, but overreached on the unknown-condition control. All raw outcomes are in `focused.synthetic.json` and reproduced by the checker. Every focused card had **no glossary**. This suggests batch/position bookkeeping merits separate testing; fewer questions plus a new sample is not a causal estimate, a new blind validation, or overall Luna qualification. The original failed78-query batch remains failed.

The entire development task used65actual calls, including3calls in earlier scopes stopped for budget failures (2rejected outputs and1valid earlier output). No additional calls were made by the offline checker, example import, wheel or adapter tests. These are usage records, not a price estimate or proof of human fidelity.
