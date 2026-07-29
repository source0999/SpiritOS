# Terra High Gate 2-J.9 Workflow Handoff

status: `WORKFLOW_SPECIFIED_AWAITING_OPERATOR_APPROVAL_TO_START_2J_9A`

schema: `source-proxy.terra-high-gate-2j-9-workflow-handoff/v1`
audience: Terra High (implementation-work role, subordinate to CodingOrchestrator; see
`TERRA_HIGH_EXECUTION_CONTRACT.md`).

You implement the sealed dispatcher one atomic gate at a time, in dependency order, after
operator approval to start. You do not redesign accepted architecture, do not execute a model
task before its gate's explicit authorization, do not touch the frozen benchmark or the daily
runtime, and never collapse gates into a decorative "complete".

## Workflow invariants (every gate)

- Work one gate at a time; verify dependencies before starting.
- Use the canonical sealed constants from `GATE_2J_9_AUTHORITY_CONSTANTS_MATRIX.md`.
- JCode disabled by default; no model request before the gate that authorizes it.
- Preserve the frozen benchmark and the daily runtime; use this isolated qualification worktree.
- Produce a receipt at every gate; commit only explicit paths after the gate's tests pass.
- Never push, merge, or advance a campaign unless explicitly authorized.
- Report partial completion truthfully.
- Stop and escalate on: identity mismatch, scope change, failed mandatory test, authority
  conflict, or a missing acceptance decision.

## Gate sequence

### Gate 2-J.9A — Authority Constants and Canonical Schemas
- objective: seal every MISSING constant or explicitly block on operator decision.
- allowed files: `source_proxy/jcode/` (schema/version constants), `docs/architecture/jcode-qualification/`.
- forbidden files: benchmark, daily runtime, production routes, frozen fixture.
- dependencies: this amendment + operator decisions #1-#5.
- tests: schema/version unit tests; constants-matrix consistency check.
- controlled failures: unresolved operator constant -> explicit BLOCK, no value invented.
- evidence: updated constants matrix; sealed envelope schemas.
- acceptance: no MISSING constant remains unblocked.
- commit policy: explicit paths only.
- next: 2-J.9B.

### Gate 2-J.9B — Containment Primitive Proof
- objective: prove fs/env/net/process-limit/cgroup isolation with inert commands.
- allowed files: `source_proxy/jcode/containment.py`, `source_proxy/jcode/cgroup_scope.py` (new), tests.
- dependencies: 2-J.9A.
- tests: containment preflight suite; no model.
- controlled failures: boundary breach -> BLOCK.
- evidence: containment preflight receipt.
- acceptance: all preflight green.
- next: 2-J.9C.

### Gate 2-J.9C — Process Supervisor
- objective: launch/readiness/timeout/cancel/forced-cleanup/descendant-cleanup/exit-class.
- allowed files: `source_proxy/jcode/supervision.py` (extend), tests, fake-executor fixture.
- dependencies: 2-J.9B.
- tests: fake-executor failure modes; no JCode model request.
- evidence: supervision receipts.
- acceptance: all lifecycle + cleanup green.
- next: 2-J.9D.

### Gate 2-J.9D — Strict Event Bridge
- objective: NDJSON schema + parser + sequence + malformed/truncation/oversized/unknown rejection + hashing.
- allowed files: `source_proxy/jcode/evidence.py` (extend), `source_proxy/jcode/event_schema.py` (new), tests.
- dependencies: 2-J.9A.
- tests: fixture event streams.
- evidence: event-contract test receipts.
- acceptance: no silent event loss; malformed rejected.
- next: 2-J.9E.

### Gate 2-J.9E — Writable Overlay and Independent Diff
- objective: disposable worktree + writable layer + protected paths + independent diff + untracked/deleted/renamed + cleanup.
- allowed files: `source_proxy/jcode/workspace.py` (new), `source_proxy/jcode/diff_collector.py` (new), tests.
- dependencies: 2-J.9B.
- tests: deterministic file fixtures.
- evidence: diff-receipt fixtures.
- acceptance: overlay isolates; diff independent and complete.
- next: 2-J.9F (and 2-J.9G needs 2-J.9C+D+E).

