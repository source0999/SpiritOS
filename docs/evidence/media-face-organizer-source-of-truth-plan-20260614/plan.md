# PLAN 10 Pivot Workflow - Media Face Organizer Source of Truth

## Plan goal

Repair the Media Face Organizer and SpiritFlix sync process around a canonical model/video ledger so organizer UI, face enrollment, CRUD actions, faceless handling, generated evidence pages, and the SpiritFlix 3001 lane all describe the same state with clear count semantics.

Sava Schultz is the golden case before generalizing. The plan must prove Sava first, stop, and ask Britton before applying the logic to all other models or the whole organization process.

## Non-goals

- Do not implement during this docs-only run.
- Do not move, rename, delete, or organize videos during planning.
- Do not edit media files, sidecars, known performer DB files, embeddings, generated organizer pages, or `/tmp/spiritos-spiritflix-stable-3001`.
- Do not claim 6513.mp4 is confirmed Sava by face recognition unless a later approved scan crosses the planned threshold with saved face evidence.
- Do not treat metadata, manual, OCR, folder, filename, or creator-handle evidence as face-rec confidence.
- Do not assume Organizer counts and SpiritFlix visible counts must match.
- Do not generalize beyond Sava without Britton approval.

## Current truth

- Face Organizer source is `/DATA/yes`; the review server is expected on port `8765`.
- SpiritFlix 3001 working copy is `/tmp/spiritos-spiritflix-stable-3001`; live lane is `http://10.0.0.186:3001/spiritflix`.
- SpiritFlix 3001 shows what Jellyfin exposes in the visible library view. That can lag or differ from source files, sidecars, and model-folder files.
- Current organizer generated Sava evidence reports 13 candidate videos, 14 accepted/enrolled samples, 10 recommended crops, 45 recommended stills, 7 model-folder matches, 0 missing-source matches, 0 new auto matches, and 1 pending video match.
- Current model index reports Sava `video_count: 11`.
- The user's observed SpiritFlix 3001 Sava lane count is 9 videos, while organizer/model/generated counts have shown 7, 10, 11, and 13 depending on surface and time.
- Current code has partial dedupe/resolve behavior and partial UI labeling, but the plan must verify whether every API, UI, generated page, and action consumes the same canonical result.
- Current code has a performer-level faceless action but not a complete video-level and creator-level faceless workflow with undo, receipts, and recommendation filtering.

## Known failure modes

- Counts are compared without naming the count type.
- Stale sidecars still imply `auto` or model ownership with 0 supporting faces.
- Metadata/manual/OCR-only evidence appears near face-rec-supported rows and looks stronger than it is.
- Faceless frames appear in recommended enrollment improvements.
- Low-confidence rows crowd the useful decision queue.
- Accepted screens and recommendations are mixed together, making the next action unclear.
- Sava's original/reuploaded 6513.mp4 path and 3001 visibility are not proved from one ledger row.
- SpiritFlix face metadata is requested only for visible Jellyfin items, so it cannot explain absent source/model-folder videos by itself.
- Frontend/API changes in source repo are not live on 3001 until copied to `/tmp/spiritos-spiritflix-stable-3001`, built, and port 3001 restarted.

## Phase 0 - Baseline audit and truth map

### Increment 0.1: Read-only current-state audit

Inspect source files, generated JSON, known performer DB summaries, existing sidecars, model folder files, media ingest receipts, Jellyfin-visible items, and SpiritFlix 3001 visible lane without modifying them.

Checks:
- Command log saved.
- Files inspected listed.
- No source, media, sidecar, DB, embedding, generated page, or 3001 working-copy edits.

### Increment 0.2: Sava count reconciliation

For Sava, reconcile source files count, model folder files count, sidecar records count, Jellyfin visible item count, SpiritFlix visible model count, enrolled accepted screen count, face-rec-supported video count, metadata/manual-only video count, and faceless video count.

Checks:
- Every count has a named type.
- Every count has file/API evidence.
- Mismatches are explained as reasons, not guessed away.

### Increment 0.3: Locate missing/mismatched videos

Locate 6513.mp4 and the other missing/mismatched video across `/DATA/yes`, `/DATA/yes/models/sava-schultz`, sidecars, media ingest receipts, generated organizer JSON, Jellyfin item IDs, and SpiritFlix visible items.

