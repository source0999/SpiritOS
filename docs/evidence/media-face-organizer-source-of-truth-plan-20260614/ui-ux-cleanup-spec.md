# Organizer UI/UX Cleanup Spec

## Purpose

The Organizer UI should become decision-first. Debug evidence, raw report details, stale sidecars, metadata-only clues, and low-value/faceless recommendations should not dominate the primary workflow.

## Default UI sections

- Needs decision.
- Auto accepted / auto added.
- Sync mismatch.
- Faceless review.
- Accepted screens dropdown.
- Debug / raw evidence drawer.

## Hide by default

- Metadata/manual-only rows pretending to be face-rec evidence.
- 0-support stale rows.
- Faceless stills in recommended screens.
- Low-confidence non-useful recommendations.
- Huge raw report details from the primary workflow.
- OCR-only clues unless the user opens debug/details.

## Label changes

### Already in model folder

Replace with separate buckets:
- Face-rec-supported model-folder videos.
- Metadata/manual-only model-folder videos.
- Faceless/manual model-folder videos.
- Stale/missing-source sidecars.

### Recommended screens

Use:
- "Needs your confirmation" for uncertain useful 50%-75% items.
- "Suggested enrollment improvements" for useful high-quality additions.

Do not show this panel when it contains only faceless, low-confidence, stale, or already-accepted frames.

### Confidence

Use "Enrollment readiness" unless a calibrated model exists.

Readiness copy must say it is an estimate based on accepted samples, video coverage, embedding rows, quality, match consistency, and pending uncertainty.

## Primary Sava layout

For Sava, the main view should show:

- Sava model header with named count types.
- Needs decision count.
- Sync mismatch count.
- Face-rec-supported videos count.
- Metadata/manual-only videos count.
- Faceless videos count.
- Accepted screens dropdown.
- Useful recommendation/confirmation panel.
- Debug drawer with raw sidecars, OCR, stale records, and source JSON links.

## Recommendation filtering

- Auto-add only >=80% plus quality pass.
- Queue 50%-75% useful uncertain samples.
- Hide under 50% from primary recommendations.
- Hide faceless frames from face-rec recommendations.
- Hide duplicate/stale rows unless they create a sync mismatch decision.

## Sync mismatch UX

Sync mismatch section should answer:

- Is the file physically present?
- Is the sidecar present and fresh?
- Is it in a model folder?
- Is it visible to Jellyfin?
- Is it visible in SpiritFlix 3001?
- Is it assigned by face-rec, manual, metadata, OCR, faceless, or unknown?
- What action is next: rescan, refresh Jellyfin, copy/build/restart 3001, confirm manually, mark faceless, deny, or no action?

## Debug/raw evidence drawer

Debug drawer may include:

- Full raw sidecar.
- OCR candidates.
- Manual decisions.
- Stale path diagnostics.
- Similarity scores.
- Quality scores.
- Generated JSON source path.
- Receipt links.

Debug drawer must not make raw evidence look like confirmed face-rec proof.

## Narrow layout checks

- Decision buttons remain visible and non-overlapping.
- Count labels wrap cleanly.
- Accepted screens dropdown is scrollable.
- Debug drawer is collapsed by default.
- Recommendation rows show path/evidence details without crowding primary actions.
