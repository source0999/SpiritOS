# Resume Map

## Cleanup Roadmap Count

Cleanup roadmap source:

- `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621`, section 17.

Cleanup stages found:

| Stage | Title | Evidence | Implementation status |
|---|---|---|---|
| F0 | Preserve full-repo freeze + audit comparison | GLM full-repo audit section 17 | Freeze exists; implementation beyond preservation not started |
| F1 | Failure taxonomy + debug receipt unification | GLM full-repo audit section 17 | Not started |
| F2 | Anti-cheat detector registry + independent selftests | GLM full-repo audit section 17 | Not started |
| F3 | Model lane / brain-switch verdict contract | GLM full-repo audit section 17 | Not started |
| F4 | Local-model packet-generation decomposition | GLM full-repo audit section 17 | Not started |
| F5 | Architecture split: API transport vs domain services | GLM full-repo audit section 17 | Not started |
| F6 | Long-running task engine split | GLM full-repo audit section 17 | Not started |
| F7 | Coding UI shell split + canonical UI decision | GLM full-repo audit section 17 | Not started |
| F8 | Context / memory / Headroom strategy cleanup | GLM full-repo audit section 17 | Not started |
| F9 | Worker / tool contract cleanup | GLM full-repo audit section 17 | Not started |
| F10 | Full-loop requalification battery | GLM full-repo audit section 17 | Not started |

- `cleanup_stages_total`: 11.
- `cleanup_stages_remaining_before_implementation`: 10 if F0 is considered this freeze/breakpoint already complete, otherwise 11.
- This count is derived from GLM audit evidence and requires Britton approval before implementation.

## Original Source Proxy Plan Queue

Plan directories found:

- `plan-00`
- `plan-01`
- `plan-02`
- `plan-03`
- `plan-04`
- `plan-05`
- `plan-06`

No Plan 7+ directory was found.

| Plan / Stage | File evidence | Current status | Approved? | Resume condition |
|---|---|---|---|---|
| Plan 3 | `plan-03/status.json`, Set A rerun `summary.json`, `4r7-validation.md`, `7-stage4r-verdict.md` | Active/not complete; Set A is NEEDS_FIX | Stage 5 not approved | Repair or reclassify A2/A5/A9 through an approved contract; do not run Set B/C until gate changes |
| Plan 4 | `plan-04/status.json` | `PLAN_WRITTEN_NOT_STARTED` | No | Only after Plan 3 is accepted and Britton approves Plan 4 |
| Plan 5 | `plan-05/status.json` | `PLAN_WRITTEN_NOT_STARTED` | No | Only after earlier plans are accepted and Britton approves |
| Plan 6 | `plan-06/status.json` | `PLAN_WRITTEN_NOT_STARTED` | No | Only after earlier plans are accepted and Britton approves |

- `remaining_major_plan_dirs_after_plan3`: Plan 4, Plan 5, Plan 6.
- `count_major_plan_dirs_after_plan3`: 3.

## Remaining Plan 3 Sub-Stages

- Set A: NEEDS_FIX.
- Set B: not run.
- Set C: not run.
- Final 3x10 verdict: not complete.
- GLM anti-cheat re-review: not accepted; GLM confirms honest NEEDS_FIX and Stage 5 not approved.

## Next Old-Plan Action If Cleanup Is Finished

If cleanup is finished and Britton wants to resume the original Source Proxy plan queue, the next old-plan action is still Plan 3 Set A closure, not Set B and not Plan 4.

Specifically:

- Re-open A2/A5/A9 evidence.
- Decide whether F1/F3 style failure taxonomy and brain-switch contract work changed how those failures should be represented.
- Re-run or revalidate only under a newly approved Plan 3 continuation.
- Do not run Set B, Set C, or Stage 5 until Set A acceptance rules are satisfied or explicitly changed.

## Must Review Before Resuming

- This breakpoint directory.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.json`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/failure-buckets.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/4r7-validation.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/7-stage4r-verdict.md`
- `docs/source-proxy-system-freeze-audit-20260621/glm-source-proxy-audit-20260621.md`
- `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md`
- `docs/full-repo-system-architecture-audit-20260621/glm-headroom-repair-log.md`
