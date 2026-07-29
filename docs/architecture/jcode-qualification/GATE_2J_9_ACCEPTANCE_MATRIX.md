# Gate 2-J.9 Acceptance Matrix

status: `GATE_ACCEPTANCE_CRITERIA_SEALED`

schema: `source-proxy.gate-2j-9-acceptance-matrix/v1`

Each gate's acceptance criteria. A gate is accepted only when every criterion is proven green
from fresh state with a receipt; partial green is reported truthfully and does not collapse
into a decorative "complete".

| Gate | Objective | Acceptance criteria | Stop conditions | Evidence |
|---|---|---|---|---|
| 2-J.9A | Authority constants + canonical schemas sealed | every MISSING constant in the constants matrix is either SEALED with a value or explicitly operator-blocked; schemas versioned; no JCode process run | operator decision unresolved for a required constant | constants matrix update; sealed envelope schemas |
| 2-J.9B | Containment primitive proof | all containment preflight tests green with inert commands; no model request | bwrap/systemd/cgroup unavailable; boundary cannot be enforced | containment preflight receipt |
| 2-J.9C | Process supervisor | launch/readiness/timeout/cancel/forced-cleanup/descendant-cleanup/exit-class green with fake executor | supervisor cannot own the tree; reap fails | supervision receipt + fake-executor tests |
| 2-J.9D | Strict event bridge | NDJSON schema + parser + sequence + malformed-stream rejection + truncation + evidence hashing green on fixtures | parser loses events or accepts malformed | event-contract test receipts |
| 2-J.9E | Writable overlay + independent diff | disposable worktree + writable layer + protected paths + independent diff + untracked/deleted/renamed accounting + cleanup green on deterministic fixtures | overlay cannot isolate; diff not independent | diff-receipt fixtures |
| 2-J.9F | Sealed inference bridge | authorized endpoint + task binding + exact model + budgets + attestation + recursion prevention + direct-provider denial green on fake model | bridge cannot prove identity; forbidden flow not rejected | bridge fake-model receipts |
| 2-J.9G | JCode no-model dispatcher integration | correct binary, fresh JCODE_HOME, env, worktree, event capture, timeout/cancel, no unauthorized access | JCode identity cannot be attested; containment leaks | no-model integration receipt |
| 2-J.9H | Single contained model smoke test (separate auth) | exact provider/model/context/budgets, complete evidence, no mutation, truthful result on one read-only diagnostic task | any identity mismatch; evidence incomplete | single-run model receipt |
| 2-J.9I | Single contained write test (separate auth) | allowed edit succeeds, protected edit fails, independent diff matches, no commit/push, evidence complete | protected edit succeeds; diff mismatch | single-run write receipt |
| 2-J.9J | Controlled failure matrix | model/provider mismatch, malformed events, timeout, cancel, tool/fs denial, protected-path, network, evidence loss, executor crash all map correctly | any failure maps to COMPLETED_VERIFIED; any cleanup leak | failure-matrix receipt |
| 2-J.9K | Qualification readiness review | operator accepts that 20-task/80-run comparison may begin | review not accepted | readiness-review decision |
| 2-J.10 | Paired harness qualification | comparison run under all prior gates' invariants; one bounded verdict; default executor unchanged | locked until 2-J.9K accepted | comparison + adoption receipt |

## Cross-cutting invariants (every gate)

- JCode disabled by default; no model task before explicit gate authorization.
- Frozen benchmark unchanged; daily runtime untouched; isolated qualification branch/worktree.
- Receipts at every gate; commit only after the gate's tests pass; never push/merge/advance
  campaigns unless explicitly authorized.
- Report partial completion truthfully; never collapse gates into a decorative complete.
