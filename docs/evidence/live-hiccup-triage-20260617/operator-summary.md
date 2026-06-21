# Operator Summary

- Runtime status now: `PARTIAL-GO`.
- Hiccup cause: `POSSIBLE`, not confirmed.
- Watcher coverage: `DRAFTS_ONLY`.
- Immediate risk: `MEDIUM`.
- Source Proxy `:8787`: up/listening; `/docs` HTTP 200 in 0.005s and `/openapi.json` HTTP 200 in 0.265s.
- Next `:3000`: up/listening; HTTPS `/spiritflix/admin` HTTP 200 in 0.100s. Plain HTTP returns empty reply because the lane is HTTPS.
- OOM in last 60m: no actual OOM/killed-process line found.
- Logs do show a CasaOS crash/restart at 03:46:18, persistent failed `mnt-spirit\x2dprojects.mount`, repeated Docker healthcheck errors for a container missing `curl`, and an unhealthy `spirit-whisper` container.
- Ollama pressure: no loaded model in `/api/ps`; `/api/tags` responded in 0.001s.
- Tailscale: endpoint churn logs, but status showed active/direct desktop connectivity.

Recommended next approval: `A. install safe read-only watchers`. If slowness repeats, approve `C. investigate OOM/memory pressure deeper`; this snapshot does not prove a fresh OOM.
