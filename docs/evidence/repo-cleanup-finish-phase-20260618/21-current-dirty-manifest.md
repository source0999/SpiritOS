# Current Dirty Manifest

Every dirty/untracked item is classified into exactly one bucket.

## README.md

- Git status: ` M`
- Bucket: G. package/dependency/config change
- Why: Package/config/docs change; only repomix-specific portions may be staged in this run.
- Risk: high
- Likely owner/task: repo config/docs
- Safe action now: inspect only
- Exact command if approved: `git diff -- README.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## package-lock.json

- Git status: ` M`
- Bucket: G. package/dependency/config change
- Why: Package/config/docs change; only repomix-specific portions may be staged in this run.
- Risk: high
- Likely owner/task: repo config/docs
- Safe action now: inspect only
- Exact command if approved: `git diff -- package-lock.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## package.json

- Git status: ` M`
- Bucket: G. package/dependency/config change
- Why: Package/config/docs change; only repomix-specific portions may be staged in this run.
- Risk: high
- Likely owner/task: repo config/docs
- Safe action now: inspect only
- Exact command if approved: `git diff -- package.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media-ingest-worker.mjs

- Git status: ` M`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git diff -- scripts/media-ingest-worker.mjs`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_enrolled_performers.html

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_enrolled_performers.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_enrolled_performers.json

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_enrolled_performers.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_enrollment_queue.html

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_enrollment_queue.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_enrollment_queue.json

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_enrollment_queue.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_gallery.html

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_gallery.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_gallery.json

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_gallery.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_organizer.py

- Git status: ` M`
- Bucket: D. media/face-organizer active work
- Why: Face organizer code/schema/model-index or active verification data.
- Risk: high
- Likely owner/task: media face organizer
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: scripts/media/face_organizer.py`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_verification_full_audit.html

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_verification_full_audit.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/known_db_audit.html

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/known_db_audit.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/known_db_audit.json

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/known_db_audit.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/manual_crop.html

- Git status: ` M`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/manual_crop.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/model_index.json

- Git status: ` M`
- Bucket: D. media/face-organizer active work
- Why: Face organizer code/schema/model-index or active verification data.
- Risk: high
- Likely owner/task: media face organizer
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: scripts/media/model_index.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/performer_verification.json

- Git status: ` M`
- Bucket: D. media/face-organizer active work
- Why: Face organizer code/schema/model-index or active verification data.
- Risk: high
- Likely owner/task: media face organizer
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: scripts/media/performer_verification.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/test_face_organizer_schema.py

- Git status: ` M`
- Bucket: D. media/face-organizer active work
- Why: Face organizer code/schema/model-index or active verification data.
- Risk: high
- Likely owner/task: media face organizer
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: scripts/media/test_face_organizer_schema.py`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/runtime-port-guard.sh

- Git status: ` M`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git diff -- scripts/runtime-port-guard.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/source-context-compress.mjs