Checks:
- 6513.mp4 row exists in the ledger with path, sidecar, receipt, Jellyfin, and SpiritFlix fields.
- 6513.mp4 is not auto-confirmed as Sava by face recognition unless later evidence meets threshold.
- The second mismatch is named by basename/path/Jellyfin item ID or marked as unresolved with the exact missing evidence.

### Increment 0.4: Produce baseline evidence and stop

Write baseline evidence and ask Britton before implementation.

Checks:
- Phase 0 closeout includes before counts and evidence paths.
- STOP recorded before Phase 1 implementation.

## Phase 1 - Canonical ledger design and adapter boundaries

### Increment 1.1: Define canonical video/model ledger builder

Design a read-first builder that emits one row per canonical video and optional model rollups.

Checks:
- Ledger includes the fields in `source-of-truth-ledger-spec.md`.
- Ledger can represent absence from Jellyfin and absence from Organizer separately.

### Increment 1.2: Identify current functions that must consume it

Map current organizer generation, API routes, SpiritFlix UI grouping, review actions, and report generation to the ledger.

Checks:
- Each consumer is listed with old source and planned new source.
- No count is computed ad hoc outside the ledger unless justified.

### Increment 1.3: Define stale sidecar handling and count semantics

Classify sidecars as fresh, stale-path, missing-source, mismatched-video, manual-only, metadata-only, face-rec-supported, faceless-video, or faceless-creator.

Checks:
- Stale sidecars do not silently count as current face-rec support.
- Metadata/manual-only rows cannot raise face-rec confidence.

### Increment 1.4: Tests/specs for ledger output

Plan fixture-based tests using Sava and at least one missing/faceless/stale-sidecar case.

Checks:
- Test names and expected outputs are documented before code changes.

## Phase 2 - CRUD sync contract implementation plan

### Increment 2.1: Map all user actions

Map accept/reject/remove screen, confirm/deny video, faceless video/model toggles, merge labels, rescan, ingest/upload/update, regenerate pages, and sync 3001.

Checks:
- Every action has preconditions, updated layers, receipts, backups, and UI refresh behavior.

### Increment 2.2: Define receipt/backup behavior

Define backup before destructive or irreversible state changes, plus append-only receipts for decisions.

Checks:
- Reset/remove actions require backup paths.
- Receipts identify actor, timestamp, old state, new state, and source evidence.

### Increment 2.3: Define regeneration and 3001 sync behavior

Define when generated organizer JSON/HTML must be refreshed and when SpiritFlix 3001 must be copied, built, and restarted.

Checks:
- Source repo edits and 3001 live state are verified separately.

### Increment 2.4: Tests/specs

Plan focused unit/schema tests for action outputs and ledger mutation contracts.

Checks:
- Tests cover success, undo, stale sidecar, faceless, and 3001 not-yet-synced states.

## Phase 3 - Sava enrollment reset and quality repair

### Increment 3.1: Backup current Sava accepted screens/embeddings/state

Before any reset, back up accepted screen records, crop/still paths, known performer DB files, embeddings, registry, model index, sidecars, and generated JSON.

Checks:
- Backup manifest is saved before state mutation.

### Increment 3.2: Reset stale/low-quality accepted samples

Reset only after approval and backup. Do not remove useful samples without receipt.

Checks:
- Before/after accepted sample counts and deleted/kept reasons recorded.

### Increment 3.3: Rescan linked videos

Rescan linked Sava source/model-folder videos with bounded scope.

Checks:
- Scan output saves faces, quality data, source video, and similarity evidence.

### Increment 3.4: Auto-add >=80% useful quality samples

Auto-add screens only when match confidence is at least 80% and face quality passes.

Checks:
- Useful additional screens beyond the initial five can be added.
- Auto-add receipt includes threshold and quality reason.

### Increment 3.5: Queue only 50%-75% useful uncertain samples

Show uncertain useful screens for Britton confirmation, not low-value frames.

Checks:
- 50%-75% items are in "Needs your confirmation".
- Under 50% items are hidden from primary recommendation UI.

### Increment 3.6: Verify 6513.mp4 bucket honestly

Put 6513.mp4 in the correct ledger bucket: face-rec-supported, manual-confirmed, metadata-only, OCR-only, faceless, unknown, denied, or missing.

Checks:
- Latest known handoff truth is preserved: 6513.mp4 had 11 faces but best similarity only 0.4608, so it is not confirmed Sava by face recognition.

