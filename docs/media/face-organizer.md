# Media Face Organizer v1

Local, GPU-first face detection and performer recognition for `/mnt/spirit-8tb/media/other`.

## Install

On the media host:

```bash
pip install insightface "onnxruntime-gpu[cuda,cudnn]" numpy pillow opencv-python-headless tqdm
```

Optional:

```bash
pip install rich
```

The script uses `ffmpeg` and `ffprobe` from `PATH`.

## Files

- Main CLI: `scripts/media/face_organizer.py`
- Known performer DB: `scripts/media/known_performers/`
- Verification report: `scripts/media/face_verification_report.html`
- Sidecar metadata: next to each video as `video.mp4.face-meta.json`
- Optional Jellyfin NFO: next to each video as `video.mp4.nfo`

## First Run

Initialize the local performer DB:

```bash
python scripts/media/face_organizer.py --init-db
```

Dry-run a tiny scan:

```bash
python scripts/media/face_organizer.py --source /mnt/spirit-8tb/media/other --sample-limit 3
```

Actually write sidecar metadata and review crops:

```bash
python scripts/media/face_organizer.py --source /mnt/spirit-8tb/media/other --sample-limit 3 --apply
```

Generate the report:

```bash
python scripts/media/face_organizer.py --source /mnt/spirit-8tb/media/other --report
```

On the Dell server, use the venv Codex installed:

```bash
cd /home/source/SpiritOS
. .venv-face-organizer/bin/activate
python scripts/media/face_organizer.py --source /DATA/yes --sample-limit 3 --apply --ctx-id -1
python scripts/media/face_organizer.py --source /DATA/yes --report
```

Write Jellyfin NFO files too:

```bash
python scripts/media/face_organizer.py --source /mnt/spirit-8tb/media/other --apply --write-nfo
```

## Confidence Rules

- `similarity >= 0.80`: clean performer name, no verification flag.
- `0.55 <= similarity < 0.80`: `possible: Name (XX% confidence) - verification needed`.
- `similarity < 0.55` or no known DB match: `unknown performer - verification needed`.
- Multiple strong faces are preserved. When no strong match exists, the top two possible matches are shown.

Every performer entry stores the raw similarity and model version so thresholds can be tuned later.

## Confirming New Performers

When a face crop in the report is correct, add it to the DB:

```bash
python scripts/media/face_organizer.py --add-performer "Real Name" --face-image "/path/to/crop.jpg" --apply
```

Then rescan with `--force` so future videos use the updated embedding index:

```bash
python scripts/media/face_organizer.py --source /mnt/spirit-8tb/media/other --force --apply
```

## Metadata Hints

The organizer can add candidate-name hints without trusting them as face IDs:

```bash
python scripts/media/face_organizer.py --source /DATA/yes --enrich-metadata --apply
```

This currently uses local filename/folder parsing by default. Numeric filenames such as `(19).MP4` will usually produce no useful hint, which is better than inventing a name. Online provider hooks are intentionally credential-gated:

```bash
PAPI_RAPIDAPI_KEY=... python scripts/media/face_organizer.py --source /DATA/yes --enrich-metadata --online-metadata --apply
```

The boundary is deliberate: internet metadata can suggest names, but only a user-confirmed local face crop should enter `known_performers`.

## Smart Rename Plan

Generate a review-only rename manifest:

```bash
python scripts/media/face_organizer.py --source /DATA/yes --rename-plan --apply
```

Output:

```text
scripts/media/rename_plan.json
```

The manifest proposes names from the best available signal:

- confirmed high-confidence face match
- metadata hint
- fallback `Unknown Performer`

It does not rename, move, delete, or overwrite videos. Entries are marked `safe_to_apply: false` until a future reviewed rename mode is added.

## Backups

Any new write mode backs up the existing sidecars, known performer DB, and current report first:

```text
scripts/media/backups/YYYYMMDDTHHMMSSZ/backup_manifest.json
```

To make an explicit backup:

```bash
python scripts/media/face_organizer.py --source /DATA/yes --backup-state --apply
```

To copy selected videos too:

```bash
python scripts/media/face_organizer.py --source /DATA/yes --backup-state --backup-videos --sample-limit 3 --apply
```

Do not use `--backup-videos` without a `--sample-limit` unless you really intend to copy the whole selected library.

## Environment Overrides

- `FACE_ORGANIZER_SOURCE`: default source directory.
- `FACE_ORGANIZER_DB`: default DB directory.
- `FACE_ORGANIZER_REPORT`: default report output path.
- `FACE_ORGANIZER_MODEL`: default InsightFace model, currently `buffalo_l`.

## Example Metadata

```json
{
  "schema": "media-face-organizer/v1",
  "video_path": "/mnt/spirit-8tb/media/other/example.mp4",
  "generated_at": "2026-06-04T20:00:00+00:00",
  "dry_run": false,
  "verification_needed": true,
  "performers": [
    {
      "id": "example-name",
      "name": "Example Name",
      "confidence": 0.7342,
      "similarity": 0.7342,
      "status": "possible",
      "verification_needed": true,
      "label": "possible: Example Name (73% confidence) - verification needed",
      "face_crop_path": "/mnt/spirit-8tb/media/other/.face-review/example/frame-03-face-01.jpg",
      "original_frame_path": "/mnt/spirit-8tb/media/other/.face-review/example/frame-03.jpg",
      "bbox": [192.0, 84.0, 420.0, 390.0],
      "detection_score": 0.9821,
      "model_version": "insightface:buffalo_l",
      "supporting_faces": 3
    }
  ],
  "metadata_hints": {
    "generated_at": "2026-06-05T01:09:47+00:00",
    "status": "candidate_hints_only",
    "candidate_names": [],
    "providers": {
      "filename": { "enabled": true },
      "papi": { "enabled": false, "configured": false }
    },
    "biometric_boundary": "Internet metadata is not imported as face identity. Confirm a local crop before adding embeddings."
  },
  "suggested_organization": {
    "eligible": false,
    "strategy": "none",
    "target_dir": null,
    "reason": "requires verification or has too many/too few high-confidence performers"
  },
  "frames_analyzed": 6,
  "faces_detected": 5,
  "duration_seconds": 728.4,
  "processing_time_seconds": 31.8,
  "model_version": "insightface:buffalo_l",
  "thresholds": {
    "auto": 0.8,
    "possible": 0.55
  }
}
```

## Organization Boundary

The script calculates `suggested_organization`, but actual move/symlink behavior is not implemented yet. That is intentional: file organization needs explicit permission before code is added or tested against real media.
