# Face Organizer Full System Integration Handoff

Copy this into a new Codex chat to start Plan 0 only.

```text
You are working in the SpiritOS repo.

Repo paths:
- Windows: Z:\
- Linux/Dell: /home/source/SpiritOS
- Main script: scripts/media/face_organizer.py
- Media source currently used by artifacts: /DATA/yes
- Current report: scripts/media/face_verification_report.html
- Current registry: scripts/media/performer_verification.json
- Current model index: scripts/media/model_index.json
- Known face DB: scripts/media/known_performers/

Read first:
- docs/plans/media/face-organizer-full-system-integration-20260613.md
- scripts/media/face_organizer_system_diag.md
- scripts/media/face_organizer_context_packet.xml

This handoff authorizes Plan 0 only.
Do not start Plan 1.
Do not implement code changes.
Do not move, rename, delete, or reorganize media.
Do not run scan/verify/organize apply commands.
Do not do internet face recognition.
Do not compare local video frames, face crops, or embeddings against Yandex or web images.
Do not download adult media, web images, thumbnails, or leaked content.
Do not use repost/leak hosts as final identity authority.
Do not infer legal names, private identity, age, location, or other personal data.
Only use public/stage/profile handles and visible text evidence.
No git branch, stash, reset, checkout, clean, commit, push, or stage.

Plan 0 - Dell report refresh and current-state lock

Goal:
Refresh the stale Dell report and capture exact current system state before any integration.

Increment 0.1 - Inspect current state.
- Inspect repo status without mutation.
- Inspect current media artifacts and timestamps.
- Inspect current report timestamp and whether `Text verification links` render.
- Inspect `known_performers` DB count and embedding rows.
- Inspect registry/model index counts.
- Record whether SSH/Dell access is available.
- Do not modify files in this increment.

Increment 0.2 - Regenerate report on Dell only if access is available.
Allowed diagnostic command:

cd /home/source/SpiritOS
. .venv-face-organizer/bin/activate
python scripts/media/face_organizer.py --source /DATA/yes --report --ctx-id -1

This report command is allowed because it refreshes only the HTML report. Do not run scan, verify-performers, organize, or any --apply command.

Increment 0.3 - Verify manual text verification links render.
- Check report HTML for `Text verification links`.
- Check `407017_720p.mp4` for Yandex/Coomer/PimpBunny text-search links if its OCR hints remain present.
- Verify links are text-search URLs only.
- Do not perform web face recognition or image comparison.
- Do not download web images/media.

Increment 0.4 - Closeout.
- Report commands run.
- Report current counts and timestamps.
- Report whether the regenerated report contains manual text verification links.
- Report any blocker such as SSH auth failure.
- State whether Plan 0 is PASS or NEEDS_FIX.

Stop after Plan 0 closeout.
Ask Britton before Plan 1.
Do not continue into Plan 1.

Required final response:
- Files modified, if any.
- Evidence commands run.
- Key findings.
- Clear statement: "No implementation was performed."
- Clear next step: "Britton must approve Plan 1 before schema work begins."
```
