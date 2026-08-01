# Model Capability vs System Failure Matrix

## Separation Result

| Question | Qwen 7B | Qwen 14B | Attribution |
| --- | --- | --- | --- |
| Can it ground Task R with all context inline? | Yes | Yes | Raw grounding capability proven. |
| Can it solve Task W with all context inline? | Yes | Semantically yes; evaluator says no | 14B result is verifier mismatch, not capability failure. |
| Can it emit the current native tool dialect? | No | No | Model/profile dialect incompatibility. |
| Does it identify that a read is needed? | Yes | Yes | Intent is present; serialization is incompatible. |
| Does minimal baseline loop complete after a valid read? | No | No | System loop exits before reinjection. |
| Do JCode tools reach the model through legacy bridge? | No | No | Bridge drops schemas/roles before inference. |
| Do tools reach the model after correction? | Yes | Yes | Bridge correction proven structurally. |
| Does corrected JCode parse the model's text read? | No | No | JCode parser/profile incompatibility. |
| Can JCode run Task W's focused test? | No | No | Required bounded test tool is absent. |
| Does the full Proxy packet remain concise/model-ready? | No | No | Context bloat/task burial and timeout pressure. |

## What the 7B Results Mean

7B is directly capable of both tiny task classes under complete inline context.
Its earlier hallucination/no-edit outcomes do not establish incapability. In
this audit it consistently recognizes the need to read, but writes the call as
assistant text JSON. It is not qualified for the current tool protocol until a
bounded text-call parser and recovery loop pass. The appropriate current
decision is `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`, not
`RAW_MODEL_CAPABILITY_LIMIT`.

## What the 14B Results Mean

14B passes direct read grounding and returns a behaviorally correct write
implementation using `re.sub`. The diagnostic safety evaluator rejects imports
and assignment nodes, so the raw recorded fail is a
`VERIFIER_EXPECTATION_MISMATCH`. 14B shares 7B's text-call dialect and also has
higher latency: four legacy/full JCode or full-packet requests reach the
300-second timeout. Latency/context qualification remains open, but the audit
does not support an incapability verdict.

## System Failures Proven by Counterfactuals

1. A passes while B fails for both models: tool dialect/parser compatibility is
   implicated.
2. Both C cells parse and execute a read but never return an answer: baseline
   agent-loop recovery is independently implicated.
3. Exact JCode capture shows tools before the legacy bridge and none after it:
   bridge transformation loss is independently implicated.
4. The correction preserves bridge fields, after which models emit text read
   calls that JCode still does not parse: bridge loss and parser incompatibility
   are separate causes.
5. Minimal direct packets complete while both full baseline packets time out:
   packet bloat/context allocation contributes independently.

The defensible verdict is `MULTI_FACTOR_FAILURE`. The system is demonstrably at
fault in several boundaries because the same models pass simpler equivalent
tasks. Neither model is yet tool-qualified, but neither is proven incapable.
