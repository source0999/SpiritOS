# Canonical Model/Video Ledger Spec

## Purpose

The canonical ledger is the single source of truth that Organizer, generated evidence pages, face enrollment, CRUD actions, audits, and SpiritFlix metadata adapters should consume. It must make absence and mismatch visible instead of collapsing everything into one count.

## Ledger grain

Primary grain: one row per canonical video candidate.

Optional rollups:
- one row per model/performer
- one row per source root
- one row per Jellyfin visible item
- one row per action receipt

## Per-video fields

- `canonical_video_id`: Stable identifier derived from resolved path, ingest receipt, sidecar lineage, and/or Jellyfin item ID. Do not rely only on basename.
- `basename`: Current video filename.
- `resolved_path`: Current resolved video path, if the file exists.
- `source_root_path`: Source root such as `/DATA/yes`.
- `model_folder_path`: Path under a model folder, if present.
- `jellyfin_item_id`: Jellyfin item ID if Jellyfin exposes the video.
- `spiritflix_visible`: Boolean for visible in SpiritFlix/Jellyfin lane.
- `organizer_visible`: Boolean for visible in Organizer page/report.
- `sidecar_path`: Face metadata sidecar path.
- `sidecar_freshness`: `fresh`, `stale_path`, `missing_source`, `path_mismatch`, `malformed`, `none`, or `unknown`.
- `media_ingest_receipt_path`: Path to `.media-ingest.json` or other upload/update receipt.
- `model_label`: Canonical display model label when known.
- `performer_id`: Known performer ID when known.
- `match_state`: `confirmed`, `needs_review`, `auto_candidate`, `denied`, `unknown`, `unscanned`, `faceless`, or `missing`.
- `match_evidence_type`: `face_rec`, `manual_confirmed`, `metadata_only`, `ocr_only`, `faceless_video`, `faceless_creator`, or `unknown`.
- `face_evidence_count`: Count of usable saved face evidence records supporting the match.
- `supporting_faces`: Array of supporting face records with crop path, frame path, similarity, quality, timestamp/frame index, and scan ID.
- `best_similarity`: Best face-rec similarity, if applicable.
- `visual_confirmed`: Boolean for Britton/user-confirmed visual match.
- `denied`: Boolean for explicit denial.
- `accepted_sample_count`: Count of accepted/enrolled samples for this model/video relationship.
- `faceless_video`: Boolean for this video marked faceless-from-creator.
- `faceless_creator`: Boolean inherited from the model/creator state.
- `needs_user_decision`: Boolean if Britton must decide.
- `sync_mismatch_reasons`: Array of reason codes such as `not_jellyfin_visible`, `missing_source_file`, `stale_sidecar`, `metadata_only`, `manual_only`, `unscanned`, `pending_3001_rebuild`, `pending_jellyfin_refresh`, `duplicate_basename`, or `path_conflict`.
- `last_scan_at`: Timestamp of last face-rec scan.
- `last_crud_action_at`: Timestamp of last accept/reject/remove/confirm/deny/faceless/merge/rescan action.

## Count types

The UI and reports must name these counts explicitly:

- `source_files_count`: Physical video files under the source root that match the query/model scope.
- `model_folder_files_count`: Physical video files under the model folder.
- `sidecar_records_count`: Sidecar records found, even if stale.
- `jellyfin_visible_item_count`: Items exposed by Jellyfin API.
- `spiritflix_visible_model_count`: Items grouped under the model in SpiritFlix visible UI.
- `enrolled_accepted_screen_count`: Accepted/enrolled face sample count.
- `face_rec_supported_video_count`: Videos with saved usable face-rec support above threshold.
- `metadata_manual_only_video_count`: Videos associated by folder/manual/metadata/OCR but not by face-rec.
- `faceless_video_count`: Videos marked faceless-from-creator.

## Evidence-type rules

- `face_rec` requires saved face-rec evidence, usable face quality, and thresholded similarity.
- `manual_confirmed` is a real decision but is not face-rec confidence.
- `metadata_only` and `ocr_only` can explain a relationship but must not raise face-rec confidence or enrollment readiness.
- `faceless_video` can belong to a model while being excluded from face-rec recommendation panels.
- `faceless_creator` means the model/creator is maintained outside normal face-enrollment pressure.
- `unknown` must remain unknown until evidence exists.

## Sava required ledger questions

- Why does Organizer report 7 model-folder matches while SpiritFlix 3001 shows 9 visible videos?
- Why does generated Sava evidence report 13 candidate videos while model index reports 11?
- Where is 6513.mp4 now, and what is its evidence bucket?
- What is the other mismatched video, and is it missing from Organizer, missing from SpiritFlix, hidden by Jellyfin, stale-sidecar-only, or counted under a different label?

## Adapter contract

Consumers must read the ledger or a ledger-derived projection:

- Organizer enrolled page.
- Organizer enrollment queue.
- Organizer verification/organization page.
- Known DB audit.
- SpiritFlix face metadata API.
- SpiritFlix model grouping and count labels.
- CRUD/action handlers.
- Media ingest/update closeout.
- 3001 sync/restart proof.
