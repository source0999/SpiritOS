# Prior Evidence Review

## Files reviewed

- docs/evidence/repo-host-cleanup-stability-audit-20260617/final-verdict.md: present
- docs/evidence/repo-host-cleanup-stability-audit-20260617/operator-summary.md: present
- docs/evidence/repo-host-cleanup-stability-audit-20260617/12-cleanup-candidates.md: present
- docs/evidence/repo-host-cleanup-stability-audit-20260617/13-do-not-touch-list.md: present
- docs/evidence/repo-host-cleanup-stability-audit-20260617/14-gitignore-and-repomix-findings.md: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/final-verdict.md: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/operator-summary.md: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/20-dirty-tree-manifest.json: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/24-task-bucket-summary.md: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/40-no-delete-cleanup-proposal.md: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/41-proposed-repomix-ignore-patch.diff.txt: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/42-proposed-archive-manifest.json: present
- docs/evidence/repo-cleanup-manifest-watchers-20260617/43-delete-candidates-hold.md: present

## Missing files

- None

## What prior audits proved

- The repo had a large but classifiable dirty tree, including active SpiritFlix S6 work, watcher/install work, Source Proxy evidence, media face-organizer artifacts, repo tooling/config changes, and generated evidence/report noise.
- Prior cleanup work was preservation-first: no delete/move/archive execution without explicit approval.
- Repomix/context bloat was a real issue and prior evidence proposed narrowing generated/raw evidence, receipts, traces, temporary outputs, backups, volumes, data folders, and build/cache directories.
- Watcher installation was previously prepared and has since been committed and installed; current baseline confirms the timer/service path is working.

## What they did not prove

- They did not prove archive/move/delete execution was approved.
- They did not repair the failed `mnt-spirit\x2dprojects.mount` unit.
- They did not resolve CasaOS, spirit-whisper, Docker healthcheck curl, or Source Proxy implementation issues.
- They did not prove that every current dirty item is safe to stage; this run refreshes that manifest.

## Forbade touching

- Media files, Jellyfin SQLite/config, service/container state, failed mount repair, active Source Proxy implementation, SpiritFlix S7 rename execution, OCR/model/VLM jobs, protected paths, and unrelated dirty files.

## Previously required approvals

- Archive/move execution, delete execution, failed mount investigation/repair, service restarts, proxy implementation work, and ambiguous ownership decisions.

## Approvals since completed

- S6 commit completed: `111d4fe9`.
- Watcher commit/install completed: `372e6c1e`; current baseline shows timer active and boot postmortem success.

## Approvals still not granted

- Archive/move execution.
- Delete execution.
- Failed mount repair.
- Service restarts.
- Proxy implementation.

## Source excerpts

### docs/evidence/repo-host-cleanup-stability-audit-20260617/final-verdict.md

```text
# Final Verdict

1. Repo cleanup readiness: **PARTIAL-GO**
2. Model storage on 8TB: **PARTIAL-GO**
3. Dell stability: **PARTIAL-GO**
4. Source Proxy/dev server runtime reliability: **NO-GO**
5. Watcher readiness: **PARTIAL-GO**

## Exact Next Approval Request for Britton

Approve a manifest-first, no-delete cleanup planning pass plus manual watcher dry-runs; separately approve any repomix ignore changes, archive/move/compress actions, and systemd/timer installs.

## Notes

- No cleanup was performed.
- No Source Proxy fixes or benchmark reruns were performed.
- No services were restarted or killed.
- Raw command output is preserved under `raw/`.


## Short Evidence Summary

- Repo raw file count is `219798`; biggest bloat classes are virtualenvs, `node_modules`, `.git`, `docs/evidence`, `.spirit-backups`, generated logs, caches, and repomix outputs.
- Model storage points to 8TB paths, but passwordless sudo could not prove `ollama` user read/write permissions, so this is `PARTIAL-GO` rather than `GO`.
- Dell/runtime drop has a strong OOM clue: `uvicorn` was killed at `2026-06-17 20:59:24 EDT`, then boot `-1` ended at `21:00:11`, and boot `0` started at `21:07:20` with an unclean jo
```

