# Runtime Snapshot

- Runtime status now: `PARTIAL-GO`.
- Load: `03:56:12 up 6:49, 9 users, load average: 1.03, 1.09, 0.70`.
- Memory: `15Gi total, 6.8Gi used, 8.8Gi available; swap 1.8Gi used of 4.0Gi`.
- Source Proxy `:8787`: up/listening.
- Next `:3000`: up/listening, HTTPS lane.
- Headroom `:8797`: up/listening.
- Ollama `:11434`: up/listening.
- Jellyfin `:8096`: up/listening and container healthy.
- Failed unit: `mnt-spirit\x2dprojects.mount` still failed.
- Top CPU at snapshot: Next server about 32%, Jellyfin about 9%, face-organizer review server about 8.5%.
- Ollama `/api/ps`: no currently loaded/running models.

Raw output: `raw/10-runtime-snapshot.txt`.

Note: a Cloudflare token visible in process command lines was redacted in raw process snapshots inside this evidence packet.
