# Media Face Organizer Source-of-Truth Plan - ARPA Closeout

Date: 2026-06-14

This is a docs-only ARPA planning run for Media Face Organizer source-of-truth repair, face enrollment UX, faceless workflow, and SpiritFlix 3001 sync repair.

No implementation was performed. No code, media files, generated organizer pages, sidecars, known performer DB files, embeddings, `/tmp/spiritos-spiritflix-stable-3001` files, git branch, git stage, git commit, git push, stash, reset, checkout, or clean operation was touched.

STOP: awaiting Britton approval before implementation.

## Files created

- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/index.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/plan.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/source-of-truth-ledger-spec.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/sync-contract.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/sava-golden-case-acceptance.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/faceless-workflow-spec.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/ui-ux-cleanup-spec.md`
- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/execution-handoff.md`

## Files inspected

- `scripts/media/face_organizer.py`
- `scripts/media-ingest-worker.mjs`
- `src/app/api/spiritflix/face-metadata/route.ts`
- `src/components/spiritflix/SpiritFlixHome.tsx`
- `src/lib/spiritflix-jellyfin-client.ts`
- `scripts/media/known_performers/`
- `scripts/media/face_enrolled_performers.json`
- `scripts/media/face_enrollment_queue.json`
- `scripts/media/model_index.json`
- `scripts/media/known_db_audit.json`
- `docs/evidence/media/face-organizer-plan-8-review-ui-correction-audit-20260613.md`
- `docs/evidence/media/face-organizer-plan-9-enrollment-queue-route-20260613.md`

Generated HTML/JSON files were inspected only as evidence. They were not edited.

## Current evidence summary

- `scripts/media/face_organizer.py` currently renders enrolled video match review with separate model-folder, missing-source, confirmed outside-library, new 80%+ match, and pending-decision buckets.
- `scripts/media/face_organizer.py` has a performer-level `mark_performer_faceless` action, but the plan still needs video-level faceless state, undo/unmark contracts, and UI placement across queue/enrolled/organization flows.
- `src/app/api/spiritflix/face-metadata/route.ts` reads sidecars from media roots and generated organizer files (`known_performers/index.json`, `face_enrolled_performers.json`, `model_index.json`) and maps only the Jellyfin items provided by SpiritFlix into status labels.
- `src/lib/spiritflix-jellyfin-client.ts` requests face metadata only for currently visible Jellyfin items, which means SpiritFlix visibility is not equivalent to source files, sidecars, model-folder files, or organizer rows.
- `src/components/spiritflix/SpiritFlixHome.tsx` has its own model alias map and displays `indexedCount` videos from visible Jellyfin grouping, while it can also show organizer candidate counts from face metadata.
- `scripts/media-ingest-worker.mjs` moves stable inbox/library files into media output paths and writes media ingest receipts, so upload/update repair must include receipt and final-path provenance in the ledger.
- Prior Plan 8 evidence says the known face DB was effectively empty beyond Sava Schultz at that time: registry/model index had 37 performers/models, known performer records had 1, and embeddings had shape `[1, 512]`.
- Prior Plan 9 evidence says no production enrollment was performed and generated queue/report pages plus review artifacts were created, while Sava's existing embedding row remained intact.
- Current `face_enrolled_performers.json` evidence for Sava Schultz reports `candidate_videos: 13`, `enrolled_samples: 14`, `recommended_crops: 10`, `recommended_stills: 45`, `library_video_matches: 7`, `missing_video_matches: 0`, `auto_video_matches: 0`, and `pending_video_matches: 1`.
- Current `model_index.json` evidence for Sava Schultz reports `video_count: 11` and `assignment_status: local-auto`.
- Current `face_enrolled_performers.json` references `/DATA/yes/6513.mp4` for Sava in generated evidence, but this docs-only run did not confirm 6513.mp4 as Sava by face recognition and did not run a new scan.

## Commands run

