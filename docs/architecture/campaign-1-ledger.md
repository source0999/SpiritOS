# Campaign 1 Ledger

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; accepted checkpoint parent: `1dd48032c34ae9787512b3c9cdda0aa4e358b84f` (the current commit is accepted only when it atomically updates this ledger and state).
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Current checkpoint

- Phase: **Phase 1**; increment: **authenticated operator issuance for coding**.
- Dirty state at checkpoint: none. The authenticated coding issuance boundary is committed atomically with this ledger update; later active files must be named explicitly and are never cleaned by the continuity process.
- Critical blocker: `none`.
- GO eligibility: `false`; authenticated operator issuance and mandatory Campaign 1 closeout gates are incomplete.
- Next concrete gate: `operator_issuance_production_route_and_design_integration` - run real route -> Authority -> Source Proxy task proof, then integrate the identical authenticated issuer into Design writeback.

## Git-bound gate status

| Gate | Status | Evidence / implementation |
| --- | --- | --- |
| Authenticated SpiritFlix no-reversion | accepted baseline | `af7fd532`, `6053b53f`, baseline receipts |
| Authority inventory | completed | `e1b9966c` |
| AR-002 duplicate cleanup | completed | `e68d3ba6`, `b9f5fdeb`, `3a01f8d6`, `42ded963` |
| Approval Authority bootstrap/lifecycle | completed | `b84bf012`, `2cf49fa9`, `b2bae870`, `540fd3d6` |
| Design Studio writeback | partial | `c438d4b7`; authenticated operator issuance integration remains |
| Cartographer containment/transfer | partial | `3a01f8d6`, `42ded963`; final acceptance remains |
| Coding durable approval/acknowledgement | substantially implemented | `b4d8e49f` through `540fd3d6` |
| operator-session foundation | completed | HTTP-only session route plus origin, CSRF, expiry, revocation, role, and audit foundation; focused Vitest proof |
| Authenticated coding issuance | substantially implemented | persisted preview reference plus signed, live operator session assertion; client authority endpoint removed; coding execution requires issued durable ID |
| AR-001 / canonical contracts / evidence / coding shell / Prompt 1 / duplicates / truthful profiles / final closeout | not started or verify | governed by plan |

## Last verified commands

`git status --short`; `git rev-parse HEAD`; `git branch --show-current`; `git log --oneline --decorate -40`; protected product-head `rev-parse` checks; `npm run campaign-1:validate-authority`; 209 backend approval/task tests; 22 execute-approved route tests; `npm run typecheck`.

Last verified: `2026-07-14T00:43:54Z`. The next ledger update is required before a turn ends and must record accepted HEAD, exact dirty files, phase, next gate, product heads, and validator result.
