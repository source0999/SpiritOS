# Safe Execution Preview Contract

## Rule

Safe execution preview answers the question: "If this were approved later, what would be required before execution?"

It does not execute anything.

Every Phase 7 preview must state:

- `would_execute=false`
- `mutated_anything=false`
- `execution_authority_granted=false`
- `approval_consumed=false`
- `worker_started=false`
- `provider_called=false`
- `git_mutation_performed=false`

## Required Inputs

- requested action
- requested target files or artifact paths
- route type or worker class, if known
- Phase 4 risk/permission preview
- Phase 5 worker selector/handoff preview
- Phase 6 behavior verifier result
- allowed files
- forbidden files
- dirty tree expectation
- rollback expectation
- verification expectation

## Preview Decisions

| Decision | Meaning |
| --- | --- |
| `preview_ready` | The plan is well shaped for later approval, but execution is still unavailable. |
| `requires_human_approval` | The request may be eligible later, but approval must be explicit and external to the preview. |
| `blocked` | The request violates policy, lacks required proof, targets protected scope, or conflicts with Phase 6 truth. |
| `unverified` | The preview cannot reach a decision because required evidence is missing. |

## Hard Gates

Execution preview must block when:

- Phase 6 verifier result is `FAIL`, `BLOCKED`, `UNVERIFIED`, or behavior proof is below the required tier for product PASS
- action targets `.env`, secrets, credentials, generated diagnostic artifacts, protected production UI, Source Proxy behavior, or git state
- action would call a provider/model without explicit spend approval
- action would start a worker automatically
- action would call `execute-approved`
- action would run sandbox terminal commands in Phase 7
- action would execute safe writes in Phase 7
- action would append durable ledger events in Phase 7

## Preview Output

A safe execution preview must produce:

- normalized request summary
- source verifier gate status
- risk and permission gate status
- worker/handoff gate status
- command or action class preview
- allowed and forbidden paths
- required approval class
- rollback plan requirement
- verification plan requirement
- receipt paths that would be produced later
- blocked reasons or missing evidence
- next safe action

## Not Product PASS

Execution preview readiness is not product PASS. Product PASS remains governed by Phase 6 behavior proof and Phase 1 truth labels.
