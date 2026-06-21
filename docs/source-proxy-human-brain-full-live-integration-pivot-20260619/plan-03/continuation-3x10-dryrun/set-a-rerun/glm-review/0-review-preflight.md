# Stage 0 — Review Preflight

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.
Host: Dell/source-server win32 review seat (Z:\ SpiritOS checkout). NOTE: this review seat is NOT the Linux server where the run executed; see environment caveat below.

## Environment

- `pwd`: `Z:\` (SpiritOS repo root)
- current HEAD: `e527563c266726ab97eb099e1a32032a9dd11064` (`fix: ground SpiritFlix smart tags in reliable frames`)
- branch: `master`
- staged files count: **0** (`git diff --cached --name-status` empty)
- dirty source_proxy files: **0** (no `source_proxy/` entries in `git diff --name-status`)
- dirty set-a-rerun files: **0** (no `set-a-rerun` entries in `git diff --name-status`)

The working tree does carry pre-existing, unrelated SpiritFlix/handoff/media dirt (e.g. `docs/handoff/spiritflix-llm-pack/*`, `scripts/media/*`, `package-lock.json`). These are NOT part of the Set A rerun and were neither created nor modified by this review. None were staged. None were touched.

## Raw evidence files found

**0 raw provider evidence files are present on this review seat.**

- `set-a-rerun/*.raw.json`: **none exist** in the repo tree.
- `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/` (the `raw_evidence_dir` every record points at): **does not exist** on this win32 host (`No such file or directory`).

The rerun records were generated on the Linux source-server and reference raw evidence under `/home/source/spiritos-evidence/`. That directory is the operator's raw-evidence store and is not checked into the repo, and is not mounted on this review seat. This review therefore **cannot independently re-read** `A1.research.raw.json`, `A2.model.attempt*.raw.json`, `A2.grader.attempt*.raw.json`, `A2.task.final.raw.json`, `A5.mac.raw.json`, etc.

This is a real, scoping limitation: the in-repo artifacts (`A*.json`, `A*.md`, `_stage4r_runner.py`, control docs) plus the runner source are the only directly inspectable evidence. Where a verdict depends on raw provider bytes, it is marked accordingly and cannot be fully confirmed by GLM from this seat.

## Records present (in-repo)

All 10 rerun records present, no A1-A10 missing:
- `A1.md`/`A1.json` … `A10.md`/`A10.json`
- control files: `0-set-a-rerun-preflight.md`, `1-prior-generator-disqualified.md`, `2-real-harness-readiness.md`, `4r-fix-preflight.md`, `4r-fix-runner-change.md`, `4r-fix-validation.md`, `6-test-results.md`, `7-stage4r-verdict.md`, `failure-buckets.md`, `summary.md`, `summary.json`, `_stage4r_runner.py` (+ `__pycache__`)

## Review-only scope confirmation

- Review only. No source patches.
- No Source Proxy runtime mutation.
- No Set A rerun, no Set B, no Set C, no Stage 5, no Plan 4.
- No staging, no commit, no push.
- No media/Jellyfin/SpiritFlix mutation.
- All writes confined to `set-a-rerun/glm-review/`.

## Method note

Because raw provider evidence is unreachable from this seat, this review leans on: (a) the runner source (which fully reveals how every boolean and gate is computed), (b) the final work-product text in each `A*.md` (which reveals whether research actually shaped the recommendation), and (c) the grader logic reproduced locally. The runner is the single most powerful artifact here: it is the exact code that produced the records, so its behavior is verifiable without the raw bytes. Several pass-invalidating findings below come directly from the runner + work-product text, not from raw provider reads, so they hold regardless of the missing raw store.