### Increment 3.7: Sava closeout and ask Britton before generalization

Close Sava with before/after counts, ledger rows, screenshots/HTML paths if generated, and SpiritFlix 3001 visibility proof if implementation includes 3001 sync.

Checks:
- Stop and ask Britton before Phase 4 all-model or generalization work.

## Phase 4 - Faceless video/creator workflow

### Increment 4.1: Add state model

Define faceless video and faceless creator state separately.

Checks:
- Faceless videos can still belong to a model via manual, metadata, or creator-folder evidence.

### Increment 4.2: Add actions

Plan mark/unmark video faceless and mark/unmark model faceless actions.

Checks:
- Undo/unmark actions and receipts are symmetrical.

### Increment 4.3: Remove faceless frames from face-rec recommendations

Filter faceless frames out of primary enrollment recommendations.

Checks:
- Faceless items appear only in faceless review/debug contexts.

### Increment 4.4: Verify undo and receipts

Verify state can be restored from UI/API actions.

Checks:
- Receipts and generated pages agree after regeneration.

## Phase 5 - SpiritFlix 3001 sync and count semantics

### Increment 5.1: Make 3001 consume canonical metadata

Plan API/adapter changes so SpiritFlix receives ledger-derived status and count types for visible items.

Checks:
- SpiritFlix cannot imply an invisible source file is absent from the organizer.

### Increment 5.2: Show visible count vs source/model count clearly

Separate visible Jellyfin count from source/model/face-rec counts.

Checks:
- UI labels prevent "7 vs 9" from becoming an unexplained contradiction.

### Increment 5.3: Confirm upload/update actions reflect in 3001

After approved implementation, copy source changes to `/tmp/spiritos-spiritflix-stable-3001`, build, restart port 3001, and verify.

Checks:
- Source repo file contents, built sidecar contents, and live 3001 behavior are all verified.

### Increment 5.4: Verify no stale 3001 mismatch

Reconcile 3001 with ledger/Jellyfin exposure after restart.

Checks:
- Remaining mismatch reasons are explicit.

## Phase 6 - Organizer UX cleanup

### Increment 6.1: Primary workflow simplification

Default UI sections become Needs decision, Auto accepted/auto added, Sync mismatch, Faceless review, Accepted screens dropdown, and Debug/raw evidence drawer.

Checks:
- Primary workflow shows only next useful decisions.

### Increment 6.2: Accepted screens dropdown

Move accepted screens out of the recommendation stream.

Checks:
- Accepted samples remain inspectable without crowding recommendations.

### Increment 6.3: Recommendation filtering

Filter faceless, low-confidence, stale, and non-useful recommendations from primary UI.

Checks:
- Under 50% and faceless frames are hidden from primary recommendations.

### Increment 6.4: Debug drawers for raw evidence

Keep raw metadata, manual-only, stale, and OCR evidence available but collapsed.

Checks:
- Debug evidence is not presented as face-rec proof.

### Increment 6.5: Mobile/narrow layout check

Verify the organizer remains usable at mobile/narrow widths.

Checks:
- Buttons and text do not overlap.

## Phase 7 - Generalization approval gate

### Increment 7.1: Sava closeout proof

Collect Sava closeout proof across ledger, organizer, generated pages, and SpiritFlix 3001 if touched.

Checks:
- Britton can compare before/after counts and path evidence.

### Increment 7.2: Ask Britton whether to generalize to all models

No all-model execution without explicit Britton approval.

Checks:
- Approval is recorded before any generalization.

## Phase closeout requirements

- Commands run.
- Files inspected or changed.
- Evidence paths.
- Before/after counts when state changes.
- Tests/checks run.
- Known limitations.
- Approval gates reached.

## Plan closeout requirements

- Sava golden case completed first.
- Canonical ledger documented and consumed by intended surfaces.
- CRUD actions synchronize layers or report pending sync clearly.
- Faceless video/creator workflow works with undo and receipts.
- Organizer UI default flow is simplified.
- SpiritFlix 3001 live state is separately verified after any implementation changes.
- Britton approval is obtained before all-model generalization.

## Stop points requiring Britton approval

- Before any implementation.
- After Phase 0 baseline audit.
- Before resetting Sava accepted screens.
- Before marking a video or model as faceless in real state.
- Before changing known performer DB or embeddings.
- Before copying/building/restarting the 3001 sidecar.
- After Sava golden case closeout and before all-model generalization.
