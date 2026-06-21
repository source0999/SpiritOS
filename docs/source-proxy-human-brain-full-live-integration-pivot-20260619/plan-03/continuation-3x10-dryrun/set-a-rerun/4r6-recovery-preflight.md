# Stage 4R6 Recovery Preflight

- checked_at: 2026-06-20T21:56:46-04:00
- host: source-server
- pwd: /home/source/SpiritOS
- current HEAD: `e527563c266726ab97eb099e1a32032a9dd11064`
- staged files count: 0
- active runner PIDs: `3949106`
- pidfile value: `3949106`
- 4r6-validation.md exists: no
- scope confirmation: recovery is limited to Stage 4R6 Set A rerun artifacts and `_stage4r_runner.py`; only A2/A5/A9 may be rerun; no Set B/C, Stage 5, Plan 4, push, media/Jellyfin mutation, route replacement, or new orchestration/event engine.

## Dirty Tree

The worktree has pre-existing unrelated SpiritFlix/media/handoff modifications and untracked files. No files were staged, so there were no staged files outside the allowed path.

## Latest 4R6 Artifacts

- 2026-06-20 21:08:14 A2.json
- 2026-06-20 21:08:14 A2.md
- 2026-06-20 21:20:09 A5.json
- 2026-06-20 21:20:09 A5.md
- 2026-06-20 21:29:58 A9.json
- 2026-06-20 21:29:58 A9.md
- 2026-06-20 21:29:58 summary.json
- 2026-06-20 21:29:58 summary.md
- 2026-06-20 21:29:58 failure-buckets.md
- 2026-06-20 21:31:19 7-stage4r-verdict.md
- 2026-06-20 21:54:10 4r6-preflight.md
- 2026-06-20 21:54:10 4r6-structured-output-selftest.md
- 2026-06-20 21:54:10 4r6-structured-output-repair.md

## Latest Raw Evidence

- A2 latest recovery raw evidence began at 2026-06-20 21:54 and reached `A2.decision_packet.attempt1.raw.json` plus validation output at 2026-06-20 21:56.
- A5 latest completed raw evidence from the previous interrupted attempt ended at 2026-06-20 21:20.
- A9 latest completed raw evidence from the previous interrupted attempt ended at 2026-06-20 21:29.
- The recovery runner log contained only `RUN A2`, so the active attempt had not completed final validation.
