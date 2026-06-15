# NEXT CHAT HANDOFF - PLAN 10 EXECUTION

You are working in the SpiritOS repo.

Repo paths:
- Dell/Linux repo: `/home/source/SpiritOS`
- Windows mapped repo: `Z:\`
- Face Organizer source: `/DATA/yes`
- Face Organizer server port: `8765`
- SpiritFlix 3001 working copy: `/tmp/spiritos-spiritflix-stable-3001`
- SpiritFlix sidecar lane: `http://10.0.0.186:3001/spiritflix`
- Face Organizer enrolled page: `http://100.111.32.31:8765/face_enrolled_performers.html`
- Face Organizer queue page: `http://100.111.32.31:8765/face_enrollment_queue.html`

Read this plan folder first:

`docs/evidence/media-face-organizer-source-of-truth-plan-20260614/`

Read these files before any implementation:
- `index.md`
- `plan.md`
- `source-of-truth-ledger-spec.md`
- `sync-contract.md`
- `sava-golden-case-acceptance.md`
- `faceless-workflow-spec.md`
- `ui-ux-cleanup-spec.md`

Use pivot workflow:
- Plan.
- Phase.
- Increment.
- Check/evidence.
- Phase closeout.
- Plan closeout.
- Stop and ask before moving forward when required.

Start with Phase 0 / Increment 0.1 only:

Phase 0 - Baseline audit and truth map.

Increment 0.1:
- Run read-only current-state audit.
- Inspect current source files, generated JSON/HTML evidence, sidecars, known performer DB summaries, Sava paths, Jellyfin/SpiritFlix visible items, and media ingest receipts.
- Do not edit code.
- Do not edit media files.
- Do not move/delete/rename videos.
- Do not edit sidecars.
- Do not edit known performer DB.
- Do not edit embeddings.
- Do not edit generated HTML/JSON pages.
- Do not edit `/tmp/spiritos-spiritflix-stable-3001`.
- Do not commit, push, stage, reset, checkout, stash, clean, or branch.
- No long face-rec scans.
- No live media organization run.
- No heavy report regeneration.

Required Phase 0 outputs:
- Exact commands run.
- Files inspected.
- Sava baseline counts by named count type.
- Count reconciliation for Organizer 7 vs SpiritFlix 3001 9.
- Location proof for 6513.mp4.
- Location proof for the other missing/mismatched video.
- Evidence bucket for 6513.mp4 without claiming face-rec confirmation unless thresholded saved face evidence exists.
- Current mismatch reasons.
- Stop after Phase 0 baseline audit and ask Britton before implementation.

Hard requirements:
- Sava Schultz is the golden case before generalization.
- Do not generalize to all models until Sava closeout is complete and Britton explicitly approves.
- Do not skip directly to all-model generalization.
- Run checks before each next increment.
- Do not treat metadata/manual/OCR-only evidence as face-rec confidence.
- Keep faceless videos out of face-rec recommendation panels.
- If later implementation changes source repo frontend/API, copy to `/tmp/spiritos-spiritflix-stable-3001`, build, restart port 3001, and verify live 3001 separately.

Stop point:

After Phase 0 baseline audit, stop and ask Britton:

"Phase 0 baseline audit is complete. Do you approve moving into Phase 1 implementation planning/code changes for the Sava-only golden case?"
