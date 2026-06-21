# New-Chat Start — Resume the Full-Repo Cleanup

Read this first in a fresh chat, then `cleanup-state.json`, then the current
stage. Do not reconstruct state from memory.

## One-paragraph context

SpiritOS Source Proxy cleanup (F1–F10), planned in
`docs/spiritos-full-repo-cleanup-20260621/`, runs on an isolated branch
`cleanup/full-repo-20260621` in worktree `../SpiritOS-cleanup-20260621`,
branched from breakpoint HEAD `927055e4`. GLM is implementation owner, **not**
acceptance authority. Terminal state is `READY_FOR_SECONDARY_REVIEW` only.
Do not run Set A/B/C, Plan 4, push, merge, or resume Plan 3.

## Exact boot sequence

1. `cd` to the **cleanup worktree** (recorded in `cleanup-state.json` →
   `isolation.cleanup_worktree`), NOT the primary `Z:\`.
2. Verify branch + HEAD:
   ```bash
   git branch --show-current   # cleanup/full-repo-20260621
   git status --porcelain       # must be clean
   git log -1 --oneline         # must equal cleanup-state.json current_cleanup_head
   ```
3. Read:
   - `docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json` (live state)
   - `docs/spiritos-full-repo-cleanup-20260621/anti-cheat-invariants.md`
   - the current stage's `plan.md`, `acceptance-contract.json`, `holdout-manifest.json`
   - the previous stage's `next-stage-handoff.md` (if past F1)
4. Run the current stage's `operator-check.sh` to confirm baseline.

## Hard rules (non-cheating constitution — overrides everything)
- No benchmark tailoring, no canned substance, no stamped success, no
  handholding, no scaffolding-as-credit, no silent fallback, no self-acceptance,
  no moving goalposts, no skipped-test success, no evidence fabrication.
- Stage verdicts are `INTERNAL_GO_PENDING_SECONDARY_REVIEW`.
- Protected paths (spiritflix/media/jellyfin) are never edited.
- No Set A/B/C, Plan 4, push, merge, old-plan resume, API/cloud call.

## If `cleanup-state.json` says `current_stage == SECONDARY_REVIEW`
The cleanup is complete and waiting for independent Codex review. Do **not** add
more stages. Read `secondary-review-handoff.md` and request review.

## If something looks contradictory
Stop with `BLOCKED_HUMAN` and state the contradiction. Do not edit a frozen
acceptance contract to make things consistent.
