# Campaign 1 Ledger

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; accepted checkpoint parent: `7725bddf872da72dc5d38407c5cb1dd06767bbec` (the current commit is accepted only when it atomically updates this ledger and state).
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Current checkpoint

- Phase: **Phase 1**; increment: **authenticated selected Prompt 1 authority lifecycle**.
- Dirty state at checkpoint: this ledger, state, and [the named redacted browser receipt](campaign-1-evidence/phase1-cross-product-browser-20260714.md). They are committed atomically with this ledger update; later active files must be named explicitly and are never cleaned by the continuity process.
- Critical blocker: `none`. The former build verification failure is resolved: its first native segfault occurred with a mixed 878 MB dev/build `.next` tree and an active Campaign dev server; the retry cutoff of 124 seconds was below the measured clean-build completion window.
- GO eligibility: `false`; the real Prompt 1 coding lifecycle now passes, but final AR-001/002/003 acceptance, canonical-shell reconciliation, duplicate-authority reconciliation, and evidence acceptance remain incomplete.
- Next concrete gate: `phase1_final_authority_acceptance_and_canonical_shell_lifecycle` - reconcile the final AR-001/002/003 acceptance matrix and canonical contracts, then complete remaining duplicate-authority/evidence gates without modifying protected products.

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
| Build verification | completed | clean `npm run build --webpack` is repeatable after stopping the Campaign-owned dev server and clearing only `.next`: final-source runs passed in 136 s (2,360,220 KB peak RSS) and 138 s (2,277,780 KB peak RSS), both with zero swaps and no orphaned build process |
| Authenticated cross-product browser regression | completed slice | [redacted browser receipt](campaign-1-evidence/phase1-cross-product-browser-20260714.md): dedicated least-privilege E2E broker, desktop and Fold Latest Added, unique player entry/video attachment, and `/coding` production shell proof on an isolated Campaign production lane; protected live lane identity and no-reversion heads were read-only verified |
| Authenticated selected Prompt 1 lifecycle | completed slice | [redacted lifecycle receipt](campaign-1-evidence/prompt1-authority-lifecycle-20260714.md): real browser Prompt 1 -> persisted preview -> authenticated operator issuance -> server-owned approval -> transactional consume/finalize -> planner/coder/reviewer/verifier/final-receipt acknowledgement proof, plus legacy issuance rejection |
| AR-001 / canonical contracts / evidence / coding shell / Prompt 1 / duplicates / truthful profiles / final closeout | not started or verify | governed by plan |

## Last verified commands

`git status --short`; `git rev-parse HEAD`; protected product-head `rev-parse` checks; two clean `npm run build` runs; `npm run test:coding-regression` (131 passed, 40 subtests); `npm run test:coding-frontend-regression` (269 passed); canonical-context Python suite (101 passed); focused authority/session/Design/frontend suite (27 passed); Python `compileall`; `npm run typecheck`; `npm run campaign-1:validate-authority`; `git diff --check`; canonical-bypass inventory; redacted changed-file secret scan; verified live protected service identity and dedicated E2E preflight; isolated production Chromium desktop/Fold/player and `/coding` shell proof using SPKI-only certificate allowance.

Last verified: `2026-07-14T02:46:00Z`. The next ledger update is required before a turn ends and must record accepted HEAD, exact dirty files, phase, next gate, product heads, and validator result.
