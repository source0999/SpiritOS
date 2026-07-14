# Campaign 1 Ledger

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; accepted checkpoint parent: `94a916e0da0a75f7e5ffdcd1064e566608a8c31d` (the current commit is accepted only when it atomically updates this ledger and state).
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Current checkpoint

- Phase: **Phase 1**; increment: **final authority acceptance and Cartographer legacy fixture migration**.
- Dirty state at checkpoint: `source_proxy/cartographer/service.py`, `source_proxy/tests/test_cartographer_api.py`, this ledger, state, [test profiles](campaign-1-test-profiles.md), and [the redacted Cartographer boundary receipt](campaign-1-evidence/cartographer-legacy-fixture-migration-20260714.md). They are committed atomically with this ledger update; later active files must be named explicitly and are never cleaned by the continuity process.
- Critical blocker: none. The registered `E2E_LOOP_ISOLATED_CANDIDATE=true` loopback-only candidate mode proved the browser lifecycle without touching the foreign port-3000 service.
- GO eligibility: `false`; Phase 1 implementation and focused acceptance evidence are complete, but Campaign 1 still requires its final cross-product evidence reconciliation and GO decision.
- Next concrete gate: `campaign1_final_closeout_go_decision` - reconcile all mandatory receipts, rerun continuity/authority truth after the atomic checkpoint, verify protected heads and secret-free evidence, then issue the Campaign 1 GO or preserve a verification failure.

## Git-bound gate status

