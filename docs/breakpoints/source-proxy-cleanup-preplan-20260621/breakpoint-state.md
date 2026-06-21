# Source Proxy Cleanup Preplan Breakpoint

- Created at: 2026-06-21T15:00:26-04:00
- Mode: documentation-only checkpoint
- Purpose: freeze the real Source Proxy plan state before cleanup planning so future AI sessions do not invent progress.

## Repo Identity

- Host: `source-server`
- Repo path: `/home/source/SpiritOS`
- Branch: `master`
- HEAD: `927055e489eb1dc9a263bf3a80cde53869e274ce`
- Staged files at preflight: 0
- Tracked dirty files at preflight: 7
- Status entries at preflight, including untracked top-level entries: 12
- Final sanity status after validation: 8 tracked dirty files and 13 status entries, due to concurrent external SpiritFlix WIP adding `src/components/spiritflix/SpiritFlixHome.tsx` after the validation block.
- Documentation-only confirmation: this task is limited to `docs/breakpoints/source-proxy-cleanup-preplan-20260621/`.

Dirty path summary from preflight:

- SpiritFlix/media tracked WIP: `docs/media/spiritflix-anime-importer.md`, `scripts/media/spiritflix_anime_import.py`, `src/components/spiritflix/SpiritFlixApp.tsx`, `src/components/spiritflix/SpiritFlixPlayer.tsx`, `src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx`, `src/lib/spiritflix-types.ts`, `src/styles/spiritflix.css`.
- Final sanity status also shows concurrent external WIP in `src/components/spiritflix/SpiritFlixHome.tsx`.
- Breakpoint docs: `docs/breakpoints/` was created by this checkpoint.
- GLM audit outputs: `docs/source-proxy-system-freeze-audit-20260621/`, `docs/full-repo-system-architecture-audit-20260621/`.
- Other untracked: `nul`, `scripts/media/spiritflix_dual_audio_anime_import.py`.

## Last Active Source Proxy Work

Last active Source Proxy work was Plan 3 Set A dry-run/rerun repair, specifically Stage 4R7 structured packet model-lane escalation for A2/A5/A9.

Evidence:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.json`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/summary.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/4r7-validation.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/7-stage4r-verdict.md`

## Real Set A Status

- Current Set A status: `NEEDS_FIX`
- Accepted: no
- Pass count: 7
- Failed count: 3
- Blocked count: 0
- Blockers: A2, A5, A9
- Current blocker class in evidence: structured packet/model-lane failures and missing accepted material output for A2/A5/A9.

Prompt status from `summary.md`:

- A1: PASS
- A2: NEEDS_FIX
- A3: PASS
- A4: PASS
- A5: NEEDS_FIX
- A6: PASS
- A7: PASS
- A8: PASS
- A9: NEEDS_FIX
- A10: PASS

Stage 4R7 acceptance validation failed with:

- A2 not PASS after 4R7, material output false, packet validation false.
- A5 not PASS after 4R7, material output false, packet validation false.
- A9 expected PASS or BLOCKED_ENV but got NEEDS_FIX.

## Stage 4R History

Evidence in the Set A rerun directory records:

- 4R fix: preflight, runner change, validation.
- 4R2: preflight, runner change, grader hardening selftest, validation.
- 4R3: preflight, runner change, validation.
- 4R4: preflight, runner change, structured packet selftest, validation.
- 4R5: preflight, contract alignment, roundtrip selftest, validation.
- 4R6: preflight, structured output repair/selftest, interrupted/resume docs, recovery preflight, runner check, recovery validation.
- 4R7: preflight, packet model escalation, model escalation selftest, validation.

The final recorded Stage 4R verdict is still `NEEDS_FIX`. `7-stage4r-verdict.md` states Stage 5 is not approved because Set A did not reach all PASS.

## Freeze/Audit State

Source-proxy-min GLM audit:

- Path: `docs/source-proxy-system-freeze-audit-20260621/`
- Status from audit evidence: complete.
- Main audit: `glm-source-proxy-audit-20260621.md`
- Mobile index: `glm-mobile-download-index.md`
- Metadata: `glm-freeze-metadata.json`
- Freeze XML: `glm-source-proxy-freeze-20260621.xml`
- Checksums: `glm-checksums.sha256`

