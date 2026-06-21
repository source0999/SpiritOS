# Secondary Review Contract — Independent Codex Review

GLM implements F1–F10 and stops at `READY_FOR_SECONDARY_REVIEW`. GLM is **not**
the acceptance authority. This document defines what independent Codex review
must check and how to run it.

## Authority
- Final acceptance requires: independent Codex review **+** Britton approval **+**
  any required repair **+** separate merge authority.
- GLM's stage verdicts are `INTERNAL_GO_PENDING_SECONDARY_REVIEW` only.

## What Codex must verify (mandatory)

### 1. Anti-cheat integrity (constitution §A–§J)
- No benchmark-specific runtime branches (F10 tailoring scan output re-checked).
- No canned substance, no stamped PASS, no handholding, no scaffolding-as-credit.
- No silent fallback (every fallback's six-field record present).
- No skipped-test success (every required test actually ran, exit codes honest).
- No evidence fabrication (spot-check reported commands against raw evidence).

### 2. Frozen-contract fidelity
- No acceptance-contract or holdout-manifest was weakened after its recorded
  freeze hash (compare `status.json` freeze hash to the file on disk).
- Every stage's `INTERNAL_GO_PENDING_SECONDARY_REVIEW` is backed by its
  acceptance contract's gates actually passing (re-run a sample).

### 3. Compatibility (the 12 preserved contracts)
- Public route paths unchanged.
- FIP0 receipt shape: existing fields byte-for-byte / normalized-JSON parity.
- FIP1–FIP6 semantics behavior-identical.
- `trace_id`, `consumer_event_id`, policy, `fake_go_detected`, verifier/grader,
  approval, apply, operator-check — all preserved.

### 4. Protected paths
- No protected path (spiritflix/media/jellyfin) edited by any stage.
- Dirty-tree check: only stage-expected files changed.

### 5. Scope discipline
- No Set A/B/C run. No Plan 4. No old-plan resume. No API/cloud call. No push.
  No merge. No primary-worktree mutation.

### 6. Caveat honesty
- Every minor caveat is environmental/deferred, has an owner + next action, and
  does not hide a required-test failure or weaken anti-cheat/contracts.

## How to run the review

```bash
# 1. Confirm the cleanup branch + terminal state
cd <cleanup-worktree>
git checkout cleanup/full-repo-20260621
cat docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json
#   -> ready_for_secondary_review == true, terminal_state_achieved == READY_FOR_SECONDARY_REVIEW

# 2. Read the handoff
cat docs/spiritos-full-repo-cleanup-20260621/secondary-review-handoff.md

# 3. Re-derive a sample of stage verdicts from raw evidence
#    (paths + hashes in each Fxx/evidence-summary.md)

# 4. Re-run the F10 terminal battery (commands + exit codes in handoff)

# 5. Re-run the tailoring scan (F10/raw)

# 6. Check frozen-contract hashes vs on-disk files
```

## Reviewer verdict options
- **ACCEPT** → Britton approval → merge authority (separate from this cleanup).
- **NEEDS_REPAIR** → specific stage/increment/gate + failing command; GLM (or a
  new session) repairs under the *existing frozen contract* (no weakening).
- **REJECT** → a constitutional violation (benchmark tailoring, stamped PASS,
  evidence fabrication, etc.) that requires Britton to re-scope.

## What review is NOT
- Not approval to run Set A/B/C. Not approval to start Plan 4. Not a merge.
- Not a substitute for Britton's per-product decisions (canonical shell, real API,
  media cleanup).
