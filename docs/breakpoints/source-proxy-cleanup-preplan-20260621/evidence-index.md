# Evidence Index

## Plan 3 Status Docs

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/status.md`

- Proves: Plan 3 status file exists and records Stage 2 complete, Stage 3 not started in the original status file, 3x10 battery not run, Plan 4 not started.
- Why it matters: establishes that historical plan status files are not enough by themselves; Set A rerun evidence must be read too.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/status.json`

- Proves: `battery_3x10_run` false and `plan_4_started` false.
- Why it matters: confirms Plan 4 was not started by the original plan machinery.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/next-plan-handoff.md`

- Proves: next plan work still requires final verdict, status JSON, evidence, operator checks, and Britton approval.
- Why it matters: reinforces the approval gate.

## Set A Rerun Summary/Failure/Verdict Docs

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.json`

- Proves: stage `4R7`, verdict `NEEDS_FIX`, pass count 7, failed count 3, blocked count 0, no Set B/C, no Plan 4, A2/A5/A9 failed.
- Why it matters: machine-readable truth for current Set A status.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.md`

- Proves: human-readable A1-A10 result list with A2/A5/A9 as `NEEDS_FIX`.
- Why it matters: quick human resume surface.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/failure-buckets.md`

- Proves: A2/A5/A9 are the NEEDS_FIX bucket and lists their failed gates.
- Why it matters: gives the exact blockers that future work must address.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/7-stage4r-verdict.md`

- Proves: Stage 4R verdict `NEEDS_FIX`; Stage 5 not approved; no Set B/C/Plan 4/media mutation/route replacement/new engine/push.
- Why it matters: hard stop source.

## 4R6/4R7 Validation Docs

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/4r6-recovery-validation.md`

- Proves: 4R6 recovery validation failed, with A2/A5/A9 still NEEDS_FIX.
- Why it matters: prevents future sessions from treating 4R6 recovery as accepted.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/4r7-validation.md`

- Proves: 4R7 selftests and JSON shape passed, but requested Set A 4R7 acceptance validation failed.
- Why it matters: separates runner health from product acceptance.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/4r7-packet-model-escalation.md`

- Proves: model-lane escalation evidence exists for the 4R7 attempt.
- Why it matters: documents that the local packet lane was tried without accepting invalid output.

Path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/4r7-model-escalation-selftest.md`

- Proves: 4R7 model escalation selftest existed and passed.
- Why it matters: shows the failure is not a missing selftest; acceptance still failed.

## Source-Proxy-Min GLM Audit Files

Path: `docs/source-proxy-system-freeze-audit-20260621/glm-source-proxy-audit-20260621.md`

- Proves: GLM source-proxy-min verdict, including real wired workflow, strong anti-cheat, incomplete brain-switch, and A2/A5/A9 honest failures.
- Why it matters: independent confirmation that Set A is not accepted.

Path: `docs/source-proxy-system-freeze-audit-20260621/glm-mobile-download-index.md`

- Proves: mobile review index for the source-proxy-min freeze/audit.
- Why it matters: tells reviewers which audit files to open on mobile.

Path: `docs/source-proxy-system-freeze-audit-20260621/glm-freeze-metadata.json`

- Proves: machine-readable source-proxy-min freeze metadata.
- Why it matters: audit identity and repeatability.

Path: `docs/source-proxy-system-freeze-audit-20260621/glm-source-proxy-freeze-20260621.xml`

- Proves: compact Source Proxy freeze context exists.
- Why it matters: source for second-opinion AI review.

Path: `docs/source-proxy-system-freeze-audit-20260621/glm-checksums.sha256`

- Proves: integrity hashes for source-proxy-min audit files.
- Why it matters: guards against corrupted review packets.

## Full-Repo GLM Audit Files

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md`

- Proves: full-repo audit verdict, current HEAD, Headroom status, cleanup roadmap, top risks, and F0-F10 plan-only sequence.
- Why it matters: authoritative source for cleanup stage count.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-mobile-index.md`

- Proves: mobile review index and intended review workflow.
- Why it matters: tells future sessions and Britton how to inspect the audit on Fold 7.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-metadata.json`

- Proves: machine-readable full-repo audit metadata, HEAD, branch, staged count, dirty-state caveats, shard table, Headroom final status, and review-only/source-mutation false.
- Why it matters: audit identity and dirty-tree context.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-headroom-repair-log.md`

- Proves: Headroom `BLOCKED_ENV` root cause and fallback.
- Why it matters: prevents future sessions from misreporting Headroom as healthy.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-index.md`

- Proves: shard names, scopes, sizes, hashes, compression method, and Headroom skipped.
- Why it matters: full-repo freeze navigation.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-001.xml`

- Proves: core OS code freeze shard exists.
- Why it matters: main AI context for Source Proxy/Coding UI review.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-002.xml`

- Proves: tooling freeze shard exists.
- Why it matters: Scout, scripts, Mac worker, ops context.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-003.xml`

- Proves: architecture docs freeze shard exists.
- Why it matters: plan history and intent context.

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-checksums.sha256`

- Proves: integrity hashes for full-repo audit files.
- Why it matters: guards against corrupted review packets.

## Cleanup Roadmap Source Section

Path: `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md`, section 17.

- Proves: roadmap stages F0 through F10 and that the roadmap is plan-only, requiring review and Britton signoff per stage.
- Why it matters: cleanup stage count must come from this file, not memory.
