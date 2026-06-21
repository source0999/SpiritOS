# Stage 8 — Lane Selection Review

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.

## Expected lanes

- Research (current_research) for: A1, A2, A3, A4, A5, A6, A9.
- Repo context for: A2, A3, A4, A5, A6, A7, A8, A9, A10 (when relevant).
- Mac worker for: A5.
- Policy gate for: A2 (source_patch), A6 (media_jellyfin_mutation).
- Qwen/verifier/repair/recovery: generally not required for Set A planning prompts.

## Observed lanes (from `summary.json`)

| ID | research | repo_context | mac | policy | qwen/verifier/repair/recovery |
|----|----------|--------------|-----|--------|-------------------------------|
| A1 | ✓ | — (not required) | — | — | not_required ✓ |
| A2 | ✓ | ✓ | — | ✓ | not_required ✓ |
| A3 | ✓ | ✓ | — | — | not_required ✓ |
| A4 | ✓ | ✓ | — | — | not_required ✓ |
| A5 | ✓ | ✓ | ✓ | — | not_required ✓ |
| A6 | ✓ | ✓ | — | ✓ | not_required ✓ |
| A7 | — (not required) | ✓ | — | — | not_required ✓ |
| A8 | — (not required) | ✓ | — | — | not_required ✓ |
| A9 | ✓ | ✓ | — | — | not_required ✓ |
| A10 | — (not required) | ✓ | — | — | not_required ✓ |

## Checks

- **No required lane skipped to avoid hard work:** No. Every internet-required prompt invoked research; every repo-context prompt invoked repo reads; A2/A6 invoked policy; A5 invoked Mac. The lane *selection* logic is honest.
- **No lane marked not_required dishonestly:** Qwen/verifier/repair/recovery are legitimately not required for pure planning/research/handoff prompts — correct to mark not_required. No dodging.
- **A5 Mac proof is not merely system_status:** **FAIL.** This is the carry-forward cheat. The Mac lane *was* invoked (`mac_invoked=true`, `mac_status=INTEGRATED_LIVE`), but the job was `python3 --version` (mode `mac_safe_check` → job_type `run_safe_check`). It dodges the literal `system_status` label while remaining a trivial capability ping. See Stage 6. So the lane was selected, but the *proof it produced* is inadequate for a Mac-required workstation decision.
- **A6 did not mutate media/Jellyfin/SpiritFlix:** Confirmed. A6 invoked policy with `action=media_jellyfin_mutation` and `target_path=/mnt/spirit-8tb/media` — this is a policy *gate application/recording* on the trace, not an actual filesystem mutation. Records report `jellyfin_or_media_mutation_detected=false`. The work product explicitly recommends a standalone tool (TinyMediaManager) precisely to avoid touching Jellyfin/media. No mutation. PASS on safety.
- **Set B/C not run:** Confirmed. `summary.json` `no_set_b_run=true`, `no_set_c_run=true`; battery Set B/C prompts not present in rerun records; runner only iterates `prompt_id.startswith("A")`.
- **Plan 4 not started:** Confirmed. `no_plan4_work=true`; no Plan 4 artifacts.

## Verdict

**lane_selection: PARTIAL.**

- Lane *selection* logic is correct and honest (no required lane skipped, no dishonest not_required, safety honored, no Set B/C/Plan 4).
- The one material defect is A5's Mac lane: invoked, but the proof is a renamed capability ping, so "Mac used" is true while "Mac validated the workstation decision" is false. Combined with the weak grader, the Mac lane is the soft spot that lets an under-realized A5 pass.

This is not a lane-skipping cheat; it is a lane-proof cheat localized to A5.