- Git status: ` M`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git diff -- scripts/source-context-compress.mjs`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/spiritos-lan-watchdog.sh

- Git status: ` M`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git diff -- scripts/spiritos-lan-watchdog.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/app/layout.tsx

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/app/layout.tsx`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/components/spiritflix/SpiritFlixPlayer.tsx

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/components/spiritflix/SpiritFlixPlayer.tsx`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix-jellyfin-client.ts

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix-jellyfin-client.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix/admin/smart/review.ts

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix/admin/smart/review.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix/admin/smart/types.ts

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix/admin/smart/types.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix/jellyfin-client.ts

- Git status: ` M`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix/jellyfin-client.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/00-baseline.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/00-baseline.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/10-runtime-snapshot.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/10-runtime-snapshot.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/20-endpoint-timing.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/20-endpoint-timing.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/30-log-findings.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/30-log-findings.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/40-process-log-review.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/40-process-log-review.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/final-verdict.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/final-verdict.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/index.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/index.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/operator-summary.md

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/operator-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/00-baseline.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/00-baseline.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/10-runtime-snapshot.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/10-runtime-snapshot.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/20-endpoint-timing.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/20-endpoint-timing.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/30-journal-last-60m.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/30-journal-last-60m.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/31-boot-history.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/31-boot-history.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/40-runtime-log-locations.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/40-runtime-log-locations.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/41-tmux-sessions.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/41-tmux-sessions.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/42-tmux-capture-source-proxy-lan.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/42-tmux-capture-source-proxy-lan.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/42-tmux-capture-spiritos-lan.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/42-tmux-capture-spiritos-lan.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/43-next-development-log-tail.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/43-next-development-log-tail.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/44-process-tree-selected.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/44-process-tree-selected.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/45-dmesg-tail.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/45-dmesg-tail.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/46-ollama-ps.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/46-ollama-ps.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/raw/47-tailscale-status.txt

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/raw/47-tailscale-status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/live-hiccup-triage-20260617/summary.json

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- docs/evidence/live-hiccup-triage-20260617/summary.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/00-baseline.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/00-baseline.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/01-current-state-summary.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/01-current-state-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/10-prior-evidence-review.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/10-prior-evidence-review.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/20-current-dirty-manifest.json

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/20-current-dirty-manifest.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/21-current-dirty-manifest.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/21-current-dirty-manifest.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/22-bucket-summary.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/22-bucket-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/30-post-commit-evidence-result.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/30-post-commit-evidence-result.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/40-repomix-ignore-patch.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/40-repomix-ignore-patch.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/41-repomix-validation.md

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/41-repomix-validation.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/raw/00-baseline.txt

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/raw/00-baseline.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/diff-name-status.txt

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/diff-name-status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/diff-numstat.txt

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/diff-numstat.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/diff-stat.txt

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/diff-stat.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/status-porcelain-uall.txt

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/status-porcelain-uall.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/untracked-exclude-standard.txt

- Git status: `??`
- Bucket: A. post-commit evidence-only leftover
- Why: This run cleanup evidence packet.
- Risk: low
- Likely owner/task: repo cleanup finish evidence
- Safe action now: stage evidence-only
- Exact command if approved: `git add -- docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/untracked-exclude-standard.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## "docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/untracked-exclude-standard.txt\r"

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: No safe cleanup classification from path alone.
- Risk: medium
- Likely owner/task: unknown
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- "docs/evidence/repo-cleanup-finish-phase-20260618/raw/git/untracked-exclude-standard.txt\r"`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/00-git-status.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/00-git-status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/00-preflight.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/00-preflight.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/10-previous-audit-read.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/10-previous-audit-read.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/20-dirty-tree-manifest.json

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/20-dirty-tree-manifest.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/21-dirty-tree-manifest.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/21-dirty-tree-manifest.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/22-untracked-manifest.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/22-untracked-manifest.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/23-modified-manifest.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/23-modified-manifest.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/24-task-bucket-summary.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/24-task-bucket-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/30-diff-triage.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/30-diff-triage.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/40-no-delete-cleanup-proposal.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/40-no-delete-cleanup-proposal.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/41-proposed-repomix-ignore-patch.diff.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/41-proposed-repomix-ignore-patch.diff.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/42-proposed-archive-manifest.json

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/42-proposed-archive-manifest.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/43-delete-candidates-hold.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/43-delete-candidates-hold.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/50-manual-watcher-dryrun.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/50-manual-watcher-dryrun.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/51-runtime-current-status.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/51-runtime-current-status.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/60-draft-watchers-summary.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/60-draft-watchers-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/61-install-plan-not-executed.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/61-install-plan-not-executed.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/62-removal-plan-not-executed.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/62-removal-plan-not-executed.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/README.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/README.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-boot-postmortem.service.example

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-boot-postmortem.service.example`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-boot-postmortem.sh

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-boot-postmortem.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-health-snapshot.service.example

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-health-snapshot.service.example`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-health-snapshot.timer.example

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-health-snapshot.timer.example`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-host-health-snapshot.sh

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-host-health-snapshot.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-model-storage-guard.sh

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-model-storage-guard.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-repo-bloat-report.sh

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-repo-bloat-report.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-service-health-snapshot.sh

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-service-health-snapshot.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/final-verdict.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/final-verdict.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/index.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/index.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/operator-summary.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/operator-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-diff-name-status.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-diff-name-status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-diff-numstat.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-diff-numstat.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-diff-stat.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-diff-stat.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-ls-others.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-ls-others.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-status-porcelain.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/git-status-porcelain.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/00-date.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/00-date.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/01-uptime.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/01-uptime.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/02-free.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/02-free.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/03-df.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/03-df.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/04-ports.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/04-ports.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/05-systemctl-failed.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/05-systemctl-failed.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/06-systemctl-ollama-docker.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/06-systemctl-ollama-docker.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/07-docker-ps.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/07-docker-ps.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/08-tmux-ls.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/08-tmux-ls.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/09-source-proxy-health.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/09-source-proxy-health.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/10-source-proxy-v1-health.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/10-source-proxy-v1-health.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/11-next-root.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/11-next-root.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/12-ollama-tags.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/12-ollama-tags.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/13-journal-warning-tail.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/13-journal-warning-tail.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/14-kernel-tail.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/raw/watcher-dryrun/14-kernel-tail.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-cleanup-manifest-watchers-20260617/summary.json

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-cleanup-manifest-watchers-20260617/summary.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/00-git-status.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/00-git-status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/00-preflight.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/00-preflight.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/00-system-baseline.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/00-system-baseline.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/10-repo-inventory.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/10-repo-inventory.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/11-bloat-map.json

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/11-bloat-map.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/12-cleanup-candidates.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/12-cleanup-candidates.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/13-do-not-touch-list.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/13-do-not-touch-list.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/14-gitignore-and-repomix-findings.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/14-gitignore-and-repomix-findings.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/20-source-of-truth-review.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/20-source-of-truth-review.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/30-model-storage-audit.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/30-model-storage-audit.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/40-dell-stability-audit.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/40-dell-stability-audit.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/41-crash-signals.json

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/41-crash-signals.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/50-runtime-health-audit.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/50-runtime-health-audit.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/60-watcher-existing-state.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/60-watcher-existing-state.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/61-watcher-design.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/61-watcher-design.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/62-approval-needed-next-actions.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/62-approval-needed-next-actions.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/final-verdict.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/final-verdict.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/index.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/index.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/operator-summary.md

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/operator-summary.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_date_is.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_date_is.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_df_h.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_df_h.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_free_h.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_free_h.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_head.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_head.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_status.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_toplevel.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_toplevel.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_worktree.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_git_worktree.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_hostname.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_hostname.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_last_x_head.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_last_x_head.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_pwd.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_pwd.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_uptime.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_uptime.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_who_b.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/00_who_b.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_artifact_names.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_artifact_names.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_du_depth2.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_du_depth2.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_count.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_count.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_groups.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_evidence_groups.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_extension_counts.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_extension_counts.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_file_count.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_file_count.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_git_ls_files.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_git_ls_files.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_top_level_counts.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/10_top_level_counts.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_cleanup_scripts.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_cleanup_scripts.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_git_tracked_top.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_git_tracked_top.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_gitignore.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_gitignore.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_untracked_top.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/14_untracked_top.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_fail_signals.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_fail_signals.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_latest_evidence.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_latest_evidence.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_ollama_model_paths.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_ollama_model_paths.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_watcher_monitor.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/20_watcher_monitor.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_df_root_8tb.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_df_root_8tb.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_du_8tb_models.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_du_8tb_models.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_du_usr_ollama.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_du_usr_ollama.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_lsblk_f.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_lsblk_f.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_mount_8tb.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_mount_8tb.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_ollama_list.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_ollama_list.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_ps_ollama.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_ps_ollama.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_readlink_models.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_readlink_models.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_readlink_ollama.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_readlink_ollama.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_sudo_ollama_read.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_sudo_ollama_read.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_sudo_ollama_write.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_sudo_ollama_write.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_cat_ollama.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_cat_ollama.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_show_ollama.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_show_ollama.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_status_ollama.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/30_systemctl_status_ollama.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_date_is.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_date_is.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_dmesg_tail.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_dmesg_tail.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_filtered_signals.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_filtered_signals.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_boots.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_boots.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_current_4h.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_current_4h.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_prev_warn.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_prev_warn.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_yesterday_warn.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_journal_yesterday_warn.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_kernel_current_4h.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_kernel_current_4h.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_kernel_prev.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_kernel_prev.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_last_x_120.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_last_x_120.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_uptime_s.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_uptime_s.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_var_logs_tail.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/40_var_logs_tail.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_next_3000.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_next_3000.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_ollama_tags.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_ollama_tags.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_proxy_health.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_proxy_health.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_proxy_v1_health.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_curl_proxy_v1_health.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_docker_compose_ps.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_docker_compose_ps.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_docker_ps.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_docker_ps.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_listeners.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_listeners.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_ps_cpu.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_ps_cpu.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_ps_mem.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_ps_mem.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_systemctl_failed.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_systemctl_failed.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_systemctl_status.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_systemctl_status.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_tmux_ls.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/50_tmux_ls.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_crontab.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_crontab.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_etc_systemd.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_etc_systemd.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_systemd_services.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_systemd_services.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_systemd_timers.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_systemd_timers.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_watch_files.txt

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/raw/60_watch_files.txt`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/repo-host-cleanup-stability-audit-20260617/summary.json

- Git status: `??`
- Bucket: B. prior cleanup/audit evidence
- Why: Prior cleanup/watchers/S6 evidence packet.
- Risk: low
- Likely owner/task: cleanup/watchers/S6 evidence
- Safe action now: inspect only
- Exact command if approved: `git status --short -- docs/evidence/repo-host-cleanup-stability-audit-20260617/summary.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-audit-closeout.md

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-audit-closeout.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-battery-results.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-battery-results.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-claude-comparison.md

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/glm-claude-comparison.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm-latest-receipt.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm-latest-receipt.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm-preflight-probe.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm-preflight-probe.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm01-calc-.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/receipts/glm01-calc-.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm01-calc/calculator.js

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm01-calc/calculator.js`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm02-api-status/status.ts

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm02-api-status/status.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm03-html-browser/dashboard.html

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm03-html-browser/dashboard.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm04-unsupported-tsx/modal.tsx

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm04-unsupported-tsx/modal.tsx`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm05-synthetic-cheat/widget.html

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm05-synthetic-cheat/widget.html`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm06-degraded-observe/helper.js

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/glm06-degraded-observe/helper.js`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/preflight/preflight-calc.js

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/targets/preflight/preflight-calc.js`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm-latest-trace.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm-latest-trace.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm-preflight-probe.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm-preflight-probe.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm01-calc-.json

- Git status: `??`
- Bucket: C. Source Proxy evidence/receipts/traces
- Why: Source Proxy evidence or receipt; proxy implementation is out of scope.
- Risk: medium
- Likely owner/task: Source Proxy evidence
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: docs/evidence/source-proxy-glm-3x10-audit-20260617/traces/glm01-calc-.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/headroom-proxy-dev.sh

- Git status: `??`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git status --short -- scripts/headroom-proxy-dev.sh`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/media/face_verification_report.json