### docs/evidence/repo-host-cleanup-stability-audit-20260617/operator-summary.md

```text
# Operator Summary

Audited the SpiritOS repo, Dell host state, Ollama model storage, recent shutdown/runtime clues, Source Proxy/dev server health, and watcher readiness.

Strongest evidence:

- Repo inventory and bloat signals: `10-repo-inventory.md`, `11-bloat-map.json`, `12-cleanup-candidates.md`.
- Model storage verdict: `PARTIAL-GO` in `30-model-storage-audit.md`.
- Dell crash/runtime evidence: `40-dell-stability-audit.md`, `41-crash-signals.json`, `50-runtime-health-audit.md`.
- Watcher state/design: `60-watcher-existing-state.md`, `61-watcher-design.md`.

Likely shutdown/server-drop cause:

- Not proven unless the filtered journal evidence in `40-dell-stability-audit.md` shows a direct power, OOM, disk, thermal, GPU, or service-failure chain. The audit records suspicious signals and unknowns separately.

Top cleanup candidates:

- Closed `docs/evidence/*` proof folders for repomix exclusion or archive review.
- Generated receipt/trace/smoke/trial/debug/tmp naming classes.
- Backup/old duplicated plans only after human review.

Approval request:

Approve a manifest-first, no-delete cleanup planning pass plus manual watcher dry-runs; separately approve any repomix ignore chan
```

### docs/evidence/repo-host-cleanup-stability-audit-20260617/12-cleanup-candidates.md

```text
# Cleanup Candidates (Permission-Gated)

No cleanup commands were run. Every command below is a later proposal only and requires Britton approval.

## docs/evidence/**
- Category: Historical evidence / generated receipts
- Reason: many prior proof/evidence trees; preserve but keep out of active repomix where possible
- Evidence source: raw/10_artifact_names.txt, raw/10_top_level_counts.txt, raw/10_du_depth2.txt
- Risk level: medium
- Recommended action: ignore from repomix or move old closed evidence to archive
- Exact command that would be run later if approved: `# add approved glob to repomix ignore config: docs/evidence/**`
- Rollback plan: create a manifest and archive copy before changes; restore paths from archive or Git if tracked.
- Example paths:
```
docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-agent-trials-collapsed-default.png
docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-agent-trials-prompt-preview-expanded.png
docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-default-desktop.png
docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-mobile-default.png
docs/evidence/agent-run
```

### docs/evidence/repo-host-cleanup-stability-audit-20260617/13-do-not-touch-list.md

```text
# Do Not Touch List

These are protected for this audit unless Britton gives explicit approval later.

- `.git/`, branches, commits, staging area, worktrees.
- Application source code under `src/`, `source_proxy/`, `backend/`, active `scripts/`, tests, and configs.
- Secret-bearing files: `.env*`, certificates, tokens, credentials, private keys.
- Runtime services: Source Proxy, Next/dev server, Ollama, Docker, SearXNG, Jellyfin, tmux sessions.
- Media paths and SpiritFlix/Jellyfin data.
- `/mnt/spirit-8tb` data except read-only checks.
- Backup evidence and backup system docs until the backup source of truth is confirmed.
- Any file currently dirty in Git unless Britton identifies it as safe.

Current dirty state:

```
## master
 M README.md
 M docs/media/spiritflix-smart-tagging-rename-plan.md
 M package-lock.json
 M package.json
 M repomix.config.json
 M scripts/media-ingest-worker.mjs
 M scripts/media/face_enrolled_performers.html
 M scripts/media/face_enrolled_performers.json
 M scripts/media/face_enrollment_queue.html
 M scripts/media/face_enrollment_queue.json
 M scripts/media/face_gallery.html
 M scripts/media/face_gallery.json
 M scripts/media/face_organizer.py
 M scripts/
```

### docs/evidence/repo-host-cleanup-stability-audit-20260617/14-gitignore-and-repomix-findings.md

```text
# Gitignore and Repomix Findings

## Inspected Files and Scripts

```
===== .gitignore
# ── Spirit OS - ignore build noise, secrets, and fat artifacts ─────────────────
.DS_Store
node_modules
.venv-source-proxy
.venv-source-proxy-windows
.venv/
.venv
.venv-*/
**/.venv/
__pycache__/
*.py[cod]
.next
.next.backup-*/
out
*.tsbuildinfo
.env.local
.claude/settings.local.json
npm-debug.log*
yarn-debug.log*
yarn-error.log*

