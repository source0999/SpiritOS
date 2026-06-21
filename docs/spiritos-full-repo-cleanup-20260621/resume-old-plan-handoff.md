# Resume-Old-Plan Handoff — Plan 3 After Cleanup

This is the **post-cleanup** resume map. Do none of it now. It is frozen here so
the resume point is unambiguous once cleanup + review + Britton approval land.

## Trigger gate (all required)
1. F1–F10 complete on `cleanup/full-repo-20260621`.
2. Independent Codex review = ACCEPT.
3. Britton approval.
4. Merge authority exercised (separate from this cleanup).
Only then may the original Source Proxy plan resume.

## Exact resume point (from breakpoint + resume-map.md)

Plan 3 is **active / not complete**. Status: `NEEDS_FIX`. Stage 5 **not approved**.

- Set A: `NEEDS_FIX` — pass 7 / fail 3 / blocked 0.
- Blockers: **A2, A5, A9** (per
  `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.json`).
- Set B: not run. Set C: not run. 3x10 battery: not complete.
- GLM anti-cheat re-review: did not accept Set A.

## Next old-plan actions (in order)

1. **Return to Plan 3.** Re-open A2/A5/A9 evidence.
2. Decide whether F1 (failure taxonomy) + F3 (brain-switch contract) + F4
   (generic decomposition) changed how those failures should be represented.
   Specifically:
   - Were A2/A5/A9 *formatting failures misread as capability failures* (the
     audit's open question)? F1's typed classification should now disambiguate.
   - Can A5/A9-style prompts be satisfied locally via F4 decomposition before any
     API escalation (F3)?
3. **Rerun Set A** on the cleaned system, under a freshly approved Plan 3
   continuation contract (not the old frozen one blindly — reconcile with F1–F4).
4. Run **independent anti-cheat review** (F2 registry) on the rerun.
5. Approve **Set B only** (Britton) → run Set B.
6. Approve **Set C only** (Britton) → run Set C.
7. Close Plan 3.
8. Consider **Plan 4** (exists, `PLAN_WRITTEN_NOT_STARTED`, not authorized).
9. Continue the remaining queue (plan-05, plan-06) per breakpoint.

## Hard constraints on resume
- Do not run Set B/C until Set A is accepted or Britton explicitly changes the gate.
- Do not use known battery prompts as cleanup acceptance (that was F10's rule).
- A2/A5/A9 may be referenced as regression cases; no benchmark-specific production
  branches may have been introduced by cleanup (F10 tailoring scan confirms).

## Evidence to read before resuming
- `docs/breakpoints/source-proxy-cleanup-preplan-20260621/resume-map.md`
- `…/plan-03/continuation-3x10-dryrun/set-a-rerun/{summary.json,summary.md,failure-buckets.md,4r7-validation.md,7-stage4r-verdict.md}`
- `docs/source-proxy-system-freeze-audit-20260621/glm-source-proxy-audit-20260621.md`
- `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md`

## Integrity caveat to resolve (not blocking, but record)
The prior source-proxy audit's freeze XML
(`glm-source-proxy-freeze-20260621.xml`) has a stale checksum (recorded
`a4693675…`, actual `e69c504e…`) — same defect class as the reconciled full-repo
shards. Britton should reconcile it for a clean Plan 3 resume. Its conclusions
markdown verifies, so findings remain trustworthy in the meantime.
