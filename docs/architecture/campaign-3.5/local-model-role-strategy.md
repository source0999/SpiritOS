# Campaign 3.5 local model role strategy

## Decision

The authenticated Source Proxy task remains the only coding control plane.
Every inference call crosses the central `model_call` authority gate and the
canonical LiteLLM router; direct Ollama dispatch is disabled for scored runs.
No hosted-provider credential is inherited by the Basic Backend 10 service.

The scored service uses bounded, role-specific routing:

| Responsibility | Source Proxy alias | Current local route | When invoked |
| --- | --- | --- | --- |
| Architect and acceptance-criteria derivation | `local` via `SOURCE_PROXY_ARCHITECT_MODEL_ALIAS` | Ollama `hermes4:latest` on the verified host | When deterministic planning cannot completely resolve the ordinary request and repository scope |
| Initial implementation | `coder` via `SPIRITOS_CODING_PRIMARY_MODEL_ALIAS` | Ollama `qwen2.5-coder:7b` on the verified host | First model-authored implementation attempt |
| Evidence-guided repair | `local` via `SOURCE_PROXY_CODER_REPAIR_MODEL_ALIAS` | Ollama `hermes4:latest` on the verified host | Second or later coder call after new parser, reviewer, verifier, test, runtime, or debugger evidence |
| Reviewer | deterministic by default; optional `SOURCE_PROXY_REVIEWER_MODEL_ALIAS` | No provider call unless explicitly configured | Every preview receives deterministic acceptance-criteria review; a configured model reviewer must have its own authorized, hash-bound call record |
| Debugger | deterministic bounded tool | No provider call | Concrete public-test or runtime failures only; command, exit status, duration, and input/output hashes are persisted and consumed by repair |
| Independent verifier | restricted Docker worker plus neutral host supervisor | No provider call | Every proposed change before a verified terminal disposition |

Model names are runtime facts rather than frozen assumptions. The router must
record the fully qualified route selected for every provider call, and the
producer identity is derived from the final successful coder call. A repair
made by `local` must never be attributed to the initial `coder` route.

## Retry and fallback ceiling

Parser/format correction and semantic reviewer-feedback correction are bounded
to three proposal attempts. Post-apply repair is also bounded and can continue
only when the attempt contains new evidence or a changed strategy. A sealed
failed attempt invalidates its exact-diff approval before a fresh proposal and
fresh approval are issued. Current on-disk state, not the original baseline,
is rebound into every repair request.

Router or local-model unavailability is classified as an environment/service
failure. It is not evidence that the coding task is impossible and it does not
authorize a hosted fallback. The service may use another installed local alias
only through the same authority, provenance, and verification boundary.

## Evidence contract

For each provider call, Source Proxy records the role/stage, requested and
resolved alias, provider and fully qualified model route, rendered-prompt hash,
raw-response hash, central-authority result, and call order. The scored runner
also commits the local Ollama artifact digest for every configured role and
rechecks the exact inventory before and after each task. Terminal proof is
ineligible if any required architect, coder, repair-coder, or configured
reviewer call is omitted, unauthorized, incomplete, misattributed, or outside
that committed local inventory.

Deterministic agents are claimed only when their real input and result receipts
are present. The runner must not convert a harness boolean, a composite
provenance hash, or a participant label into authentication, raw model output,
or debugger evidence. The verifier and private oracle likewise share one
preflight-resolved immutable Docker image ID; the mutable input tag is never
used for either scored execution command.