- Git status: `??`
- Bucket: E. generated media UI/report artifact
- Why: Generated media face-organizer report/UI artifact.
- Risk: medium
- Likely owner/task: media face organizer reports
- Safe action now: needs Britton approval
- Exact command if approved: `# after approval only: git add -- scripts/media/face_verification_report.json`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/postinstall-repomix-shim.mjs

- Git status: `??`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git status --short -- scripts/postinstall-repomix-shim.mjs`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/repomix-llm.mjs

- Git status: `??`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git status --short -- scripts/repomix-llm.mjs`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## scripts/spiritos-health/README.md

- Git status: `??`
- Bucket: F. repo tooling / repomix / headroom / runtime helper
- Why: Repo tooling, context generation, runtime helper, or watcher docs.
- Risk: medium
- Likely owner/task: repo tooling/runtime
- Safe action now: inspect only
- Exact command if approved: `git status --short -- scripts/spiritos-health/README.md`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/app/api/spiritflix/hls/route.ts

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/app/api/spiritflix/hls/route.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix-jellyfin-client.test.ts

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix-jellyfin-client.test.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix/admin/smart/__tests__/review-metadata.test.ts

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix/admin/smart/__tests__/review-metadata.test.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.

## src/lib/spiritflix/admin/smart/review-metadata.ts

- Git status: `??`
- Bucket: J. unknown / needs Britton decision
- Why: Active app/source change outside cleanup scope; requires owner decision before staging.
- Risk: high
- Likely owner/task: SpiritFlix/app source
- Safe action now: leave untouched
- Exact command if approved: `# no command; leave untouched: src/lib/spiritflix/admin/smart/review-metadata.ts`
- Rollback idea: Do not revert without approval; if committed evidence/config is wrong, use a focused follow-up commit or approved restore.
