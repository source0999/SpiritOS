# Modified Manifest

## `README.md`
- status: ` M`
- bucket: J - Unknown / needs Britton decision
- reason: Tracked project file outside the named active buckets; requires focused review.
- risk: medium
- likely owner/task: unknown/project docs or app shell
- safe immediate action: needs Britton decision
- exact later command if approved: `git diff -- README.md`
- rollback idea: No action without explicit decision.

## `docs/media/spiritflix-smart-tagging-rename-plan.md`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- docs/media/spiritflix-smart-tagging-rename-plan.md  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `package-lock.json`
- status: ` M`
- bucket: I - Config/package/dependency change
- reason: Package/config dependency or repomix behavior change.
- risk: high
- likely owner/task: repo config/dependency review
- safe immediate action: needs Britton decision
- exact later command if approved: `git diff -- package-lock.json  # inspect before any commit/revert`
- rollback idea: No action; if changed later, use a focused revert only with approval.

## `package.json`
- status: ` M`
- bucket: I - Config/package/dependency change
- reason: Package/config dependency or repomix behavior change.
- risk: high
- likely owner/task: repo config/dependency review
- safe immediate action: needs Britton decision
- exact later command if approved: `git diff -- package.json  # inspect before any commit/revert`
- rollback idea: No action; if changed later, use a focused revert only with approval.

## `repomix.config.json`
- status: ` M`
- bucket: I - Config/package/dependency change
- reason: Package/config dependency or repomix behavior change.
- risk: high
- likely owner/task: repo config/dependency review
- safe immediate action: needs Britton decision
- exact later command if approved: `git diff -- repomix.config.json  # inspect before any commit/revert`
- rollback idea: No action; if changed later, use a focused revert only with approval.

## `scripts/media-ingest-worker.mjs`
- status: ` M`
- bucket: E - Repo tooling / repomix / headroom / runtime helper
- reason: Repo tooling / runtime helper script area.
- risk: medium
- likely owner/task: repo tooling/runtime helper
- safe immediate action: inspect only
- exact later command if approved: `git add -- scripts/media-ingest-worker.mjs  # only if tooling slice approved`
- rollback idea: Preserve file; later revert only with approval.

## `scripts/media/face_enrolled_performers.html`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_enrolled_performers.html >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/face_enrolled_performers.json`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_enrolled_performers.json >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/face_enrollment_queue.html`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_enrollment_queue.html >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/face_enrollment_queue.json`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_enrollment_queue.json >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/face_gallery.html`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_gallery.html >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/face_gallery.json`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_gallery.json >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/face_organizer.py`
- status: ` M`
- bucket: B - Media/face organizer active work
- reason: Media/face organizer active code/test/support file.
- risk: high
- likely owner/task: media/face organizer
- safe immediate action: keep as-is
- exact later command if approved: `git add -- scripts/media/face_organizer.py  # only after media closeout approval`
- rollback idea: Do not revert; preserve until owner closes the workflow.

## `scripts/media/face_verification_full_audit.html`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/face_verification_full_audit.html >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/known_db_audit.html`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/known_db_audit.html >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/known_db_audit.json`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/known_db_audit.json >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/manual_crop.html`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/manual_crop.html >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/model_index.json`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/model_index.json >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/performer_verification.json`
- status: ` M`
- bucket: H - Generated UI/report artifact
- reason: Generated media/face organizer report artifact.
- risk: medium
- likely owner/task: media/face organizer generated report
- safe immediate action: maybe ignore later
- exact later command if approved: `printf "%s\n" scripts/media/performer_verification.json >> .gitignore  # proposal only, do not run now`
- rollback idea: Remove future ignore line or restore from artifact copy.

## `scripts/media/test_face_organizer_schema.py`
- status: ` M`
- bucket: B - Media/face organizer active work
- reason: Media/face organizer active code/test/support file.
- risk: high
- likely owner/task: media/face organizer
- safe immediate action: keep as-is
- exact later command if approved: `git add -- scripts/media/test_face_organizer_schema.py  # only after media closeout approval`
- rollback idea: Do not revert; preserve until owner closes the workflow.

## `scripts/runtime-port-guard.sh`
- status: ` M`
- bucket: E - Repo tooling / repomix / headroom / runtime helper
- reason: Repo tooling / runtime helper script area.
- risk: medium
- likely owner/task: repo tooling/runtime helper
- safe immediate action: inspect only
- exact later command if approved: `git add -- scripts/runtime-port-guard.sh  # only if tooling slice approved`
- rollback idea: Preserve file; later revert only with approval.

## `scripts/source-context-compress.mjs`
- status: ` M`
- bucket: E - Repo tooling / repomix / headroom / runtime helper
- reason: Repo tooling / runtime helper script area.
- risk: medium
- likely owner/task: repo tooling/runtime helper
- safe immediate action: inspect only
- exact later command if approved: `git add -- scripts/source-context-compress.mjs  # only if tooling slice approved`
- rollback idea: Preserve file; later revert only with approval.

## `scripts/spiritos-lan-watchdog.sh`
- status: ` M`
- bucket: E - Repo tooling / repomix / headroom / runtime helper
- reason: Repo tooling / runtime helper script area.
- risk: medium
- likely owner/task: repo tooling/runtime helper
- safe immediate action: inspect only
- exact later command if approved: `git add -- scripts/spiritos-lan-watchdog.sh  # only if tooling slice approved`
- rollback idea: Preserve file; later revert only with approval.

## `src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/app/api/spiritflix/admin/smart/analysis/route.ts`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/app/api/spiritflix/admin/smart/analysis/route.ts  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/app/layout.tsx`
- status: ` M`
- bucket: J - Unknown / needs Britton decision
- reason: Tracked project file outside the named active buckets; requires focused review.
- risk: medium
- likely owner/task: unknown/project docs or app shell
- safe immediate action: needs Britton decision
- exact later command if approved: `git diff -- src/app/layout.tsx`
- rollback idea: No action without explicit decision.

## `src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/lib/spiritflix/admin/smart/index.ts`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/lib/spiritflix/admin/smart/index.ts  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/lib/spiritflix/admin/smart/review.ts`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/lib/spiritflix/admin/smart/review.ts  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/lib/spiritflix/admin/smart/types.ts`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/lib/spiritflix/admin/smart/types.ts  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.

## `src/styles/spiritflix.css`
- status: ` M`
- bucket: A - SpiritFlix S6 smart tagging active work
- reason: SpiritFlix admin smart-tagging / rename-preview surface.
- risk: high
- likely owner/task: SpiritFlix S6 smart tagging
- safe immediate action: keep as-is
- exact later command if approved: `git add -- src/styles/spiritflix.css  # only after SpiritFlix S6 approval`
- rollback idea: Do not revert; preserve current working copy or restore from commit/stash only if Britton approves.