oldSpiritOS.xml
models/
*.gguf
backend/.env
backend/**/*.log
data/source-proxy/*.json
.cursor/

certificates

# ── SpiritOS AI / temp / generated junk (post-cleanup) ─────────────────────
/attaches
/can
/concrete
/correct
/dev_commands
/does
/file
/hardware
/next
/Oracle
/POST
/probe
/routes
/see
/tool
/typo
/vague
SPIRIT_ENABLE_DEV_COMMAND_TOOLS=false
spirit_oracle_fairy_demo.*
spiritos_dashboard_finished_demo*
spirit-os@*

# Repomix outputs (never commit)
repomix-output*.xml
repomix-output*.ast*

# Heavy local media and archives. Keep source assets outside git unless a
# future commit explicitly uses Git LFS or another reviewed storage path.
*.mp4
*.mov
*.m4v
*.avi
*.mkv
*.webm
*.zip
*.7z
*.rar
*.tar
*.tar.gz
*.tgz

# Common temp
*.log
*.tmp
OIWWJQ~A
I8JTCW~Z
OV31EM~O
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/final-verdict.md

```text
# Final Verdict

1. Dirty tree split verdict: PARTIAL-GO
2. Cleanup readiness: PARTIAL-GO
3. Watcher dry-run verdict: PARTIAL-GO
4. Runtime current status: PARTIAL-GO

## Recommended Independent Approval Prompts
- A. approve repomix ignore patch only
- B. approve archive/move manifest only
- C. approve watcher install only
- D. approve service restart/recovery only
- E. approve SpiritFlix S6 closeout/test run only
- F. approve media/face organizer closeout only

## Stop Line
Stop here. No cleanup, ignore changes, archive/move/compress actions, watcher installs, or service restarts are approved by this packet.
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/operator-summary.md

```text
# Operator Summary

- evidence root: `docs/evidence/repo-cleanup-manifest-watchers-20260617`
- dirty/untracked files classified: 207
- top buckets: F=91, G=51, A=17, C=16, H=13, E=7
- runtime currently down or uncertain: yes; see `51-runtime-current-status.md` and raw watcher outputs
- watcher drafts ready: yes, drafts only and not installed

Next approval request: choose exactly one independent approval from `final-verdict.md` before any actual cleanup or runtime change.
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/20-dirty-tree-manifest.json

```text
{
  "generated_at": "2026-06-17T22:15:47.010712",
  "repo": "/home/source/SpiritOS",
  "head": "158b489fcf813a701f8a7a1bf3f8be5770511448",
  "items": [
    {
      "path": "README.md",
      "git_status_code": " M",
      "bucket": "J",
      "bucket_name": "Unknown / needs Britton decision",
      "reason": "Tracked project file outside the named active buckets; requires focused review.",
      "risk": "medium",
      "likely_owner_task": "unknown/project docs or app shell",
      "safe_immediate_action": "needs Britton decision",
      "exact_command_later_if_approved": "git diff -- README.md",
      "rollback_idea": "No action without explicit decision.",
      "numstat": {
        "added": "30",
        "deleted": "12"
      }
    },
    {
      "path": "docs/media/spiritflix-smart-tagging-rename-plan.md",
      "git_status_code": " M",
      "bucket": "A",
      "bucket_name": "SpiritFlix S6 smart tagging active work",
      "reason": "SpiritFlix admin smart-tagging / rename-preview surface.",
      "risk": "high",
      "likely_owner_task": "SpiritFlix S6 smart tagging",
      "safe_immediate_action": "keep as-is",
      "exact_command_later_if_approved": "git add -- docs/med
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/24-task-bucket-summary.md

```text
# Task Bucket Summary

- total classified items: 207
- modified/tracked items: 34
- untracked items: 173

- A - SpiritFlix S6 smart tagging active work: 17
- B - Media/face organizer active work: 2
- C - Source Proxy audit/evidence: 16
- D - Source Proxy FIP receipt or generated trace/evidence: 5
- E - Repo tooling / repomix / headroom / runtime helper: 7
- F - Backup/system evidence: 91
- G - New cleanup audit evidence: 51
- H - Generated UI/report artifact: 13
- I - Config/package/dependency change: 3
- J - Unknown / needs Britton decision: 2
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/40-no-delete-cleanup-proposal.md

```text
# No-Delete Cleanup Proposal

No commands in this proposal have been executed.

## Level A: Repomix Ignore Candidates Only
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/`
- `docs/evidence/source-proxy-glm-3x10-audit-20260617/`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/*.json`
- `docs/evidence/repo-cleanup-manifest-watchers-20260617/`
- `scripts/media/*.html`
- `scripts/media/*_report.json`
- `scripts/media/face_*_queue.json`
- `scripts/media/face_*_performers.json`
- `scripts/media/face_gallery.json`
- `scripts/media/known_db_audit.json`
- `scripts/media/performer_verification.json`
- `scripts/media/model_index.json`

## Level B: Archive/Move Candidates
Candidate generated evidence/reports could later move to `/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617/` after approval. Do not move now. See `42-proposed-archive-manifest.json`.

## Level C: Delete Candidates
None approved yet. No delete candidate is recommended in Phase 1B because current evidence is not enough to prove stale, duplicated, generated, and recoverable status for every file.
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/41-proposed-repomix-ignore-patch.diff.txt

```text
diff --git a/repomix.config.json b/repomix.config.json
--- a/repomix.config.json
+++ b/repomix.config.json
@@ PROPOSED ONLY - DO NOT APPLY @@
+// Proposed ignore additions only; translate into the existing repomix ignore/exclude shape after approval.
+docs/evidence/repo-host-cleanup-stability-audit-20260617/
+docs/evidence/source-proxy-glm-3x10-audit-20260617/
+docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/*.json
+docs/evidence/repo-cleanup-manifest-watchers-20260617/
+scripts/media/*.html
+scripts/media/*_report.json
+scripts/media/face_*_queue.json
+scripts/media/face_*_performers.json
+scripts/media/face_gallery.json
+scripts/media/known_db_audit.json
+scripts/media/performer_verification.json
+scripts/media/model_index.json
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/42-proposed-archive-manifest.json

```text
{
  "not_executed": true,
  "archive_root": "/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617",
  "items": [
    {
      "path": "scripts/media/face_enrolled_performers.html",
      "bucket": "H",
      "reason": "Generated media/face organizer report artifact.",
      "proposed_destination": "/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617/scripts/media/face_enrolled_performers.html",
      "proposed_command_not_executed": "mkdir -p /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617/scripts/media && mv -- scripts/media/face_enrolled_performers.html /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617/scripts/media/face_enrolled_performers.html",
      "rollback_not_executed": "mkdir -p scripts/media && mv -- /mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617/scripts/media/face_enrolled_performers.html scripts/media/face_enrolled_performers.html"
    },
    {
      "path": "scripts/media/face_enrolled_performers.json",
      "bucket": "H",
      "reason": "Generated media/face organizer report artifact.",
      "proposed_destination": "/mnt/spirit-8tb/spiritos-archives/repo-cleanup-20260617/scripts/media/face_enrolled_performers.json",
      "proposed_co
```

### docs/evidence/repo-cleanup-manifest-watchers-20260617/43-delete-candidates-hold.md

```text
# Delete Candidates Hold

None approved yet. Phase 1B recommends no deletion.
```