| Gate | Status | Evidence / implementation |
| --- | --- | --- |
| Authenticated SpiritFlix no-reversion | accepted baseline | `af7fd532`, `6053b53f`, baseline receipts |
| Authority inventory | completed | `e1b9966c` |
| AR-002 duplicate cleanup | completed slice | `e68d3ba6`, `b9f5fdeb`, `3a01f8d6`, `42ded963`, `e8e26978`; mounted direct execution routes removed, legacy mutation routes fail closed |
| Approval Authority bootstrap/lifecycle | completed | `b84bf012`, `2cf49fa9`, `b2bae870`, `540fd3d6` |
| Design Studio writeback | completed slice | authenticated operator route resolves persisted previews; canonical writeback now consumes/finalizes with server-assigned design-writeback/reviewer/verifier/evidence acknowledgement envelope and redacted durable receipt |
| Cartographer containment/transfer | completed slice | durable proposal selection preview -> authenticated operator issuance -> canonical non-mutating transfer consumer -> transactional consume/finalize -> matched acknowledgement receipt; legacy direct transfer fails closed |
| Coding durable approval/acknowledgement | substantially implemented | `b4d8e49f` through `540fd3d6` |
| operator-session foundation | completed | HTTP-only session route plus origin, CSRF, expiry, revocation, role, and audit foundation; focused Vitest proof |
| Authenticated coding issuance | completed slice | real HTTP route -> persisted preview -> authenticated issuance -> durable task apply -> consume/finalize; all four acknowledgement roles share one ID/generation |
| Runtime evidence | completed slice | [redacted operator issuance receipt](campaign-1-evidence/operator-issuance-runtime-20260714.md) documents the coding and Design HTTP chains; [runtime recovery receipt](campaign-1-evidence/phase1-runtime-lane-recovery-20260714.md) records the passing registered isolated browser lifecycle |
| Build verification | completed | clean `npm run build --webpack` is repeatable after stopping the Campaign-owned dev server and clearing only `.next`: final-source runs passed in 136 s (2,360,220 KB peak RSS) and 138 s (2,277,780 KB peak RSS), both with zero swaps and no orphaned build process |
| Authenticated cross-product browser regression | completed slice | [redacted browser receipt](campaign-1-evidence/phase1-cross-product-browser-20260714.md): dedicated least-privilege E2E broker, desktop and Fold Latest Added, unique player entry/video attachment, and `/coding` production shell proof on an isolated Campaign production lane; protected live lane identity and no-reversion heads were read-only verified |
| Authenticated selected Prompt 1 lifecycle | completed slice | [redacted lifecycle receipt](campaign-1-evidence/prompt1-authority-lifecycle-20260714.md): real browser Prompt 1 -> persisted preview -> authenticated operator issuance -> server-owned approval -> transactional consume/finalize -> planner/coder/reviewer/verifier/final-receipt acknowledgement proof, plus legacy issuance rejection |
| Canonical in-shell operator control | completed slice | [redacted shell receipt](campaign-1-evidence/canonical-operator-shell-20260714.md): native prompts removed; one shell control provides session status, credential clearing, authenticated issuance, and revoke/logout; Coder 10’s strict apply/reverse fixture and real Prompt 1 browser lifecycle use that control |
| Reconciliation index and truthful profiles | completed slice | [evidence index](campaign-1-evidence-index.md), [test profiles](campaign-1-test-profiles.md), `e8e26978` successor checkpoint |
| AR-001 ordinary BFF session migration | completed slice | server-owned opaque session/BFF implementation; [redacted receipt](campaign-1-evidence/ar001-server-owned-session-20260714.md); 64 focused tests passed |
| AR-001 admin mutation containment | completed slice | ordinary media session remains insufficient; all seven bounded writers require the distinct durable Authority and canonical `spiritflix-admin-executor` consume/finalize path |
| AR-001 direct mutation routes | completed slice | `db6d4c97`, `0ee7b694`, `2961548a`, `af1646ed`, `57f9f9db`: all seven inventoried routes return `410 spiritflix_admin_direct_mutation_forbidden` |
| AR-001 durable admin authority contract | completed slice | shared Authority supports `spiritflix_admin_mutation` preview, issue, consume, and finalize through `spiritflix-admin-executor` |
| AR-001 smart-rescan executor migration | completed slice | `6210a333`: authenticated operator preview/approval and Authority consume/finalize now gate the bounded rescan trigger |
| AR-001 remaining admin writer migration | completed slice | `7d54606c`: admin/actions, smart/analysis, smart/batch, videos/model, videos/tags, videos/face-learning all migrated to the same consume/finalize authority pattern; 16/16 focused tests pass |
| Cartographer legacy mutation boundary | completed slice | retired direct helpers now fail closed before legacy gate/filesystem code; safe-write and verification routes remain absent; branch/commit/push direct routes reject; canonical selection routes are singular; [redacted receipt](campaign-1-evidence/cartographer-legacy-fixture-migration-20260714.md); complete Cartographer profile 263 passed |
| Phase 1 authority acceptance | completed slice | all admin writers, AR-002 durable selection/consumer acknowledgement, AR-003 Design writeback acknowledgement, canonical coding lifecycle, and focused final matrix are committed subject to this atomic checkpoint |

## Last verified commands

`PYTHONPATH=. .venv-campaign1/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -q` (**263 passed**, 3 existing deprecation warnings); `PYTHONPATH=. .venv-campaign1/bin/python -m pytest source_proxy/tests/test_campaign_approval_authority.py source_proxy/tests/test_long_running_tasks.py -q` (**83 passed**, 1 existing deprecation warning); Design production-route suite (**32 passed**); Design receipt negatives (**9 cases passed**); `npm run test:coding-regression` (**131 passed**, 10 existing async-mock warnings); `npm run test:coding-frontend-regression` (**269 passed**, existing React `act` warnings); `npm run typecheck` (**passed**); `npm run build` (**passed**); registered isolated `run-coding-e2e-loop` (**PASS**: real model generation, visible operator login, durable preview/approval, consume/finalize, acknowledgement, managed Chromium proof, undo/reset/clean rerun). Authority/continuity validators, `git diff --check`, scoped secret scan, and protected-head checks are rerun at the atomic checkpoint.

Last verified: `2026-07-14T21:45:54Z`. The next ledger update must record the Campaign 1 final closeout decision and protected-head truth.
