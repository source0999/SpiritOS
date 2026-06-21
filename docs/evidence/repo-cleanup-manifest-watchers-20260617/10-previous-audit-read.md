# Previous Audit Read

## Files Checked

- `docs/evidence/repo-host-cleanup-stability-audit-20260617/index.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/final-verdict.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/operator-summary.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/12-cleanup-candidates.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/13-do-not-touch-list.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/30-model-storage-audit.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/40-dell-stability-audit.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/50-runtime-health-audit.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/61-watcher-design.md`: present
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/62-approval-needed-next-actions.md`: present

## What Prior Audit Proved
- Repo cleanup readiness, model storage, Dell stability, and watcher readiness were partial rather than complete approvals.
- Source Proxy / Next runtime reliability was explicitly not ready; downtime and OOM evidence were part of the prior packet.
- Ollama model storage appeared routed to `/mnt/spirit-8tb/ollama-models`, but sudo proof as the `ollama` user remained blocked.

## What Remains Unknown
- Whether runtime services have recovered since the audit.
- Whether dirty-tree files are active work, generated artifacts, or candidates for ignore/archive until this manifest classifies them.
- Whether watcher installation is approved; this packet only drafts watcher files.

## Explicit Do Not Touch / Approval Themes
- Do not clean, delete, move, archive, restart, or install without separate Britton approval.
- Treat SpiritFlix S6 and media/face-organizer work as active until separately closed out.
- Keep generated evidence and runtime helper changes separate from product implementation.

## Exact Next Approvals Requested By Prior Packet
- Cleanup approval.
- Watcher approval.
- Runtime recovery/service restart approval.
- Follow-up proof for model storage and runtime stability.

## Evidence Snippets
### index.md
- # Repo Host Cleanup Stability Audit 2026-06-17
- - `12-cleanup-candidates.md`
- - `13-do-not-touch-list.md`
- - `50-runtime-health-audit.md`
- - `60-watcher-existing-state.md`
- - `61-watcher-design.md`
- - `62-approval-needed-next-actions.md`
- This audit created report files only under this evidence folder. It did not clean, delete, move, archive, stage, commit, reset, restart, kill, patch source code, install watchers, or change services.
### final-verdict.md
- 1. Repo cleanup readiness: **PARTIAL-GO**
- 2. Model storage on 8TB: **PARTIAL-GO**
- 3. Dell stability: **PARTIAL-GO**
- 4. Source Proxy/dev server runtime reliability: **NO-GO**
- 5. Watcher readiness: **PARTIAL-GO**
- ## Exact Next Approval Request for Britton
- Approve a manifest-first, no-delete cleanup planning pass plus manual watcher dry-runs; separately approve any repomix ignore changes, archive/move/compress actions, and systemd/timer installs.
- - No cleanup was performed.
- - Model storage points to 8TB paths, but passwordless sudo could not prove `ollama` user read/write permissions, so this is `PARTIAL-GO` rather than `GO`.
- - Dell/runtime drop has a strong OOM clue: `uvicorn` was killed at `2026-06-17 20:59:24 EDT`, then boot `-1` ended at `21:00:11`, and boot `0` started at `21:07:20` with an unclean journal warning.
### operator-summary.md
- Audited the SpiritOS repo, Dell host state, Ollama model storage, recent shutdown/runtime clues, Source Proxy/dev server health, and watcher readiness.
- - Repo inventory and bloat signals: `10-repo-inventory.md`, `11-bloat-map.json`, `12-cleanup-candidates.md`.
- - Model storage verdict: `PARTIAL-GO` in `30-model-storage-audit.md`.
- - Dell crash/runtime evidence: `40-dell-stability-audit.md`, `41-crash-signals.json`, `50-runtime-health-audit.md`.
- - Watcher state/design: `60-watcher-existing-state.md`, `61-watcher-design.md`.
- Likely shutdown/server-drop cause:
- - Not proven unless the filtered journal evidence in `40-dell-stability-audit.md` shows a direct power, OOM, disk, thermal, GPU, or service-failure chain. The audit records suspicious signals and unknowns separately.
- Top cleanup candidates:
- Approval request:
- Approve a manifest-first, no-delete cleanup planning pass plus manual watcher dry-runs; separately approve any repomix ignore changes, archive/move/compress actions, and systemd/timer installs.
- The Dell did not merely have an app hiccup: the journal shows an OOM kill of `uvicorn` immediately before the previous boot ended, followed by an unclean reboot window. Source Proxy and the Next/dev server were still down when audited. Olla
### 12-cleanup-candidates.md
- # Cleanup Candidates (Permission-Gated)
- No cleanup commands were run. Every command below is a later proposal only and requires Britton approval.
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-agent-trials-collapsed-default.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-agent-trials-prompt-preview-expanded.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-default-desktop.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-mobile-default.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-running-ui-local-state.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/blocked-copy-issue-report.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/closeout.md
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/default-desktop-widget.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/expanded-prompt-queue.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/final-ui-cleanup-2026-05-28.md
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-1.2-default-desktop.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-2.1-agent-trials-open.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-2.2-agent-trials-command-compact.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.1-prompt-preview-collapsed.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.1-prompt-preview-expanded.png
- docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.2-desktop-scroll.png
### 13-do-not-touch-list.md
- # Do Not Touch List
- These are protected for this audit unless Britton gives explicit approval later.
- - Runtime services: Source Proxy, Next/dev server, Ollama, Docker, SearXNG, Jellyfin, tmux sessions.
-  M scripts/runtime-port-guard.sh
- ?? docs/evidence/repo-host-cleanup-stability-audit-20260617/
### 30-model-storage-audit.md
- Verdict: **PARTIAL-GO**
- ## Ollama Path Resolution
- `/usr/share/ollama/.ollama` resolves to:
- /mnt/spirit-8tb/ollama-models
- `/usr/share/ollama/.ollama/models` resolves to:
- /mnt/spirit-8tb/ollama-models/models
- 0	/usr/share/ollama/.ollama
- 88K	/mnt/spirit-8tb/ollama-models/models/manifests
- 34G	/mnt/spirit-8tb/ollama-models
- 34G	/mnt/spirit-8tb/ollama-models/models
- 34G	/mnt/spirit-8tb/ollama-models/models/blobs
- ## Runtime Configuration
- User=ollama
- FragmentPath=/etc/systemd/system/ollama.service
- # /etc/systemd/system/ollama.service
- Description=Ollama Service
- ExecStart=/usr/local/bin/ollama serve
- User=ollama
### 40-dell-stability-audit.md
- Jun 17 20:58:20 source-server kernel: python invoked oom-killer: gfp_mask=0x140cca(GFP_HIGHUSER_MOVABLE|__GFP_COMP), order=0, oom_score_adj=0
- Jun 17 21:47:32 source-server sudo[24502]:   source : a password is required ; PWD=/home/source/SpiritOS ; USER=ollama ; COMMAND=/usr/bin/test -r /mnt/spirit-8tb/ollama-models
- Jun 17 21:47:32 source-server sudo[24513]:   source : a password is required ; PWD=/home/source/SpiritOS ; USER=ollama ; COMMAND=/usr/bin/test -w /mnt/spirit-8tb/ollama-models
- Jun 17 21:11:43 source-server dockerd[2004]: time="2026-06-17T21:11:43.845279280-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec fail
- Jun 17 21:11:43 source-server casaos-app-management[6499]: 2026-06-17T21:11:43.934-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.jellyseerr.device
- Jun 17 21:11:45 source-server casaos-app-management[6499]: 2026-06-17T21:11:45.343-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.medusa.cap_add mu
- Jun 17 21:11:55 source-server casaos-app-management[6499]: 2026-06-17T21:11:55.337-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.trilium.cap_add m
- Jun 17 21:11:55 source-server casaos-app-management[6499]: 2026-06-17T21:11:55.563-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.twingate-connecto
- Jun 17 21:11:57 source-server casaos-app-management[6499]: 2026-06-17T21:11:57.223-0400        info        appstore size changed, update app store        {"url": "https://casaos.app/store/main.zip", "func": "service.(*appStore).UpdateCatalo
- Jun 17 21:11:57 source-server casaos-app-management[6499]: 2026-06-17T21:11:57.809-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "parsing : yaml: unmarshal errors:\n  li
- Jun 17 21:11:58 source-server casaos-app-management[6499]: 2026-06-17T21:11:58.202-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.psitransfer.ports
- Jun 17 21:12:13 source-server dockerd[2004]: time="2026-06-17T21:12:13.898774896-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec fail
- Jun 17 21:12:14 source-server casaos-app-management[6499]: 2026-06-17T21:12:14.434-0400        info        appstore size changed, update app store        {"url": "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master
- Jun 17 21:12:15 source-server casaos-app-management[6499]: 2026-06-17T21:12:15.293-0400        info        failed to parse compose app - contact the contributor of this app to fix it        {"error": "validating : services.redis.healthcheck
- Jun 17 21:12:43 source-server dockerd[2004]: time="2026-06-17T21:12:43.952547328-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec fail
- Jun 17 21:13:14 source-server dockerd[2004]: time="2026-06-17T21:13:14.023871600-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec fail
- Jun 17 21:13:27 source-server casaos[1518]: 2026-06-17T21:13:27.023-0400        info        CPU thermal zone found: x86_pkg_temp, path: /sys/devices/virtual/thermal/thermal_zone3.        {"func": "service.GetCPUThermalZone", "file": "/home/
- Jun 17 21:13:44 source-server dockerd[2004]: time="2026-06-17T21:13:44.092120428-04:00" level=warning msg="Health check for container 892c03f267e642503edabbdd3a17dd78e410aea368697db793ca020a3d39169e error: OCI runtime exec failed: exec fail
### 50-runtime-health-audit.md
- # Runtime Health Audit
- source      4824  1.4  0.6 11814816 104320 ?     Sl   21:10   0:37 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/ou
- ollama      1448  0.0  0.1 2160960 21088 ?       Ssl  21:08   0:00 /usr/local/bin/ollama serve
- root        1437  0.0  0.1 109688 17452 ?        Ssl  21:08   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
- source      4824  1.4  0.6 11814816 104320 ?     Sl   21:10   0:37 /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/node /home/source/.cursor-server/bin/linux-x64/5702c9cfca656d8710fad58402fe37f14345e3a0/ou
- ● ollama.service - Ollama Service
-      Loaded: loaded (/etc/systemd/system/ollama.service; enabled; preset: enabled)
-    Main PID: 1448 (ollama)
-      CGroup: /system.slice/ollama.service
-              └─1448 /usr/local/bin/ollama serve
- Jun 17 21:08:29 source-server ollama[1448]: time=2026-06-17T21:08:29.861-04:00 level=INFO source=runner.go:67 msg="discovering available GPUs..."
- Jun 17 21:08:29 source-server ollama[1448]: time=2026-06-17T21:08:29.904-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 38321"
- Jun 17 21:08:50 source-server ollama[1448]: time=2026-06-17T21:08:47.032-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 36023"
- Jun 17 21:09:04 source-server ollama[1448]: time=2026-06-17T21:09:04.909-04:00 level=INFO source=runner.go:106 msg="experimental Vulkan support disabled.  To enable, set OLLAMA_VULKAN=1"
- Jun 17 21:09:04 source-server ollama[1448]: time=2026-06-17T21:09:04.909-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 35011"
- Jun 17 21:09:04 source-server ollama[1448]: time=2026-06-17T21:09:04.909-04:00 level=INFO source=server.go:444 msg="starting runner" cmd="/usr/local/bin/ollama runner --ollama-engine --port 43967"
- Jun 17 21:09:05 source-server ollama[1448]: time=2026-06-17T21:09:05.158-04:00 level=INFO source=types.go:42 msg="inference compute" id=GPU-bd0daa29-1aa2-b006-4f01-a3b10d85b36a filter_id="" library=CUDA compute=8.6 name=CUDA0 description="N
- Jun 17 21:09:05 source-server ollama[1448]: time=2026-06-17T21:09:05.158-04:00 level=INFO source=routes.go:1860 msg="vram-based default context" total_vram="12.0 GiB" default_num_ctx=4096
### 61-watcher-design.md
- # Watcher Design
- No watchers were installed. This is an approval-gated design only.
- - Approval needed: approval to add script/config and install timer
- - Purpose: checks Source Proxy, Next, Ollama, Docker, SearXNG, and Jellyfin when applicable
- - Approval needed: approval to define service list and alert behavior
- - Approval needed: approval to install boot-time unit
- - Purpose: verifies Ollama paths resolve under /mnt/spirit-8tb and alerts on OS-disk model storage
- - Approval needed: approval to install timer and choose alert channel
- - Approval needed: approval to add repo script/config and timer
### 62-approval-needed-next-actions.md
- # Approval Needed Next Actions
- 3. Approve or reject writing watcher scripts/configs under repo docs/ops or scripts.
- No cleanup, service change, watcher install, restart, delete, move, stage, commit, push, reset, checkout, prune, archive, or source patch was performed in this audit.
