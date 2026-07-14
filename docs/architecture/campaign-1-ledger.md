# Campaign 1 Ledger

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; accepted checkpoint parent: `34581ac5c1dfa453d9ac273044050ef8afbc53d6` (the current commit is accepted only when it atomically updates this ledger and state).
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Current checkpoint

- Phase: **Phase 1**; increment: **operator issuance runtime and Design integration**.
- Dirty state at checkpoint: none. The runtime and Design issuance boundary is committed atomically with this ledger update; later active files must be named explicitly and are never cleaned by the continuity process.
- Critical blocker: `none`; build verification failed and is recorded as a verification failure, not an external blocker.
- GO eligibility: `false`; full Campaign 1 closeout is incomplete and the current build verification has not passed.
- Next concrete gate: `resolve_campaign_build_verification_failure_and_full_closeout` - reproduce and resolve the campaign-worktree build failure, then resume remaining AR-001/002/003 and closeout gates.

## Git-bound gate status

| Gate | Status | Evidence / implementation |
| --- | --- | --- |
| Authenticated SpiritFlix no-reversion | accepted baseline | `af7fd532`, `6053b53f`, baseline receipts |
| Authority inventory | completed | `e1b9966c` |
| AR-002 duplicate cleanup | completed | `e68d3ba6`, `b9f5fdeb`, `3a01f8d6`, `42ded963` |
| Approval Authority bootstrap/lifecycle | completed | `b84bf012`, `2cf49fa9`, `b2bae870`, `540fd3d6` |
| Design Studio writeback | substantially implemented | authenticated operator route resolves persisted Design previews and the canonical writeback consume/finalize chain has real HTTP proof |
| Cartographer containment/transfer | partial | `3a01f8d6`, `42ded963`; final acceptance remains |
| Coding durable approval/acknowledgement | substantially implemented | `b4d8e49f` through `540fd3d6` |
| operator-session foundation | completed | HTTP-only session route plus origin, CSRF, expiry, revocation, role, and audit foundation; focused Vitest proof |
| Authenticated coding issuance | completed slice | real HTTP route -> persisted preview -> authenticated issuance -> durable task apply -> consume/finalize; all four acknowledgement roles share one ID/generation |
| Runtime evidence | completed slice | [redacted operator issuance receipt](campaign-1-evidence/operator-issuance-runtime-20260714.md) documents the coding and Design HTTP chains |
| Build verification | verification failure | `npm run build` segfaulted once during optimized compilation and then timed out after 124 seconds; no build GO claim |
| AR-001 / canonical contracts / evidence / coding shell / Prompt 1 / duplicates / truthful profiles / final closeout | not started or verify | governed by plan |

## Last verified commands

`git status --short`; `git rev-parse HEAD`; `git branch --show-current`; `git log --oneline --decorate -40`; protected product-head `rev-parse` checks; `npm run campaign-1:validate-authority`; 209 backend approval/task tests; 22 execute-approved route tests; `npm run typecheck`.

Last verified: `2026-07-14T01:06:19Z`. The next ledger update is required before a turn ends and must record accepted HEAD, exact dirty files, phase, next gate, product heads, and validator result.