Full-repo GLM audit:

- Path: `docs/full-repo-system-architecture-audit-20260621/`
- Status from audit evidence: complete.
- Main audit: `glm-full-repo-audit-20260621.md`
- Mobile index: `glm-full-repo-mobile-index.md`
- Metadata: `glm-full-repo-metadata.json`
- Shard index: `glm-full-repo-freeze-20260621-shard-index.md`
- Shards: `glm-full-repo-freeze-20260621-shard-001.xml`, `glm-full-repo-freeze-20260621-shard-002.xml`, `glm-full-repo-freeze-20260621-shard-003.xml`
- Headroom log: `glm-headroom-repair-log.md`
- Checksums: `glm-full-repo-checksums.sha256`

Headroom status:

- `BLOCKED_ENV`
- Cause in evidence: Cursor owns port 8797 and the available Headroom CLI is a Linux venv that cannot execute from the Windows git-bash context used by the audit.
- Fallback used: tree-sitter Repomix compression; Headroom compression was not applied.

## Cleanup Roadmap State

The cleanup roadmap is proposed by the GLM full-repo audit in section 17. It is plan-only and not implemented.

Roadmap stages found:

- F0 - Preserve full-repo freeze + audit comparison
- F1 - Failure taxonomy + debug receipt unification
- F2 - Anti-cheat detector registry + independent selftests
- F3 - Model lane / brain-switch verdict contract
- F4 - Local-model packet-generation decomposition
- F5 - Architecture split: API transport vs domain services
- F6 - Long-running task engine split
- F7 - Coding UI shell split + canonical UI decision
- F8 - Context / memory / Headroom strategy cleanup
- F9 - Worker / tool contract cleanup
- F10 - Full-loop requalification battery

Cleanup stages total: 11.

Cleanup stages remaining before implementation: 10 if F0 is considered satisfied by preserving the freeze and this breakpoint; otherwise 11. This is derived from the GLM audit and requires Britton approval before implementation.

Implementation started: no.

First recommended implementation stage after review: F1, with F5 called out as the next high-leverage architecture split after taxonomy.

## Remaining Old Plan Queue After Cleanup

Plan directories found under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/`: `plan-00` through `plan-06`.

Plan 3 is still active/not complete because:

- Set A is `NEEDS_FIX`.
- Set B was not run.
- Set C was not run.
- Final 3x10 verdict is not complete.
- GLM anti-cheat re-review did not accept Set A as complete.

Major plan directories after Plan 3:

- Plan 4: exists, `PLAN_WRITTEN_NOT_STARTED`, not authorized.
- Plan 5: exists, `PLAN_WRITTEN_NOT_STARTED`, not authorized.
- Plan 6: exists, `PLAN_WRITTEN_NOT_STARTED`, not authorized.

Count of major plan dirs after Plan 3: 3.

Do not invent Plan 7 or later from memory; no such directories were found.

## Explicitly Not Approved

- Stage 5: not approved.
- Set B: not approved/not run.
- Set C: not approved/not run.
- Full 3x10 battery: not complete.
- Plan 4: not started/not approved.
- Cleanup implementation: not approved.
- Source implementation: not approved by this checkpoint.
- SpiritFlix/media/Jellyfin mutation: not approved by this checkpoint.

## Resume Instructions

Before resuming old Source Proxy work:

1. Read this breakpoint directory.
2. Read `summary.json`, `summary.md`, `failure-buckets.md`, `4r7-validation.md`, and `7-stage4r-verdict.md`.
3. Read the source-proxy-min and full-repo GLM audit summaries.
4. Review the F0-F10 cleanup roadmap and decide whether cleanup gets a separate approved plan.
5. If cleanup is approved, start with a reviewed F1 plan; do not implement directly from the GLM audit text.
6. If old Plan 3 resumes before cleanup, the next old-plan action is to repair A2/A5/A9 Set A acceptance or explicitly classify them with a new approved verdict contract. Do not run Set B/C until Set A is accepted or Britton explicitly changes the gate.
