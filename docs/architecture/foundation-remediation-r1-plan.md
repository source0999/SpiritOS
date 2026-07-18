# SpiritOS Foundation Remediation R1 Plan

Campaign: `spiritos-foundation-remediation-r1`

Base: `2b8ead66578d7f7053c01cb987e011b763c1c03d`

Branch: `codex/spiritos-foundation-remediation-r1-20260717`

Mutable worktree: `/home/source/SpiritOS-foundation-remediation-r1-20260717`

## Checkpoint discipline

Each coherent slice is implemented, focused-tested, repaired, explicitly staged,
committed, and reconciled in the state, ledger, and evidence index. A checkpoint
commit contains both state and ledger; the recorded source head may therefore be
the checkpoint's first parent. Unknown files are never staged. Protected refs and
worktrees are read-only. No push is permitted.

## Ordered gates

### R1.0 — Control plane and falsification baseline

- Create the goal, plan, state, ledger, authority inventory, evidence index, and
  test-profile registry.
- Add strict continuity, authority/call-graph, evidence-provenance, test-profile,
  and completion validators plus completion regression tests.
- Record inherited validator contradictions and keep GO false.

### R1.1 — Portable canonical authority

- Resolve repository/worktree identity from explicit server configuration and the
  registered Git worktree set.
- Reject unregistered roots, symlink/path escape, stale source heads, and caller
  substitution.
- Isolate durable authority state by canonical root identity.

### R1.2 — Cartographer authority

- Make proposal review load only a persisted proposal and server-owned operator
  identity.
- Bind proposal, snapshot hash, decision, reason, target, expected state, and
  resulting state.
- Consume authority before a transactional replace; invoke review, verification,
  and evidence consumers independently; rollback/fail closed on failure.
- Keep Cartographer proposal-only and prohibit direct transfer/write authority.

### R1.3 — SpiritFlix administrative authority

- Route every production administrative writer through one transactional helper.
- Bind complete mutation envelopes, expected current state, and expected result.
- Verify result state before successful finalization; compensate or report an
  explicit non-success state if verification/finalization fails.
- Wire a real authenticated issuer path for production callers.

### R1.4 — Design security preservation

- Remove hard-coded roots and synthesized acknowledgements.
- Require a real issuer/consumer, consuming transition before write, exact payload
  binding, independent verification/evidence, and rollback on failed finalization.
- Do not add any Design feature or lane.

### R1.5 — Coding lifecycle and independent participants

- Apply success remains `applied_needs_verification` with approval `consuming`.
- Invoke reviewer, verifier, anti-cheat, and evidence recorder as distinct consumers
  against one immutable artifact hash.
- Persist invocation/output/consumption IDs. Only the orchestrator may finalize
  success after every required participant passes.
- On failure, finalize failed and compensate where mutation has occurred.

### R1.6 — Target adapters 1–10

- Add target-owned commands and exact task specifications for every LumaCart prompt.
- Keep productive prompts model-authored; implement truthful no-op and protected-path
  behavior for prompts 9 and 10.
- Reject an identity-only lifecycle.

### R1.7 — Production CodingOrchestrator

- Make HTTP task creation register the canonical orchestrator.
- Make model output, approval, execution, verification, evidence, recovery, and final
  result flow through the persisted state machine.
- Remove live imports/calls that bypass the orchestrator.

### R1.8 — Runtime contracts and Cartographer transfer

- Enforce version, producer, consumer, schema, artifact hash, and acknowledgement at
  every live boundary.
- Reject unknown/malformed/unconsumed output.
- Require a real persisted Cartographer proposal selection and transfer event in the
  proving lineage.

### R1.9 — Backend-owned state and recovery

- Make Source Proxy SQLite/orchestrator state the only decision-bearing task truth.
- Reduce Next coding-runs storage to an explicitly non-authoritative view/cache.
- Persist failure, timeout, retry, fallback, replacement provider/model, claim-ceiling
  impact, and final recovery in one run lineage.

### R1.10 — Immutable evidence model

- Implement the v1 receipt schema, content-addressed checkpoint records, immutable
  participant/proving manifests, and source/build/claim-ceiling validation.
- Make profile evidence bind an exact command, result, artifact hash, source commit,
  and distinct profile identity. Do not issue the terminal receipt before the proving
  task and closeout profiles have run.

### R1.11 — Clean production proving task

From a new isolated checkout at the tested source commit, prove the real HTTP route,
orchestrator, context, runtime contracts, Cartographer transfer, model routing,
model-authored non-empty diff, target adapter, authenticated approval, apply,
independent participants, late finalization, in-line controlled recovery, undo/reset,
clean rerun, and temporary credential/service revocation.

### R1.12 — Closeout

Run all registered profiles, production build, secret scan, Git integrity and protected
head checks. Then generate and commit the source-bound terminal receipt and immutable
manifest, create the annotated terminal tag, verified recovery bundle, SHA-256 sidecar,
and restoration instructions. Only after the clean tagged tree and recovery anchor
revalidate may the evaluator set GO true and emit
`SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE`. Author the roadmap correction, but do not
start the next campaign.

## Gate dependency

`R1.0 → R1.1 → (R1.2, R1.3, R1.4) → R1.5 → R1.6 → R1.7 → R1.8 → R1.9 → R1.10 → R1.11 → R1.12`

Parallel implementation is allowed only where file ownership and authority boundaries
do not overlap. The terminal evaluator is intentionally incapable of accepting a gate
from Markdown prose or a self-declared GO field.
