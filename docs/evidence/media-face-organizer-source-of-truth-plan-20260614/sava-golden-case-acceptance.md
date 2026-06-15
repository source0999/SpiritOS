# Sava Golden Case Acceptance

## Purpose

Sava Schultz is the proof case. Nothing should be generalized to all models until Sava's source, organizer, enrollment, faceless handling, and SpiritFlix 3001 count semantics are repaired and Britton approves moving forward.

## Baseline audit requirements

- Answer why Organizer says 7 while SpiritFlix 3001 shows 9.
- Explicitly locate 6513.mp4.
- Explicitly locate the other missing/mismatched video.
- Record source files count, model folder files count, sidecar records count, Jellyfin visible item count, SpiritFlix visible Sava count, enrolled accepted screen count, face-rec-supported video count, metadata/manual-only video count, and faceless video count.
- Preserve the known truth that 6513.mp4 is not confirmed Sava by face recognition from the latest handoff: the latest scan found 11 faces but best similarity was only 0.4608.
- Do not use metadata/manual/OCR-only evidence as face-rec confidence.

## Required 6513.mp4 behavior

- 6513.mp4 must have a ledger row with basename, resolved path, source root, model folder path if present, sidecar path, media ingest receipt path if present, Jellyfin item ID if visible, SpiritFlix visibility, Organizer visibility, evidence type, best similarity, supporting faces, and mismatch reasons.
- 6513.mp4 must not be auto-confirmed as Sava by face-rec unless a later approved scan crosses the planned threshold with saved face evidence.
- If it is assigned to Sava only by manual/metadata/folder/OCR evidence, it must be labeled that way.
- If it is not visible in 3001, the closeout must explain whether Jellyfin has not exposed it, it is in another folder/library, it is missing from source, it has a stale sidecar, or it is hidden by label mismatch.

## Accepted screen reset requirements

- Reset accepted screens only after backup.
- Backup must include known performer DB files, embeddings, performer map, registry/model index, current Sava accepted sample records, crop/still paths, generated Sava JSON, and any relevant sidecars.
- Use best high-quality source frames from linked videos, not stale low-quality old samples.
- Pick the 5 best initial accepted screens.
- Do not stop at 5 if additional screens are useful and high quality.
- Auto-add additional useful screens only when match confidence is at least 80% and face quality passes.
- Queue useful uncertain screens around 50%-75% for Britton confirmation.
- Hide under 50% matches and faceless frames from the primary recommendation UI except in debug/faceless views.

## UI acceptance

- Accepted screens appear in a dropdown/details area, not mixed with recommendations.
- Recommendation panel shows only useful next decisions.
- "Recommended screens" should become "Needs your confirmation" or "Suggested enrollment improvements" only when the panel contains useful decisions.
- "Already in model folder" must split into face-rec-supported, metadata/manual-only, and faceless/manual buckets.
- "Confidence" must be renamed or clarified as "Enrollment readiness" unless there is a calibrated confidence model.

## Enrollment readiness definition

Enrollment readiness is an estimate, not fake certainty. It should consider:

- Accepted sample count.
- Useful source video coverage.
- Embedding rows.
- Face quality.
- Match consistency.
- Pending uncertainty.
- Faceless and metadata/manual-only exclusions.

Readiness must not be inflated by metadata-only, manual-only, OCR-only, or faceless evidence.

## Closeout proof

The Sava closeout must show:

- Before/after counts by named count type.
- Ledger rows for every Sava candidate video.
- 6513.mp4 evidence bucket and path proof.
- The other mismatch evidence bucket and path proof.
- Accepted screen backup path.
- Accepted screen before/after count.
- Auto-added screen receipts.
- Queued uncertain screen receipts.
- Hidden/rejected/low-confidence/faceless counts.
- Generated organizer evidence paths if regenerated.
- SpiritFlix 3001 visible proof if implementation touched 3001.
- STOP and ask Britton before generalizing.