### Gate 2-J.9F — Sealed Inference Bridge
- objective: authorized endpoint + task binding + exact model + budgets + attestation + recursion prevention + direct-provider denial.
- allowed files: `source_proxy/jcode/sealed_inference_bridge.py` (new), tests, fake-model fixture.
- dependencies: 2-J.9A, 2-J.9B.
- tests: fake-model endpoint; real-model identity probe ONLY if operator sealed decision #5.
- controlled failures: forbidden flow not rejected -> BLOCK.
- evidence: bridge fake-model receipts.
- acceptance: all forbidden flows rejected; identity attested.
- next: 2-J.9G.

### Gate 2-J.9G — JCode No-Model Dispatcher Integration
- objective: launch attested JCode binary in containment, no model requests; prove binary/JCODE_HOME/env/worktree/event-capture/timeout-cancel/no-unauthorized-access.
- allowed files: `source_proxy/jcode/dispatcher.py` (new), tests.
- dependencies: 2-J.9B, 2-J.9C, 2-J.9D, 2-J.9E, 2-J.9F.
- tests: no-model integration suite.
- controlled failures: identity unattested or containment leak -> BLOCK.
- evidence: no-model integration receipt.
- acceptance: correct identity + isolation + capture + control.
- next: 2-J.9H (requires separate operator authorization).

### Gate 2-J.9H — Single Contained Model Smoke Test (separate operator authorization)
- objective: one new non-benchmark read-only diagnostic task; prove exact provider/model/context/budgets/evidence/no-mutation/truthful result.
- allowed files: run evidence only (no source change unless a bug is found and separately authorized).
- dependencies: 2-J.9G + operator authorization.
- controlled failures: identity mismatch / evidence incomplete -> BLOCK, no retry without auth.
- evidence: single-run model receipt.
- acceptance: exact identity + complete evidence + no mutation.
- next: 2-J.9I.

### Gate 2-J.9I — Single Contained Write Test (separate operator authorization)
- objective: one new non-benchmark task with tiny authorized writable scope; allowed edit succeeds, protected edit fails, diff matches, no commit/push, evidence complete.
- dependencies: 2-J.9H + operator authorization.
- evidence: single-run write receipt.
- acceptance: as above.
- next: 2-J.9J.

### Gate 2-J.9J — Controlled Failure Matrix
- objective: model/provider mismatch, malformed events, timeout, cancel, tool denial, fs denial, protected-path, network, evidence loss, executor crash all map correctly and clean up.
- dependencies: 2-J.9G (and 2-J.9H/I where a model is needed).
- evidence: failure-matrix receipt.
- acceptance: no failure maps to COMPLETED_VERIFIED; no cleanup leak.
- next: 2-J.9K.

### Gate 2-J.9K — Qualification Readiness Review
- objective: determine whether the 20-task/80-run comparison may begin. Do not begin automatically.
- dependencies: 2-J.9J.
- evidence: readiness-review decision (operator).
- acceptance: operator acceptance.
- next: 2-J.10 (locked until 2-J.9K accepted).

### Gate 2-J.10 — Paired Harness Qualification
- objective: run the comparison under all invariants; one bounded verdict; default executor unchanged.
- dependencies: 2-J.9K operator acceptance.
- evidence: comparison + adoption receipt.
- acceptance: bounded verdict; no default-executor change without separate adoption decision.

## Required handoff packet fields (after each gate)

`campaign_id`, `gate_id`, current branch, current full HEAD, gate attempted, prerequisites
checked, files changed, tests run, controlled failures run, evidence paths, unresolved risks,
exact stop reason, next authorized gate. See `COMPACT_HANDOFF_PACKET.md` for the live example.

## First authorized workflow gate

**Gate 2-J.9A — Authority Constants and Canonical Schemas**, to start only after operator
approval and after the operator decisions #1-#5 in the architecture spec are sealed (or
explicitly blocked).
