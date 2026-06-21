# Log Findings Last 60 Minutes

- OOM / killed process signature: not found. The grep section header matched the word `oom`, but there were no actual OOM/killed-process lines in the last-60-minute journal output.
- Source Proxy / uvicorn crash: not found.
- Next crash: not found.
- CasaOS crash: found. `casaos.service` logged `fatal error: found pointer to free object` at 03:46:18 and systemd recorded `Failed with result 'exit-code'`; it restarted immediately.
- Mount issue: persistent failed unit `mnt-spirit\x2dprojects.mount`; CasaOS also logged storage check messages.
- Docker issue: repeated healthcheck errors for one container because `curl` is missing inside that container, plus `copy stream failed`; Docker service itself remained active.
- Jellyfin: container was up and healthy.
- Ollama: service active; `/api/ps` showed no loaded model, so no active model memory pressure at snapshot time.
- Network/Tailscale: endpoint churn logs present, but `tailscale status` showed the Windows desktop active/direct and the Fold idle.
- Thermal: CasaOS reported finding the CPU thermal zone; no overheating/throttle message was found in the sampled lines.

Raw outputs:

- `raw/30-journal-last-60m.txt`
- `raw/31-boot-history.txt`