```powershell
Get-Content -LiteralPath 'C:\Users\smith\.codex\attachments\40f4cec9-0beb-474a-8b51-09e0c661cf6c\pasted-text.txt'
Select-String -Path 'C:\Users\smith\.codex\memories\MEMORY.md' -Pattern 'SpiritFlix|Jellyfin|media-ingest|Z:|SpiritOS' -Context 2,2
git status --short
Get-ChildItem -LiteralPath 'scripts\media' -Force | Select-Object Name,Length,LastWriteTime
Get-ChildItem -LiteralPath 'docs\evidence' -Force | Select-Object Name,LastWriteTime | Sort-Object LastWriteTime -Descending | Select-Object -First 30
rg -n "Sava|6513|face_enrolled|known_db|faceless|recommended|Already in model folder|SpiritFlix|3001" scripts/media/face_organizer.py scripts/media-ingest-worker.mjs src/app/api/spiritflix/face-metadata/route.ts src/components/spiritflix/SpiritFlixHome.tsx src/lib/spiritflix-jellyfin-client.ts
git status --short --untracked-files=all
Get-Content -LiteralPath 'src\app\api\spiritflix\face-metadata\route.ts' -TotalCount 260
Get-Content -LiteralPath 'scripts\media\face_organizer.py' | Select-Object -Skip 6070 -First 95
Get-Content -LiteralPath 'scripts\media\face_organizer.py' | Select-Object -Skip 6840 -First 120
Get-Content -LiteralPath 'scripts\media-ingest-worker.mjs' -TotalCount 260
Get-Content -LiteralPath 'src\app\api\spiritflix\face-metadata\route.ts' | Select-Object -Skip 220 -First 120
Get-Content -LiteralPath 'src\components\spiritflix\SpiritFlixHome.tsx' | Select-Object -Skip 80 -First 80
Get-Content -LiteralPath 'src\components\spiritflix\SpiritFlixHome.tsx' | Select-Object -Skip 880 -First 130
Get-Content -LiteralPath 'src\lib\spiritflix-jellyfin-client.ts' | Select-Object -Skip 250 -First 180
Get-ChildItem -LiteralPath 'scripts\media\known_performers' -Force | Select-Object Name,Length,LastWriteTime
$path='scripts\media\face_enrolled_performers.json'; $json=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json; $json.groups | Where-Object { $_.name -match 'Sava' -or $_.slug -match 'sava' } | Select-Object name,slug,candidate_videos,@{n='enrolled_samples';e={@($_.enrolled_samples).Count}},@{n='recommended_crops';e={@($_.recommended_crops).Count}},@{n='recommended_stills';e={@($_.recommended_stills).Count}},@{n='library_video_matches';e={@($_.library_video_matches).Count}},@{n='missing_video_matches';e={@($_.missing_video_matches).Count}},@{n='auto_video_matches';e={@($_.auto_video_matches).Count}},@{n='pending_video_matches';e={@($_.pending_video_matches).Count}} | Format-List
$path='scripts\media\model_index.json'; $json=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json; $json.models | Where-Object { $_.name -match 'Sava' -or $_.slug -match 'sava' } | ConvertTo-Json -Depth 6
$paths=@('scripts\media\face_enrolled_performers.json','scripts\media\face_enrollment_queue.json','scripts\media\known_db_audit.json'); foreach($path in $paths){ $json=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json; Write-Output "--- $path"; if($json.groups){ Write-Output "groups=$(@($json.groups).Count)" }; if($json.performers){ Write-Output "performers=$(@($json.performers).Count)" }; if($json.summary){ $json.summary | Format-List | Out-String | Write-Output } }
Get-ChildItem -LiteralPath 'docs\evidence\media' -Recurse -Force | Select-Object FullName,Length,LastWriteTime | Sort-Object LastWriteTime -Descending | Select-Object -First 30
rg -n "6513|Sava Schultz|sava-schultz|savaschultz|missing source|model-folder|confidence_estimate|recommended_stills|library_video_matches|pending_video_matches" scripts/media/face_enrolled_performers.json scripts/media/face_enrollment_queue.json scripts/media/known_db_audit.json scripts/media/face_organizer.py docs/evidence/media
Get-Content -LiteralPath 'docs\evidence\media\face-organizer-plan-9-enrollment-queue-route-20260613.md'
Get-Content -LiteralPath 'docs\evidence\media\face-organizer-plan-8-review-ui-correction-audit-20260613.md'
$path='scripts\media\face_enrolled_performers.json'; $json=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json; $g=$json.groups | Where-Object { $_.name -eq 'Sava Schultz' }; $g | Select-Object name,slug,candidate_videos,recommendations_refreshed_at,confidence_estimate | ConvertTo-Json -Depth 8
Get-ChildItem -LiteralPath 'docs\evidence\media-face-organizer-source-of-truth-plan-20260614' -Force | Select-Object Name,Length
rg -n "STOP: awaiting Britton approval|No implementation was performed|Sava Schultz is the golden case|6513.mp4|Phase 0 / Increment 0.1" docs/evidence/media-face-organizer-source-of-truth-plan-20260614
git status --short --untracked-files=all -- docs/evidence/media-face-organizer-source-of-truth-plan-20260614
git diff --name-only -- docs/evidence/media-face-organizer-source-of-truth-plan-20260614
Get-Content -LiteralPath 'docs\evidence\media-face-organizer-source-of-truth-plan-20260614\execution-handoff.md'
```

## Git status summary

Full repository `git status` over `Z:\` timed out during this docs-only run. Scoped status for this plan folder showed exactly the eight new untracked docs files under:

- `docs/evidence/media-face-organizer-source-of-truth-plan-20260614/`

Scoped `git diff --name-only -- docs/evidence/media-face-organizer-source-of-truth-plan-20260614` was empty because the created docs are untracked, not modified tracked files.

## Stop

Do not implement. Do not patch source code. Do not mutate media or generated organizer artifacts. Stop and ask Britton for approval before implementation.
