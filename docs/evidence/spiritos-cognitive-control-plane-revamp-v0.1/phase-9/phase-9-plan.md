# Phase 9 Plan - Controlled Live Proof

## Authorization

Phase 9 is authorized by Britton for the smallest controlled live proof after Phase 8 dry-run readiness.

Allowed files:

- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`

Allowed live action:

- non-mutating browser proof against one existing static artifact

Forbidden actions:

- no source code changes outside evidence docs
- no production UI changes
- no Source Proxy behavior changes
- no worker execution
- no provider/model calls
- no Obsidian writes
- no git mutation
- no generated benchmark artifact mutation
- no `execute-approved` route calls
- no sandbox terminal command execution
- no safe-write execution
- no workflow runner execution
- no artifact file mutation

## Proof Candidate

Selected proof:

- Fixture: `timer-false-negative`
- Artifact: `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/01-make-a-timer-app/workspace/index.html`
- Reason: Phase 8 recommended the timer pass-preservation fixture as the smallest controlled live proof candidate.

## Stop Conditions

Stop and mark NO-GO or PARTIAL if:

- exact artifact target cannot be located
- browser proof toolchain is unavailable
- artifact fails to load
- Start/Stop controls are missing
- timer does not count upward after Start
- timer does not freeze after Stop
- proof would require artifact mutation, provider/model calls, workers, git mutation, or production changes

## PIVOT Increments

| Increment | Scope | Verdict |
| --- | --- | --- |
| 9.1 | Preflight and proof target selection | GO |
| 9.2 | Timer controlled live proof | GO |
| 9.3 | Phase 9 closeout and Phase 10 handoff | GO |

## Boundary

This phase proves one existing artifact behavior. It does not generalize to broad benchmark readiness, automatic learning, worker execution, or production control-plane implementation.
