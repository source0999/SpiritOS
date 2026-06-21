# Jellyfin Scan Result

- Jellyfin health endpoint: OK before scan.
- Scan method: HTTP API `POST /Library/Refresh` to local Jellyfin.
- Scan response: HTTP 204.
- Jellyfin restart: no.
- Manual DB edit: no.
- Unrelated anime stale rows: not modified.
- After scan Jellyfin YES library paths: 353 `.mp4`, 0 `.mkv`, 0 `.ts`, 0 `.mov`, 0 `.m4v`.
- YES Folder Queue stale refs: 0.
- Active session after scan: one SpiritFlix playback session; no transcode info reported by Sessions API.
