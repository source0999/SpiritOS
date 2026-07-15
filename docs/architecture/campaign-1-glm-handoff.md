# Campaign 1 GLM Handoff

Status: **Campaign 1 remains open; do not begin Campaign 2.**

## Checkout and invariants

- Worktree: `/home/source/SpiritOS-campaign-1-20260712`
- Branch: `codex/spiritos-campaign-1-foundation-20260712`
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Never push, mutate protected worktrees, or alter borrowed SpiritFlix `_worktrees/`.

## Accepted work

- Phase 2 shared contracts and ESLint boundary enforcement: `a36c4437`.
- Phase 3 canonical cockpit, labs isolation, evidence externalization, discovery exclusions, and target-plugin browser ownership: `893c4b5e`.
- Python target adapter, durable acknowledgement binding, target command ownership, reset identity, and all-Coder-10 contexts: `af137da5..489f3737`.
- Duplicate-path classification and obsolete target-mode helper removal: `edf29096`, `84271f66`.
- Named product test-profile registry: `99e2b336`.

## Current closeout status

- `npm run campaign-1:validate-continuity`, `npm run campaign-1:validate-authority`, and `npm run campaign-1:validate-test-profiles` pass.
- Dell isolated Candidate build passed. Its exact `/coding` route is 200 with the canonical shell marker; `/design-demo/coding` redirects to `/coding`; `/chat` is 200.
- The full isolated Prompt 1 browser harness reached the authenticated operator UI but cannot proceed without `SPIRITOS_OPERATOR_E2E_SECRET`. No secret was found in approved Campaign env sources or running proxy environments. This is not a pass and must be rerun after credential provisioning.

## Required next action

Provide the test-only operator credential only through the approved Dell-local runtime configuration, rerun the isolated `run-coding-e2e-loop` lifecycle, then perform the full Campaign 1 acceptance matrix and protected-head reconciliation. Do not substitute a source-text, curl, or prior receipt for that browser lifecycle.
