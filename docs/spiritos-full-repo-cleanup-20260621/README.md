# SpiritOS Full-Repo Cleanup — Planning Packet

**Cleanup ID:** `full-repo-20260621`
**Owner (this packet):** GLM — cleanup planning + implementation owner. **Not** the final acceptance authority.
**Created:** 2026-06-21 (after P0 GO)
**Source plan:** GLM full-repo audit §17 cleanup roadmap
(`docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md`)
**Approved breakpoint:** `docs/breakpoints/source-proxy-cleanup-preplan-20260621/`
**Approved breakpoint HEAD:** `927055e489eb1dc9a263bf3a80cde53869e274ce`

## What this packet is

A durable, reviewable plan for the F1–F10 full-repo cleanup of the Source Proxy
subsystem and adjacent cleanup-owned code. It exists so that:

- implementation cannot drift from a frozen, evidence-backed contract;
- every stage has a frozen acceptance contract + generic holdout manifest
  *before* any source edit (non-cheating constitution §8);
- secondary review (independent Codex) gets a complete, honest handoff;
- the original Source Proxy plan (Plan 3) can be safely resumed only after
  cleanup + review + Britton approval.

## The only permitted terminal state

```
READY_FOR_SECONDARY_REVIEW
```

Never: `FULLY_ACCEPTED`, `DAILY_DRIVER_READY`, `PLAN_3_COMPLETE`, `SET_A_ACCEPTED`,
`CLEANUP_MERGED`. GLM may not self-accept; stage verdicts are
`INTERNAL_GO_PENDING_SECONDARY_REVIEW` until independent Codex review + Britton.

## What this cleanup is NOT

- Not a resume of Plan 3. Not Set A/B/C. Not Plan 4.
- Not a media/SpiritFlix/Jellyfin cleanup (protected — deferred).
- Not a deletion of alternate coding shells (Britton's decision).
- Not real API/cloud enablement (Britton's decision).
- Not a replacement of the canonical `/coding` route.

## Packet map

**Top level (this dir):**
| File | Purpose |
|---|---|
| `master-plan.md` | Stage-by-stage goal/why/files/invariants/rollback |
| `cleanup-state.json` | Machine-readable live state (current stage, verdicts) |
| `breakpoint-readback.md` | P0 verification record (fresh) |
| `baseline-manifest.json` | P0 baseline facts (heads, hashes, gap classification) |
| `dependency-map.md` | Enforced stage ordering + rationale |
| `risk-register.md` | Top risks + mitigations |
| `ownership-map.md` | Which subsystem each stage owns / must not touch |
| `compatibility-and-rollback-contract.md` | Public contracts that must be preserved |
| `anti-cheat-invariants.md` | The non-cheating constitution, operationalized |
| `coding-and-commenting-standard.md` | Required code qualities |
| `evidence-budget.md` | What evidence each stage must produce/retain |
| `secondary-review-contract.md` | What Codex must check + how to run it |
| `secondary-review-handoff.md` | Written at completion (F10) |
| `resume-old-plan-handoff.md` | Exact resume point for Plan 3 (post-cleanup) |
| `new-chat-start.md` | Boot file for a fresh chat resuming this cleanup |

**Per stage (`F01/` … `F10/`):** `plan.md`, `status.md`, `status.json`,
`acceptance-contract.json`, `holdout-manifest.json`, `increment-manifest.md`,
`operator-check.sh`, `evidence-summary.md`, `codex-review-report.md`,
`next-stage-handoff.md`, `evidence/`.

No raw-log forests in Git — raw logs live under the evidence root recorded in
`cleanup-state.json`.

## Live state snapshot

See `cleanup-state.json`. Until P2 commits this packet:
`planning_packet=GO`, `implementation_started=false`, `current_stage=F01`.

## How to resume in a fresh chat

Read `new-chat-start.md` first, then `cleanup-state.json`, then the current
stage's `plan.md` + `acceptance-contract.json` + prior `next-stage-handoff.md`.
